"""
Database management for LanceDB Server
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from datetime import datetime
import structlog

from .config import settings

logger = structlog.get_logger()

# Database engine and session
engine = None
async_session = None

# Base model
Base = declarative_base()


class APIKey(Base):
    """API Key model for authentication"""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    permissions = Column(Text)  # JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)


class Database(Base):
    """Database metadata model"""
    __tablename__ = "databases"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Table(Base):
    """Table metadata model"""
    __tablename__ = "tables"
    
    id = Column(String(36), primary_key=True)
    database_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    schema_info = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    row_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


async def init_database():
    """Initialize database connection and create tables"""
    global engine, async_session
    
    try:
        # Create async engine
        engine = create_async_engine(
            settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
            echo=settings.LANCEDB_LOG_LEVEL.upper() == "DEBUG",
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
        )
        
        # Create session maker
        async_session = async_sessionmaker(
            engine,
            expire_on_commit=False
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database connection established")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def get_session():
    """Get database session"""
    if async_session is None:
        await init_database()
    
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_database():
    """Close database connection"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connection closed") 