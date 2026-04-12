from fastapi import APIRouter

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/")
async def get_feed():
    """Get today's curated feed items."""
    return {"items": []}
