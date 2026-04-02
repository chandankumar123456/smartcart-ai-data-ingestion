# SmartCart AI Data Ingestion

An autonomous grocery data ingestion system that fetches, cleans, deduplicates, and stores product data from the Open Food Facts API.

## Features

- **Multi-agent pipeline**: Modular agents for source selection, extraction, cleaning, deduplication, and storage
- **Open Food Facts integration**: Fetches real grocery product data across multiple categories
- **Async-first**: Built with `asyncio`, `httpx`, and SQLAlchemy async engine
- **Rate limiting & retries**: Per-domain token bucket rate limiter with exponential backoff
- **Deduplication**: SHA256 fingerprinting + `difflib.SequenceMatcher` similarity checks
- **REST API**: FastAPI with endpoints for triggering jobs, monitoring status, and querying products
- **Scheduled ingestion**: APScheduler for periodic data refreshes (default: every 6 hours)

## Project Structure

```
agents/          # Modular pipeline agents
pipeline/        # Orchestrator and job management
api/             # FastAPI routes
db/              # SQLAlchemy models and async operations
utils/           # HTTP client, rate limiter, validators, logger
tests/           # pytest test suite
main.py          # Application entry point
```

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingest/start` | Start ingestion job |
| GET | `/ingest/status` | List all jobs |
| GET | `/ingest/status/{job_id}` | Get specific job status |
| GET | `/ingest/logs` | Get logs for all jobs |
| GET | `/ingest/logs/{job_id}` | Get logs for specific job |
| GET | `/products` | List products (supports `category`, `brand`, `search` filters) |
| POST | `/products/search-ingest` | Search products online, ingest into DB, then return DB-backed results |
| GET | `/health` | Health check |

## Running Tests

```bash
python -m pytest tests/ -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./smartcart.db` | Database connection URL |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SCHEDULER_INTERVAL_HOURS` | `6` | Hours between scheduled ingestion runs |
| `MAX_PAGES_PER_SOURCE` | `3` | Maximum pages to fetch per category |
| `REQUEST_DELAY_SECONDS` | `1.0` | Delay between requests (rate limiting) |
| `MAX_RETRIES` | `3` | Maximum HTTP retry attempts |
