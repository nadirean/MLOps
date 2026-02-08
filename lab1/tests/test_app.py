from app import welcome_root, health_check, predict_endpoint
from api.models.iris import PredictRequest


def test_welcome_root():
    response = welcome_root()
    assert response == {"message": "Welcome to the ML API"}


def test_health_check():
    response = health_check()
    assert response == {"status": "ok"}


def test_predict_endpoint():
    request = PredictRequest(
        sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
    )
    response = predict_endpoint(request)
    assert response.prediction in ["setosa", "versicolor", "virginica"]
