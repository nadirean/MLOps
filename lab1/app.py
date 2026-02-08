from fastapi import FastAPI
from api.models.iris import PredictRequest, PredictResponse
from inference import load_model, predict

app = FastAPI()
model = load_model()


@app.get("/")
def welcome_root():
    return {"message": "Welcome to the ML API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(request: PredictRequest):
    data = [
        request.sepal_length,
        request.sepal_width,
        request.petal_length,
        request.petal_width,
    ]
    prediction = predict(model, data)
    return PredictResponse(prediction=prediction)
