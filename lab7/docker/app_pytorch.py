import time
import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModel, AutoTokenizer

app = FastAPI()

model_name = "sentence-transformers/multi-qa-mpnet-base-cos-v1"
tokenizer = None
model = None

class TextRequest(BaseModel):
    text: str

@app.on_event("startup")
async def startup_event():
    global tokenizer, model
    print("Loading model...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    
    # Compile the model
    print("Compiling model...", flush=True)
    try:
        # Note: torch.compile is lazy. Actual compilation happens at first run.
        compiled_model = torch.compile(model)
        
        # Warmup (triggers compilation)
        print("Warming up (this triggers compilation)...", flush=True)
        sample_text = "This is a sample text for warmup."
        inputs = tokenizer(sample_text, padding=True, truncation=True, return_tensors="pt")
        with torch.inference_mode():
            _ = compiled_model(**inputs)
        
        # If successful, use the compiled model
        model = compiled_model
        print("Model compiled and ready.", flush=True)
    except Exception as e:
        print(f"WARNING: Model compilation failed: {e}", flush=True)
        print("Falling back to eager execution.", flush=True)
        # model remains the original eager model

@app.post("/predict")
async def predict(request: TextRequest):
    inputs = tokenizer(request.text, padding=True, truncation=True, return_tensors="pt")
    
    start_time = time.time()
    with torch.inference_mode():
        _ = model(**inputs)
    end_time = time.time()
    
    return {"inference_time_ms": (end_time - start_time) * 1000}
