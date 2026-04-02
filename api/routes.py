from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import IngestionJob, Product
from db.operations import get_all_jobs, get_job
from pipeline.orchestrator import IngestionOrchestrator
from utils.logger import logger

router = APIRouter()
orchestrator = IngestionOrchestrator()


class IngestStartRequest(BaseModel):
    source: str = "all"
    categories: list[str] | None = None


def _job_to_dict(job: IngestionJob) -> dict:
    return {
        "id": job.id,
        "status": job.status,
        "source": job.source,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "products_added": job.products_added,
        "products_updated": job.products_updated,
        "duplicates_skipped": job.duplicates_skipped,
        "errors": job.errors,
    }


@router.post("/ingest/start")
async def ingest_start(
    body: IngestStartRequest = IngestStartRequest(),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Start a new ingestion job."""
    job_id = await orchestrator.start_job(source=body.source, categories=body.categories)
    return {"job_id": job_id, "status": "started"}


@router.get("/ingest/status")
async def ingest_status_all(
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """List all jobs with status."""
    jobs = await get_all_jobs(session)
    return [_job_to_dict(j) for j in jobs]


@router.get("/ingest/status/{job_id}")
async def ingest_status(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get specific job status."""
    job = await get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_dict(job)


@router.get("/ingest/logs")
async def ingest_logs_all(
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Get logs for all recent jobs."""
    jobs = await get_all_jobs(session)
    return [{"job_id": j.id, "status": j.status, "logs": j.logs or []} for j in jobs]


@router.get("/ingest/logs/{job_id}")
async def ingest_logs(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get logs for specific job."""
    job = await get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job.id, "status": job.status, "logs": job.logs or []}


@router.get("/products")
async def list_products(
    category: str | None = Query(default=None),
    brand: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """List products with optional filters."""
    query = select(Product).where(Product.is_active.is_(True))

    if category:
        query = query.where(Product.category.ilike(f"%{category}%"))
    if brand:
        query = query.where(Product.brand.ilike(f"%{brand}%"))
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    products = result.scalars().all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "price": p.price,
            "quantity": p.quantity,
            "unit": p.unit,
            "image_url": p.image_url,
            "availability": p.availability,
            "source": p.source,
            "region": p.region,
            "is_active": p.is_active,
            "last_seen_at": p.last_seen_at.isoformat() if p.last_seen_at else None,
        }
        for p in products
    ]


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "smartcart-ai-data-ingestion"}
