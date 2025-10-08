from fastapi.testclient import TestClient
from app import app, transformer, classifier

client = TestClient(app)


def test_valid_input():
    """Test inference with valid input strings."""
    response = client.post("/predict", json={"text": "I love this product"})
    assert response.status_code == 200
    assert "prediction" in response.json()
    assert response.json()["prediction"] in ["negative", "neutral", "positive"]


def test_multiple_samples():
    """Test inference works for multiple sample strings."""
    samples = [
        "This is terrible",
        "It's okay, nothing special",
        "Absolutely amazing experience",
    ]
    for sample in samples:
        response = client.post("/predict", json={"text": sample})
        assert response.status_code == 200
        assert response.json()["prediction"] in ["negative", "neutral", "positive"]


def test_empty_string():
    """Test that empty string is rejected."""
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_missing_text_field():
    """Test that missing text field returns error."""
    response = client.post("/predict", json={})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_invalid_input_type():
    """Test that non-string input is rejected."""
    response = client.post("/predict", json={"text": 123})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_model_loading():
    """Test that models are loaded without errors."""
    assert transformer is not None
    assert classifier is not None


def test_response_format():
    """Test that response is valid JSON with correct structure."""
    response = client.post("/predict", json={"text": "Good service"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "prediction" in data
    assert isinstance(data["prediction"], str)
