import re
from html.parser import HTMLParser

from utils.logger import logger


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


class CleaningAgent:
    """Normalizes and cleans raw product data."""

    UNIT_NORMALIZATION: dict[str, str] = {
        "kg": "kg",
        "kilogram": "kg",
        "kilograms": "kg",
        "g": "g",
        "gram": "g",
        "grams": "g",
        "l": "L",
        "liter": "L",
        "litre": "L",
        "liters": "L",
        "litres": "L",
        "ml": "ml",
        "milliliter": "ml",
        "millilitre": "ml",
        "milliliters": "ml",
        "millilitres": "ml",
        "lb": "lb",
        "pound": "lb",
        "pounds": "lb",
        "oz": "oz",
        "ounce": "oz",
        "ounces": "oz",
        "cl": "cl",
        "centiliter": "cl",
        "centilitre": "cl",
    }

    CATEGORY_MAP: dict[str, str] = {
        "beverages": "Beverages",
        "drinks": "Beverages",
        "juices": "Beverages",
        "sodas": "Beverages",
        "waters": "Beverages",
        "dairy": "Dairy",
        "milk": "Dairy",
        "cheese": "Dairy",
        "yogurt": "Dairy",
        "yogurts": "Dairy",
        "butter": "Dairy",
        "fruits": "Fruits & Vegetables",
        "vegetables": "Fruits & Vegetables",
        "produce": "Fruits & Vegetables",
        "meat": "Meat & Seafood",
        "seafood": "Meat & Seafood",
        "fish": "Meat & Seafood",
        "poultry": "Meat & Seafood",
        "snacks": "Snacks",
        "chips": "Snacks",
        "cookies": "Snacks",
        "crackers": "Snacks",
        "bakery": "Bakery",
        "bread": "Bakery",
        "pastries": "Bakery",
        "cereals": "Breakfast & Cereals",
        "breakfast": "Breakfast & Cereals",
        "oatmeal": "Breakfast & Cereals",
        "frozen": "Frozen Foods",
        "condiments": "Condiments & Sauces",
        "sauces": "Condiments & Sauces",
        "dressings": "Condiments & Sauces",
        "oils": "Oils & Fats",
        "fats": "Oils & Fats",
        "grains": "Grains & Pasta",
        "pasta": "Grains & Pasta",
        "rice": "Grains & Pasta",
        "noodles": "Grains & Pasta",
        "canned": "Canned & Jarred Goods",
        "jarred": "Canned & Jarred Goods",
        "personal care": "Personal Care",
        "hygiene": "Personal Care",
        "cleaning": "Household & Cleaning",
        "household": "Household & Cleaning",
        "groceries": "Groceries",
        "spreads": "Condiments & Sauces",
        "jams": "Condiments & Sauces",
    }

    def parse_tag(self, tag: str, prefix: str = "en:") -> str:
        """Strip a language prefix (e.g. 'en:') from an Open Food Facts tag and title-case the result."""
        if tag.startswith(prefix):
            tag = tag[len(prefix):]
        return tag.replace("-", " ").title()

    def clean_name(self, name: str) -> str:
        """Strip HTML, normalize whitespace, title case."""
        if not name:
            return ""
        stripper = _HTMLStripper()
        stripper.feed(name)
        text = stripper.get_text()
        text = re.sub(r"\s+", " ", text).strip()
        return text.title()

    def normalize_unit(self, quantity_str: str) -> tuple[float | None, str | None]:
        """Parse '500 g' -> (500.0, 'g'), '1kg' -> (1.0, 'kg')."""
        if not quantity_str:
            return None, None
        quantity_str = quantity_str.strip()
        match = re.match(r"^([\d.,]+)\s*([a-zA-Z]+)", quantity_str)
        if not match:
            return None, None
        try:
            amount = float(match.group(1).replace(",", "."))
        except ValueError:
            return None, None
        raw_unit = match.group(2).lower()
        normalized = self.UNIT_NORMALIZATION.get(raw_unit)
        return amount, normalized

    def standardize_category(self, raw_category: str) -> str:
        """Map raw category string to a standard category."""
        if not raw_category:
            return "Other"
        for keyword, standard in self.CATEGORY_MAP.items():
            if keyword in raw_category.lower():
                return standard
        return "Other"

    def clean_price(self, price) -> float | None:
        """Parse and validate price."""
        if price is None:
            return None
        try:
            value = float(price)
            return value if value >= 0 else None
        except (TypeError, ValueError):
            return None

    def clean_product(self, raw: dict) -> dict | None:
        """Clean a single raw product dict into standardized format."""
        try:
            name = self.clean_name(raw.get("product_name") or raw.get("name") or "")
            if not name:
                return None

            brand = raw.get("brands") or raw.get("brand") or ""
            brand = re.sub(r"\s+", " ", brand).strip() if brand else None

            raw_category = raw.get("categories") or raw.get("category") or ""
            category = self.standardize_category(raw_category)

            qty_str = raw.get("quantity") or ""
            quantity, unit = self.normalize_unit(qty_str)

            image_url = raw.get("image_url") or raw.get("image_front_url") or None

            countries = raw.get("countries_tags") or []
            region = self.parse_tag(countries[0]) if countries else None

            stores = raw.get("stores_tags") or []
            source = stores[0] if stores else raw.get("source", "open_food_facts")

            return {
                "name": name,
                "brand": brand,
                "category": category,
                "price": None,
                "quantity": quantity,
                "unit": unit,
                "image_url": image_url,
                "availability": True,
                "source": source or "open_food_facts",
                "region": region,
                "raw_data": raw,
            }
        except Exception as exc:
            logger.warning(f"Failed to clean product: {exc}")
            return None

    def clean_batch(self, raw_products: list[dict]) -> list[dict]:
        """Clean a batch of products, dropping invalid ones."""
        cleaned = []
        for raw in raw_products:
            result = self.clean_product(raw)
            if result:
                cleaned.append(result)
        logger.info(f"Cleaned {len(cleaned)}/{len(raw_products)} products")
        return cleaned
