import shutil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.upload_repository import create_uploaded_file, get_files_by_session_id


def ensure_upload_dir_exists() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def save_project_file(db: Session, session_id: int, file: UploadFile):
    upload_dir = ensure_upload_dir_exists()
    session_dir = upload_dir / f"session_{session_id}"
    session_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename or "uploaded_file").name
    file_path = session_dir / safe_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return create_uploaded_file(
        db=db,
        session_id=session_id,
        original_name=safe_name,
        stored_path=str(file_path),
        file_type=file.content_type,
    )


def list_session_files(db: Session, session_id: int):
    return get_files_by_session_id(db, session_id)