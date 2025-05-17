"""Tests for the email processing API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.app import app
from src.api.dependencies import get_api_key, get_gmail_client, get_ai_processor, get_slack_client
from src.utils.exceptions import (
    GmailServiceError,
    AIServiceError,
    SlackServiceError,
    GmailAPIError
)
from src.core.types import AnalyzedEmailData, EmailData


@pytest.fixture
def test_client_fixture():
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
def mock_gmail_client_instance():
    """Provides a MagicMock instance for GmailClient."""
    return MagicMock()

@pytest.fixture
def mock_ai_processor_instance():
    """Provides a MagicMock instance for AIProcessor."""
    return MagicMock()

@pytest.fixture
def mock_slack_client_instance():
    """Provides a MagicMock instance for SlackServiceClient."""
    return MagicMock()


@pytest.fixture
def mock_process_email_success_override(
    mock_gmail_client_instance, 
    mock_ai_processor_instance, 
    mock_slack_client_instance, 
    mock_analyzed_regular_email_data: AnalyzedEmailData
):
    """Configures mock instances for successful regular email processing."""
    mock_gmail_client_instance.get_email_details.return_value = mock_analyzed_regular_email_data
    # apply_urgent_label should not be called for regular email
    mock_gmail_client_instance.apply_urgent_label = MagicMock() 

    mock_ai_processor_instance.process_email.return_value = {
        **mock_analyzed_regular_email_data, # Simulate AI adding its analysis
        'is_urgent': False 
    }
    
    # send_urgent_email_notification should not be called
    mock_slack_client_instance.send_urgent_email_notification = MagicMock()

    return mock_gmail_client_instance, mock_ai_processor_instance, mock_slack_client_instance


@pytest.fixture
def mock_process_urgent_email_override(
    mock_gmail_client_instance, 
    mock_ai_processor_instance, 
    mock_slack_client_instance, 
    mock_analyzed_urgent_email_data: AnalyzedEmailData
):
    """Configures mock instances for successful urgent email processing."""
    mock_gmail_client_instance.get_email_details.return_value = mock_analyzed_urgent_email_data
    mock_gmail_client_instance.apply_urgent_label.return_value = True

    mock_ai_processor_instance.process_email.return_value = {
        **mock_analyzed_urgent_email_data, # Simulate AI adding its analysis
        'is_urgent': True
    }
    mock_slack_client_instance.send_urgent_email_notification.return_value = True
    return mock_gmail_client_instance, mock_ai_processor_instance, mock_slack_client_instance

@pytest.fixture
def mock_email_history_processing_override(mock_gmail_client_instance, mock_email_data: EmailData):
    """Configures mock Gmail client for history processing using overrides."""
    mock_gmail_client_instance.get_history.return_value = {
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
    mock_gmail_client_instance.get_email_details.return_value = mock_email_data
    mock_gmail_client_instance.apply_urgent_label.return_value = True
    return mock_gmail_client_instance


def test_process_email_endpoint_regular(
    test_client_fixture, 
    mock_process_email_success_override, # Use the new fixture
    mock_api_key # For header if not overriding get_api_key, or for lambda if overriding
):
    """Test processing a regular (non-urgent) email using dependency_overrides."""
    gmail_client, ai_processor, slack_client = mock_process_email_success_override
    
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_api_key] = lambda: mock_api_key # Ensures endpoint auth passes
    app.dependency_overrides[get_gmail_client] = lambda: gmail_client
    app.dependency_overrides[get_ai_processor] = lambda: ai_processor
    app.dependency_overrides[get_slack_client] = lambda: slack_client
    
    try:
        response = test_client_fixture.post(
            "/api/v1/emails/process",
            json={"email_id": "test123"}
            # No explicit header needed here if get_api_key is overridden to just return the key
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["email_id"] == "test123"
        assert data["is_urgent"] is False
        assert "message" in data
        
        gmail_client.get_email_details.assert_called_once_with("test123")
        ai_processor.process_email.assert_called_once()
        gmail_client.apply_urgent_label.assert_not_called()
        slack_client.send_urgent_email_notification.assert_not_called()
    finally:
        app.dependency_overrides = original_overrides


def test_process_email_endpoint_urgent(
    test_client_fixture, 
    mock_process_urgent_email_override, # Use new fixture
    mock_api_key
):
    """Test processing an urgent email using dependency_overrides."""
    gmail_client, ai_processor, slack_client = mock_process_urgent_email_override
    
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_api_key] = lambda: mock_api_key
    app.dependency_overrides[get_gmail_client] = lambda: gmail_client
    app.dependency_overrides[get_ai_processor] = lambda: ai_processor
    app.dependency_overrides[get_slack_client] = lambda: slack_client

    try:
        response = test_client_fixture.post(
            "/api/v1/emails/process",
            json={"email_id": "urgent123"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["email_id"] == "urgent123"
        assert data["is_urgent"] is True
        assert "message" in data
        
        gmail_client.get_email_details.assert_called_once_with("urgent123")
        ai_processor.process_email.assert_called_once()
        gmail_client.apply_urgent_label.assert_called_once_with("urgent123")
        slack_client.send_urgent_email_notification.assert_called_once()
    finally:
        app.dependency_overrides = original_overrides


def test_process_email_not_found(
    test_client_fixture, 
    mock_gmail_client_instance, # Use generic instance
    mock_ai_processor_instance, 
    mock_slack_client_instance,
    mock_api_key
):
    """Test processing an email that doesn't exist using dependency_overrides."""
    mock_gmail_client_instance.get_email_details.return_value = None # Key configuration for this test
    
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_api_key] = lambda: mock_api_key
    app.dependency_overrides[get_gmail_client] = lambda: mock_gmail_client_instance
    app.dependency_overrides[get_ai_processor] = lambda: mock_ai_processor_instance
    app.dependency_overrides[get_slack_client] = lambda: mock_slack_client_instance
    
    try:
        response = test_client_fixture.post(
            "/api/v1/emails/process",
            json={"email_id": "nonexistent123"}
        )
        
        assert response.status_code == 202 
        data = response.json()
        assert data["success"] is False
        assert data["email_id"] == "nonexistent123"
        assert "not found" in data["message"].lower() or "could not be retrieved" in data["message"].lower()
    finally:
        app.dependency_overrides = original_overrides

# Refactoring error handling tests
def test_process_email_gmail_service_error(
    test_client_fixture,
    mock_ai_processor_instance, 
    mock_slack_client_instance,
    mock_api_key
):
    """Test handling GmailServiceError during GmailClient instantiation within get_gmail_client."""
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_api_key] = lambda: mock_api_key
    # AI and Slack clients can be standard mocks, as they are not the focus
    app.dependency_overrides[get_ai_processor] = lambda: mock_ai_processor_instance
    app.dependency_overrides[get_slack_client] = lambda: mock_slack_client_instance
    # Do NOT override get_gmail_client itself. Let the original run.

    try:
        # Mock GmailClient.__init__ to raise the error, so get_gmail_client catches it
        with patch('src.api.dependencies.GmailClient.__init__', side_effect=GmailServiceError("Mocked Gmail Init Error")):
            response = test_client_fixture.post(
                "/api/v1/emails/process",
                json={"email_id": "test123"}
            )
        assert response.status_code == 503 
        data = response.json()
        assert "Gmail service unavailable" in data["detail"] # Message from HTTPException in original get_gmail_client
    finally:
        app.dependency_overrides = original_overrides


def test_process_email_ai_service_error(
    test_client_fixture, 
    mock_gmail_client_instance, # Configured to return some email data
    mock_slack_client_instance,
    mock_api_key,
    mock_email_data: EmailData
):
    """Test handling AIServiceError during AIProcessor instantiation within get_ai_processor."""
    mock_gmail_client_instance.get_email_details.return_value = mock_email_data

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_api_key] = lambda: mock_api_key
    app.dependency_overrides[get_gmail_client] = lambda: mock_gmail_client_instance # Gmail client is fine here
    app.dependency_overrides[get_slack_client] = lambda: mock_slack_client_instance
    # Do NOT override get_ai_processor itself. Let the original run.

    try:
        # Mock AIProcessor.__init__ to raise the error, so get_ai_processor catches it
        with patch('src.api.dependencies.AIProcessor.__init__', side_effect=AIServiceError("Mocked AI Init Error")):
            response = test_client_fixture.post(
                "/api/v1/emails/process",
                json={"email_id": "test123"}
            )
        assert response.status_code == 503
        data = response.json()
        assert "AI service unavailable" in data["detail"] # Message from HTTPException in original get_ai_processor
    finally:
        app.dependency_overrides = original_overrides


def test_process_history_endpoint(
    test_client_fixture, 
    mock_email_history_processing_override, # Use new fixture
    mock_ai_processor_instance, # Generic mock for AI
    mock_slack_client_instance, # Generic mock for Slack
    mock_api_key
):
    """Test processing Gmail history updates using dependency_overrides."""
    gmail_client = mock_email_history_processing_override
    # Configure AI mock for this test if its behavior is important
    mock_ai_processor_instance.process_email.return_value = {'is_urgent': False, 'summary': 'Test summary'}

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_api_key] = lambda: mock_api_key
    app.dependency_overrides[get_gmail_client] = lambda: gmail_client
    app.dependency_overrides[get_ai_processor] = lambda: mock_ai_processor_instance
    app.dependency_overrides[get_slack_client] = lambda: mock_slack_client_instance
    
    try:
        response = test_client_fixture.post(
            "/api/v1/emails/history",
            json={"history_id": "12345"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["history_id"] == "12345"
        assert "processed_emails" in data
        assert data["processed_emails"] == 1 # Based on mock_email_history_processing_override
        assert "message" in data
    finally:
        app.dependency_overrides = original_overrides


def test_process_history_empty(
    test_client_fixture, 
    mock_gmail_client_instance, # Generic mock
    mock_ai_processor_instance,
    mock_slack_client_instance,
    mock_api_key
):
    """Test processing empty history with no new messages using dependency_overrides."""
    mock_gmail_client_instance.get_history.return_value = {'history': [], 'historyId': 'empty123'} # Key config
    
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_api_key] = lambda: mock_api_key
    app.dependency_overrides[get_gmail_client] = lambda: mock_gmail_client_instance
    app.dependency_overrides[get_ai_processor] = lambda: mock_ai_processor_instance
    app.dependency_overrides[get_slack_client] = lambda: mock_slack_client_instance
        
    try:
        response = test_client_fixture.post(
            "/api/v1/emails/history",
            json={"history_id": "empty123"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["history_id"] == "empty123"
        assert data["processed_emails"] == 0
        assert "No new messages found" in data["message"] # Check for specific message
    finally:
        app.dependency_overrides = original_overrides


def test_process_history_gmail_api_error(
    test_client_fixture,
    mock_ai_processor_instance,
    mock_slack_client_instance,
    mock_api_key
):
    """Test handling GmailAPIError during history processing (raised by the client method, not the dependency getter)."""
    
    # This test assumes the error is raised by the *method* of the GmailClient,
    # not by the get_gmail_client dependency provider itself.
    # The get_gmail_client provider is expected to succeed in providing a client.
    
    gmail_client_raising_error = MagicMock()
    gmail_client_raising_error.get_history.side_effect = GmailAPIError("Mocked API error during history processing")

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_api_key] = lambda: mock_api_key
    app.dependency_overrides[get_gmail_client] = lambda: gmail_client_raising_error # Provide the client that will raise on method call
    app.dependency_overrides[get_ai_processor] = lambda: mock_ai_processor_instance
    app.dependency_overrides[get_slack_client] = lambda: mock_slack_client_instance
            
    try:
        response = test_client_fixture.post(
            "/api/v1/emails/history",
            json={"history_id": "error123"}
        )
        
        # The endpoint itself should catch GmailAPIError and return a 503 or specific error response.
        # Check the email router's error handling for this.
        # Assuming the router catches GmailAPIError from client.get_history()
        # and translates it to a 503 response for client-side errors.
        assert response.status_code == 503 
        data = response.json()
        # The original error message from the mock is included in the detail
        assert "Gmail API error: Mocked API error during history processing" == data["detail"] 
    finally:
        app.dependency_overrides = original_overrides

# Note: mock_email_data, mock_analyzed_regular_email_data, mock_analyzed_urgent_email_data
# should be available from conftest.py. If not, define them here or ensure they are imported.
# The fixture mock_api_key is assumed to be from conftest.py for setting up API_KEY in api_settings.
# If overriding get_api_key to `lambda: "some-key"`, the header in test_client calls might not be strictly necessary
# but good practice if other parts of the system might expect the header. 