from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.repositories.session_repository import get_session_by_id_and_user_id
from app.schemas.upload import UploadedFileResponse
from app.services.upload_service import save_project_file, list_session_files

router = APIRouter()


@router.post("/project-files/{session_id}", response_model=UploadedFileResponse)
def upload_project_file(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = get_session_by_id_and_user_id(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return save_project_file(db, session_id, file)


@router.get("/project-files/{session_id}", response_model=list[UploadedFileResponse])
def get_project_files(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = get_session_by_id_and_user_id(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return list_session_files(db, session_id)