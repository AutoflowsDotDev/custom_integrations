import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
from functools import lru_cache

class APISettings(BaseSettings):
    """API settings for the FastAPI application."""
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Email Triage API"
    DEBUG: bool = False
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "API for email triage workflow automation"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Security settings
    API_KEY_NAME: str = "X-API-KEY"
    API_KEY: Optional[str] = None
    
    # Monitoring settings
    ENABLE_METRICS: bool = True
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra fields
    }

@lru_cache()
def get_api_settings() -> APISettings:
    """Returns the API settings."""
    return APISettings()

api_settings = get_api_settings() 