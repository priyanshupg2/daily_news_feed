"""
Conference proceedings source fetcher.

Fetches recent papers from top AI/ML conferences using the DBLP API.
DBLP is a free, comprehensive CS bibliography database.

API docs: https://dblp.org/faq/How+to+use+the+dblp+search+API.html

Conferences tracked:
- NeurIPS (Neural Information Processing Systems)
- ICML (International Conference on Machine Learning)
- ACL (Association for Computational Linguistics)
- ICLR (International Conference on Learning Representations)
- AAAI (Association for the Advancement of AI)
- CVPR (Computer Vision and Pattern Recognition)
- EMNLP (Empirical Methods in NLP)
"""

import hashlib
import logging
from datetime import date, datetime, timezone

import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

DBLP_SEARCH_URL = "https://dblp.org/search/publ/api"

CONFERENCES = [
    {"venue": "NeurIPS", "query": "venue:NeurIPS"},
    {"venue": "ICML", "query": "venue:ICML"},
    {"venue": "ACL", "query": "venue:ACL"},
    {"venue": "ICLR", "query": "venue:ICLR"},
    {"venue": "AAAI", "query": "venue:AAAI"},
    {"venue": "CVPR", "query": "venue:CVPR"},
    {"venue": "EMNLP", "query": "venue:EMNLP"},
]

RESULTS_PER_VENUE = 50
CURRENT_YEAR = date.today().year


class ConferencesSource:
    source_name: str = "conferences"

    def __init__(self, conferences: list[dict] | None = None, results_per_venue: int = RESULTS_PER_VENUE):
        self.conferences = conferences or CONFERENCES
        self.results_per_venue = results_per_venue

    async def fetch(self) -> list[RawItem]:
        """Fetch recent conference papers from DBLP."""
        all_items: list[RawItem] = []
        seen_keys: set[str] = set()

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for conf in self.conferences:
                try:
                    items = await self._search_venue(client, conf)
                    for item in items:
                        if item.source_id not in seen_keys:
                            seen_keys.add(item.source_id)
                            all_items.append(item)
                except Exception:
                    logger.exception(f"DBLP search failed for: {conf['venue']}")

        logger.info(f"Conferences: fetched {len(all_items)} papers from {len(self.conferences)} venues")
        return all_items

    async def _search_venue(self, client: httpx.AsyncClient, conf: dict) -> list[RawItem]:
        """Search DBLP for recent papers from a conference venue."""
        params = {
            "q": conf["query"],
            "format": "json",
            "h": self.results_per_venue,
        }

        response = await client.get(DBLP_SEARCH_URL, params=params)

        if response.status_code == 429:
            logger.warning(f"DBLP rate limited for {conf['venue']}")
            return []

        response.raise_for_status()
        data = response.json()

        hits = data.get("result", {}).get("hits", {}).get("hit", [])
        items: list[RawItem] = []

        for hit in hits:
            item = self._parse_hit(hit, conf["venue"])
            if item:
                items.append(item)

        return items

    def _parse_hit(self, hit: dict, venue: str) -> RawItem | None:
        """Parse a DBLP search hit into a RawItem."""
        info = hit.get("info", {})
        title = info.get("title")
        key = info.get("key")

        if not title or not key:
            return None

        # Authors
        authors_data = info.get("authors", {}).get("author", [])
        if isinstance(authors_data, dict):
            authors_data = [authors_data]
        authors = ", ".join(
            a.get("text", a) if isinstance(a, dict) else str(a)
            for a in authors_data
        )

        # Year
        year = info.get("year")
        published_at = None
        if year:
            try:
                published_at = datetime(int(year), 1, 1, tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        # URL
        url = info.get("ee") or info.get("url") or f"https://dblp.org/rec/{key}"
        # ee can be a list
        if isinstance(url, list):
            url = url[0]

        item_id = hashlib.sha256(f"dblp:{key}".encode()).hexdigest()[:16]

        return RawItem(
            id=item_id,
            source="conferences",
            source_id=key,
            title=title.rstrip("."),
            url=url,
            content=None,  # DBLP doesn't provide abstracts
            authors=authors or None,
            published_at=published_at,
            fetch_date=date.today(),
            metadata={
                "dblp_key": key,
                "venue": venue,
                "year": year,
                "type": info.get("type"),
                "dblp_url": f"https://dblp.org/rec/{key}",
            },
        )
