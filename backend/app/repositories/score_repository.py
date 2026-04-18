from sqlalchemy.orm import Session
from app.models.score import Score


def create_score(
    db: Session,
    session_id: int,
    message_id: int | None,
    category: str,
    score: float,
    confidence: float | None = None,
):
    db_score = Score(
        session_id=session_id,
        message_id=message_id,
        category=category,
        score=score,
        confidence=confidence,
    )
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return db_score


def get_scores_by_session_id(db: Session, session_id: int):
    return (
        db.query(Score)
        .filter(Score.session_id == session_id)
        .order_by(Score.id.asc())
        .all()
    )


def get_scores_by_session_ids(db: Session, session_ids: list[int]):
    if not session_ids:
        return []
    return (
        db.query(Score)
        .filter(Score.session_id.in_(session_ids))
        .order_by(Score.id.asc())
        .all()
    )