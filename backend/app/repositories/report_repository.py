from sqlalchemy.orm import Session
from app.models.report import Report


def create_report(
    db: Session,
    session_id: int,
    summary: str,
    strengths: str,
    weaknesses: str,
    study_plan: str,
):
    existing = db.query(Report).filter(Report.session_id == session_id).first()
    if existing:
        return existing

    report = Report(
        session_id=session_id,
        summary=summary,
        strengths=strengths,
        weaknesses=weaknesses,
        study_plan=study_plan,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report_by_session_id(db: Session, session_id: int):
    return db.query(Report).filter(Report.session_id == session_id).first()


def get_reports_by_session_ids(db: Session, session_ids: list[int]):
    if not session_ids:
        return []
    return db.query(Report).filter(Report.session_id.in_(session_ids)).all()