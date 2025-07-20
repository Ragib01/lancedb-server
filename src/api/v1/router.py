"""
Main API router for LanceDB Server v1
"""

from fastapi import APIRouter
from .endpoints import databases, tables, auth, status

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    databases.router,
    prefix="/databases",
    tags=["databases"]
)

api_router.include_router(
    tables.router,
    prefix="/databases/{database_name}/tables",
    tags=["tables"]
)

api_router.include_router(
    status.router,
    prefix="/status",
    tags=["status"]
) 