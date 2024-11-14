# server.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn
import time
import logging
from prometheus_client import (
    Counter, Histogram, CONTENT_TYPE_LATEST,
    generate_latest, REGISTRY,
    multiprocess, CollectorRegistry
)
import os
from typing import Optional

from settings import settings

# Initialize FastAPI instance
app = FastAPI(
    title="AxiomVerse Internal API",
    description="Secure internal API for AxiomVerse system",
    version=settings.API_VERSION
)

# Initialize metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Initialize additional metrics
ACTIVE_CONNECTIONS = Counter(
    'active_connections_total',
    'Total number of active connections'
)

VECTOR_OPERATIONS = Counter(
    'vector_operations_total',
    'Total number of vector operations',
    ['operation_type']
)

CONSENSUS_ROUNDS = Counter(
    'consensus_rounds_total',
    'Total number of consensus rounds'
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)

    response.headers["X-Process-Time"] = str(process_time)
    return response


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    registry = REGISTRY
    if 'prometheus_multiproc_dir' in os.environ:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)

    return Response(
        generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.API_VERSION
    }


# Example of using vector operation metrics
@app.post("/vectors/create")
async def create_vector():
    VECTOR_OPERATIONS.labels(operation_type="create").inc()
    # Your vector creation logic here
    return {"status": "created"}


@app.post("/vectors/update")
async def update_vector():
    VECTOR_OPERATIONS.labels(operation_type="update").inc()
    # Your vector update logic here
    return {"status": "updated"}


@app.post("/consensus/start")
async def start_consensus():
    CONSENSUS_ROUNDS.inc()
    # Your consensus logic here
    return {"status": "consensus_started"}


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Start server
    uvicorn.run(
        app,
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.DEBUG,
        workers=settings.server.workers,
        log_level="info"
    )