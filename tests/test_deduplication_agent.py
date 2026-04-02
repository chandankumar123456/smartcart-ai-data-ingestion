import pytest

from agents.deduplication_agent import DeduplicationAgent


@pytest.fixture
def agent():
    return DeduplicationAgent()


def test_compute_fingerprint_consistent(agent):
    fp1 = agent.compute_fingerprint("Nutella", "Ferrero", 400.0, "g")
    fp2 = agent.compute_fingerprint("Nutella", "Ferrero", 400.0, "g")
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA256 hex


def test_compute_fingerprint_case_insensitive(agent):
    fp1 = agent.compute_fingerprint("NUTELLA", "FERRERO", 400.0, "g")
    fp2 = agent.compute_fingerprint("nutella", "ferrero", 400.0, "g")
    assert fp1 == fp2


def test_compute_fingerprint_different_products(agent):
    fp1 = agent.compute_fingerprint("Nutella", "Ferrero", 400.0, "g")
    fp2 = agent.compute_fingerprint("Nutella", "Ferrero", 200.0, "g")
    assert fp1 != fp2


def test_similarity_ratio(agent):
    assert agent.similarity_ratio("hello", "hello") == 1.0
    assert agent.similarity_ratio("hello", "world") < 0.5
    ratio = agent.similarity_ratio("Nutella Spread", "Nutella Chocolate Spread")
    assert ratio > 0.7


def test_is_duplicate_true(agent):
    a = {"name": "Nutella Spread", "brand": "Ferrero", "quantity": 400.0, "unit": "g"}
    b = {"name": "Nutella Spread", "brand": "Ferrero", "quantity": 400.0, "unit": "g"}
    assert agent.is_duplicate(a, b) is True


def test_is_duplicate_false_different_brand(agent):
    a = {"name": "Chocolate Spread", "brand": "Ferrero", "quantity": 400.0, "unit": "g"}
    b = {"name": "Chocolate Spread", "brand": "Nutiva", "quantity": 400.0, "unit": "g"}
    assert agent.is_duplicate(a, b) is False


def test_is_duplicate_false_different_name(agent):
    a = {"name": "Apple Juice", "brand": "Tropicana", "quantity": 1.0, "unit": "L"}
    b = {"name": "Orange Juice", "brand": "Tropicana", "quantity": 1.0, "unit": "L"}
    assert agent.is_duplicate(a, b) is False


def test_deduplicate_batch_removes_duplicates(agent):
    products = [
        {"name": "Milk", "brand": "Brand A", "quantity": 1.0, "unit": "L"},
        {"name": "Milk", "brand": "Brand A", "quantity": 1.0, "unit": "L"},
        {"name": "Bread", "brand": "Brand B", "quantity": 500.0, "unit": "g"},
    ]
    result = agent.deduplicate_batch(products)
    assert len(result) == 2
    names = {p["name"] for p in result}
    assert "Milk" in names
    assert "Bread" in names


def test_deduplicate_batch_adds_fingerprint(agent):
    products = [
        {"name": "Milk", "brand": "Brand A", "quantity": 1.0, "unit": "L"},
    ]
    result = agent.deduplicate_batch(products)
    assert "fingerprint" in result[0]
    assert len(result[0]["fingerprint"]) == 64


def test_deduplicate_batch_respects_existing_fingerprint(agent):
    fp = agent.compute_fingerprint("Milk", "Brand A", 1.0, "L")
    products = [
        {"name": "Milk", "brand": "Brand A", "quantity": 1.0, "unit": "L", "fingerprint": fp},
        {"name": "Milk", "brand": "Brand A", "quantity": 1.0, "unit": "L", "fingerprint": fp},
    ]
    result = agent.deduplicate_batch(products)
    assert len(result) == 1
