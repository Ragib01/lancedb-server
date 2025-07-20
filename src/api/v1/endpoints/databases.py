"""
Database management endpoints for LanceDB Server
"""

import os
import uuid
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
import lancedb

from core.config import settings
from core.database import get_session, Database as DatabaseModel
from api.v1.auth import get_current_user, require_read, require_write
from api.exceptions import DatabaseNotFoundError
from api.middleware import record_database_operation

router = APIRouter()


class DatabaseCreate(BaseModel):
    """Database creation request"""
    name: str
    description: Optional[str] = None


class DatabaseResponse(BaseModel):
    """Database response"""
    id: str
    name: str
    path: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    table_count: Optional[int] = None


class DatabaseList(BaseModel):
    """Database list response"""
    databases: List[DatabaseResponse]
    total: int


@router.get("/", response_model=DatabaseList)
async def list_databases(
    current_user: dict = Depends(require_read),
    session: AsyncSession = Depends(get_session)
):
    """List all databases"""
    
    result = await session.execute(
        select(DatabaseModel).where(DatabaseModel.is_active == True).order_by(DatabaseModel.created_at.desc())
    )
    databases = result.scalars().all()
    
    db_list = []
    for db in databases:
        # Count tables for each database
        table_count = 0
        try:
            lance_db = lancedb.connect(db.path)
            table_count = len(lance_db.table_names())
        except Exception:
            pass  # If we can't count tables, just leave it as 0
        
        db_list.append(DatabaseResponse(
            id=db.id,
            name=db.name,
            path=db.path,
            created_at=db.created_at,
            updated_at=db.updated_at,
            is_active=db.is_active,
            table_count=table_count
        ))
    
    record_database_operation("list", "all", "success")
    return DatabaseList(databases=db_list, total=len(db_list))


@router.post("/", response_model=DatabaseResponse)
async def create_database(
    db_data: DatabaseCreate,
    current_user: dict = Depends(require_write),
    session: AsyncSession = Depends(get_session)
):
    """Create new database"""
    
    # Check if database already exists
    result = await session.execute(
        select(DatabaseModel).where(
            DatabaseModel.name == db_data.name,
            DatabaseModel.is_active == True
        )
    )
    existing_db = result.scalar_one_or_none()
    
    if existing_db:
        record_database_operation("create", db_data.name, "error")
        raise HTTPException(status_code=409, detail=f"Database '{db_data.name}' already exists")
    
    # Create database path
    db_path = os.path.join(settings.LANCEDB_DATA_DIR, db_data.name)
    os.makedirs(db_path, exist_ok=True)
    
    try:
        # Initialize LanceDB database
        lance_db = lancedb.connect(db_path)
        
        # Create database record
        db_record = DatabaseModel(
            id=str(uuid.uuid4()),
            name=db_data.name,
            path=db_path,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        session.add(db_record)
        await session.commit()
        await session.refresh(db_record)
        
        record_database_operation("create", db_data.name, "success")
        
        return DatabaseResponse(
            id=db_record.id,
            name=db_record.name,
            path=db_record.path,
            created_at=db_record.created_at,
            updated_at=db_record.updated_at,
            is_active=db_record.is_active,
            table_count=0
        )
        
    except Exception as e:
        record_database_operation("create", db_data.name, "error")
        raise HTTPException(status_code=500, detail=f"Failed to create database: {str(e)}")


@router.get("/{database_name}", response_model=DatabaseResponse)
async def get_database(
    database_name: str,
    current_user: dict = Depends(require_read),
    session: AsyncSession = Depends(get_session)
):
    """Get specific database"""
    
    result = await session.execute(
        select(DatabaseModel).where(
            DatabaseModel.name == database_name,
            DatabaseModel.is_active == True
        )
    )
    db = result.scalar_one_or_none()
    
    if not db:
        record_database_operation("get", database_name, "error")
        raise DatabaseNotFoundError(database_name)
    
    # Count tables
    table_count = 0
    try:
        lance_db = lancedb.connect(db.path)
        table_count = len(lance_db.table_names())
    except Exception:
        pass
    
    record_database_operation("get", database_name, "success")
    
    return DatabaseResponse(
        id=db.id,
        name=db.name,
        path=db.path,
        created_at=db.created_at,
        updated_at=db.updated_at,
        is_active=db.is_active,
        table_count=table_count
    )


@router.delete("/{database_name}")
async def delete_database(
    database_name: str,
    current_user: dict = Depends(require_write),
    session: AsyncSession = Depends(get_session)
):
    """Delete database"""
    
    result = await session.execute(
        select(DatabaseModel).where(
            DatabaseModel.name == database_name,
            DatabaseModel.is_active == True
        )
    )
    db = result.scalar_one_or_none()
    
    if not db:
        record_database_operation("delete", database_name, "error")
        raise DatabaseNotFoundError(database_name)
    
    try:
        # Mark database as inactive instead of actually deleting
        # This preserves data and allows for recovery
        db.is_active = False
        db.updated_at = datetime.utcnow()
        await session.commit()
        
        record_database_operation("delete", database_name, "success")
        
        return {"message": f"Database '{database_name}' deleted successfully"}
        
    except Exception as e:
        record_database_operation("delete", database_name, "error")
        raise HTTPException(status_code=500, detail=f"Failed to delete database: {str(e)}")


@router.get("/{database_name}/tables")
async def list_database_tables(
    database_name: str,
    current_user: dict = Depends(require_read),
    session: AsyncSession = Depends(get_session)
):
    """List tables in database"""
    
    result = await session.execute(
        select(DatabaseModel).where(
            DatabaseModel.name == database_name,
            DatabaseModel.is_active == True
        )
    )
    db = result.scalar_one_or_none()
    
    if not db:
        raise DatabaseNotFoundError(database_name)
    
    try:
        lance_db = lancedb.connect(db.path)
        table_names = lance_db.table_names()
        
        tables = []
        for table_name in table_names:
            try:
                table = lance_db.open_table(table_name)
                row_count = len(table)
                tables.append({
                    "name": table_name,
                    "row_count": row_count,
                    "schema": str(table.schema)
                })
            except Exception:
                tables.append({
                    "name": table_name,
                    "row_count": 0,
                    "schema": "unknown"
                })
        
        return {
            "database": database_name,
            "tables": tables,
            "total": len(tables)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}") 