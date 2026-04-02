import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import orchestrator, router
from db.database import init_db
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    interval_hours = int(os.getenv("SCHEDULER_INTERVAL_HOURS", "6"))
    orchestrator.start_scheduler(interval_hours=interval_hours)
    logger.info("SmartCart AI Data Ingestion service started")
    yield
    orchestrator.stop_scheduler()
    logger.info("SmartCart AI Data Ingestion service stopped")


app = FastAPI(
    title="SmartCart AI Data Ingestion",
    version="1.0.0",
    description="Autonomous grocery data ingestion system",
    lifespan=lifespan,
)

app.include_router(router)
