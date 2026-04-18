from sqlalchemy.orm import Session

from app.models.interview_session import InterviewSession
from app.schemas.session import SessionCreate


def create_session(db: Session, user_id: int, session_data: SessionCreate) -> InterviewSession:
    db_session = InterviewSession(
        user_id=user_id,
        track=session_data.track,
        level=session_data.level,
        mode=session_data.mode,
        status="created",
        current_question_index=0,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_session_by_id(db: Session, session_id: int):
    return db.query(InterviewSession).filter(InterviewSession.id == session_id).first()


def get_session_by_id_and_user_id(db: Session, session_id: int, user_id: int):
    return (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
        .first()
    )


def get_sessions_by_user_id(db: Session, user_id: int):
    return (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.id.desc())
        .all()
    )