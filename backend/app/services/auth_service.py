from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import create_user, get_user_by_email, get_user_by_id
from app.schemas.auth import UserCreate, UserLogin


def register_user(db: Session, user_data: UserCreate):
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = hash_password(user_data.password)

    return create_user(
        db=db,
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
    )


def login_user(db: Session, login_data: UserLogin):
    user = get_user_by_email(db, login_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.password_hash.startswith("$2"):
        raise HTTPException(status_code=500, detail="User password hash is invalid or from an old seed")

    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user.id))
    return {
        "access_token": token,
        "token_type": "bearer",
    }


def fetch_user_by_id(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user