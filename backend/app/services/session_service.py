from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.session_repository import (
    create_session,
    get_session_by_id_and_user_id,
    get_sessions_by_user_id,
)
from app.schemas.session import SessionCreate


def create_new_session(db: Session, current_user_id: int, session_data: SessionCreate):
    return create_session(db, current_user_id, session_data)


def fetch_owned_session_by_id(db: Session, session_id: int, current_user_id: int):
    session = get_session_by_id_and_user_id(db, session_id, current_user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def fetch_user_sessions(db: Session, current_user_id: int):
    return get_sessions_by_user_id(db, current_user_id)