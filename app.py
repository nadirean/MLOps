from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    prediction: str


@app.post("/predict")
def predict(request: PredictRequest) -> PredictResponse:
    return PredictResponse(prediction="positive")
