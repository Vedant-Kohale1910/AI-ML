"""FastAPI scoring API for single and batch predictions."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from scoring.schema import CustomerInput, BatchInput
from scoring.scorer import score_single, score_batch, _load_artifacts

app = FastAPI(
    title="Churn Score Extraction API",
    description="Task 13 — Production scoring interface for churn prediction model",
    version="1.0.0"
)


@app.on_event("startup")
def load_model():
    _load_artifacts()
    print("[API] Model loaded and ready.")


@app.get("/health")
def health():
    _, _, meta = _load_artifacts()
    return {"status": "ok", "model_version": meta['model_version'], "model_hash": meta['model_hash']}


@app.get("/model/info")
def model_info():
    _, _, meta = _load_artifacts()
    return meta


@app.post("/score/single")
def predict_single(record: CustomerInput, record_id: str = None):
    try:
        result = score_single(record, record_id=record_id)
        return result.dict()
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring error: {e}")


@app.post("/score/batch")
def predict_batch(batch: BatchInput):
    try:
        result = score_batch(batch)
        return result.dict()
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch scoring error: {e}")


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"error": "Input validation failed", "details": exc.errors()})


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
