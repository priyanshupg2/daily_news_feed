"""
TechCrunch source fetcher.

Fetches AI/ML-related articles from TechCrunch via their public RSS feed.
Filters posts by AI/ML keywords since TechCrunch covers all of tech.
"""

import hashlib
import logging
import re
from datetime import date, datetime, timezone

import feedparser
import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

FEED_URL = "https://techcrunch.com/feed/"

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "claude", "gemini",
    "openai", "anthropic", "mistral", "meta ai",
    "neural", "transformer", "diffusion", "generative",
    "chatbot", "copilot", "agent", "agentic",
    "computer vision", "nlp", "robotics",
    "gpu", "nvidia", "cuda", "inference",
    "fine-tuning", "rlhf", "training",
    "foundation model", "multimodal",
]

USER_AGENT = "DailyNewsFeed/1.0 (AI research aggregator)"


class TechCrunchSource:
    source_name: str = "techcrunch"

    async def fetch(self) -> list[RawItem]:
        """Fetch AI/ML articles from TechCrunch RSS."""
        headers = {"User-Agent": USER_AGENT}

        async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
            try:
                response = await client.get(FEED_URL)
                response.raise_for_status()
            except Exception:
                logger.exception("Failed to fetch TechCrunch RSS")
                return []

        feed = feedparser.parse(response.text)
        items: list[RawItem] = []

        for entry in feed.entries:
            if not self._is_ai_related(entry):
                continue
            item = self._parse_entry(entry)
            if item:
                items.append(item)

        logger.info(f"TechCrunch: fetched {len(items)} AI/ML articles from {len(feed.entries)} total")
        return items

    def _is_ai_related(self, entry) -> bool:
        """Check if an entry is related to AI/ML."""
        title = (getattr(entry, "title", "") or "").lower()
        summary = (getattr(entry, "summary", "") or "").lower()
        tags = [t.get("term", "").lower() for t in getattr(entry, "tags", []) if t.get("term")]

        text = f"{title} {summary} {' '.join(tags)}"
        return any(kw in text for kw in AI_KEYWORDS)

    def _parse_entry(self, entry) -> RawItem | None:
        """Parse a feedparser entry into a RawItem."""
        title = getattr(entry, "title", None)
        link = getattr(entry, "link", None)
        if not title:
            return None

        entry_id = getattr(entry, "id", None) or link or title
        source_id = hashlib.sha256(entry_id.encode()).hexdigest()[:16]
        item_id = hashlib.sha256(f"techcrunch:{source_id}".encode()).hexdigest()[:16]

        # Clean summary
        content = None
        if hasattr(entry, "summary"):
            content = re.sub(r"<[^>]+>", "", entry.summary).strip()
            if len(content) > 2000:
                content = content[:2000] + "..."

        # Published date
        published_at = None
        published = getattr(entry, "published_parsed", None)
        if published:
            try:
                published_at = datetime(*published[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        author = getattr(entry, "author", None)
        tags = [t.get("term", "") for t in getattr(entry, "tags", []) if t.get("term")]

        return RawItem(
            id=item_id,
            source="techcrunch",
            source_id=source_id,
            title=title,
            url=link,
            content=content,
            authors=author,
            published_at=published_at,
            fetch_date=date.today(),
            metadata={
                "entry_id": entry_id,
                "tags": tags,
            },
        )
