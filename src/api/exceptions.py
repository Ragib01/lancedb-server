"""
Exception handlers for LanceDB Server
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog
from typing import Any, Dict

logger = structlog.get_logger()


class LanceDBException(Exception):
    """Base exception for LanceDB operations"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseNotFoundError(LanceDBException):
    """Raised when database is not found"""
    def __init__(self, database_name: str):
        super().__init__(f"Database '{database_name}' not found", 404)


class TableNotFoundError(LanceDBException):
    """Raised when table is not found"""
    def __init__(self, table_name: str):
        super().__init__(f"Table '{table_name}' not found", 404)


class AuthenticationError(LanceDBException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)


class AuthorizationError(LanceDBException):
    """Raised when authorization fails"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, 403)


class ValidationError(LanceDBException):
    """Raised when validation fails"""
    def __init__(self, message: str):
        super().__init__(message, 422)


async def lancedb_exception_handler(request: Request, exc: LanceDBException) -> JSONResponse:
    """Handle LanceDB custom exceptions"""
    logger.error("LanceDB exception", error=exc.message, status_code=exc.status_code)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "status_code": exc.status_code
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    logger.error("HTTP exception", error=str(exc.detail), status_code=exc.status_code)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    logger.error("Unhandled exception", error=str(exc), exception_type=exc.__class__.__name__)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "status_code": 500
            }
        }
    )


def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to FastAPI app"""
    app.add_exception_handler(LanceDBException, lancedb_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 