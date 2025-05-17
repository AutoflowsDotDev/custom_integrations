"""Tests for the webhook API endpoints."""
import pytest
import json
import base64
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from src.api.app import app
from src.api.models import ProcessHistoryRequest


class AsyncMockResponse:
    """Mock async response for process_history."""
    def __init__(self, data):
        self.data = data
        
    async def __call__(self, *args, **kwargs):
        return self.data


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_pubsub_payload():
    """Create a mock Pub/Sub push notification payload."""
    # Create message data (simulating Gmail notification)
    data = {
        'emailAddress': 'user@example.com',
        'historyId': '12345'
    }
    json_data = json.dumps(data)
    encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
    
    # Create mock message
    return {
        "message": {
            "data": encoded_data,
            "messageId": "test-message-id",
            "publishTime": "2020-01-01T00:00:00Z"
        },
        "subscription": "projects/test-project/subscriptions/test-subscription"
    }


@pytest.fixture
def mock_process_history_response():
    """Return a mock response for process_history."""
    return {
        "success": True,
        "history_id": "12345",
        "processed_emails": 1,
        "message": "Processed 1 emails from history update"
    }


def test_webhook_pubsub_valid(test_client, mock_pubsub_payload, mock_process_history_response):
    """Test webhook endpoint with valid Pub/Sub payload."""
    # Setup AsyncMock for process_history
    async_mock = AsyncMockResponse(mock_process_history_response)
    
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"), \
         patch('src.api.dependencies.get_gmail_client', return_value=MagicMock()), \
         patch('src.api.dependencies.get_ai_processor', return_value=MagicMock()), \
         patch('src.api.dependencies.get_slack_client', return_value=MagicMock()), \
         patch('src.api.routers.webhook.process_history', new=async_mock):
        
        response = test_client.post(
            "/api/v1/webhook/pubsub",
            json=mock_pubsub_payload
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data


def test_webhook_pubsub_invalid_payload(test_client):
    """Test webhook endpoint with invalid Pub/Sub payload (missing message)."""
    invalid_payload = {
        "subscription": "projects/test-project/subscriptions/test-subscription"
    }
    
    # Don't mock process_history as it shouldn't be called in this case
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"):
        response = test_client.post(
            "/api/v1/webhook/pubsub",
            json=invalid_payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "message" in data["detail"]


def test_webhook_pubsub_invalid_message(test_client):
    """Test webhook endpoint with invalid Pub/Sub message (missing data)."""
    invalid_payload = {
        "message": {
            "messageId": "test-message-id",
            "publishTime": "2020-01-01T00:00:00Z"
        },
        "subscription": "projects/test-project/subscriptions/test-subscription"
    }
    
    # Don't mock process_history as it shouldn't be called in this case
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"):
        response = test_client.post(
            "/api/v1/webhook/pubsub",
            json=invalid_payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "data" in data["detail"]


def test_webhook_pubsub_invalid_data(test_client):
    """Test webhook endpoint with invalid Pub/Sub data (not base64 encoded)."""
    invalid_payload = {
        "message": {
            "data": "not-base64-encoded",
            "messageId": "test-message-id",
            "publishTime": "2020-01-01T00:00:00Z"
        },
        "subscription": "projects/test-project/subscriptions/test-subscription"
    }
    
    # Don't mock process_history as it shouldn't be called in this case
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"):
        response = test_client.post(
            "/api/v1/webhook/pubsub",
            json=invalid_payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "decoding" in data["detail"]


def test_webhook_pubsub_missing_history_id(test_client):
    """Test webhook endpoint with missing historyId in the data."""
    # Create message data without historyId
    data = {
        'emailAddress': 'user@example.com'
    }
    json_data = json.dumps(data)
    encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
    
    invalid_payload = {
        "message": {
            "data": encoded_data,
            "messageId": "test-message-id",
            "publishTime": "2020-01-01T00:00:00Z"
        },
        "subscription": "projects/test-project/subscriptions/test-subscription"
    }
    
    # Don't mock process_history as it shouldn't be called in this case
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"):
        response = test_client.post(
            "/api/v1/webhook/pubsub",
            json=invalid_payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "historyId" in data["detail"] 