from fastapi import Header, HTTPException, Depends, status
from typing import Optional

from src.api.config import api_settings
from src.gmail_service.gmail_client import GmailClient
from src.ai_service.ai_processor import AIProcessor
from src.slack_service.slack_client import SlackServiceClient
from src.utils.exceptions import (
    GmailServiceError,
    AIServiceError,
    SlackServiceError
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def get_api_key(x_api_key: str = Header(None)):
    """Validate API key."""
    if api_settings.API_KEY_NAME and api_settings.API_KEY:
        if x_api_key != api_settings.API_KEY:
            logger.warning(f"Invalid API key attempt: {x_api_key[:5]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
    return x_api_key

async def get_gmail_client() -> GmailClient:
    """Get Gmail client for dependency injection."""
    try:
        return GmailClient()
    except GmailServiceError as e:
        logger.error(f"Failed to initialize Gmail client: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail service unavailable"
        )

async def get_ai_processor() -> AIProcessor:
    """Get AI processor for dependency injection."""
    try:
        return AIProcessor()
    except AIServiceError as e:
        logger.error(f"Failed to initialize AI processor: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable"
        )

async def get_slack_client() -> SlackServiceClient:
    """Get Slack client for dependency injection."""
    try:
        return SlackServiceClient()
    except SlackServiceError as e:
        logger.error(f"Failed to initialize Slack client: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Slack service unavailable"
        ) 