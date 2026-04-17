from sqlalchemy.orm import Session
from app.repositories.session_repository import create_session, get_session_by_id
from app.schemas.session import SessionCreate


def create_new_session(db: Session, session_data: SessionCreate):
    return create_session(db, session_data)


def fetch_session_by_id(db: Session, session_id: int):
    return get_session_by_id(db, session_id)