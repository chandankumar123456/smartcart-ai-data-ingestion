import re
from html.parser import HTMLParser
from urllib.parse import urlparse


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def sanitize_name(name: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    if not name:
        return ""
    stripper = _HTMLStripper()
    stripper.feed(name)
    text = stripper.get_text()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def validate_price(price) -> float | None:
    """Return a non-negative float price or None."""
    if price is None:
        return None
    try:
        value = float(price)
        return value if value >= 0 else None
    except (TypeError, ValueError):
        return None


def validate_url(url: str | None) -> str | None:
    """Return url if valid http/https URL, else None."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return url
    except Exception:
        pass
    return None


def validate_required_fields(data: dict, required: list[str]) -> list[str]:
    """Return list of missing required field names."""
    return [f for f in required if not data.get(f)]


def validate_product_data(data: dict) -> dict:
    """Sanitize and validate a product data dict. Raises ValueError on critical failures."""
    name = sanitize_name(data.get("name", ""))
    if not name:
        raise ValueError("Product name is required")

    result = dict(data)
    result["name"] = name
    result["price"] = validate_price(data.get("price"))
    result["image_url"] = validate_url(data.get("image_url"))

    return result
