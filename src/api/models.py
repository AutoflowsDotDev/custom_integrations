from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class EmailProcessRequest(BaseModel):
    """Model for requesting email processing."""
    email_id: str = Field(..., description="The ID of the email to process")

class EmailProcessResponse(BaseModel):
    """Model for email processing response."""
    success: bool = Field(..., description="Whether the processing was successful")
    email_id: str = Field(..., description="The ID of the processed email")
    is_urgent: Optional[bool] = Field(None, description="Whether the email was classified as urgent")
    message: Optional[str] = Field(None, description="Additional information about the processing")

class ProcessHistoryRequest(BaseModel):
    """Model for processing history updates."""
    history_id: str = Field(..., description="The history ID from Gmail notification")

class ProcessHistoryResponse(BaseModel):
    """Model for history processing response."""
    success: bool = Field(..., description="Whether the history processing was successful")
    history_id: str = Field(..., description="The history ID that was processed")
    processed_emails: int = Field(0, description="Number of emails processed")
    message: Optional[str] = Field(None, description="Additional information about the processing")

class ServiceStatus(str, Enum):
    """Service status enum."""
    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"

class ServiceHealthResponse(BaseModel):
    """Model for service health check response."""
    status: ServiceStatus = Field(..., description="Overall service status")
    uptime: float = Field(..., description="Service uptime in seconds")
    version: str = Field(..., description="Service version")
    services: Dict[str, ServiceStatus] = Field(..., description="Status of individual services")
    message: Optional[str] = Field(None, description="Additional information about service health") 