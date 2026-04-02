class SourceSelectionAgent:
    """Selects best available data source based on health/reliability."""

    SOURCES = [
        {
            "name": "open_food_facts",
            "url": "https://world.openfoodfacts.org/api/v2/search",
            "priority": 1,
            "healthy": True,
        },
        {
            "name": "open_food_facts_category",
            "url": "https://world.openfoodfacts.org/category/",
            "priority": 2,
            "healthy": True,
        },
    ]

    def select_sources(self) -> list[dict]:
        """Return ordered list of healthy sources by priority."""
        return sorted(
            [s for s in self.SOURCES if s["healthy"]],
            key=lambda s: s["priority"],
        )

    def mark_source_unhealthy(self, name: str) -> None:
        """Mark a source as unhealthy after failure."""
        for source in self.SOURCES:
            if source["name"] == name:
                source["healthy"] = False
                break

    def reset_source_health(self, name: str) -> None:
        """Reset source health after successful use."""
        for source in self.SOURCES:
            if source["name"] == name:
                source["healthy"] = True
                break
