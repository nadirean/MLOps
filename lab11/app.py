from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from sentence_transformers import SentenceTransformer
import joblib

app = FastAPI()

# Load models at startup
transformer = SentenceTransformer("model/sentence_transformer.model")
classifier = joblib.load("model/classifier.joblib")

LABEL_MAP = {0: "negative", 1: "neutral", 2: "positive"}


class PredictRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v


class PredictResponse(BaseModel):
    prediction: str


@app.post("/predict")
def predict(request: PredictRequest) -> PredictResponse:
    embedding = transformer.encode([request.text])
    prediction = classifier.predict(embedding)[0]
    return PredictResponse(prediction=LABEL_MAP[prediction])
