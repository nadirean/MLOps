from fastapi.testclient import TestClient
from sentiment_app.app import app

client = TestClient(app)


def test_valid_input():
    response = client.post("/predict", json={"text": "I love this product"})
    assert response.status_code == 200
    assert "prediction" in response.json()


def test_empty_string():
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422
