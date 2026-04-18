from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.history import SessionHistoryItem
from app.schemas.score import SessionScoreSummaryResponse
from app.services.history_service import get_user_history, get_session_score_summary

router = APIRouter()


@router.get("/sessions", response_model=list[SessionHistoryItem])
def list_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_user_history(db, current_user.id)


@router.get("/scores/{session_id}", response_model=SessionScoreSummaryResponse)
def get_score_summary(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_session_score_summary(db, session_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result