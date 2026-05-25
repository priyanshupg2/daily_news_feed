import json
import logging
from datetime import date as _date

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from src.db.database import get_db
from src.intelligence.pipeline import run_full_pipeline, run_intelligence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/")
async def get_feed(
    date: str | None = Query(None, description="YYYY-MM-DD; defaults to today"),
    lens: str | None = Query(None, description="Filter by lens id"),
):
    feed_date = date or _date.today().isoformat()

    async with get_db() as db:
        if lens:
            cursor = await db.execute(
                """
                SELECT DISTINCT fi.* FROM feed_items fi
                JOIN feed_item_lenses fil ON fil.feed_item_id = fi.id
                WHERE fi.feed_date = ?
                  AND fi.final_rank IS NOT NULL
                  AND fil.lens_id = ?
                ORDER BY fi.final_rank DESC
                """,
                (feed_date, lens),
            )
        else:
            cursor = await db.execute(
                """
                SELECT * FROM feed_items
                WHERE feed_date = ? AND final_rank IS NOT NULL
                ORDER BY final_rank DESC
                """,
                (feed_date,),
            )
        briefs = [dict(r) for r in await cursor.fetchall()]

        for brief in briefs:
            await _hydrate_brief(db, brief)

    return {"feed_date": feed_date, "lens": lens, "briefs": briefs}


@router.get("/{brief_id}")
async def get_brief(brief_id: str):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM feed_items WHERE id = ?", (brief_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Brief not found")
        brief = dict(row)
        await _hydrate_brief(db, brief)
    return brief


@router.post("/refresh")
async def refresh_feed(background_tasks: BackgroundTasks, full: bool = False):
    if full:
        background_tasks.add_task(run_full_pipeline)
    else:
        background_tasks.add_task(run_intelligence)
    return {"status": "started", "full": full}


@router.post("/{brief_id}/read")
async def mark_read(brief_id: str, time_spent_seconds: int = 0):
    async with get_db() as db:
        await db.execute(
            """
            UPDATE feed_items
            SET is_read = 1, read_at = CURRENT_TIMESTAMP,
                time_spent_seconds = ?
            WHERE id = ?
            """,
            (time_spent_seconds, brief_id),
        )
        await db.commit()
    return {"status": "ok"}


async def _hydrate_brief(db, brief: dict) -> None:
    cursor = await db.execute(
        """
        SELECT fil.lens_id, fil.relevance_score, l.name, l.accent_token
        FROM feed_item_lenses fil
        JOIN lenses l ON l.id = fil.lens_id
        WHERE fil.feed_item_id = ?
        ORDER BY fil.relevance_score DESC
        """,
        (brief["id"],),
    )
    lens_rows = [dict(r) for r in await cursor.fetchall()]
    brief["lenses"] = lens_rows
    brief["primary_lens"] = lens_rows[0]["lens_id"] if lens_rows else None

    cursor = await db.execute(
        """
        SELECT bc.n, bc.text, bc.source_item_id, bc.citation_text,
               bc.confidence, i.url AS source_url, i.source AS source,
               i.title AS source_title
        FROM brief_claims bc
        LEFT JOIN items i ON i.id = bc.source_item_id
        WHERE bc.feed_item_id = ?
        ORDER BY bc.n
        """,
        (brief["id"],),
    )
    brief["claims"] = [dict(r) for r in await cursor.fetchall()]

    try:
        brief["source_links"] = json.loads(brief["source_links"] or "[]")
    except Exception:
        brief["source_links"] = []
    brief["source_count"] = len(brief["source_links"])
