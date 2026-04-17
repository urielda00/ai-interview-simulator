from fastapi import FastAPI
from app.api.router import api_router
from app.core.database import Base, engine
from app.core.config import settings
import app.models

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "AI Interview Simulator API is running"}