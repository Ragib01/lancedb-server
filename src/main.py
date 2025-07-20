#!/usr/bin/env python3
"""
LanceDB Server - Main Application Entry Point
"""

import os
import asyncio
import uvloop
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from core.config import settings
from core.database import init_database
from core.redis_client import init_redis
from api.v1.router import api_router
from api.middleware import PrometheusMiddleware
from api.exceptions import add_exception_handlers

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting LanceDB Server", version="1.0.0")
    
    # Initialize database
    await init_database()
    logger.info("Database initialized")
    
    # Initialize Redis
    await init_redis()
    logger.info("Redis initialized")
    
    # Create data directory if it doesn't exist
    os.makedirs(settings.LANCEDB_DATA_DIR, exist_ok=True)
    logger.info("Data directory ready", path=settings.LANCEDB_DATA_DIR)
    
    yield
    
    logger.info("Shutting down LanceDB Server")

# Create FastAPI application
app = FastAPI(
    title="LanceDB Server",
    description="Remote LanceDB Server with REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.LANCEDB_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus middleware
app.add_middleware(PrometheusMiddleware)

# Add exception handlers
add_exception_handlers(app)

# Include API routes
app.include_router(api_router, prefix="/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "lancedb-server",
        "version": "1.0.0"
    }

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

if __name__ == "__main__":
    # Use uvloop for better performance
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.LANCEDB_HOST,
        port=settings.LANCEDB_PORT,
        log_level=settings.LANCEDB_LOG_LEVEL.lower(),
        reload=False,
        workers=1,
        loop="uvloop"
    ) 