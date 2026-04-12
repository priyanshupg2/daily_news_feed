from fastapi import APIRouter

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/")
async def get_profile():
    """Get user profile."""
    return {"profile": None}
