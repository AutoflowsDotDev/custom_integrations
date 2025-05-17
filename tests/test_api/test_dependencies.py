"""Tests for the API dependencies."""
import pytest
from fastapi import HTTPException, Header
from unittest.mock import patch, MagicMock, AsyncMock

from src.api.dependencies import get_api_key, get_gmail_client, get_ai_processor, get_slack_client
from src.utils.exceptions import GmailServiceError, AIServiceError, SlackServiceError


@pytest.mark.asyncio
async def test_get_api_key_valid():
    """Test get_api_key dependency with valid API key."""
    with patch('src.api.dependencies.api_settings') as mock_settings:
        mock_settings.API_KEY_NAME = "X-API-KEY"
        mock_settings.API_KEY = "valid-api-key"
        
        # Call with valid API key
        result = await get_api_key(x_api_key="valid-api-key")
        
        # Should return the provided API key
        assert result == "valid-api-key"


@pytest.mark.asyncio
async def test_get_api_key_invalid():
    """Test get_api_key dependency with invalid API key."""
    with patch('src.api.dependencies.api_settings') as mock_settings:
        mock_settings.API_KEY_NAME = "X-API-KEY"
        mock_settings.API_KEY = "valid-api-key"
        
        # Call with invalid API key, should raise HTTPException
        with pytest.raises(HTTPException) as excinfo:
            await get_api_key(x_api_key="invalid-api-key")
        
        # Verify exception
        assert excinfo.value.status_code == 401
        assert "Invalid API key" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_api_key_none():
    """Test get_api_key dependency with None API key."""
    with patch('src.api.dependencies.api_settings') as mock_settings:
        mock_settings.API_KEY_NAME = "X-API-KEY"
        mock_settings.API_KEY = "valid-api-key"
        
        # Call with None API key, should raise HTTPException
        with pytest.raises(HTTPException) as excinfo:
            await get_api_key(x_api_key=None)
        
        # Verify exception
        assert excinfo.value.status_code == 401
        assert "Invalid API key" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_api_key_disabled():
    """Test get_api_key dependency when API key validation is disabled."""
    with patch('src.api.dependencies.api_settings') as mock_settings:
        # Disable API key validation
        mock_settings.API_KEY_NAME = None
        mock_settings.API_KEY = None
        
        # Call with any API key, should succeed
        result = await get_api_key(x_api_key="any-key")
        assert result == "any-key"
        
        # Call with None API key, should also succeed
        result = await get_api_key(x_api_key=None)
        assert result is None


@pytest.mark.asyncio
async def test_get_gmail_client_success():
    """Test get_gmail_client dependency when successful."""
    gmail_client_mock = MagicMock()
    
    with patch('src.api.dependencies.GmailClient', return_value=gmail_client_mock):
        result = await get_gmail_client()
        assert result == gmail_client_mock


@pytest.mark.asyncio
async def test_get_gmail_client_error():
    """Test get_gmail_client dependency when error occurs."""
    with patch('src.api.dependencies.GmailClient', side_effect=GmailServiceError("Service unavailable")):
        with pytest.raises(HTTPException) as excinfo:
            await get_gmail_client()
        
        assert excinfo.value.status_code == 503
        assert "Gmail service unavailable" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_ai_processor_success():
    """Test get_ai_processor dependency when successful."""
    ai_processor_mock = MagicMock()
    
    with patch('src.api.dependencies.AIProcessor', return_value=ai_processor_mock):
        result = await get_ai_processor()
        assert result == ai_processor_mock


@pytest.mark.asyncio
async def test_get_ai_processor_error():
    """Test get_ai_processor dependency when error occurs."""
    with patch('src.api.dependencies.AIProcessor', side_effect=AIServiceError("Service unavailable")):
        with pytest.raises(HTTPException) as excinfo:
            await get_ai_processor()
        
        assert excinfo.value.status_code == 503
        assert "AI service unavailable" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_slack_client_success():
    """Test get_slack_client dependency when successful."""
    slack_client_mock = MagicMock()
    
    with patch('src.api.dependencies.SlackServiceClient', return_value=slack_client_mock):
        result = await get_slack_client()
        assert result == slack_client_mock


@pytest.mark.asyncio
async def test_get_slack_client_error():
    """Test get_slack_client dependency when error occurs."""
    with patch('src.api.dependencies.SlackServiceClient', side_effect=SlackServiceError("Service unavailable")):
        with pytest.raises(HTTPException) as excinfo:
            await get_slack_client()
        
        assert excinfo.value.status_code == 503
        assert "Slack service unavailable" in excinfo.value.detail 