import asyncio
import json
import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from src.db.database import get_db
from src.discovery.engine import DiscoveryEngine
from src.discovery.sources.arxiv import ArxivSource
from src.discovery.sources.conferences import ConferencesSource
from src.discovery.sources.github_trending import GitHubTrendingSource
from src.discovery.sources.hackernews import HackerNewsSource
from src.discovery.sources.reddit import RedditSource
from src.discovery.sources.semantic_scholar import SemanticScholarSource
from src.discovery.sources.tech_blogs import TechBlogsSource
from src.discovery.sources.techcrunch import TechCrunchSource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/discovery", tags=["discovery"])

_discovery_lock = asyncio.Lock()

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


@router.get("/stats")
async def get_stats(date: date = Query(default=None)):
    """Per-source item counts for a given date. Powers the dashboard."""
    fetch_date = date or __import__("datetime").date.today()

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT source, COUNT(*) as count FROM items WHERE fetch_date = ? GROUP BY source",
            (fetch_date.isoformat(),),
        )
        rows = await cursor.fetchall()
        sources = [{"source": row["source"], "count": row["count"]} for row in rows]
        total = sum(s["count"] for s in sources)

        cursor = await db.execute(
            "SELECT MAX(fetched_at) as latest_fetch FROM items WHERE fetch_date = ?",
            (fetch_date.isoformat(),),
        )
        row = await cursor.fetchone()
        latest_fetch = row["latest_fetch"] if row else None

    return {
        "date": fetch_date.isoformat(),
        "total": total,
        "sources": sources,
        "latest_fetch": latest_fetch,
    }


@router.get("/groups")
async def get_groups(
    source: str = Query(..., description="Source to group (e.g. techblogs)"),
    date: date = Query(default=None),
    key: str = Query(default="blog", description="Metadata JSON key to group by"),
):
    """Group items within a source by a metadata key. Powers sub-dashboards."""
    fetch_date = date or __import__("datetime").date.today()

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT json_extract(metadata, '$.' || ?) as group_name, COUNT(*) as count
               FROM items
               WHERE fetch_date = ? AND source = ?
               AND json_extract(metadata, '$.' || ?) IS NOT NULL
               GROUP BY group_name
               ORDER BY count DESC""",
            (key, fetch_date.isoformat(), source, key),
        )
        rows = await cursor.fetchall()
        groups = [{"name": row["group_name"], "count": row["count"]} for row in rows]

    return {"source": source, "date": fetch_date.isoformat(), "key": key, "groups": groups}


@router.get("/items/{item_id}")
async def get_item_detail(item_id: str):
    """Full detail for a single item. Powers the item detail page."""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    return _row_to_full_item(row)


@router.get("/items")
async def get_items(
    source: str = Query(..., description="Source: arxiv, hackernews, etc."),
    date: date = Query(default=None),
    group: str = Query(default=None, description="Filter by metadata group (e.g. blog name)"),
    group_key: str = Query(default="blog", description="Metadata key for group filter"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List items for a source and date. Returns only id, title, published_at."""
    fetch_date = date or __import__("datetime").date.today()

    if group:
        where = "fetch_date = ? AND source = ? AND json_extract(metadata, '$.' || ?) = ?"
        params = (fetch_date.isoformat(), source, group_key, group)
        count_params = params
    else:
        where = "fetch_date = ? AND source = ?"
        params = (fetch_date.isoformat(), source)
        count_params = params

    async with get_db() as db:
        cursor = await db.execute(
            f"""SELECT id, title, published_at FROM items
               WHERE {where}
               ORDER BY published_at DESC
               LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        )
        rows = await cursor.fetchall()
        items = [
            {
                "id": row["id"],
                "title": row["title"],
                "published_at": row["published_at"],
            }
            for row in rows
        ]

        cursor = await db.execute(
            f"SELECT COUNT(*) as count FROM items WHERE {where}",
            count_params,
        )
        total_row = await cursor.fetchone()
        total = total_row["count"]

    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/run")
async def run_discovery(source: str = Query(default=None)):
    """Trigger a discovery run. Returns count of new items stored."""
    if _discovery_lock.locked():
        raise HTTPException(status_code=409, detail="Discovery is already running")

    if source and source not in ALL_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source: {source}. Available: {list(ALL_SOURCES.keys())}",
        )

    async with _discovery_lock:
        if source:
            sources = [ALL_SOURCES[source]()]
        else:
            sources = [cls() for cls in ALL_SOURCES.values()]

        engine = DiscoveryEngine(sources)
        stored = await engine.run()

    return {"stored": stored, "message": f"Discovery complete. {stored} new items stored."}


def _row_to_full_item(row) -> dict:
    """Convert an aiosqlite Row to a full item dict."""
    metadata = None
    if row["metadata"]:
        try:
            metadata = json.loads(row["metadata"])
        except (json.JSONDecodeError, TypeError):
            metadata = row["metadata"]

    return {
        "id": row["id"],
        "source": row["source"],
        "source_id": row["source_id"],
        "title": row["title"],
        "url": row["url"],
        "content": row["content"],
        "authors": row["authors"],
        "published_at": row["published_at"],
        "fetch_date": row["fetch_date"],
        "metadata": metadata,
    }
