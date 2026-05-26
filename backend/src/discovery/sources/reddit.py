import asyncio
import logging
from datetime import date, datetime, timezone

import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

USER_AGENT = "Prism/0.1 by /u/priyanshupg2"
SUBREDDITS = ["MachineLearning", "LocalLLaMA", "singularity"]
LIMIT = 25
INTER_REQUEST_DELAY_SECONDS = 2


class RedditSource:
    source_name = "reddit"

    async def fetch(self) -> list[RawItem]:
        items: list[RawItem] = []
        today = date.today()

        async with httpx.AsyncClient(
            timeout=30.0, headers={"User-Agent": USER_AGENT}
        ) as client:
            for idx, subreddit in enumerate(SUBREDDITS):
                if idx > 0:
                    await asyncio.sleep(INTER_REQUEST_DELAY_SECONDS)

                url = f"https://www.reddit.com/r/{subreddit}/top.json"
                params = {"t": "day", "limit": str(LIMIT)}

                try:
                    response = await client.get(url, params=params)
                    if response.status_code == 429:
                        logger.warning(
                            f"Reddit rate-limited on r/{subreddit}, skipping"
                        )
                        continue
                    response.raise_for_status()
                    payload = response.json()
                except Exception:
                    logger.exception(f"Reddit fetch failed for r/{subreddit}")
                    continue

                children = (payload.get("data") or {}).get("children") or []
                for child in children:
                    try:
                        data = child.get("data") or {}
                        post_id = data.get("id")
                        title = data.get("title")
                        if not post_id or not title:
                            continue

                        permalink = data.get("permalink") or ""
                        full_permalink = f"https://reddit.com{permalink}"
                        is_self = bool(data.get("is_self"))
                        item_url = full_permalink if is_self else data.get("url")
                        content = data.get("selftext") if is_self else None

                        created_utc = data.get("created_utc")
                        published_at = None
                        if created_utc is not None:
                            published_at = datetime.fromtimestamp(
                                float(created_utc), tz=timezone.utc
                            )

                        items.append(
                            RawItem(
                                id=f"reddit:{post_id}",
                                source=self.source_name,
                                source_id=post_id,
                                title=title,
                                url=item_url,
                                content=content,
                                authors=data.get("author"),
                                published_at=published_at,
                                fetch_date=today,
                                metadata={
                                    "subreddit": subreddit,
                                    "score": data.get("score"),
                                    "num_comments": data.get("num_comments"),
                                    "permalink": full_permalink,
                                },
                            )
                        )
                    except Exception:
                        logger.exception(
                            f"Failed to parse Reddit post in r/{subreddit}"
                        )

        return items
