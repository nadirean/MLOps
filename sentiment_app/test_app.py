from unittest.mock import MagicMock
import pytest
import numpy as np
from fastapi.testclient import TestClient
from sentiment_app import app as app_module

client = TestClient(app_module.app)

@pytest.fixture(autouse=True)
def mock_models():
    """Mock the ONNX models and tokenizer to allow tests to run without artifacts."""
    app_module.tokenizer = MagicMock()
    app_module.embedding_session = MagicMock()
    app_module.classifier_session = MagicMock()

    mock_encoded = MagicMock()
    mock_encoded.ids = [1, 2, 3]
    mock_encoded.attention_mask = [1, 1, 1]
    app_module.tokenizer.encode.return_value = mock_encoded
    app_module.embedding_session.run.return_value = [np.zeros((1, 768))]
    app_module.classifier_session.run.return_value = [np.array([0])]

    mock_input = MagicMock()
    mock_input.name = "float_input"
    app_module.classifier_session.get_inputs.return_value = [mock_input]


def test_valid_input():
    response = client.post("/predict", json={"text": "I love this product"})
    assert response.status_code == 200
    assert "prediction" in response.json()
    assert response.json()["prediction"] in ["negative", "neutral", "positive"]


def test_empty_string():
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422
