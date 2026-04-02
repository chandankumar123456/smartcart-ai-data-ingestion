from db.models import Base, Product, IngestionJob
from db.database import init_db, get_session, engine, AsyncSessionLocal
from db.operations import (
    upsert_product,
    get_product_by_fingerprint,
    mark_stale_products,
    get_job,
    create_job,
    update_job,
    append_job_log,
    get_all_jobs,
)

__all__ = [
    "Base",
    "Product",
    "IngestionJob",
    "init_db",
    "get_session",
    "engine",
    "AsyncSessionLocal",
    "upsert_product",
    "get_product_by_fingerprint",
    "mark_stale_products",
    "get_job",
    "create_job",
    "update_job",
    "append_job_log",
    "get_all_jobs",
]
