from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.user_repository import create_user, get_user_by_email, get_user_by_id
from app.schemas.auth import UserCreate


def register_user(db: Session, user_data: UserCreate):
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    return create_user(db, user_data)


def fetch_user_by_id(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user