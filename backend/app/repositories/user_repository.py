from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserCreate


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_data: UserCreate):
    user = User(
        email=user_data.email,
        password_hash=user_data.password,
        full_name=user_data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user