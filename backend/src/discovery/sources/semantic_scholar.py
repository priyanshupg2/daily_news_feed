"""
Semantic Scholar source fetcher.

Uses the Semantic Scholar Academic Graph API to fetch recent influential
AI/ML papers. Free REST API, no API key required.

API docs: https://api.semanticscholar.org/api-docs/
"""

import hashlib
import logging
from datetime import date, datetime, timezone

import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

# Fields to request from the API
FIELDS = "title,abstract,authors,url,year,citationCount,influentialCitationCount,venue,publicationDate,fieldsOfStudy"

# Queries to run — each captures a different slice of AI/ML research
QUERIES = [
    "large language model",
    "deep learning",
    "reinforcement learning",
    "computer vision transformer",
    "neural network inference",
]

# Only fetch papers from recent years
YEAR_FILTER = f"{date.today().year - 1}-"  # last year to now

RESULTS_PER_QUERY = 50


class SemanticScholarSource:
    source_name: str = "semanticscholar"

    def __init__(self, queries: list[str] | None = None, results_per_query: int = RESULTS_PER_QUERY):
        self.queries = queries or QUERIES
        self.results_per_query = results_per_query

    async def fetch(self) -> list[RawItem]:
        """Fetch recent AI/ML papers from Semantic Scholar."""
        all_items: list[RawItem] = []
        seen_ids: set[str] = set()

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for query in self.queries:
                try:
                    items = await self._search(client, query)
                    for item in items:
                        if item.source_id not in seen_ids:
                            seen_ids.add(item.source_id)
                            all_items.append(item)
                except Exception:
                    logger.exception(f"Semantic Scholar search failed for: {query}")

        logger.info(f"SemanticScholar: fetched {len(all_items)} papers across {len(self.queries)} queries")
        return all_items

    async def _search(self, client: httpx.AsyncClient, query: str) -> list[RawItem]:
        """Search for papers matching a query."""
        params = {
            "query": query,
            "limit": self.results_per_query,
            "fields": FIELDS,
            "sort": "publicationDate",
            "year": YEAR_FILTER,
        }

        response = await client.get(S2_SEARCH_URL, params=params)

        if response.status_code == 429:
            logger.warning("Semantic Scholar rate limited")
            return []

        response.raise_for_status()
        data = response.json()

        items: list[RawItem] = []
        for paper in data.get("data", []):
            item = self._parse_paper(paper)
            if item:
                items.append(item)

        return items

    def _parse_paper(self, paper: dict) -> RawItem | None:
        """Parse a Semantic Scholar paper object into a RawItem."""
        paper_id = paper.get("paperId")
        title = paper.get("title")

        if not paper_id or not title:
            return None

        # Authors
        authors_list = paper.get("authors", [])
        authors = ", ".join(a.get("name", "") for a in authors_list if a.get("name"))

        # Published date
        published_at = None
        pub_date = paper.get("publicationDate")
        if pub_date:
            try:
                published_at = datetime.strptime(pub_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        # URL
        url = paper.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}"

        # Abstract
        abstract = paper.get("abstract")
        if abstract and len(abstract) > 2000:
            abstract = abstract[:2000] + "..."

        # Generate stable ID
        item_id = hashlib.sha256(f"s2:{paper_id}".encode()).hexdigest()[:16]

        return RawItem(
            id=item_id,
            source="semanticscholar",
            source_id=paper_id,
            title=title,
            url=url,
            content=abstract,
            authors=authors or None,
            published_at=published_at,
            fetch_date=date.today(),
            metadata={
                "paper_id": paper_id,
                "year": paper.get("year"),
                "citation_count": paper.get("citationCount", 0),
                "influential_citation_count": paper.get("influentialCitationCount", 0),
                "venue": paper.get("venue"),
                "fields_of_study": paper.get("fieldsOfStudy", []),
                "s2_url": f"https://www.semanticscholar.org/paper/{paper_id}",
            },
        )
