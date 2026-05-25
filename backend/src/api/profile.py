import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.db.database import get_db

router = APIRouter(prefix="/profile", tags=["profile"])


class LensUpdate(BaseModel):
    name: str | None = None
    thesis: str | None = None
    working_topics: list[str] | None = None
    learning_topics: list[str] | None = None
    active: bool | None = None


@router.get("/")
async def get_profile():
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM user_profile WHERE id = 'default'"
        )
        row = await cursor.fetchone()
    return {"profile": dict(row) if row else None}


@router.get("/lenses")
async def list_lenses():
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM lenses ORDER BY sort_order, id"
        )
        rows = await cursor.fetchall()
    return {
        "lenses": [
            {
                "id": r["id"],
                "name": r["name"],
                "accent_token": r["accent_token"],
                "thesis": r["thesis"],
                "working_topics": json.loads(r["working_topics"] or "[]"),
                "learning_topics": json.loads(r["learning_topics"] or "[]"),
                "active": bool(r["active"]),
                "sort_order": r["sort_order"] or 0,
            }
            for r in rows
        ]
    }


@router.put("/lenses/{lens_id}")
async def update_lens(lens_id: str, body: LensUpdate):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM lenses WHERE id = ?", (lens_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Lens not found")

        fields: list[str] = []
        values: list = []
        if body.name is not None:
            fields.append("name = ?"); values.append(body.name)
        if body.thesis is not None:
            fields.append("thesis = ?"); values.append(body.thesis)
        if body.working_topics is not None:
            fields.append("working_topics = ?")
            values.append(json.dumps(body.working_topics))
        if body.learning_topics is not None:
            fields.append("learning_topics = ?")
            values.append(json.dumps(body.learning_topics))
        if body.active is not None:
            fields.append("active = ?"); values.append(1 if body.active else 0)
        if not fields:
            return {"status": "no-op"}
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(lens_id)
        await db.execute(
            f"UPDATE lenses SET {', '.join(fields)} WHERE id = ?",
            tuple(values),
        )
        await db.commit()
    return {"status": "ok"}
