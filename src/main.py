import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

from brainstorming import brain
from add_content import add_data

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GMP Deviation Brainstorming API",
    description="API for GMP deviation ingestion and expert brainstorming",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),  # Configure in .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BrainstormingRequest(BaseModel):
    data: Dict[str, Any]


class AddDataRequest(BaseModel):
    data: Dict[str, Any]

@app.get("/")
def health_check():
    logger.info("Health check endpoint accessed")
    return {
        "status": "running",
        "message": "GMP Brainstorming API is live",
        "version": "1.0.0"
    }

@app.get("/health")
def detailed_health():
    """Detailed health check for monitoring"""
    try:
        # Could add Redis/ChromaDB connectivity checks here
        return {
            "status": "healthy",
            "service": "GMP Deviation API",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/brainstorming")
def run_brainstorming(request: BrainstormingRequest):
    try:
        logger.info("Brainstorming request received")
        result = brain(request.data)
        logger.info("Brainstorming completed successfully")
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Brainstorming error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Brainstorming failed: {str(e)}"
        )
@app.post("/adddata")
def ingest_deviation(request: AddDataRequest):
    try:
        logger.info("Add data request received")
        response = add_data(request.data)
        logger.info(f"Data added successfully with ID: {response}")
        return {
            "status": "success",
            "deviation_id": response
        }
    except Exception as e:
        logger.error(f"Add data error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Data ingestion failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("APP_ENV", "production") == "development",  # Only reload in dev
        log_level="info"
    )

