from fastapi import APIRouter
from pydantic import BaseModel

from src.db.database import get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackItemIn(BaseModel):
    feed_item_id: str
    action: str  # 'like' | 'dislike' | 'save' | 'mute'
    comment: str | None = None


class FeedbackAnnotationIn(BaseModel):
    item_id: str
    lens_id: str | None = None
    field: str
    original_value: str | None = None
    user_value: str | None = None
    comment: str | None = None


@router.post("/item")
async def submit_item_feedback(body: FeedbackItemIn):
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO feedback_items (feed_item_id, action, comment)
            VALUES (?, ?, ?)
            """,
            (body.feed_item_id, body.action, body.comment),
        )
        await db.commit()
    return {"status": "ok"}


@router.post("/annotation")
async def submit_annotation_feedback(body: FeedbackAnnotationIn):
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO feedback_annotations
              (item_id, lens_id, field, original_value, user_value, comment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                body.item_id,
                body.lens_id,
                body.field,
                body.original_value,
                body.user_value,
                body.comment,
            ),
        )
        await db.commit()
    return {"status": "ok"}
