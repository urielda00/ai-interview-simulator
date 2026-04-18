import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def validate_credentials(email: str, password: str) -> bool:
    return bool(email and password)

def login_user(email: str, password: str):
    if not validate_credentials(email, password):
        raise ValueError("invalid credentials")
    token = jwt.encode({"sub": email}, "secret", algorithm="HS256")
    password_hash = pwd_context.hash(password)
    return {"token": token, "password_hash": password_hash}
