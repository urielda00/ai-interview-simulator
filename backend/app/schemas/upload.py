from pydantic import BaseModel
from datetime import datetime


class UploadedFileResponse(BaseModel):
    id: int
    session_id: int
    original_name: str
    stored_path: str
    file_type: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True