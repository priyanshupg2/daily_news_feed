from fastapi import APIRouter

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/")
async def submit_feedback():
    """Submit feedback on a feed item."""
    return {"status": "received"}
