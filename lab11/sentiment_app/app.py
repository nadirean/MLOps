from pathlib import Path
from typing import Optional

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from tokenizers import Tokenizer
from mangum import Mangum

from src.scripts.settings import get_settings

settings = get_settings()
app = FastAPI()
handler = Mangum(app)


def _load_tokenizer(path: Path) -> Optional[Tokenizer]:
    try:
        return Tokenizer.from_file(str(path))
    except Exception as exc:  # pragma: no cover - load-time failure
        print(f"Failed to load tokenizer at {path}: {exc}")
        return None


def _load_session(path: Path) -> Optional[ort.InferenceSession]:
    try:
        return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    except Exception as exc:  # pragma: no cover - load-time failure
        print(f"Failed to load ONNX session at {path}: {exc}")
        return None


tokenizer = _load_tokenizer(settings.onnx_tokenizer_path)
embedding_session = _load_session(settings.onnx_embedding_model_path)
classifier_session = _load_session(settings.onnx_classifier_path)

SENTIMENT_MAP = {0: "negative", 1: "neutral", 2: "positive"}


class PredictRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v.strip()


class PredictResponse(BaseModel):
    prediction: str


@app.post("/predict")
def predict(request: PredictRequest) -> PredictResponse:
    if tokenizer is None or embedding_session is None or classifier_session is None:
        raise HTTPException(status_code=503, detail="Model artifacts not loaded")

    encoded = tokenizer.encode(request.text)
    input_ids = np.array([encoded.ids], dtype=np.int64)
    attention_mask = np.array([encoded.attention_mask], dtype=np.int64)

    embedding_inputs = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
    }
    embeddings = embedding_session.run(None, embedding_inputs)[0]

    classifier_input_name = classifier_session.get_inputs()[0].name
    classifier_inputs = {classifier_input_name: embeddings.astype(np.float32)}
    prediction = classifier_session.run(None, classifier_inputs)[0]

    label = SENTIMENT_MAP.get(int(prediction[0]), "unknown")
    return PredictResponse(prediction=label)
