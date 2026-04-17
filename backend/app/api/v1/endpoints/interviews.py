from fastapi import APIRouter

router = APIRouter()


@router.get("/placeholder")
def interviews_placeholder():
    return {"message": "interviews endpoint placeholder"}