"""
Tech Blogs RSS source fetcher.

Fetches posts from curated AI/ML blogs via RSS feeds.
Uses feedparser (already a project dependency).

Blogs:
- Lilian Weng (lilianweng.github.io)
- Jay Alammar (jalammar.github.io)
- Chip Huyen (huyenchip.com)
- Sebastian Raschka (sebastianraschka.com)
- The Gradient (thegradient.pub)
- Distill.pub
- OpenAI Blog
- Google AI Blog
- Meta AI Blog
"""

import hashlib
import logging
from datetime import date, datetime, timezone

import feedparser
import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

# Curated AI/ML blog RSS feeds
FEEDS = [
    {
        "name": "Lilian Weng",
        "url": "https://lilianweng.github.io/index.xml",
    },
    {
        "name": "Jay Alammar",
        "url": "https://jalammar.github.io/feed.xml",
    },
    {
        "name": "Chip Huyen",
        "url": "https://huyenchip.com/feed.xml",
    },
    {
        "name": "Sebastian Raschka",
        "url": "https://sebastianraschka.com/blog/feed.xml",
    },
    {
        "name": "The Gradient",
        "url": "https://thegradient.pub/rss/",
    },
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.research.google/feeds/posts/default?alt=rss",
    },
    {
        "name": "Meta AI",
        "url": "https://ai.meta.com/blog/rss/",
    },
    {
        "name": "Anthropic",
        "url": "https://www.anthropic.com/feed.xml",
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
    },
    {
        "name": "Andrej Karpathy",
        "url": "https://karpathy.github.io/feed.xml",
    },
]

USER_AGENT = "DailyNewsFeed/1.0 (AI research aggregator)"


class TechBlogsSource:
    source_name: str = "techblogs"

    def __init__(self, feeds: list[dict] | None = None):
        self.feeds = feeds or FEEDS

    async def fetch(self) -> list[RawItem]:
        """Fetch posts from all RSS feeds."""
        all_items: list[RawItem] = []
        seen_urls: set[str] = set()

        headers = {"User-Agent": USER_AGENT}

        async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
            for feed_info in self.feeds:
                try:
                    items = await self._fetch_feed(client, feed_info)
                    for item in items:
                        url_key = item.url or item.source_id
                        if url_key not in seen_urls:
                            seen_urls.add(url_key)
                            all_items.append(item)
                except Exception:
                    logger.exception(f"Failed to fetch blog: {feed_info['name']}")

        logger.info(f"TechBlogs: fetched {len(all_items)} posts from {len(self.feeds)} feeds")
        return all_items

    async def _fetch_feed(self, client: httpx.AsyncClient, feed_info: dict) -> list[RawItem]:
        """Fetch and parse a single RSS feed."""
        feed_name = feed_info["name"]
        feed_url = feed_info["url"]

        try:
            response = await client.get(feed_url)
            if response.status_code == 429:
                logger.warning(f"Rate limited fetching {feed_name}")
                return []
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} fetching {feed_name}")
            return []

        feed = feedparser.parse(response.text)
        items: list[RawItem] = []

        for entry in feed.entries[:20]:  # Cap at 20 per blog
            item = self._parse_entry(entry, feed_name)
            if item:
                items.append(item)

        return items

    def _parse_entry(self, entry, feed_name: str) -> RawItem | None:
        """Parse a feedparser entry into a RawItem."""
        title = getattr(entry, 'title', None)
        link = getattr(entry, 'link', None)

        if not title:
            return None

        # Generate a stable ID from the link or id
        entry_id = getattr(entry, 'id', None) or link or title
        source_id = hashlib.sha256(entry_id.encode()).hexdigest()[:16]
        item_id = hashlib.sha256(f"techblogs:{source_id}".encode()).hexdigest()[:16]

        # Extract content/summary
        content = None
        if hasattr(entry, 'summary'):
            content = entry.summary
            # Strip HTML tags for cleaner storage
            import re
            content = re.sub(r'<[^>]+>', '', content).strip()
            if len(content) > 2000:
                content = content[:2000] + "..."

        # Published date
        published_at = None
        published = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
        if published:
            try:
                published_at = datetime(*published[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        # Authors
        author = getattr(entry, 'author', None) or feed_name

        # Tags/categories
        tags = []
        if hasattr(entry, 'tags'):
            tags = [t.get('term', '') for t in entry.tags if t.get('term')]

        return RawItem(
            id=item_id,
            source="techblogs",
            source_id=source_id,
            title=title,
            url=link,
            content=content,
            authors=author,
            published_at=published_at,
            fetch_date=date.today(),
            metadata={
                "blog": feed_name,
                "entry_id": entry_id,
                "tags": tags,
            },
        )
