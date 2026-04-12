import json
import logging

from src.db.database import get_db
from src.db.models import RawItem
from src.discovery.sources.base import Source

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Fetches items from all registered sources, deduplicates, and stores them."""

    def __init__(self, sources: list[Source]):
        self.sources = sources

    async def run(self) -> int:
        """Run discovery across all sources. Returns count of newly stored items."""
        all_items: list[RawItem] = []

        for source in self.sources:
            try:
                items = await source.fetch()
                logger.info(
                    f"Fetched {len(items)} items from {source.source_name}"
                )
                all_items.extend(items)
            except Exception:
                logger.exception(
                    f"Failed to fetch from {source.source_name}"
                )

        stored = await self._store_items(all_items)
        logger.info(f"Stored {stored} new items out of {len(all_items)} total")
        return stored

    async def _store_items(self, items: list[RawItem]) -> int:
        """Store items in the database, skipping duplicates via UNIQUE constraint."""
        stored = 0
        async with get_db() as db:
            for item in items:
                try:
                    await db.execute(
                        """
                        INSERT INTO items (
                            id, source, source_id, title, url, content,
                            authors, published_at, fetch_date, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item.id,
                            item.source,
                            item.source_id,
                            item.title,
                            item.url,
                            item.content,
                            item.authors,
                            item.published_at.isoformat()
                            if item.published_at
                            else None,
                            item.fetch_date.isoformat(),
                            json.dumps(item.metadata)
                            if item.metadata
                            else None,
                        ),
                    )
                    stored += 1
                except Exception:
                    # Duplicate (source, source_id) — skip silently
                    pass
            await db.commit()
        return stored
