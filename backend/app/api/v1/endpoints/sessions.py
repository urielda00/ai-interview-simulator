from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.i18n import normalize_language
from app.schemas.session import SessionCreate, SessionResponse
from app.services.session_service import (
    create_new_session,
    fetch_owned_session_by_id,
    fetch_user_sessions,
)

router = APIRouter()


@router.post("/", response_model=SessionResponse)
def create_session(
    session_data: SessionCreate,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    resolved_language = normalize_language(session_data.language, accept_language)
    enriched_session_data = SessionCreate(
        track=session_data.track,
        level=session_data.level,
        mode=session_data.mode,
        language=resolved_language,
    )
    return create_new_session(db, current_user.id, enriched_session_data)


@router.get("/", response_model=list[SessionResponse])
def list_my_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return fetch_user_sessions(db, current_user.id)


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return fetch_owned_session_by_id(db, session_id, current_user.id)