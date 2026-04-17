from fastapi import APIRouter

router = APIRouter()


@router.get("/placeholder")
def sessions_placeholder():
    return {"message": "sessions endpoint placeholder"}