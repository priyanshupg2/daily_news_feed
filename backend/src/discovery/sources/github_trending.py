"""
GitHub Trending source fetcher.

Uses the GitHub REST API (no auth) to find recently popular AI/ML repos.
The search API allows sorting by stars and filtering by recent activity.

API docs: https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28

Rate limit: 10 requests/minute unauthenticated.
"""

import hashlib
import logging
from datetime import date, datetime, timedelta, timezone

import httpx

from src.db.models import RawItem

logger = logging.getLogger(__name__)

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

# Queries to find AI/ML repos that were recently pushed to
QUERIES = [
    "machine learning",
    "large language model",
    "deep learning",
    "transformer neural network",
    "LLM inference",
]

USER_AGENT = "DailyNewsFeed/1.0"
RESULTS_PER_QUERY = 30


class GitHubTrendingSource:
    source_name: str = "github"

    def __init__(self, queries: list[str] | None = None, results_per_query: int = RESULTS_PER_QUERY):
        self.queries = queries or QUERIES
        self.results_per_query = results_per_query

    async def fetch(self) -> list[RawItem]:
        """Fetch trending AI/ML repos from GitHub."""
        all_items: list[RawItem] = []
        seen_repos: set[str] = set()

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
        }

        # Only look at repos pushed to in the last 7 days
        pushed_after = (date.today() - timedelta(days=7)).isoformat()

        async with httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True) as client:
            for query in self.queries:
                try:
                    items = await self._search(client, query, pushed_after)
                    for item in items:
                        if item.source_id not in seen_repos:
                            seen_repos.add(item.source_id)
                            all_items.append(item)
                except Exception:
                    logger.exception(f"GitHub search failed for: {query}")

        logger.info(f"GitHub: fetched {len(all_items)} repos across {len(self.queries)} queries")
        return all_items

    async def _search(self, client: httpx.AsyncClient, query: str, pushed_after: str) -> list[RawItem]:
        """Search GitHub for repos matching a query, sorted by stars."""
        q = f"{query} pushed:>{pushed_after}"
        params = {
            "q": q,
            "sort": "stars",
            "order": "desc",
            "per_page": self.results_per_query,
        }

        response = await client.get(GITHUB_SEARCH_URL, params=params)

        if response.status_code == 403:
            logger.warning("GitHub API rate limited")
            return []
        response.raise_for_status()

        data = response.json()
        items: list[RawItem] = []

        for repo in data.get("items", []):
            item = self._parse_repo(repo)
            if item:
                items.append(item)

        return items

    def _parse_repo(self, repo: dict) -> RawItem | None:
        """Parse a GitHub API repo object into a RawItem."""
        full_name = repo.get("full_name")
        if not full_name:
            return None

        description = repo.get("description") or ""

        # Published date = pushed_at (most recent activity)
        published_at = None
        pushed_at = repo.get("pushed_at")
        if pushed_at:
            try:
                published_at = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            except ValueError:
                pass

        item_id = hashlib.sha256(f"github:{full_name}".encode()).hexdigest()[:16]

        title = f"{full_name}: {description}" if description else full_name

        return RawItem(
            id=item_id,
            source="github",
            source_id=full_name,
            title=title,
            url=repo.get("html_url", f"https://github.com/{full_name}"),
            content=description or None,
            authors=repo.get("owner", {}).get("login", full_name.split("/")[0]),
            published_at=published_at,
            fetch_date=date.today(),
            metadata={
                "repo": full_name,
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language"),
                "topics": repo.get("topics", []),
                "open_issues": repo.get("open_issues_count", 0),
                "license": (repo.get("license") or {}).get("spdx_id"),
                "github_url": repo.get("html_url"),
            },
        )
