from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from brainstorming import brain
from  add_content import add_data

app = FastAPI(
    title="GMP Deviation Brainstorming API",
    description="API for GMP deviation ingestion and expert brainstorming",
    version="1.0.0"
)

class BrainstormingRequest(BaseModel):
    data: Dict[str, Any]


class AddDataRequest(BaseModel):
    data: Dict[str, Any]

@app.get("/")
def health_check():
    return {
        "status": "running",
        "message": "GMP Brainstorming API is live"
    }
@app.post("/brainstorming")
def run_brainstorming(request: BrainstormingRequest):
    try:
        result = brain(request.data)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@app.post("/adddata")
def ingest_deviation(request: AddDataRequest):
    try:
        response = add_data(request.data)
        return {
            "status": "success",
            "response": response
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0",  port=int(os.environ.get("PORT", 3000)))

