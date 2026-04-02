from sqlalchemy.ext.asyncio import AsyncSession

from db.operations import upsert_product
from utils.logger import logger


class StorageAgent:
    """Persists cleaned, deduplicated products to database."""

    async def store_product(self, session: AsyncSession, product: dict) -> tuple[str, bool]:
        """Store or update product. Returns (action, success)."""
        try:
            action, success = await upsert_product(session, product)
            return action, success
        except Exception as exc:
            logger.error(f"store_product error: {exc}")
            return "error", False

    async def store_batch(self, session: AsyncSession, products: list[dict]) -> dict:
        """Store batch. Returns stats: {inserted, updated, skipped, errors}."""
        stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
        for product in products:
            action, success = await self.store_product(session, product)
            if not success:
                stats["errors"] += 1
            elif action == "inserted":
                stats["inserted"] += 1
            elif action == "updated":
                stats["updated"] += 1
            else:
                stats["skipped"] += 1
        logger.info(f"Batch storage complete: {stats}")
        return stats
