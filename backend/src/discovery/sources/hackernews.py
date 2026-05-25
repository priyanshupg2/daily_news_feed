import logging
from datetime import date, datetime, timezone

import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

HN_API = "http://hn.algolia.com/api/v1/search_by_date"
USER_AGENT = "Prism/0.1 (https://github.com/priyanshupg2/daily_news_feed)"
MIN_POINTS = 50
HITS_PER_PAGE = 50


class HackerNewsSource:
    source_name = "hackernews"

    async def fetch(self) -> list[RawItem]:
        unix_24h_ago = int(datetime.now(timezone.utc).timestamp()) - 24 * 3600
        params = {
            "tags": "story",
            "numericFilters": f"created_at_i>{unix_24h_ago},points>{MIN_POINTS}",
            "hitsPerPage": str(HITS_PER_PAGE),
        }

        try:
            async with httpx.AsyncClient(
                timeout=30.0, headers={"User-Agent": USER_AGENT}
            ) as client:
                response = await client.get(HN_API, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            logger.exception("HackerNews fetch failed")
            return []

        items: list[RawItem] = []
        today = date.today()

        for hit in payload.get("hits", []) or []:
            try:
                object_id = str(hit.get("objectID") or "")
                if not object_id:
                    continue

                hn_url = f"https://news.ycombinator.com/item?id={object_id}"
                story_url = hit.get("story_url") or hit.get("url")
                url = story_url or hn_url

                story_text = hit.get("story_text")
                content = story_text if not story_url else None

                created_at = hit.get("created_at")
                published_at = None
                if created_at:
                    try:
                        published_at = datetime.fromisoformat(
                            created_at.replace("Z", "+00:00")
                        )
                    except ValueError:
                        created_i = hit.get("created_at_i")
                        if created_i is not None:
                            published_at = datetime.fromtimestamp(
                                int(created_i), tz=timezone.utc
                            )

                title = hit.get("title") or hit.get("story_title") or ""
                if not title:
                    continue

                items.append(
                    RawItem(
                        id=f"hackernews:{object_id}",
                        source=self.source_name,
                        source_id=object_id,
                        title=title,
                        url=url,
                        content=content,
                        authors=hit.get("author"),
                        published_at=published_at,
                        fetch_date=today,
                        metadata={
                            "points": hit.get("points"),
                            "num_comments": hit.get("num_comments"),
                            "hn_url": hn_url,
                        },
                    )
                )
            except Exception:
                logger.exception("Failed to parse HackerNews hit")

        return items
