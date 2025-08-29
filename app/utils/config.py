# app/utils/config.py
"""
Configuration management using Pydantic settings.
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    api_port: int = 8000
    environment: str = "development"
    log_level: str = "INFO"
    
    # Snowflake Configuration
    snowflake_user: str
    snowflake_password: str
    snowflake_account: str
    snowflake_database: str = "retail_analytics"
    snowflake_schema: str = "analytics"  # Use analytics schema (dbt output)
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_role: str = "SYSADMIN"
    
    # Local AI Configuration (instead of OpenAI)
    local_ai_backend: str = "ollama"
    local_ai_model: str = "llama3.1:8b"
    local_ai_host: str = "localhost"
    local_ai_port: int = 11434
    local_ai_temperature: float = 0.1
    local_ai_max_tokens: int = 1000
    
    # Query Configuration
    default_max_rows: int = 100
    max_query_timeout: int = 60
    enable_query_caching: bool = False  # Disable for development
    
    # Security
    allowed_origins: List[str] = ["*"]
    
    # Monitoring
    enable_metrics: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()