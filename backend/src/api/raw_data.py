from fastapi import APIRouter

router = APIRouter(prefix="/raw", tags=["raw_data"])


@router.get("/items")
async def get_raw_items():
    """Get raw fetched items."""
    return {"items": []}
