"""
Hacker News source fetcher.

Uses the HN Algolia API to search for AI/ML/LLM related stories.
API docs: https://hn.algolia.com/api

Strategy:
- Search for AI/ML keywords in top stories from the last 24h
- Also fetch from front page top stories and filter
- Dedup by story ID
"""

import hashlib
import logging
import time
from datetime import date, datetime, timezone

import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
ALGOLIA_ITEM_URL = "https://hn.algolia.com/api/v1/items"
HN_ITEM_URL = "https://news.ycombinator.com/item?id="

# Keywords to filter for AI/ML relevance
AI_KEYWORDS = [
    "AI",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "LLM",
    "large language model",
    "GPT",
    "Claude",
    "transformer",
    "diffusion",
    "CUDA",
    "GPU",
    "inference",
    "fine-tuning",
    "fine tuning",
    "RLHF",
    "reinforcement learning",
    "computer vision",
    "NLP",
    "natural language",
    "embedding",
    "vector database",
    "RAG",
    "retrieval augmented",
    "model training",
    "pytorch",
    "tensorflow",
    "jax",
    "hugging face",
    "huggingface",
    "openai",
    "anthropic",
    "mistral",
    "llama",
    "gemini",
    "MLOps",
    "model serving",
    "quantization",
    "distillation",
    "attention mechanism",
    "tokenizer",
    "benchmark",
    "MMLU",
    "foundation model",
    "multimodal",
    "agent",
    "agentic",
    "MCP",
    "model context protocol",
]

# Number of results to request per keyword search
RESULTS_PER_SEARCH = 50

# How far back to look (in seconds) — 48 hours to catch things we might have missed
LOOKBACK_SECONDS = 48 * 60 * 60


class HackerNewsSource:
    source_name: str = "hackernews"

    def __init__(self, max_results: int = 200):
        self.max_results = max_results

    async def fetch(self) -> list[RawItem]:
        """Fetch AI/ML related stories from Hacker News."""
        seen_ids: set[str] = set()
        all_items: list[RawItem] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Strategy 1: Search by key AI terms (most signal)
            search_items = await self._search_by_keywords(client)
            for item in search_items:
                if item.source_id not in seen_ids:
                    seen_ids.add(item.source_id)
                    all_items.append(item)

            # Strategy 2: Get front page and filter
            front_items = await self._fetch_front_page(client)
            for item in front_items:
                if item.source_id not in seen_ids:
                    seen_ids.add(item.source_id)
                    all_items.append(item)

        logger.info(f"HackerNews: fetched {len(all_items)} AI/ML stories")
        return all_items[:self.max_results]

    async def _search_by_keywords(self, client: httpx.AsyncClient) -> list[RawItem]:
        """Search HN Algolia for AI/ML keywords."""
        items: list[RawItem] = []
        cutoff = int(time.time()) - LOOKBACK_SECONDS

        # Group keywords into batches to reduce API calls
        # Algolia supports OR queries
        keyword_batches = [
            " OR ".join(f'"{kw}"' for kw in AI_KEYWORDS[i:i + 5])
            for i in range(0, len(AI_KEYWORDS), 5)
        ]

        for query in keyword_batches:
            try:
                params = {
                    "query": query,
                    "tags": "story",
                    "numericFilters": f"created_at_i>{cutoff}",
                    "hitsPerPage": RESULTS_PER_SEARCH,
                }
                response = await client.get(ALGOLIA_SEARCH_URL, params=params)
                response.raise_for_status()
                data = response.json()

                for hit in data.get("hits", []):
                    item = self._parse_hit(hit)
                    if item:
                        items.append(item)

            except Exception:
                logger.exception(f"HN search failed for query batch")
                continue

        return items

    async def _fetch_front_page(self, client: httpx.AsyncClient) -> list[RawItem]:
        """Fetch current front page stories and filter for AI/ML relevance."""
        items: list[RawItem] = []

        try:
            params = {
                "tags": "front_page",
                "hitsPerPage": 100,
            }
            response = await client.get(ALGOLIA_SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()

            for hit in data.get("hits", []):
                # Check if title or URL contains AI/ML keywords
                title = (hit.get("title") or "").lower()
                url = (hit.get("url") or "").lower()
                combined = f"{title} {url}"

                is_relevant = any(
                    kw.lower() in combined for kw in AI_KEYWORDS
                )
                if is_relevant:
                    item = self._parse_hit(hit)
                    if item:
                        items.append(item)

        except Exception:
            logger.exception("Failed to fetch HN front page")

        return items

    def _parse_hit(self, hit: dict) -> RawItem | None:
        """Parse an Algolia search hit into a RawItem."""
        object_id = hit.get("objectID")
        title = hit.get("title")

        if not object_id or not title:
            return None

        # URL: prefer the story URL, fallback to HN comments page
        url = hit.get("url") or f"{HN_ITEM_URL}{object_id}"

        # Published time
        published_at = None
        created_at_i = hit.get("created_at_i")
        if created_at_i:
            published_at = datetime.fromtimestamp(created_at_i, tz=timezone.utc)

        # Content: use story text if available (for Ask HN, Show HN)
        story_text = hit.get("story_text") or ""

        # Generate stable ID
        item_id = hashlib.sha256(f"hn:{object_id}".encode()).hexdigest()[:16]

        return RawItem(
            id=item_id,
            source="hackernews",
            source_id=str(object_id),
            title=title,
            url=url,
            content=story_text if story_text else None,
            authors=hit.get("author"),
            published_at=published_at,
            fetch_date=date.today(),
            metadata={
                "hn_id": object_id,
                "points": hit.get("points"),
                "num_comments": hit.get("num_comments"),
                "story_url": hit.get("url"),
                "hn_url": f"{HN_ITEM_URL}{object_id}",
                "tags": hit.get("_tags", []),
            },
        )
