from fastapi import APIRouter, Query

from src.db.database import get_db

router = APIRouter(prefix="/raw", tags=["raw_data"])


@router.get("/items")
async def get_raw_items(
    source: str | None = Query(None),
    lens: str | None = Query(None),
    topic: str | None = Query(None),
    limit: int = Query(100, le=500),
):
    where = ["i.fetched_at >= datetime('now', '-48 hours')"]
    params: list = []
    if source:
        where.append("i.source = ?"); params.append(source)
    if topic:
        where.append(
            "EXISTS (SELECT 1 FROM item_annotations a WHERE a.item_id = i.id AND a.topic_tag = ?)"
        )
        params.append(topic)
    if lens:
        # Show every item that was scored under this lens, including
        # heuristic-stub annotations (relevance 0.0). The raw-data
        # browser is the audit surface — filtering by relevance here
        # would hide the items the pre-gate skipped, which is exactly
        # what an audit needs to see.
        where.append(
            "EXISTS (SELECT 1 FROM item_annotations a "
            "WHERE a.item_id = i.id AND a.lens_id = ?)"
        )
        params.append(lens)

    async with get_db() as db:
        cursor = await db.execute(
            f"""
            SELECT i.id, i.source, i.title, i.url, i.authors,
                   i.published_at, i.fetched_at
            FROM items i
            WHERE {' AND '.join(where)}
            ORDER BY i.fetched_at DESC
            LIMIT ?
            """,
            tuple(params + [limit]),
        )
        items = [dict(r) for r in await cursor.fetchall()]

        for item in items:
            cursor = await db.execute(
                """
                SELECT lens_id, relevance_score, topic_tag, rationale
                FROM item_annotations
                WHERE item_id = ?
                """,
                (item["id"],),
            )
            item["annotations"] = [dict(r) for r in await cursor.fetchall()]

    return {"items": items, "count": len(items)}
