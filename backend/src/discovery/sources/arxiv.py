"""
arXiv source fetcher.

Fetches recent papers from cs.LG, cs.CL, cs.AI categories using the arXiv API.
API docs: https://info.arxiv.org/help/api/index.html

The arXiv API returns Atom XML. We query for papers from the last 24-48 hours
across the three most relevant CS categories for AI/ML research.
"""

import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone

import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"

# Categories relevant to AI/ML/NLP/Inference
CATEGORIES = ["cs.LG", "cs.CL", "cs.AI"]

# Max results per query (arXiv API limit is 2000, but we keep it reasonable)
MAX_RESULTS_PER_CATEGORY = 100


class ArxivSource:
    source_name: str = "arxiv"

    def __init__(self, max_results_per_category: int = MAX_RESULTS_PER_CATEGORY):
        self.max_results = max_results_per_category

    async def fetch(self) -> list[RawItem]:
        """Fetch recent papers from arXiv across target categories."""
        all_items: list[RawItem] = []
        seen_ids: set[str] = set()

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for category in CATEGORIES:
                try:
                    items = await self._fetch_category(client, category)
                    for item in items:
                        if item.source_id not in seen_ids:
                            seen_ids.add(item.source_id)
                            all_items.append(item)
                except Exception:
                    logger.exception(f"Failed to fetch arXiv category {category}")

        logger.info(f"arXiv: fetched {len(all_items)} unique papers across {len(CATEGORIES)} categories")
        return all_items

    async def _fetch_category(self, client: httpx.AsyncClient, category: str) -> list[RawItem]:
        """Fetch papers for a single arXiv category."""
        # Search for recent papers in the category, sorted by submission date
        query = f"cat:{category}"
        params = {
            "search_query": query,
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        response = await client.get(ARXIV_API_URL, params=params)
        response.raise_for_status()

        return self._parse_atom_feed(response.text, category)

    def _parse_atom_feed(self, xml_text: str, category: str) -> list[RawItem]:
        """Parse arXiv Atom XML response into RawItem list."""
        # arXiv uses Atom namespace
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        root = ET.fromstring(xml_text)
        items: list[RawItem] = []

        for entry in root.findall("atom:entry", ns):
            try:
                item = self._parse_entry(entry, ns, category)
                if item:
                    items.append(item)
            except Exception:
                logger.exception("Failed to parse arXiv entry")
                continue

        return items

    def _parse_entry(self, entry: ET.Element, ns: dict, category: str) -> RawItem | None:
        """Parse a single Atom entry into a RawItem."""
        # Extract arXiv ID from the <id> tag (format: http://arxiv.org/abs/XXXX.XXXXX)
        id_elem = entry.find("atom:id", ns)
        if id_elem is None or id_elem.text is None:
            return None

        arxiv_url = id_elem.text.strip()
        arxiv_id = arxiv_url.split("/abs/")[-1]  # e.g., "2401.12345v1"
        # Normalize: strip version suffix for dedup
        base_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id

        title_elem = entry.find("atom:title", ns)
        title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else ""

        summary_elem = entry.find("atom:summary", ns)
        abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None and summary_elem.text else ""

        # Authors
        authors = []
        for author_elem in entry.findall("atom:author", ns):
            name_elem = author_elem.find("atom:name", ns)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())

        # Published date
        published_elem = entry.find("atom:published", ns)
        published_at = None
        if published_elem is not None and published_elem.text:
            try:
                published_at = datetime.fromisoformat(
                    published_elem.text.strip().replace("Z", "+00:00")
                )
            except ValueError:
                pass

        # Categories (all of them)
        categories = []
        for cat_elem in entry.findall("atom:category", ns):
            term = cat_elem.get("term")
            if term:
                categories.append(term)

        # PDF link
        pdf_url = None
        for link_elem in entry.findall("atom:link", ns):
            if link_elem.get("title") == "pdf":
                pdf_url = link_elem.get("href")
                break

        # Generate stable ID
        item_id = hashlib.sha256(f"arxiv:{base_id}".encode()).hexdigest()[:16]

        return RawItem(
            id=item_id,
            source="arxiv",
            source_id=base_id,
            title=title,
            url=arxiv_url,
            content=abstract,
            authors=", ".join(authors),
            published_at=published_at,
            fetch_date=date.today(),
            metadata={
                "arxiv_id": arxiv_id,
                "categories": categories,
                "primary_category": category,
                "pdf_url": pdf_url,
            },
        )
