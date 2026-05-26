import asyncio
import logging
from datetime import date, datetime, timezone

import feedparser
import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"
USER_AGENT = "Prism/0.1 (https://github.com/priyanshupg2/daily_news_feed)"
CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]
MAX_RESULTS = 50
POLITE_DELAY_SECONDS = 3


class ArxivSource:
    source_name = "arxiv"

    async def fetch(self) -> list[RawItem]:
        search_query = "+OR+".join(f"cat:{c}" for c in CATEGORIES)
        params = {
            "search_query": search_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(MAX_RESULTS),
        }

        try:
            async with httpx.AsyncClient(
                timeout=30.0, headers={"User-Agent": USER_AGENT}
            ) as client:
                response = await client.get(ARXIV_API, params=params)
                response.raise_for_status()
                body = response.text
        except Exception:
            logger.exception("arXiv fetch failed")
            await asyncio.sleep(POLITE_DELAY_SECONDS)
            return []

        items: list[RawItem] = []
        today = date.today()
        cutoff = datetime.now(timezone.utc).timestamp() - 24 * 3600

        feed = feedparser.parse(body)
        for entry in feed.entries:
            try:
                raw_id = entry.id
                # e.g. http://arxiv.org/abs/2401.12345v1 -> 2401.12345, v1
                tail = raw_id.rsplit("/", 1)[-1]
                version = "v1"
                if "v" in tail:
                    arxiv_id, _, ver = tail.rpartition("v")
                    if ver.isdigit():
                        version = f"v{ver}"
                    else:
                        arxiv_id = tail
                else:
                    arxiv_id = tail

                published_struct = getattr(entry, "published_parsed", None)
                if published_struct is None:
                    continue
                published_at = datetime(*published_struct[:6], tzinfo=timezone.utc)

                if published_at.timestamp() < cutoff:
                    continue

                categories: list[str] = []
                primary = getattr(entry, "arxiv_primary_category", None)
                if primary and isinstance(primary, dict) and primary.get("term"):
                    categories.append(primary["term"])
                for tag in getattr(entry, "tags", []) or []:
                    term = tag.get("term") if isinstance(tag, dict) else None
                    if term and term not in categories:
                        categories.append(term)

                authors = ", ".join(
                    a.get("name", "") for a in getattr(entry, "authors", []) or []
                ).strip(", ") or None

                url = None
                for link in getattr(entry, "links", []) or []:
                    if link.get("rel") == "alternate":
                        url = link.get("href")
                        break
                if url is None:
                    url = getattr(entry, "link", None)

                summary = getattr(entry, "summary", "") or ""
                content = " ".join(summary.split()) or None

                items.append(
                    RawItem(
                        id=f"arxiv:{arxiv_id}",
                        source=self.source_name,
                        source_id=arxiv_id,
                        title=" ".join(entry.title.split()),
                        url=url,
                        content=content,
                        authors=authors,
                        published_at=published_at,
                        fetch_date=today,
                        metadata={"categories": categories, "version": version},
                    )
                )
            except Exception:
                logger.exception("Failed to parse arXiv entry")

        await asyncio.sleep(POLITE_DELAY_SECONDS)
        return items
