"""
Authentication module for LanceDB Server
"""

import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_session, APIKey
from api.exceptions import AuthenticationError, AuthorizationError

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.LANCEDB_JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.LANCEDB_JWT_SECRET, 
        algorithm=settings.LANCEDB_JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.LANCEDB_JWT_SECRET, 
            algorithms=[settings.LANCEDB_JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise AuthenticationError("Invalid token")


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate new API key"""
    return f"ldb_{uuid.uuid4().hex}"


async def get_api_key_from_db(api_key_hash: str, session: AsyncSession) -> Optional[APIKey]:
    """Get API key from database"""
    result = await session.execute(
        select(APIKey).where(
            APIKey.key_hash == api_key_hash,
            APIKey.is_active == True
        )
    )
    return result.scalar_one_or_none()


async def verify_api_key(api_key: str, session: AsyncSession) -> Optional[dict]:
    """Verify API key and return user info"""
    api_key_hash = hash_api_key(api_key)
    key_record = await get_api_key_from_db(api_key_hash, session)
    
    if not key_record:
        return None
    
    # Update last used timestamp
    key_record.last_used = datetime.utcnow()
    await session.commit()
    
    # Parse permissions
    permissions = json.loads(key_record.permissions) if key_record.permissions else []
    
    return {
        "id": key_record.id,
        "name": key_record.name,
        "permissions": permissions,
        "type": "api_key"
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> dict:
    """Get current authenticated user"""
    
    if not settings.LANCEDB_AUTH_ENABLED:
        # Authentication disabled, return default user
        return {
            "id": "default",
            "name": "default",
            "permissions": ["read", "write", "admin"],
            "type": "default"
        }
    
    token = credentials.credentials
    
    # Try JWT token first
    if token.startswith("eyJ"):  # JWT tokens start with eyJ
        try:
            payload = verify_token(token)
            return payload.get("user", {})
        except AuthenticationError:
            pass
    
    # Try API key
    user = await verify_api_key(token, session)
    if user:
        return user
    
    raise AuthenticationError("Invalid authentication credentials")


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(user: dict = Depends(get_current_user)):
        user_permissions = user.get("permissions", [])
        if permission not in user_permissions and "admin" not in user_permissions:
            raise AuthorizationError(f"Permission '{permission}' required")
        return user
    return decorator


# Permission dependencies
require_read = require_permission("read")
require_write = require_permission("write")
require_admin = require_permission("admin") 