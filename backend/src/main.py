from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db.database import init_db
from src.api import feed, profile, feedback, raw_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Daily News Feed", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feed.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(raw_data.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
