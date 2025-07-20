"""
Configuration management for LanceDB Server
"""

import os
from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Server configuration
    LANCEDB_HOST: str = "0.0.0.0"
    LANCEDB_PORT: int = 9000
    LANCEDB_DATA_DIR: str = "/data"
    LANCEDB_LOG_LEVEL: str = "INFO"
    LANCEDB_MAX_CONNECTIONS: int = 100
    
    # Authentication
    LANCEDB_AUTH_ENABLED: bool = True
    LANCEDB_JWT_SECRET: str = "change-this-secret-key"
    LANCEDB_JWT_ALGORITHM: str = "HS256"
    LANCEDB_JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    LANCEDB_CORS_ORIGINS: List[str] = ["*"]
    
    # PostgreSQL configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "lancedb"
    POSTGRES_USER: str = "lancedb"
    POSTGRES_PASSWORD: str = "password"
    
    # Redis configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_pass"
    REDIS_DB: int = 0
    
    # Derived properties
    @property
    def database_url(self) -> str:
        """PostgreSQL database URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def redis_url(self) -> str:
        """Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings() 