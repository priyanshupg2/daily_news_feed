import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import feed, feedback, profile, raw_data
from src.config import settings
from src.db.database import init_db
from src.intelligence.pipeline import run_discovery, run_full_pipeline

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    # Discovery every 2h, full pipeline at 06:00 local time daily.
    scheduler.add_job(
        run_discovery,
        CronTrigger(hour="*/2"),
        id="discovery",
        replace_existing=True,
    )
    scheduler.add_job(
        run_full_pipeline,
        CronTrigger(hour=6, minute=0),
        id="daily_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: discovery=every 2h, pipeline=06:00 daily")

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(title="Prism (Daily News Feed)", version="0.1.0", lifespan=lifespan)

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
    return {
        "status": "ok",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_configured": bool(settings.ANTHROPIC_API_KEY),
    }
