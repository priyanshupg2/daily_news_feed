"""
Reddit source fetcher.

Fetches hot posts from ML/AI subreddits using Reddit's public JSON API.
No authentication required — uses the .json endpoint trick.

Target subreddits:
- r/MachineLearning — academic papers, industry news
- r/LocalLLaMA — local inference, open-source models
- r/artificial — general AI news
"""

import hashlib
import logging
from datetime import date, datetime, timezone

import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

REDDIT_BASE = "https://www.reddit.com"

# Subreddits to fetch from
SUBREDDITS = [
    "MachineLearning",
    "LocalLLaMA",
    "artificial",
]

# User agent (Reddit requires a descriptive UA, blocks generic ones)
USER_AGENT = "DailyNewsFeed/1.0 (AI research aggregator; contact: github.com/priyanshupg2/daily_news_feed)"

# Posts per subreddit
POSTS_PER_SUBREDDIT = 50


class RedditSource:
    source_name: str = "reddit"

    def __init__(
        self,
        subreddits: list[str] | None = None,
        posts_per_sub: int = POSTS_PER_SUBREDDIT,
    ):
        self.subreddits = subreddits or SUBREDDITS
        self.posts_per_sub = posts_per_sub

    async def fetch(self) -> list[RawItem]:
        """Fetch hot posts from target subreddits."""
        all_items: list[RawItem] = []
        seen_ids: set[str] = set()

        headers = {"User-Agent": USER_AGENT}

        async with httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True) as client:
            for subreddit in self.subreddits:
                try:
                    items = await self._fetch_subreddit(client, subreddit)
                    for item in items:
                        if item.source_id not in seen_ids:
                            seen_ids.add(item.source_id)
                            all_items.append(item)
                except Exception:
                    logger.exception(f"Failed to fetch Reddit r/{subreddit}")

        logger.info(f"Reddit: fetched {len(all_items)} posts across {len(self.subreddits)} subreddits")
        return all_items

    async def _fetch_subreddit(
        self, client: httpx.AsyncClient, subreddit: str
    ) -> list[RawItem]:
        """Fetch hot posts from a single subreddit."""
        items: list[RawItem] = []

        # Fetch both hot and top-today for better coverage
        for sort in ["hot", "top"]:
            try:
                url = f"{REDDIT_BASE}/r/{subreddit}/{sort}.json"
                params = {"limit": self.posts_per_sub, "t": "day"}  # t=day for top

                response = await client.get(url, params=params)

                if response.status_code == 429:
                    logger.warning(f"Reddit rate limited on r/{subreddit}/{sort}")
                    continue
                response.raise_for_status()

                data = response.json()
                posts = data.get("data", {}).get("children", [])

                for post_wrapper in posts:
                    post = post_wrapper.get("data", {})
                    item = self._parse_post(post, subreddit)
                    if item:
                        items.append(item)

            except httpx.HTTPStatusError as e:
                logger.warning(f"Reddit HTTP error r/{subreddit}/{sort}: {e.response.status_code}")
            except Exception:
                logger.exception(f"Failed to fetch r/{subreddit}/{sort}")

        return items

    def _parse_post(self, post: dict, subreddit: str) -> RawItem | None:
        """Parse a Reddit post JSON into a RawItem."""
        post_id = post.get("id")
        title = post.get("title")

        if not post_id or not title:
            return None

        # Skip stickied/pinned posts (usually rules/FAQs)
        if post.get("stickied"):
            return None

        # URL: link posts have a url, self posts use the permalink
        url = post.get("url")
        permalink = post.get("permalink")
        reddit_url = f"{REDDIT_BASE}{permalink}" if permalink else None

        # For self posts, the url points to the reddit post itself
        is_self = post.get("is_self", False)
        external_url = url if not is_self else None

        # Content: self text for text posts
        selftext = post.get("selftext", "")
        # Truncate very long self posts
        if len(selftext) > 2000:
            selftext = selftext[:2000] + "..."

        # Published time
        published_at = None
        created_utc = post.get("created_utc")
        if created_utc:
            published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc)

        # Generate stable ID
        item_id = hashlib.sha256(f"reddit:{post_id}".encode()).hexdigest()[:16]

        return RawItem(
            id=item_id,
            source="reddit",
            source_id=str(post_id),
            title=title,
            url=external_url or reddit_url or "",
            content=selftext if selftext else None,
            authors=post.get("author"),
            published_at=published_at,
            fetch_date=date.today(),
            metadata={
                "reddit_id": post_id,
                "subreddit": subreddit,
                "score": post.get("score", 0),
                "upvote_ratio": post.get("upvote_ratio"),
                "num_comments": post.get("num_comments", 0),
                "permalink": reddit_url,
                "external_url": external_url,
                "is_self": is_self,
                "link_flair_text": post.get("link_flair_text"),
                "domain": post.get("domain"),
            },
        )
