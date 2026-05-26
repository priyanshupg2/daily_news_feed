import logging
from datetime import date

from src.discovery.engine import DiscoveryEngine
from src.discovery.sources.arxiv import ArxivSource
from src.discovery.sources.hackernews import HackerNewsSource
from src.discovery.sources.reddit import RedditSource
from src.intelligence.annotator import annotate_recent_items
from src.intelligence.clusterer import build_clusters
from src.intelligence.merger import build_briefs
from src.intelligence.ranker import rank_and_select
from src.intelligence.trend import judge_trends
from src.llm.provider import Providers, get_providers

logger = logging.getLogger(__name__)


def default_sources() -> list:
    return [
        ArxivSource(),
        HackerNewsSource(),
        RedditSource(),
    ]


async def run_discovery() -> int:
    engine = DiscoveryEngine(default_sources())
    return await engine.run()


async def run_intelligence(
    feed_date: date | None = None,
    providers: Providers | None = None,
) -> dict:
    feed_date = feed_date or date.today()
    providers = providers or get_providers()

    annotated = await annotate_recent_items(providers)
    clusters = await build_clusters(feed_date, providers.sonnet)
    trends = await judge_trends(feed_date, providers.opus)
    briefs = await build_briefs(feed_date, providers.opus)
    kept = await rank_and_select(feed_date)

    return {
        "feed_date": feed_date.isoformat(),
        "annotated_pairs": annotated,
        "clusters": clusters,
        "trends_judged": trends,
        "briefs_generated": briefs,
        "briefs_kept": kept,
    }


async def run_full_pipeline(
    feed_date: date | None = None,
    providers: Providers | None = None,
) -> dict:
    discovered = await run_discovery()
    intel = await run_intelligence(feed_date, providers)
    return {"discovered": discovered, **intel}
