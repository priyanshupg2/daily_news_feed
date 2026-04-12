"""
CLI script to run the discovery engine manually.

Usage:
    cd backend
    uv run python -m src.discovery.run
    uv run python -m src.discovery.run --source arxiv
    uv run python -m src.discovery.run --source hackernews
    uv run python -m src.discovery.run --source reddit
"""

import argparse
import asyncio
import logging
import sys

from src.db.database import init_db
from src.discovery.engine import DiscoveryEngine
from src.discovery.sources.arxiv import ArxivSource
from src.discovery.sources.conferences import ConferencesSource
from src.discovery.sources.github_trending import GitHubTrendingSource
from src.discovery.sources.hackernews import HackerNewsSource
from src.discovery.sources.reddit import RedditSource
from src.discovery.sources.semantic_scholar import SemanticScholarSource
from src.discovery.sources.tech_blogs import TechBlogsSource
from src.discovery.sources.techcrunch import TechCrunchSource

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

ALL_SOURCES = {
    "arxiv": ArxivSource,
    "hackernews": HackerNewsSource,
    "reddit": RedditSource,
    "github": GitHubTrendingSource,
    "semanticscholar": SemanticScholarSource,
    "techblogs": TechBlogsSource,
    "techcrunch": TechCrunchSource,
    "conferences": ConferencesSource,
}


async def main(source_filter: str | None = None):
    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Build source list
    if source_filter:
        if source_filter not in ALL_SOURCES:
            logger.error(f"Unknown source: {source_filter}. Available: {list(ALL_SOURCES.keys())}")
            sys.exit(1)
        sources = [ALL_SOURCES[source_filter]()]
        logger.info(f"Running discovery for: {source_filter}")
    else:
        sources = [cls() for cls in ALL_SOURCES.values()]
        logger.info(f"Running discovery for all {len(sources)} sources")

    # Run discovery
    engine = DiscoveryEngine(sources)
    stored = await engine.run()

    logger.info(f"Discovery complete. {stored} new items stored.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the discovery engine")
    parser.add_argument(
        "--source",
        choices=list(ALL_SOURCES.keys()),
        help="Run only a specific source (default: all)",
    )
    args = parser.parse_args()

    asyncio.run(main(args.source))
