import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models import Base
from db.operations import (
    append_job_log,
    create_job,
    get_job,
    get_product_by_fingerprint,
    upsert_product,
)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s

    await engine.dispose()


SAMPLE_PRODUCT = {
    "name": "Test Milk",
    "brand": "Dairy Co",
    "category": "Dairy",
    "price": None,
    "quantity": 1.0,
    "unit": "L",
    "image_url": None,
    "availability": True,
    "source": "open_food_facts",
    "region": "France",
    "raw_data": {},
    "fingerprint": "abc123fingerprint456",
}


@pytest.mark.asyncio
async def test_upsert_product_insert(session):
    action, success = await upsert_product(session, SAMPLE_PRODUCT)
    assert success is True
    assert action == "inserted"


@pytest.mark.asyncio
async def test_upsert_product_update(session):
    await upsert_product(session, SAMPLE_PRODUCT)
    updated = dict(SAMPLE_PRODUCT)
    updated["brand"] = "Updated Brand"
    action, success = await upsert_product(session, updated)
    assert success is True
    assert action == "updated"

    product = await get_product_by_fingerprint(session, SAMPLE_PRODUCT["fingerprint"])
    assert product is not None
    assert product.brand == "Updated Brand"


@pytest.mark.asyncio
async def test_upsert_product_no_fingerprint(session):
    bad = dict(SAMPLE_PRODUCT)
    del bad["fingerprint"]
    action, success = await upsert_product(session, bad)
    assert success is False
    assert action == "error"


@pytest.mark.asyncio
async def test_create_and_get_job(session):
    job = await create_job(session, source="open_food_facts")
    assert job.id is not None
    assert job.status == "pending"
    assert job.source == "open_food_facts"

    fetched = await get_job(session, job.id)
    assert fetched is not None
    assert fetched.id == job.id


@pytest.mark.asyncio
async def test_get_job_not_found(session):
    result = await get_job(session, "nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_append_job_log(session):
    job = await create_job(session, source="test")
    await append_job_log(session, job.id, "First message")
    await append_job_log(session, job.id, "Second message")

    fetched = await get_job(session, job.id)
    assert fetched is not None
    assert len(fetched.logs) == 2
    assert fetched.logs[0]["message"] == "First message"
    assert fetched.logs[1]["message"] == "Second message"


@pytest.mark.asyncio
async def test_get_product_by_fingerprint_not_found(session):
    result = await get_product_by_fingerprint(session, "doesnotexist")
    assert result is None
