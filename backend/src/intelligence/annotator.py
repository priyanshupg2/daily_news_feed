import asyncio
import json
import logging
import re

from src.config import settings
from src.db.database import get_db
from src.db.models import Lens
from src.intelligence.lenses import (
    lens_context_block,
    lens_keyword_set,
    load_active_lenses,
)
from src.llm.provider import LLMProvider, Providers

logger = logging.getLogger(__name__)


ANNOTATION_SCHEMA = {
    "type": "object",
    "properties": {
        "relevance_score": {"type": "number", "minimum": 0, "maximum": 1},
        "quality_score": {"type": "number", "minimum": 0, "maximum": 1},
        "novelty_score": {"type": "number", "minimum": 0, "maximum": 1},
        "importance_score": {"type": "number", "minimum": 0, "maximum": 1},
        "topic_tag": {"type": "string"},
        "rationale": {"type": "string"},
    },
    "required": [
        "relevance_score",
        "quality_score",
        "novelty_score",
        "importance_score",
        "topic_tag",
        "rationale",
    ],
    "additionalProperties": False,
}


def _heuristic_relevance(item: dict, kw: set[str]) -> float:
    """Token-overlap pre-gate. Returns a number in [0, 1] that's used to
    skip Sonnet calls on items that share no vocabulary with the lens."""
    if not kw:
        return 0.5  # no signal — let the LLM decide
    text = " ".join(
        filter(None, [item.get("title"), item.get("content") or ""])
    ).lower()
    tokens = set(re.findall(r"[a-z][a-z\-]{2,}", text))
    if not tokens:
        return 0.0
    hits = tokens & kw
    return min(1.0, len(hits) / 5.0)


async def annotate_items_for_lens(
    items: list[dict],
    lens: Lens,
    provider: LLMProvider,
) -> None:
    """Score every (item, lens) pair, writing into item_annotations."""
    kw = lens_keyword_set(lens)
    system = lens_context_block(lens)

    async def annotate_one(item: dict) -> None:
        # Heuristic short-circuit: zero overlap → cheap stub annotation.
        prior = _heuristic_relevance(item, kw)
        if prior < 0.01:
            await _store_annotation(
                item_id=item["id"],
                lens_id=lens.id,
                annotation={
                    "relevance_score": 0.0,
                    "quality_score": 0.3,
                    "novelty_score": 0.3,
                    "importance_score": 0.3,
                    "topic_tag": "off_topic",
                    "rationale": "Pre-gate: zero token overlap with lens.",
                },
                llm_model="heuristic",
            )
            return

        prompt = (
            "Score the item below against the lens. Return a single JSON "
            "object with the schema fields. relevance_score is how much "
            "this item would matter to the lens's thesis right now; "
            "importance_score is its standalone significance; "
            "novelty_score is how new this development is; "
            "quality_score is how rigorous the source appears. "
            "topic_tag is a snake_case noun phrase (≤4 words). "
            "rationale is one sentence.\n\n"
            f"ITEM\n"
            f"source: {item.get('source')}\n"
            f"title: {item.get('title')}\n"
            f"author: {item.get('authors') or '(unknown)'}\n"
            f"content: {(item.get('content') or '')[:2000]}\n"
        )

        try:
            result = await provider.complete_json(
                prompt=prompt,
                system=system,
                schema=ANNOTATION_SCHEMA,
            )
        except Exception:
            logger.exception(
                "Annotation failed for item=%s lens=%s", item["id"], lens.id
            )
            return

        if not result or "relevance_score" not in result:
            logger.warning("Empty annotation for %s/%s", item["id"], lens.id)
            return

        await _store_annotation(
            item_id=item["id"],
            lens_id=lens.id,
            annotation=result,
            llm_model=getattr(provider, "model", "unknown"),
        )

    await asyncio.gather(*(annotate_one(it) for it in items))


async def _store_annotation(
    item_id: str,
    lens_id: str,
    annotation: dict,
    llm_model: str,
) -> None:
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO item_annotations
              (item_id, lens_id, relevance_score, quality_score,
               novelty_score, importance_score, topic_tag, rationale,
               llm_model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                lens_id,
                annotation.get("relevance_score"),
                annotation.get("quality_score"),
                annotation.get("novelty_score"),
                annotation.get("importance_score"),
                annotation.get("topic_tag"),
                annotation.get("rationale"),
                llm_model,
            ),
        )
        await db.commit()


async def annotate_recent_items(
    providers: Providers, hours: int = 36
) -> int:
    """Score every item from the last `hours` window against every active
    lens. Skips (item, lens) pairs already scored."""
    lenses = await load_active_lenses()
    if not lenses:
        logger.warning("No active lenses; skipping annotation")
        return 0

    total = 0
    for lens in lenses:
        async with get_db() as db:
            cursor = await db.execute(
                f"""
                SELECT i.id, i.source, i.title, i.content, i.authors
                FROM items i
                WHERE i.fetched_at >= datetime('now', '-{int(hours)} hours')
                  AND NOT EXISTS (
                    SELECT 1 FROM item_annotations a
                    WHERE a.item_id = i.id AND a.lens_id = ?
                  )
                """,
                (lens.id,),
            )
            rows = await cursor.fetchall()
        items = [dict(r) for r in rows]
        if not items:
            continue
        logger.info(
            "Annotating %d items for lens=%s", len(items), lens.id
        )
        await annotate_items_for_lens(items, lens, providers.sonnet)
        total += len(items)
    return total
