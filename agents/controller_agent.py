from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from agents.cleaning_agent import CleaningAgent
from agents.deduplication_agent import DeduplicationAgent
from agents.extraction_agent import CATEGORIES, ExtractionAgent
from agents.source_selection_agent import SourceSelectionAgent
from agents.storage_agent import StorageAgent
from db.operations import append_job_log, update_job
from utils.logger import logger


class ControllerAgent:
    """Orchestrates the full ingestion pipeline for a single job."""

    def __init__(self) -> None:
        self.source_agent = SourceSelectionAgent()
        self.extraction_agent = ExtractionAgent()
        self.cleaning_agent = CleaningAgent()
        self.dedup_agent = DeduplicationAgent()
        self.storage_agent = StorageAgent()

    async def run_job(
        self,
        job_id: str,
        session: AsyncSession,
        categories: list[str] | None = None,
        max_pages: int = 3,
    ) -> dict:
        """Run full pipeline and return final stats."""
        stats = {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "duplicates_skipped": 0,
        }

        await update_job(session, job_id, status="running", started_at=datetime.now(timezone.utc))
        await session.commit()
        await append_job_log(session, job_id, "Job started")
        await session.commit()

        selected_sources = self.source_agent.select_sources()
        if not selected_sources:
            await append_job_log(session, job_id, "No healthy sources available")
            await update_job(session, job_id, status="failed", completed_at=datetime.now(timezone.utc))
            await session.commit()
            return stats

        target_categories = categories or CATEGORIES

        for source in selected_sources:
            source_name = source["name"]
            await append_job_log(session, job_id, f"Processing source: {source_name}")

            try:
                for category in target_categories:
                    for page in range(1, max_pages + 1):
                        await append_job_log(
                            session, job_id, f"Extracting category={category} page={page}"
                        )
                        await session.commit()

                        try:
                            raw_products = await self.extraction_agent.extract_from_open_food_facts(
                                category=category, page=page
                            )
                        except Exception as exc:
                            logger.error(f"Extraction error ({source_name}, {category}, p{page}): {exc}")
                            stats["errors"] += 1
                            self.source_agent.mark_source_unhealthy(source_name)
                            break

                        if not raw_products:
                            break

                        cleaned = self.cleaning_agent.clean_batch(raw_products)
                        before_dedup = len(cleaned)

                        # Add fingerprints before dedup
                        for p in cleaned:
                            p["fingerprint"] = self.dedup_agent.compute_fingerprint(
                                p.get("name", ""),
                                p.get("brand"),
                                p.get("quantity"),
                                p.get("unit"),
                            )

                        deduped = self.dedup_agent.deduplicate_batch(cleaned)
                        duplicates_in_batch = before_dedup - len(deduped)
                        stats["duplicates_skipped"] += duplicates_in_batch

                        batch_stats = await self.storage_agent.store_batch(session, deduped)
                        await session.commit()

                        stats["inserted"] += batch_stats["inserted"]
                        stats["updated"] += batch_stats["updated"]
                        stats["skipped"] += batch_stats["skipped"]
                        stats["errors"] += batch_stats["errors"]

                        await append_job_log(
                            session,
                            job_id,
                            f"Page {page} done: +{batch_stats['inserted']} inserted, "
                            f"{batch_stats['updated']} updated, {duplicates_in_batch} dupes skipped",
                        )
                        await session.commit()

                self.source_agent.reset_source_health(source_name)

            except Exception as exc:
                logger.error(f"Source {source_name} failed: {exc}")
                self.source_agent.mark_source_unhealthy(source_name)
                stats["errors"] += 1

        await update_job(
            session,
            job_id,
            status="completed",
            completed_at=datetime.now(timezone.utc),
            products_added=stats["inserted"],
            products_updated=stats["updated"],
            duplicates_skipped=stats["duplicates_skipped"],
            errors=stats["errors"],
        )
        await append_job_log(session, job_id, f"Job completed. Stats: {stats}")
        await session.commit()

        logger.info(f"Job {job_id} completed: {stats}")
        return stats
