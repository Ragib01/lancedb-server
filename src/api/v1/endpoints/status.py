"""
Status endpoints for LanceDB Server
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
import psutil
import time
from datetime import datetime

from core.config import settings
from core.database import get_session
from core.redis_client import get_redis
from api.v1.auth import get_current_user

router = APIRouter()


class SystemStatus(BaseModel):
    """System status response model"""
    service: str
    version: str
    status: str
    uptime_seconds: float
    timestamp: datetime
    system: Dict[str, Any]
    database: Dict[str, Any]
    redis: Dict[str, Any]


# Track server start time
start_time = time.time()


@router.get("/", response_model=SystemStatus)
async def get_system_status(
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive system status"""
    
    # Calculate uptime
    uptime = time.time() - start_time
    
    # System information
    system_info = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_usage": dict(psutil.virtual_memory()._asdict()),
        "disk_usage": dict(psutil.disk_usage('/data')._asdict()) if psutil.disk_usage('/data') else {},
        "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
    }
    
    # Database status
    db_status = {"status": "unknown", "connection_pool": {}}
    try:
        async for session in get_session():
            await session.execute("SELECT 1")
            db_status["status"] = "healthy"
            break
    except Exception as e:
        db_status["status"] = "unhealthy"
        db_status["error"] = str(e)
    
    # Redis status
    redis_status = {"status": "unknown", "info": {}}
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        redis_info = await redis_client.info()
        redis_status["status"] = "healthy"
        redis_status["info"] = {
            "connected_clients": redis_info.get("connected_clients", 0),
            "used_memory_human": redis_info.get("used_memory_human", "unknown"),
            "keyspace_hits": redis_info.get("keyspace_hits", 0),
            "keyspace_misses": redis_info.get("keyspace_misses", 0),
        }
    except Exception as e:
        redis_status["status"] = "unhealthy"
        redis_status["error"] = str(e)
    
    return SystemStatus(
        service="lancedb-server",
        version="1.0.0",
        status="healthy",
        uptime_seconds=uptime,
        timestamp=datetime.utcnow(),
        system=system_info,
        database=db_status,
        redis=redis_status
    ) 