from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.report import ReportResponse
from app.services.report_service import get_session_report

router = APIRouter()


@router.get("/{session_id}", response_model=ReportResponse)
def get_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_session_report(db, session_id, current_user.id)