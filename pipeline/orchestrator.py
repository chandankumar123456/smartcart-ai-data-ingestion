import asyncio
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from agents.controller_agent import ControllerAgent
from db.database import AsyncSessionLocal
from db.operations import create_job
from utils.logger import logger


class IngestionOrchestrator:
    """Manages job queue and scheduling."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.active_jobs: dict[str, asyncio.Task] = {}
        self._controller = ControllerAgent()

    async def start_job(
        self, source: str = "all", categories: list[str] | None = None
    ) -> str:
        """Create and start a new ingestion job. Returns job_id."""
        async with AsyncSessionLocal() as session:
            job = await create_job(session, source)
            job_id = job.id
            await session.commit()

        task = asyncio.create_task(self._run_job_task(job_id, categories))
        self.active_jobs[job_id] = task
        task.add_done_callback(lambda t: self.active_jobs.pop(job_id, None))
        logger.info(f"Started ingestion job {job_id}")
        return job_id

    async def _run_job_task(self, job_id: str, categories: list[str] | None) -> None:
        try:
            async with AsyncSessionLocal() as session:
                await self._controller.run_job(job_id, session, categories=categories)
        except Exception as exc:
            logger.error(f"Job {job_id} task failed: {exc}")
            async with AsyncSessionLocal() as session:
                from db.operations import update_job
                await update_job(
                    session,
                    job_id,
                    status="failed",
                    completed_at=datetime.now(timezone.utc),
                )
                await session.commit()

    def get_job_status(self, job_id: str) -> str:
        if job_id in self.active_jobs:
            return "running"
        return "unknown"

    def start_scheduler(self, interval_hours: int = 6) -> None:
        """Schedule periodic ingestion every N hours."""
        self.scheduler.add_job(
            self.start_job,
            "interval",
            hours=interval_hours,
            id="periodic_ingestion",
            replace_existing=True,
        )
        if not self.scheduler.running:
            self.scheduler.start()
        logger.info(f"Scheduler started with {interval_hours}h interval")

    def stop_scheduler(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")
