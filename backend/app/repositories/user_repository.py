from sqlalchemy.orm import Session
from app.models.user import User


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, password_hash: str, full_name: str | None = None):
    user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user