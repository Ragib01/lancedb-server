"""
Middleware for LanceDB Server
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge
import structlog

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'lancedb_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'lancedb_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'lancedb_active_connections',
    'Number of active connections'
)

DATABASE_OPERATIONS = Counter(
    'lancedb_database_operations_total',
    'Total number of database operations',
    ['operation', 'database', 'status']
)

VECTOR_SEARCH_DURATION = Histogram(
    'lancedb_vector_search_duration_seconds',
    'Vector search duration in seconds',
    ['database', 'table']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Increment active connections
        ACTIVE_CONNECTIONS.inc()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            endpoint = request.url.path
            method = request.method
            status_code = response.status_code
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            endpoint = request.url.path
            method = request.method
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            logger.error("Request failed", error=str(e), endpoint=endpoint)
            raise
            
        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()


def record_database_operation(operation: str, database: str, status: str):
    """Record database operation metric"""
    DATABASE_OPERATIONS.labels(
        operation=operation,
        database=database,
        status=status
    ).inc()


def record_vector_search(database: str, table: str, duration: float):
    """Record vector search metric"""
    VECTOR_SEARCH_DURATION.labels(
        database=database,
        table=table
    ).observe(duration) 