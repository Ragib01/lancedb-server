"""
Authentication endpoints for LanceDB Server
"""

import uuid
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session, APIKey
from api.v1.auth import (
    get_current_user, 
    require_admin, 
    generate_api_key, 
    hash_api_key
)

router = APIRouter()


class APIKeyCreate(BaseModel):
    """API Key creation request"""
    name: str
    permissions: List[str] = ["read"]


class APIKeyResponse(BaseModel):
    """API Key response"""
    id: str
    name: str
    key: Optional[str] = None  # Only returned on creation
    permissions: List[str]
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]


class APIKeyList(BaseModel):
    """API Key list response"""
    keys: List[APIKeyResponse]
    total: int


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Create new API key"""
    
    # Generate new API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # Create database record
    key_record = APIKey(
        id=str(uuid.uuid4()),
        name=key_data.name,
        key_hash=api_key_hash,
        permissions=json.dumps(key_data.permissions),
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    session.add(key_record)
    await session.commit()
    await session.refresh(key_record)
    
    return APIKeyResponse(
        id=key_record.id,
        name=key_record.name,
        key=api_key,  # Return key only on creation
        permissions=key_data.permissions,
        is_active=key_record.is_active,
        created_at=key_record.created_at,
        last_used=key_record.last_used
    )


@router.get("/api-keys", response_model=APIKeyList)
async def list_api_keys(
    current_user: dict = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """List all API keys"""
    
    result = await session.execute(
        select(APIKey).where(APIKey.is_active == True).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    
    api_keys = []
    for key in keys:
        permissions = json.loads(key.permissions) if key.permissions else []
        api_keys.append(APIKeyResponse(
            id=key.id,
            name=key.name,
            permissions=permissions,
            is_active=key.is_active,
            created_at=key.created_at,
            last_used=key.last_used
        ))
    
    return APIKeyList(keys=api_keys, total=len(api_keys))


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: dict = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Get specific API key"""
    
    result = await session.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.is_active == True)
    )
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    permissions = json.loads(key.permissions) if key.permissions else []
    
    return APIKeyResponse(
        id=key.id,
        name=key.name,
        permissions=permissions,
        is_active=key.is_active,
        created_at=key.created_at,
        last_used=key.last_used
    )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """Revoke API key"""
    
    result = await session.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.is_active == True)
    )
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Mark as inactive instead of deleting
    key.is_active = False
    await session.commit()
    
    return {"message": "API key revoked successfully"}


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user": current_user,
        "authenticated": True
    } 