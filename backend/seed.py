from app.core.database import SessionLocal
from app.models.user import User

def seed_users():
    db = SessionLocal()

    existing_user = db.query(User).filter(User.email == "demo@example.com").first()
    if existing_user:
        print("Demo user already exists")
        db.close()
        return

    demo_user = User(
        email="demo@example.com",
        password_hash="demo-not-real-hash",
        full_name="Demo User"
    )

    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)

    print(f"Created demo user with id={demo_user.id}")

    db.close()

if __name__ == "__main__":
    seed_users()