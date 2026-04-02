import hashlib
from difflib import SequenceMatcher

from utils.logger import logger


class DeduplicationAgent:
    """Detects and merges duplicate products."""

    def compute_fingerprint(
        self,
        name: str,
        brand: str | None,
        quantity: float | None,
        unit: str | None,
    ) -> str:
        """Create stable SHA256 hash for dedup. Normalizes inputs before hashing."""
        normalized = "|".join(
            [
                (name or "").lower().strip(),
                (brand or "").lower().strip(),
                str(quantity) if quantity is not None else "",
                (unit or "").lower().strip(),
            ]
        )
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def similarity_ratio(self, a: str, b: str) -> float:
        """String similarity using SequenceMatcher."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def is_duplicate(
        self, product_a: dict, product_b: dict, threshold: float = 0.85
    ) -> bool:
        """Check if two products are duplicates based on name+brand+quantity similarity."""
        name_sim = self.similarity_ratio(
            product_a.get("name", ""),
            product_b.get("name", ""),
        )
        if name_sim < threshold:
            return False

        brand_a = (product_a.get("brand") or "").lower().strip()
        brand_b = (product_b.get("brand") or "").lower().strip()
        if brand_a and brand_b and brand_a != brand_b:
            return False

        qty_a = product_a.get("quantity")
        qty_b = product_b.get("quantity")
        unit_a = (product_a.get("unit") or "").lower()
        unit_b = (product_b.get("unit") or "").lower()
        if qty_a is not None and qty_b is not None:
            if qty_a != qty_b or unit_a != unit_b:
                return False

        return True

    def deduplicate_batch(self, products: list[dict]) -> list[dict]:
        """Remove duplicates within a batch before storage, using fingerprint."""
        seen_fingerprints: set[str] = set()
        unique: list[dict] = []
        for product in products:
            fp = product.get("fingerprint")
            if not fp:
                fp = self.compute_fingerprint(
                    product.get("name", ""),
                    product.get("brand"),
                    product.get("quantity"),
                    product.get("unit"),
                )
                product["fingerprint"] = fp
            if fp not in seen_fingerprints:
                seen_fingerprints.add(fp)
                unique.append(product)
        skipped = len(products) - len(unique)
        if skipped:
            logger.info(f"Deduplication removed {skipped} duplicates from batch")
        return unique
