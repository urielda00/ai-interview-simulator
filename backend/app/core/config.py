import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    APP_NAME: str = os.getenv("APP_NAME", "AI Interview Simulator API")

settings = Settings()