# app/api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import uvicorn
import asyncio
import logging
from pydantic import BaseModel, ConfigDict
from pydantic.v1.config import Extra

from app.settings import load_config
from modules.vectorchain import LocalVectorNode



# Models
class VectorCreate(BaseModel):
    coordinates: List[float]
    metadata: Dict[str, Any] = None

    class Config:
        extra = Extra.allow

class VectorVerify(BaseModel):
    vector_id: str
    proof: Dict[str, Any]

    class Config:
        extra = Extra.allow

class QuantumOperation(BaseModel):
    operation: str
    params: Dict[str, Any]

    class Config:
        extra = Extra.allow

# Initialize FastAPI and Vector Node
app = FastAPI(title="Vector Node API")
vector_node: LocalVectorNode = None

@app.on_event("startup")
async def startup_event():
    global vector_node
    # Load config and initialize vector node
    config = load_config()
    vector_node = LocalVectorNode(config)

@app.middleware("http")
async def add_process_time_header(request, call_next):
    response = await call_next(request)
    return response

# API Endpoints
@app.post("/vectors/create")
async def create_vector(data: VectorCreate):
    """Create a new vector with quantum properties."""
    try:
        result = await vector_node.create_vector(
            data.coordinates,
            data.metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/vectors/verify")
async def verify_vector(data: VectorVerify):
    """Verify a vector's quantum proof."""
    try:
        result = await vector_node.verify_vector(
            data.vector_id,
            data.proof
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/vectors/{vector_id}/proof")
async def generate_proof(vector_id: str):
    """Generate a new quantum proof for a vector."""
    try:
        result = await vector_node.generate_proof(vector_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/quantum/operation")
async def quantum_operation(data: QuantumOperation):
    """Process quantum-specific operations."""
    try:
        result = await vector_node.process_quantum_operation(
            data.operation,
            data.params
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """Check node health."""
    return {
        "status": "healthy",
        "node_id": vector_node.node_id if vector_node else None
    }

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4
    )