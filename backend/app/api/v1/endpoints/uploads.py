from fastapi import APIRouter

router = APIRouter()


@router.get("/placeholder")
def uploads_placeholder():
    return {"message": "uploads endpoint placeholder"}