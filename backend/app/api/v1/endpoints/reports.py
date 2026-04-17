from fastapi import APIRouter

router = APIRouter()


@router.get("/placeholder")
def reports_placeholder():
    return {"message": "reports endpoint placeholder"}