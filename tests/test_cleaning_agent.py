import pytest

from agents.cleaning_agent import CleaningAgent


@pytest.fixture
def agent():
    return CleaningAgent()


def test_clean_name(agent):
    assert agent.clean_name("  hello   world  ") == "Hello World"
    assert agent.clean_name("<b>Nutella</b>") == "Nutella"
    assert agent.clean_name("") == ""


def test_normalize_unit_grams(agent):
    qty, unit = agent.normalize_unit("500 g")
    assert qty == 500.0
    assert unit == "g"

    qty, unit = agent.normalize_unit("200grams")
    assert qty == 200.0
    assert unit == "g"


def test_normalize_unit_kg(agent):
    qty, unit = agent.normalize_unit("1kg")
    assert qty == 1.0
    assert unit == "kg"

    qty, unit = agent.normalize_unit("2.5 kilograms")
    assert qty == 2.5
    assert unit == "kg"


def test_normalize_unit_liters(agent):
    qty, unit = agent.normalize_unit("1 liter")
    assert qty == 1.0
    assert unit == "L"

    qty, unit = agent.normalize_unit("750ml")
    assert qty == 750.0
    assert unit == "ml"


def test_normalize_unit_invalid(agent):
    qty, unit = agent.normalize_unit("")
    assert qty is None
    assert unit is None

    qty, unit = agent.normalize_unit("no numbers here")
    assert qty is None
    assert unit is None


def test_standardize_category(agent):
    assert agent.standardize_category("dairy products") == "Dairy"
    assert agent.standardize_category("beverages and drinks") == "Beverages"
    assert agent.standardize_category("snacks and chips") == "Snacks"
    assert agent.standardize_category("unknown stuff") == "Other"
    assert agent.standardize_category("") == "Other"


def test_clean_product(agent):
    raw = {
        "product_name": "Nutella",
        "brands": "Ferrero",
        "categories": "spreads",
        "quantity": "400 g",
        "image_url": "https://images.openfoodfacts.org/nutella.jpg",
        "countries_tags": ["en:france"],
        "stores_tags": ["carrefour"],
    }
    result = agent.clean_product(raw)
    assert result is not None
    assert result["name"] == "Nutella"
    assert result["brand"] == "Ferrero"
    assert result["quantity"] == 400.0
    assert result["unit"] == "g"
    assert result["region"] == "France"


def test_clean_product_no_name(agent):
    result = agent.clean_product({"brands": "Ferrero"})
    assert result is None


def test_clean_batch(agent):
    raw_list = [
        {"product_name": "Milk", "brands": "Brand A", "quantity": "1 L"},
        {"product_name": "", "brands": "Brand B"},  # invalid - no name
        {"product_name": "Bread", "brands": "Brand C"},
    ]
    result = agent.clean_batch(raw_list)
    assert len(result) == 2
    assert result[0]["name"] == "Milk"
    assert result[1]["name"] == "Bread"
