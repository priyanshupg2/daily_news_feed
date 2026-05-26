import json
import logging

from src.db.database import get_db
from src.db.models import Lens

logger = logging.getLogger(__name__)


async def load_active_lenses() -> list[Lens]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM lenses WHERE active = 1 ORDER BY sort_order, id"
        )
        rows = await cursor.fetchall()
    return [_row_to_lens(r) for r in rows]


async def load_all_lenses() -> list[Lens]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM lenses ORDER BY sort_order, id"
        )
        rows = await cursor.fetchall()
    return [_row_to_lens(r) for r in rows]


async def load_lens(lens_id: str) -> Lens | None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM lenses WHERE id = ?", (lens_id,)
        )
        row = await cursor.fetchone()
    return _row_to_lens(row) if row else None


def _row_to_lens(row) -> Lens:
    return Lens(
        id=row["id"],
        name=row["name"],
        accent_token=row["accent_token"],
        thesis=row["thesis"],
        working_topics=json.loads(row["working_topics"] or "[]"),
        learning_topics=json.loads(row["learning_topics"] or "[]"),
        active=bool(row["active"]),
        sort_order=row["sort_order"] or 0,
    )


def lens_keyword_set(lens: Lens) -> set[str]:
    """The bag of lower-cased single-word tokens we use for the heuristic
    relevance pre-gate. Cheap, deterministic, and good enough to skip the
    obvious zeros before the Sonnet call."""
    bag: set[str] = set()
    for topic in lens.working_topics + lens.learning_topics:
        for token in topic.replace("_", " ").split():
            if len(token) >= 3:
                bag.add(token.lower())
    if lens.thesis:
        for token in lens.thesis.split():
            cleaned = token.strip(".,;:()[]\"'").lower()
            if len(cleaned) >= 4 and cleaned.isalpha():
                bag.add(cleaned)
    return bag


def lens_context_block(lens: Lens) -> str:
    """Plain-text description of the lens for prompt injection."""
    return (
        f"Lens: {lens.name}\n"
        f"Thesis: {lens.thesis or '(unset)'}\n"
        f"Working topics: {', '.join(lens.working_topics) or '(none)'}\n"
        f"Learning topics: {', '.join(lens.learning_topics) or '(none)'}"
    )
