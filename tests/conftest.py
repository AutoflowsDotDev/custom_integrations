"""Common pytest fixtures for tests."""
import os
import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.core.types import EmailData, AnalyzedEmailData


@pytest.fixture(scope="session", autouse=True)
def mock_env_variables():
    """Set environment variables for testing."""
    os.environ["GOOGLE_CLIENT_SECRETS_JSON_PATH"] = "dummy/path/client_secret.json"
    os.environ["GOOGLE_CREDENTIALS_JSON_PATH"] = "dummy/path/credentials.json"
    os.environ["GOOGLE_CLOUD_PROJECT_ID"] = "test-project-id"
    os.environ["GOOGLE_PUBSUB_TOPIC_ID"] = "test-topic-id"
    os.environ["GOOGLE_PUBSUB_SUBSCRIPTION_ID"] = "test-subscription-id"
    os.environ["SLACK_BOT_TOKEN"] = "xoxb-test-token"
    os.environ["SLACK_CHANNEL_ID"] = "C123456789"
    os.environ["LOG_LEVEL"] = "DEBUG"
    yield
    # No need to clean up - environment variables are process-scoped


@pytest.fixture
def mock_email_data() -> EmailData:
    """Create a mock email data for testing."""
    return {
        'id': 'test123',
        'thread_id': 'thread123',
        'subject': 'Test Subject',
        'sender': 'sender@example.com',
        'body_plain': 'This is a test email body.',
        'body_html': '<p>This is a test email body.</p>',
        'received_timestamp': datetime.now(),
        'snippet': 'This is a test email...'
    }


@pytest.fixture
def mock_urgent_email_data() -> EmailData:
    """Create a mock urgent email data for testing."""
    return {
        'id': 'urgent123',
        'thread_id': 'urgentthread123',
        'subject': 'URGENT: Action Required Immediately',
        'sender': 'important@example.com',
        'body_plain': 'This is an urgent matter that requires immediate attention! Please respond ASAP.',
        'body_html': '<p>This is an urgent matter that requires immediate attention! Please respond ASAP.</p>',
        'received_timestamp': datetime.now(),
        'snippet': 'This is an urgent matter...'
    }


@pytest.fixture
def mock_analyzed_urgent_email_data(mock_urgent_email_data) -> AnalyzedEmailData:
    """Create a mock analyzed urgent email data for testing."""
    return {
        **mock_urgent_email_data,
        'is_urgent': True,
        'summary': 'Urgent matter requiring immediate attention and response.'
    }


@pytest.fixture
def mock_analyzed_regular_email_data(mock_email_data) -> AnalyzedEmailData:
    """Create a mock analyzed regular email data for testing."""
    return {
        **mock_email_data,
        'is_urgent': False,
        'summary': 'Regular test email with no urgency.'
    }


@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service for testing."""
    mock_service = MagicMock()
    
    # Configure users().messages().get() chain
    mock_message = MagicMock()
    mock_messages = MagicMock()
    mock_messages.get.return_value = mock_message
    
    # Configure users().labels().list() and create() chain
    mock_label = MagicMock()
    mock_labels = MagicMock()
    mock_labels.list.return_value = mock_label
    mock_labels.create.return_value = mock_label
    
    # Configure users().watch() chain
    mock_watch = MagicMock()
    
    # Configure users().stop() chain
    mock_stop = MagicMock()
    
    # Configure users().history().list() chain
    mock_history_list = MagicMock()
    mock_history = MagicMock()
    mock_history.list.return_value = mock_history_list
    
    # Configure users().messages().modify() chain
    mock_modify = MagicMock()
    mock_messages.modify.return_value = mock_modify
    
    mock_users = MagicMock()
    mock_users.messages.return_value = mock_messages
    mock_users.labels.return_value = mock_labels
    mock_users.watch.return_value = mock_watch
    mock_users.stop.return_value = mock_stop
    mock_users.history.return_value = mock_history
    
    mock_service.users.return_value = mock_users
    
    return mock_service


@pytest.fixture
def mock_history_response():
    """Mock history response from Gmail API."""
    return {
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


@pytest.fixture
def mock_gmail_client(mock_gmail_service, mock_history_response):
    """Create a mock GmailClient with common test methods configured."""
    with patch('src.gmail_service.gmail_client.build') as mock_build:
        mock_build.return_value = mock_gmail_service
        
        with patch('os.path.exists', return_value=True), \
             patch('src.gmail_service.gmail_client.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)
            
            from src.gmail_service.gmail_client import GmailClient
            client = GmailClient()
            
            # Configure common mock methods
            client.get_history = MagicMock(return_value=mock_history_response)
            
            yield client 