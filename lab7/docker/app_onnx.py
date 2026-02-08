import time
import onnxruntime as ort
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer
import numpy as np

app = FastAPI()

model_name = "sentence-transformers/multi-qa-mpnet-base-cos-v1"
tokenizer = None
ort_session = None

class TextRequest(BaseModel):
    text: str

@app.on_event("startup")
async def startup_event():
    global tokenizer, ort_session
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    print("Loading ONNX model...")
    # Load the optimized model
    sess_options = ort.SessionOptions()
    # Disable optimizations as they are already baked into the model
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
    
    ort_session = ort.InferenceSession(
        "model_optimized.onnx",
        sess_options=sess_options,
        providers=["CPUExecutionProvider"]
    )
    print("Model ready.")

@app.post("/predict")
async def predict(request: TextRequest):
    inputs = tokenizer(request.text, padding=True, truncation=True, return_tensors="np")
    
    inputs_onnx = {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"],
    }
    
    start_time = time.time()
    _ = ort_session.run(None, inputs_onnx)
    end_time = time.time()
    
    return {"inference_time_ms": (end_time - start_time) * 1000}
