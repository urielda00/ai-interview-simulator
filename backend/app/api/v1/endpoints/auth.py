from fastapi import APIRouter

router = APIRouter()


@router.get("/placeholder")
def auth_placeholder():
    return {"message": "auth endpoint placeholder"}