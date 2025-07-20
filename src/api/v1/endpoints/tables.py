"""
Table management and vector search endpoints for LanceDB Server
"""

import time
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import lancedb
import pandas as pd
import pyarrow as pa

from core.config import settings
from core.database import get_session, Database as DatabaseModel
from api.v1.auth import get_current_user, require_read, require_write
from api.exceptions import DatabaseNotFoundError, TableNotFoundError
from api.middleware import record_database_operation, record_vector_search

router = APIRouter()


class TableCreate(BaseModel):
    """Table creation request"""
    name: str
    data: List[Dict[str, Any]]
    mode: str = "create"  # create, overwrite, append


class VectorSearch(BaseModel):
    """Vector search request"""
    vector: List[float]
    limit: int = 10
    metric: str = "cosine"  # cosine, l2, dot
    where: Optional[str] = None
    select: Optional[List[str]] = None


class TableResponse(BaseModel):
    """Table response"""
    name: str
    row_count: int
    schema: Dict[str, Any]
    created_at: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response"""
    results: List[Dict[str, Any]]
    query_time_ms: float
    total_rows_searched: int


async def get_database_connection(database_name: str, session: AsyncSession):
    """Get database connection"""
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
        return lance_db
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to database: {str(e)}")


@router.post("/{table_name}", response_model=TableResponse)
async def create_or_update_table(
    database_name: str,
    table_name: str,
    table_data: TableCreate,
    current_user: dict = Depends(require_write),
    session: AsyncSession = Depends(get_session)
):
    """Create or update table with data"""
    
    lance_db = await get_database_connection(database_name, session)
    
    try:
        # Convert data to DataFrame
        df = pd.DataFrame(table_data.data)
        
        if table_data.mode == "create":
            # Create new table
            table = lance_db.create_table(table_name, df)
        elif table_data.mode == "overwrite":
            # Overwrite existing table
            table = lance_db.create_table(table_name, df, mode="overwrite")
        elif table_data.mode == "append":
            # Append to existing table
            if table_name in lance_db.table_names():
                table = lance_db.open_table(table_name)
                table.add(df)
            else:
                # Create new table if it doesn't exist
                table = lance_db.create_table(table_name, df)
        else:
            raise HTTPException(status_code=400, detail="Invalid mode. Use 'create', 'overwrite', or 'append'")
        
        # Get table info
        row_count = len(table)
        schema = table.schema
        
        record_database_operation("table_create", f"{database_name}.{table_name}", "success")
        
        return TableResponse(
            name=table_name,
            row_count=row_count,
            schema={"fields": [{"name": field.name, "type": str(field.type)} for field in schema]},
            created_at=str(time.time())
        )
        
    except Exception as e:
        record_database_operation("table_create", f"{database_name}.{table_name}", "error")
        raise HTTPException(status_code=500, detail=f"Failed to create table: {str(e)}")


@router.get("/{table_name}", response_model=TableResponse)
async def get_table_info(
    database_name: str,
    table_name: str,
    current_user: dict = Depends(require_read),
    session: AsyncSession = Depends(get_session)
):
    """Get table information"""
    
    lance_db = await get_database_connection(database_name, session)
    
    if table_name not in lance_db.table_names():
        raise TableNotFoundError(table_name)
    
    try:
        table = lance_db.open_table(table_name)
        row_count = len(table)
        schema = table.schema
        
        return TableResponse(
            name=table_name,
            row_count=row_count,
            schema={"fields": [{"name": field.name, "type": str(field.type)} for field in schema]}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table info: {str(e)}")


@router.post("/{table_name}/search", response_model=SearchResponse)
async def search_table(
    database_name: str,
    table_name: str,
    search_request: VectorSearch,
    current_user: dict = Depends(require_read),
    session: AsyncSession = Depends(get_session)
):
    """Perform vector search on table"""
    
    start_time = time.time()
    
    lance_db = await get_database_connection(database_name, session)
    
    if table_name not in lance_db.table_names():
        raise TableNotFoundError(table_name)
    
    try:
        table = lance_db.open_table(table_name)
        
        # Build search query
        query = table.search(search_request.vector).limit(search_request.limit)
        
        # Add metric if specified
        if search_request.metric == "l2":
            query = query.metric("l2")
        elif search_request.metric == "dot":
            query = query.metric("dot")
        # cosine is default
        
        # Add where clause if specified
        if search_request.where:
            query = query.where(search_request.where)
        
        # Add select clause if specified
        if search_request.select:
            query = query.select(search_request.select)
        
        # Execute search
        results = query.to_list()
        
        query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        total_rows = len(table)
        
        # Record metrics
        record_vector_search(database_name, table_name, query_time / 1000)
        record_database_operation("search", f"{database_name}.{table_name}", "success")
        
        return SearchResponse(
            results=results,
            query_time_ms=query_time,
            total_rows_searched=total_rows
        )
        
    except Exception as e:
        record_database_operation("search", f"{database_name}.{table_name}", "error")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/{table_name}/data")
async def add_data_to_table(
    database_name: str,
    table_name: str,
    data: List[Dict[str, Any]],
    current_user: dict = Depends(require_write),
    session: AsyncSession = Depends(get_session)
):
    """Add data to existing table"""
    
    lance_db = await get_database_connection(database_name, session)
    
    if table_name not in lance_db.table_names():
        raise TableNotFoundError(table_name)
    
    try:
        table = lance_db.open_table(table_name)
        df = pd.DataFrame(data)
        table.add(df)
        
        record_database_operation("table_insert", f"{database_name}.{table_name}", "success")
        
        return {
            "message": f"Added {len(data)} rows to table '{table_name}'",
            "rows_added": len(data),
            "total_rows": len(table)
        }
        
    except Exception as e:
        record_database_operation("table_insert", f"{database_name}.{table_name}", "error")
        raise HTTPException(status_code=500, detail=f"Failed to add data: {str(e)}")


@router.get("/{table_name}/data")
async def get_table_data(
    database_name: str,
    table_name: str,
    limit: int = Query(100, description="Number of rows to return"),
    offset: int = Query(0, description="Number of rows to skip"),
    current_user: dict = Depends(require_read),
    session: AsyncSession = Depends(get_session)
):
    """Get data from table"""
    
    lance_db = await get_database_connection(database_name, session)
    
    if table_name not in lance_db.table_names():
        raise TableNotFoundError(table_name)
    
    try:
        table = lance_db.open_table(table_name)
        
        # Get data with pagination
        query = table.to_lance().take(list(range(offset, min(offset + limit, len(table)))))
        df = query.to_pandas()
        
        # Convert to records
        data = df.to_dict('records')
        
        return {
            "data": data,
            "total_rows": len(table),
            "offset": offset,
            "limit": limit,
            "returned_rows": len(data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data: {str(e)}")


@router.delete("/{table_name}")
async def delete_table(
    database_name: str,
    table_name: str,
    current_user: dict = Depends(require_write),
    session: AsyncSession = Depends(get_session)
):
    """Delete table"""
    
    lance_db = await get_database_connection(database_name, session)
    
    if table_name not in lance_db.table_names():
        raise TableNotFoundError(table_name)
    
    try:
        lance_db.drop_table(table_name)
        
        record_database_operation("table_delete", f"{database_name}.{table_name}", "success")
        
        return {"message": f"Table '{table_name}' deleted successfully"}
        
    except Exception as e:
        record_database_operation("table_delete", f"{database_name}.{table_name}", "error")
        raise HTTPException(status_code=500, detail=f"Failed to delete table: {str(e)}") 