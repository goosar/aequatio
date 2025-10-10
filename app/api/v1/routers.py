from fastapi import APIRouter  # type: ignore[import]

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "aequatio API v1"}


