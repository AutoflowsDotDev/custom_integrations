"""Common pytest fixtures for tests."""
import os
import json
import pytest
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch
import base64

# Add pytest-asyncio configuration
pytest_plugins = ['pytest_asyncio']
# Set default async fixture scope to function to avoid deprecation warning
pytestmark = pytest.mark.asyncio_mode("strict")

from src.core.types import EmailData, AnalyzedEmailData


# Mock Google Cloud Pub/Sub package before imports
class MockTypes:
    """Mock types for Google Cloud Pub/Sub."""
    class ReceivedMessage:
        """Mock ReceivedMessage class."""
        pass


class MockPubSub:
    """Mock class for Google Cloud Pub/Sub."""
    SubscriberClient = MagicMock
    PublisherClient = MagicMock
    types = MockTypes


# Create module structure for google.cloud.pubsub_v1
class MockGoogleCloud:
    """Mock class for Google Cloud."""
    pubsub_v1 = MockPubSub()


# Add to sys.modules to mock the imports
sys.modules['google.cloud'] = MockGoogleCloud()
sys.modules['google.cloud.pubsub_v1'] = MockPubSub()
sys.modules['google.cloud.pubsub_v1.types'] = MockTypes()


@pytest.fixture(scope="session", autouse=True)
def mock_env_variables():
    """Set environment variables for testing."""
    os.environ["GOOGLE_CLIENT_SECRETS_JSON_PATH"] = "dummy/path/client_secret.json"
    os.environ["GOOGLE_CREDENTIALS_JSON_PATH"] = "dummy/path/credentials.json"
    os.environ["GOOGLE_SERVICE_ACCOUNT_PATH"] = "dummy/path/service_account.json"
    os.environ["GOOGLE_CLOUD_PROJECT_ID"] = "test-project-id"
    os.environ["GOOGLE_PUBSUB_TOPIC_ID"] = "test-topic-id"
    os.environ["GOOGLE_PUBSUB_SUBSCRIPTION_ID"] = "test-subscription-id"
    os.environ["SLACK_BOT_TOKEN"] = "xoxb-test-token"
    os.environ["SLACK_CHANNEL_ID"] = "C123456789"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["API_KEY"] = "test-api-key"
    yield
    # No need to clean up - environment variables are process-scoped


@pytest.fixture(scope="session", autouse=True)
def mock_service_files():
    """Mock the existence of service account files."""
    # Create a more specific mock for file existence
    original_exists = os.path.exists
    
    def mock_exists(path):
        # Return True for service account files mentioned in env vars or test paths
        if (path.endswith('service_account.json') or 
            path.endswith('credentials.json') or 
            path.endswith('client_secret.json') or
            path in ['dummy/path/service_account.json', 'dummy/path/credentials.json', 'dummy/path/client_secret.json']):
            return True
        # Fall back to real implementation for other paths
        return original_exists(path)
    
    # Pre-dump the fake service account JSON so that tests reading the file
    # get deterministic content.
    _FAKE_SERVICE_ACCOUNT_JSON = json.dumps({
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test_private_key_id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nTEST_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
        "client_email": "test-client-email@example.com",
        "client_id": "test_client_id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-client-email%40example.com"
    })

    # Cache the original built-in open so we can delegate to it for all non-mock
    # paths. This prevents interference with third-party libraries such as
    # coverage.py, which need to read their own binary data files.
    _real_open = open  # noqa: A001 – shadowing built-in on purpose within scope

    def _mocked_open(path, mode="r", *args, **kwargs):  # noqa: D401,E501
        """Selective open mock.

        Only intercepts read operations for the credential/service-account JSON
        files used by the Gmail client setup. For all other paths (including
        coverage data files opened in binary mode), the real ``open`` built-in
        is used to avoid type errors like the one seen when combining coverage
        reports.
        """

        # Normalize the incoming path to something we can match on.
        _path_str = str(path)

        # Detect if this is one of the credential files we want to fake.
        if any(
            _path_str.endswith(suffix)
            for suffix in (
                "service_account.json",
                "credentials.json",
                "client_secret.json",
            )
        ) and "r" in mode:
            mock_file = MagicMock()
            # Ensure read() returns *bytes* if the caller opened in binary
            # mode, otherwise str. This maintains compatibility with the
            # caller's expectations.
            content_bytes = _FAKE_SERVICE_ACCOUNT_JSON.encode()
            if "b" in mode:
                mock_file.read.return_value = content_bytes
            else:
                mock_file.read.return_value = _FAKE_SERVICE_ACCOUNT_JSON

            # Context manager support
            mock_file.__enter__.return_value = mock_file
            mock_file.__exit__.return_value = None

            return mock_file

        # Fallback to the real open for everything else.
        return _real_open(path, mode, *args, **kwargs)

    with patch('os.path.exists', mock_exists), \
         patch('builtins.open', _mocked_open), \
         patch('json.load', side_effect=lambda f: json.loads(f.read())):
        yield


@pytest.fixture(scope="session", autouse=True)
def mock_transformers_pipeline():
    """Mock the transformers pipeline to avoid loading the actual models."""
    with patch('transformers.pipeline') as mock_pipeline:
        def pipeline_side_effect(task, model=None):
            pipeline_mock = MagicMock()
            if task == "text-classification":
                # Configure the mock to return a non-urgent classification by default
                pipeline_mock.return_value = [{"label": "NOT_URGENT", "score": 0.80}]
            elif task == "summarization":
                # Configure the mock to return a simple summary
                pipeline_mock.return_value = [{"summary_text": "This is a summary of the email."}]
            else:
                pipeline_mock.return_value = []
            return pipeline_mock
        
        mock_pipeline.side_effect = pipeline_side_effect
        yield mock_pipeline


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


@pytest.fixture
def mock_pubsub_message():
    """Create a mock Pub/Sub message."""
    # Create message data (simulating Gmail notification)
    data = {
        'emailAddress': 'user@example.com',
        'historyId': '12345'
    }
    json_data = json.dumps(data)
    encoded_data = base64.b64encode(json_data.encode('utf-8'))
    
    # Create mock message
    message = MagicMock()
    message.message_id = 'test-message-id'
    message.data = MagicMock(spec=bytes)
    
    # Configure the decode method
    message.data.decode.return_value = json_data
    
    message.ack = MagicMock()
    message.nack = MagicMock()
    
    return message 