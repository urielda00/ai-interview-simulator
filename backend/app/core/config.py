import json
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    APP_NAME: str = os.getenv("APP_NAME", "AI Interview Simulator API")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "")
    OPENAI_TIMEOUT_SECONDS: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "20"))
    OPENAI_MAX_RETRIES: int = int(os.getenv("OPENAI_MAX_RETRIES", "1"))

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

    PROJECT_AWARE_MAX_FILES: int = int(os.getenv("PROJECT_AWARE_MAX_FILES", "5"))
    PROJECT_AWARE_MAX_FILE_BYTES: int = int(os.getenv("PROJECT_AWARE_MAX_FILE_BYTES", "200000"))
    PROJECT_AWARE_MAX_TOTAL_CHARS: int = int(os.getenv("PROJECT_AWARE_MAX_TOTAL_CHARS", "25000"))

    PROJECT_AWARE_TEXT_EXTENSIONS: list[str] = json.loads(
        os.getenv(
            "PROJECT_AWARE_TEXT_EXTENSIONS",
            """
            [
              ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt", ".go", ".rb", ".php",
              ".cs", ".cpp", ".c", ".h", ".hpp", ".swift", ".rs", ".scala", ".sql",
              ".json", ".yml", ".yaml", ".toml", ".ini", ".env", ".md", ".txt", ".xml", ".html", ".css"
            ]
            """,
        )
    )

    PROJECT_AWARE_TEXT_MIME_PREFIXES: list[str] = json.loads(
        os.getenv(
            "PROJECT_AWARE_TEXT_MIME_PREFIXES",
            """
            [
              "text/",
              "application/json",
              "application/xml",
              "application/javascript",
              "application/x-javascript",
              "application/typescript",
              "application/x-python-code"
            ]
            """,
        )
    )


settings = Settings()