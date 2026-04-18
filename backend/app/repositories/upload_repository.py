from sqlalchemy.orm import Session
from app.models.uploaded_file import UploadedFile


def create_uploaded_file(
    db: Session,
    session_id: int,
    original_name: str,
    stored_path: str,
    file_type: str | None = None,
):
    db_file = UploadedFile(
        session_id=session_id,
        original_name=original_name,
        stored_path=stored_path,
        file_type=file_type,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_files_by_session_id(db: Session, session_id: int):
    return (
        db.query(UploadedFile)
        .filter(UploadedFile.session_id == session_id)
        .order_by(UploadedFile.id.asc())
        .all()
    )