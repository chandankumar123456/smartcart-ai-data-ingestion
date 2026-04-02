import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models import Base
from db.database import get_session


@pytest.fixture(scope="module")
def test_app():
    """Create a test FastAPI app backed by in-memory SQLite (set via conftest)."""
    from main import app
    return app


@pytest.fixture(scope="module")
def client(test_app):
    with TestClient(test_app) as c:
        yield c


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


def test_ingest_start(client, mocker):
    mocker.patch(
        "api.routes.orchestrator.start_job",
        return_value="test-job-id-123",
    )
    response = client.post("/ingest/start", json={"source": "open_food_facts"})
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-job-id-123"
    assert data["status"] == "started"


def test_ingest_start_default(client, mocker):
    mocker.patch(
        "api.routes.orchestrator.start_job",
        return_value="test-job-id-456",
    )
    response = client.post("/ingest/start")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data


def test_ingest_status(client):
    response = client.get("/ingest/status")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_ingest_status_not_found(client):
    response = client.get("/ingest/status/nonexistent-job-id")
    assert response.status_code == 404


def test_ingest_logs(client):
    response = client.get("/ingest/logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_ingest_logs_not_found(client):
    response = client.get("/ingest/logs/nonexistent-job-id")
    assert response.status_code == 404


def test_list_products(client):
    response = client.get("/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_products_with_filters(client):
    response = client.get("/products?category=Dairy&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_products_search_ingest(client, mocker):
    mocker.patch(
        "api.routes.extraction_agent.extract_by_query",
        return_value=[
            {
                "product_name": "Amul Milk 500ml",
                "brands": "Amul",
                "categories": "Milk,Dairy",
                "quantity": "500 ml",
                "image_url": "https://example.com/img.jpg",
                "countries_tags": ["en:india"],
                "stores_tags": ["blinkit"],
            }
        ],
    )

    response = client.post("/products/search-ingest", json={"query": "amul milk"})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "amul milk"
    assert data["fetched"] >= 1
    assert "storage" in data
    assert isinstance(data["results"], list)
    assert any("Amul Milk" in item["name"] for item in data["results"])


def test_products_search_ingest_empty_query(client):
    response = client.post("/products/search-ingest", json={"query": "   "})
    assert response.status_code == 400


def test_products_search_ingest_invalid_page_size(client):
    response = client.post("/products/search-ingest", json={"query": "milk", "page_size": 0})
    assert response.status_code == 422


def test_products_search_ingest_invalid_max_pages(client):
    response = client.post("/products/search-ingest", json={"query": "milk", "max_pages": 0})
    assert response.status_code == 422
