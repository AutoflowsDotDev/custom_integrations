"""Tests for the email processing API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.app import app
from src.utils.exceptions import (
    GmailServiceError,
    AIServiceError,
    SlackServiceError,
    GmailAPIError
)


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_api_key():
    """Mock API key for tests."""
    with patch('src.api.dependencies.api_settings') as mock_settings:
        mock_settings.API_KEY_NAME = "X-API-KEY"
        mock_settings.API_KEY = "test-api-key"
        yield "test-api-key"


@pytest.fixture
def mock_process_email_success(mock_analyzed_regular_email_data):
    """Mock successful email processing."""
    gmail_client = MagicMock()
    gmail_client.get_email_details.return_value = mock_analyzed_regular_email_data
    gmail_client.apply_urgent_label.return_value = True

    ai_processor = MagicMock()
    ai_processor.process_email.return_value = {
        **mock_analyzed_regular_email_data,
        'is_urgent': False
    }

    slack_client = MagicMock()
    slack_client.send_urgent_email_notification.return_value = True

    return gmail_client, ai_processor, slack_client


@pytest.fixture
def mock_process_urgent_email(mock_analyzed_urgent_email_data):
    """Mock processing of an urgent email."""
    gmail_client = MagicMock()
    gmail_client.get_email_details.return_value = mock_analyzed_urgent_email_data
    gmail_client.apply_urgent_label.return_value = True

    ai_processor = MagicMock()
    ai_processor.process_email.return_value = {
        **mock_analyzed_urgent_email_data,
        'is_urgent': True
    }

    slack_client = MagicMock()
    slack_client.send_urgent_email_notification.return_value = True

    return gmail_client, ai_processor, slack_client


@pytest.fixture
def mock_email_history_processing():
    """Mock Gmail client for history processing."""
    # Create a mock Gmail client
    gmail_client = MagicMock()
    
    # Configure get_history to return valid history data
    gmail_client.get_history.return_value = {
        'history': [
            {
                'id': '12345',
                'messagesAdded': [
                    {'message': {'id': 'msg1'}}
                ]
            }
        ],
        'historyId': '12346'
    }
    
    # Configure get_email_details to return a test email
    gmail_client.get_email_details.return_value = {
        'id': 'msg1',
        'thread_id': 'thread123',
        'subject': 'Test Subject',
        'sender': 'sender@example.com',
        'body_plain': 'This is a test email body.',
        'body_html': '<p>This is a test email body.</p>',
        'received_timestamp': '2023-01-01T12:00:00Z',
        'snippet': 'This is a test email...'
    }
    
    # Configure apply_urgent_label
    gmail_client.apply_urgent_label.return_value = True
    
    return gmail_client


def test_process_email_endpoint_regular(test_client, mock_process_email_success):
    """Test processing a regular (non-urgent) email."""
    gmail_client, ai_processor, slack_client = mock_process_email_success
    
    # Mock everything needed for this test to avoid service account errors
    with patch('src.gmail_service.gmail_client.GmailClient.__init__', return_value=None), \
         patch('src.ai_service.ai_processor.AIProcessor.__init__', return_value=None), \
         patch('src.slack_service.slack_client.SlackServiceClient.__init__', return_value=None), \
         patch('src.api.dependencies.get_api_key', return_value="test-api-key"), \
         patch('src.api.dependencies.get_gmail_client', return_value=gmail_client), \
         patch('src.api.dependencies.get_ai_processor', return_value=ai_processor), \
         patch('src.api.dependencies.get_slack_client', return_value=slack_client), \
         patch('src.api.routers.email.get_gmail_client', return_value=gmail_client), \
         patch('src.api.routers.email.get_ai_processor', return_value=ai_processor), \
         patch('src.api.routers.email.get_slack_client', return_value=slack_client):
        
        response = test_client.post(
            "/api/v1/emails/process",
            json={"email_id": "test123"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["email_id"] == "test123"
        assert data["is_urgent"] is False
        assert "message" in data
        
        # Verify that the clients were called as expected
        gmail_client.get_email_details.assert_called_once_with("test123")
        ai_processor.process_email.assert_called_once()
        
        # Urgent actions should not be performed
        gmail_client.apply_urgent_label.assert_not_called()
        slack_client.send_urgent_email_notification.assert_not_called()


def test_process_email_endpoint_urgent(test_client, mock_process_urgent_email):
    """Test processing an urgent email."""
    gmail_client, ai_processor, slack_client = mock_process_urgent_email
    
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"), \
         patch('src.api.dependencies.get_gmail_client', return_value=gmail_client), \
         patch('src.api.dependencies.get_ai_processor', return_value=ai_processor), \
         patch('src.api.dependencies.get_slack_client', return_value=slack_client):
        
        response = test_client.post(
            "/api/v1/emails/process",
            json={"email_id": "urgent123"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["email_id"] == "urgent123"
        assert data["is_urgent"] is True
        assert "message" in data
        
        # Verify that the clients were called as expected
        gmail_client.get_email_details.assert_called_once_with("urgent123")
        ai_processor.process_email.assert_called_once()
        
        # Urgent actions should be performed
        gmail_client.apply_urgent_label.assert_called_once_with("urgent123")
        slack_client.send_urgent_email_notification.assert_called_once()


def test_process_email_not_found(test_client):
    """Test processing an email that doesn't exist."""
    gmail_client = MagicMock()
    gmail_client.get_email_details.return_value = None
    
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"), \
         patch('src.api.dependencies.get_gmail_client', return_value=gmail_client), \
         patch('src.api.dependencies.get_ai_processor', return_value=MagicMock()), \
         patch('src.api.dependencies.get_slack_client', return_value=MagicMock()):
        
        response = test_client.post(
            "/api/v1/emails/process",
            json={"email_id": "nonexistent123"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is False
        assert data["email_id"] == "nonexistent123"
        assert "not found" in data["message"].lower() or "could not be retrieved" in data["message"].lower()


def test_process_email_gmail_error(test_client):
    """Test handling Gmail service errors."""
    gmail_client = MagicMock()
    gmail_client.get_email_details.side_effect = GmailServiceError("Gmail error")
    
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"), \
         patch('src.api.dependencies.get_gmail_client', return_value=gmail_client), \
         patch('src.api.dependencies.get_ai_processor', return_value=MagicMock()), \
         patch('src.api.dependencies.get_slack_client', return_value=MagicMock()):
        
        response = test_client.post(
            "/api/v1/emails/process",
            json={"email_id": "test123"}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert "Gmail service error" in data["detail"]


def test_process_email_ai_error(test_client, mock_email_data):
    """Test handling AI service errors."""
    gmail_client = MagicMock()
    gmail_client.get_email_details.return_value = mock_email_data
    
    ai_processor = MagicMock()
    ai_processor.process_email.side_effect = AIServiceError("AI error")
    
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"), \
         patch('src.api.dependencies.get_gmail_client', return_value=gmail_client), \
         patch('src.api.dependencies.get_ai_processor', return_value=ai_processor), \
         patch('src.api.dependencies.get_slack_client', return_value=MagicMock()):
        
        response = test_client.post(
            "/api/v1/emails/process",
            json={"email_id": "test123"}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert "AI service error" in data["detail"]


def test_process_history_endpoint(test_client, mock_email_history_processing):
    """Test processing Gmail history updates."""
    gmail_client = mock_email_history_processing
    
    ai_processor = MagicMock()
    ai_processor.process_email.return_value = {'is_urgent': False, 'summary': 'Test summary'}
    
    slack_client = MagicMock()
    
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"), \
         patch('src.api.dependencies.get_gmail_client', return_value=gmail_client), \
         patch('src.api.dependencies.get_ai_processor', return_value=ai_processor), \
         patch('src.api.dependencies.get_slack_client', return_value=slack_client):
        
        response = test_client.post(
            "/api/v1/emails/history",
            json={"history_id": "12345"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["history_id"] == "12345"
        assert "processed_emails" in data
        assert "message" in data


def test_process_history_empty(test_client):
    """Test processing empty history with no new messages."""
    gmail_client = MagicMock()
    gmail_client.get_history.return_value = {'history': []}
    
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"), \
         patch('src.api.dependencies.get_gmail_client', return_value=gmail_client), \
         patch('src.api.dependencies.get_ai_processor', return_value=MagicMock()), \
         patch('src.api.dependencies.get_slack_client', return_value=MagicMock()):
        
        response = test_client.post(
            "/api/v1/emails/history",
            json={"history_id": "12345"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["history_id"] == "12345"
        assert data["processed_emails"] == 0


def test_process_history_gmail_api_error(test_client):
    """Test handling Gmail API errors during history processing."""
    gmail_client = MagicMock()
    gmail_client.get_history.side_effect = GmailAPIError("API error")
    
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"), \
         patch('src.api.dependencies.get_gmail_client', return_value=gmail_client), \
         patch('src.api.dependencies.get_ai_processor', return_value=MagicMock()), \
         patch('src.api.dependencies.get_slack_client', return_value=MagicMock()):
        
        response = test_client.post(
            "/api/v1/emails/history",
            json={"history_id": "12345"}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert "Gmail API error" in data["detail"] 