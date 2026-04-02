from utils.http_client import fetch
from utils.logger import logger

CATEGORIES = [
    "en:groceries",
    "en:beverages",
    "en:dairy-products",
    "en:snacks",
    "en:cereals",
    "en:fruits",
    "en:vegetables",
]

FIELDS = "code,product_name,brands,categories,quantity,image_url,countries_tags,stores_tags,nutriments"


class ExtractionAgent:
    """Fetches raw product data from sources."""

    async def extract_from_open_food_facts(
        self, category: str = "en:groceries", page: int = 1, page_size: int = 50
    ) -> list[dict]:
        """Call Open Food Facts API and return list of raw product dicts."""
        url = (
            f"https://world.openfoodfacts.org/api/v2/search"
            f"?categories_tags={category}&page={page}&page_size={page_size}&fields={FIELDS}"
        )
        logger.info(f"Extracting from Open Food Facts: category={category} page={page}")
        data = await fetch(url)
        if not data or "products" not in data:
            logger.warning(f"No products returned for category={category} page={page}")
            return []

        products = data["products"]
        logger.info(f"Retrieved {len(products)} raw products from Open Food Facts (category={category})")
        return products

    async def extract_from_category(self, category: str, page: int = 1) -> list[dict]:
        """Extract from a specific category tag."""
        return await self.extract_from_open_food_facts(category=category, page=page)

    async def extract_by_query(
        self,
        query: str,
        page: int = 1,
        page_size: int = 50,
    ) -> list[dict]:
        """Search Open Food Facts by free-text query and return raw products."""
        url = (
            f"https://world.openfoodfacts.org/api/v2/search"
            f"?search_terms={query}&page={page}&page_size={page_size}&fields={FIELDS}"
        )
        logger.info(f"Extracting by query from Open Food Facts: query={query} page={page}")
        data = await fetch(url)
        if not data or "products" not in data:
            logger.warning(f"No products returned for query={query} page={page}")
            return []

        products = data["products"]
        logger.info(f"Retrieved {len(products)} raw products from query={query}")
        return products

    async def extract(self, source: dict, **kwargs) -> list[dict]:
        """Route to appropriate extraction method based on source name."""
        name = source.get("name", "")
        if name in ("open_food_facts", "open_food_facts_category"):
            return await self.extract_from_open_food_facts(**kwargs)
        logger.warning(f"Unknown source: {name}")
        return []
