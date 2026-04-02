import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import IngestionJob, Product
from utils.logger import logger


async def upsert_product(session: AsyncSession, product_data: dict) -> tuple[str, bool]:
    """Insert or update a product by fingerprint. Returns (action, success)."""
    fingerprint = product_data.get("fingerprint")
    if not fingerprint:
        return "error", False

    try:
        existing = await get_product_by_fingerprint(session, fingerprint)
        now = datetime.now(timezone.utc)

        if existing:
            for key, value in product_data.items():
                if key not in ("id", "created_at", "fingerprint") and value is not None:
                    setattr(existing, key, value)
            existing.updated_at = now
            existing.last_seen_at = now
            existing.is_active = True
            await session.flush()
            return "updated", True
        else:
            product = Product(
                id=str(uuid.uuid4()),
                **{k: v for k, v in product_data.items() if k != "id"},
            )
            session.add(product)
            await session.flush()
            return "inserted", True
    except Exception as exc:
        logger.error(f"upsert_product error: {exc}")
        return "error", False


async def get_product_by_fingerprint(session: AsyncSession, fingerprint: str) -> Product | None:
    result = await session.execute(select(Product).where(Product.fingerprint == fingerprint))
    return result.scalars().first()


async def mark_stale_products(session: AsyncSession, cutoff_hours: int = 48) -> int:
    """Deactivate products not seen within cutoff_hours. Returns count updated."""
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(hours=cutoff_hours)
    result = await session.execute(
        update(Product)
        .where(Product.last_seen_at < cutoff, Product.is_active.is_(True))  # noqa: E712
        .values(is_active=False, updated_at=datetime.now(timezone.utc))
    )
    await session.flush()
    return result.rowcount


async def get_job(session: AsyncSession, job_id: str) -> IngestionJob | None:
    result = await session.execute(select(IngestionJob).where(IngestionJob.id == job_id))
    return result.scalars().first()


async def create_job(session: AsyncSession, source: str) -> IngestionJob:
    job = IngestionJob(
        id=str(uuid.uuid4()),
        status="pending",
        source=source,
        logs=[],
    )
    session.add(job)
    await session.flush()
    return job


async def update_job(session: AsyncSession, job_id: str, **kwargs) -> None:
    await session.execute(update(IngestionJob).where(IngestionJob.id == job_id).values(**kwargs))
    await session.flush()


async def append_job_log(session: AsyncSession, job_id: str, message: str) -> None:
    job = await get_job(session, job_id)
    if job is None:
        return
    current_logs = list(job.logs or [])
    current_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": message})
    job.logs = current_logs
    await session.flush()


async def get_all_jobs(session: AsyncSession, limit: int = 50) -> list[IngestionJob]:
    result = await session.execute(
        select(IngestionJob).order_by(IngestionJob.started_at.desc().nullslast()).limit(limit)
    )
    return list(result.scalars().all())
