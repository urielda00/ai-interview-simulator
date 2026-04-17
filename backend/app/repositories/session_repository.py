from sqlalchemy.orm import Session
from app.models.interview_session import InterviewSession
from app.schemas.session import SessionCreate


def create_session(db: Session, session_data: SessionCreate) -> InterviewSession:
    db_session = InterviewSession(
        user_id=session_data.user_id,
        track=session_data.track,
        level=session_data.level,
        mode=session_data.mode,
        status="created",
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_session_by_id(db: Session, session_id: int):
    return db.query(InterviewSession).filter(InterviewSession.id == session_id).first()