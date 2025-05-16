"""Tests for the gmail_client module."""
import os
import json
import base64
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, mock_open

import pytest
from googleapiclient.errors import HttpError

from src.gmail_service.gmail_client import GmailClient
from src.core.config import GMAIL_USER_ID, GMAIL_LABEL_URGENT


@pytest.fixture
def mock_http_error():
    """Create a mock HttpError for testing."""
    mock_resp = MagicMock()
    mock_resp.status = 400
    mock_resp.reason = "Bad Request"
    return HttpError(resp=mock_resp, content=b'{"error": {"message": "Error message"}}')


@pytest.fixture
def mock_email_response():
    """Create a mock email response for testing."""
    payload = {
        'headers': [
            {'name': 'Subject', 'value': 'Test Subject'},
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'Date', 'value': 'Wed, 1 Jun 2023 10:00:00 +0000 (UTC)'}
        ],
        'parts': [
            {
                'mimeType': 'text/plain',
                'body': {'data': base64.urlsafe_b64encode(b'Plain text body').decode('ASCII')}
            },
            {
                'mimeType': 'text/html',
                'body': {'data': base64.urlsafe_b64encode(b'<p>HTML body</p>').decode('ASCII')}
            }
        ]
    }
    
    return {
        'id': 'msg123',
        'threadId': 'thread123',
        'snippet': 'Email snippet...',
        'payload': payload
    }


@patch('src.gmail_service.gmail_client.build')
class TestGmailClient:
    """Tests for the GmailClient class."""

    def test_init_successful(self, mock_build, mock_gmail_service):
        """Test successful initialization of GmailClient."""
        # Arrange
        mock_build.return_value = mock_gmail_service
        
        # Mock Credentials.from_authorized_user_file to return valid credentials
        with patch('os.path.exists', return_value=True), \
             patch('src.gmail_service.gmail_client.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)
            
            # Act
            client = GmailClient()
            
            # Assert
            assert client.service is not None
            assert client.service == mock_gmail_service
            mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds.from_authorized_user_file.return_value)

    def test_init_credentials_invalid(self, mock_build, mock_gmail_service):
        """Test initialization when credentials exist but are invalid."""
        # Arrange
        mock_build.return_value = mock_gmail_service
        
        # Mock invalid credentials that need refresh
        with patch('os.path.exists', return_value=True), \
             patch('src.gmail_service.gmail_client.Credentials') as mock_creds, \
             patch('src.gmail_service.gmail_client.Request') as mock_request:
            mock_instance = MagicMock(valid=False, expired=True, refresh_token=True)
            mock_creds.from_authorized_user_file.return_value = mock_instance
            
            # Act
            client = GmailClient()
            
            # Assert
            mock_instance.refresh.assert_called_once_with(mock_request.return_value)
            mock_build.assert_called_once()

    def test_init_oauth_flow(self, mock_build, mock_gmail_service):
        """Test initialization with OAuth flow when no credentials exist."""
        # Arrange
        mock_build.return_value = mock_gmail_service
        
        with patch('os.path.exists', side_effect=[False, True]), \
             patch('src.gmail_service.gmail_client.InstalledAppFlow') as mock_flow, \
             patch('builtins.open', mock_open()) as mock_file:
            mock_flow_instance = MagicMock()
            mock_flow.from_client_secrets_file.return_value = mock_flow_instance
            mock_flow_instance.run_local_server.return_value = MagicMock(to_json=lambda: '{"token": "test"}')
            
            # Act
            client = GmailClient()
            
            # Assert
            mock_flow.from_client_secrets_file.assert_called_once()
            mock_flow_instance.run_local_server.assert_called_once()
            mock_file().write.assert_called_once_with('{"token": "test"}')

    def test_get_or_create_label_existing(self, mock_build, mock_gmail_service):
        """Test getting an existing label."""
        # Arrange
        mock_build.return_value = mock_gmail_service
        
        # Mock label list response
        mock_labels_response = {'labels': [
            {'id': 'label123', 'name': GMAIL_LABEL_URGENT}
        ]}
        mock_gmail_service.users().labels().list().execute.return_value = mock_labels_response
        
        with patch('os.path.exists', return_value=True), \
             patch('src.gmail_service.gmail_client.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)
            client = GmailClient()
            
            # Reset mocks to clear initialization calls
            mock_gmail_service.reset_mock()
            mock_gmail_service.users().labels().list.reset_mock()
            
            # Act
            label_id = client._get_or_create_label(GMAIL_LABEL_URGENT)
            
            # Assert
            assert label_id == 'label123'
            mock_gmail_service.users().labels().list.assert_called_once_with(userId=GMAIL_USER_ID)
            mock_gmail_service.users().labels().create.assert_not_called()

    def test_get_or_create_label_new(self, mock_build, mock_gmail_service):
        """Test creating a new label."""
        # Arrange
        mock_build.return_value = mock_gmail_service
        
        # Mock empty label list response
        mock_labels_response = {'labels': []}
        mock_gmail_service.users().labels().list().execute.return_value = mock_labels_response
        
        # Mock label creation response
        mock_created_label = {'id': 'newlabel123', 'name': GMAIL_LABEL_URGENT}
        mock_gmail_service.users().labels().create().execute.return_value = mock_created_label
        
        with patch('os.path.exists', return_value=True), \
             patch('src.gmail_service.gmail_client.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)
            client = GmailClient()
            
            # Reset mock to clear the init call
            mock_gmail_service.users().labels().list.reset_mock()
            mock_gmail_service.users().labels().create.reset_mock()
            
            # Act
            label_id = client._get_or_create_label(GMAIL_LABEL_URGENT)
            
            # Assert
            assert label_id == 'newlabel123'
            mock_gmail_service.users().labels().list.assert_called_once_with(userId=GMAIL_USER_ID)
            mock_gmail_service.users().labels().create.assert_called_once()

    def test_get_email_details(self, mock_build, mock_gmail_service, mock_email_response):
        """Test fetching email details."""
        # Arrange
        mock_build.return_value = mock_gmail_service
        mock_gmail_service.users().messages().get().execute.return_value = mock_email_response
        
        with patch('os.path.exists', return_value=True), \
             patch('src.gmail_service.gmail_client.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)
            client = GmailClient()
            
            # Act
            email_data = client.get_email_details('msg123')
            
            # Assert
            assert email_data is not None
            assert email_data['id'] == 'msg123'
            assert email_data['thread_id'] == 'thread123'
            assert email_data['subject'] == 'Test Subject'
            assert email_data['sender'] == 'sender@example.com'
            assert email_data['body_plain'] == 'Plain text body'
            assert email_data['body_html'] == '<p>HTML body</p>'
            assert isinstance(email_data['received_timestamp'], datetime)
            assert email_data['snippet'] == 'Email snippet...'

    def test_get_email_details_http_error(self, mock_build, mock_gmail_service, mock_http_error):
        """Test handling HTTP errors when fetching email details."""
        # Arrange
        mock_build.return_value = mock_gmail_service
        mock_gmail_service.users().messages().get().execute.side_effect = mock_http_error
        
        with patch('os.path.exists', return_value=True), \
             patch('src.gmail_service.gmail_client.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)
            client = GmailClient()
            
            # Act
            email_data = client.get_email_details('msg123')
            
            # Assert
            assert email_data is None

    def test_apply_urgent_label(self, mock_build, mock_gmail_service):
        """Test applying urgent label to an email."""
        # Arrange
        mock_build.return_value = mock_gmail_service
        
        with patch('os.path.exists', return_value=True), \
             patch('src.gmail_service.gmail_client.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)
            client = GmailClient()
            client.urgent_label_id = 'urgent_label_123'
            
            # Act
            result = client.apply_urgent_label('msg123')
            
            # Assert
            assert result is True
            mock_gmail_service.users().messages().modify.assert_called_once_with(
                userId=GMAIL_USER_ID, 
                id='msg123', 
                body={'addLabelIds': ['urgent_label_123'], 'removeLabelIds': []}
            )

    def test_setup_push_notifications(self, mock_build, mock_gmail_service):
        """Test setting up push notifications."""
        # Arrange
        mock_build.return_value = mock_gmail_service
        mock_watch_response = {
            'historyId': '12345',
            'expiration': str(int(datetime.now(timezone.utc).timestamp() * 1000) + 60*60*1000)  # 1 hour from now
        }
        mock_gmail_service.users().watch().execute.return_value = mock_watch_response
        
        with patch('os.path.exists', return_value=True), \
             patch('src.gmail_service.gmail_client.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)
            client = GmailClient()
            
            # Mock the label_id to avoid get_or_create_label calls
            client.urgent_label_id = 'mock_label_id'
            
            # Reset mocks
            mock_gmail_service.reset_mock()
            mock_gmail_service.users().watch.reset_mock()
            
            # Act
            result = client.setup_push_notifications()
            
            # Assert
            assert result is True
            
            # Verify watch was called with correct parameters
            assert mock_gmail_service.users().watch.call_count > 0
            
            # Verify request body
            watch_call_args = mock_gmail_service.users().watch.call_args_list[0]
            assert 'userId' in watch_call_args[1]
            assert watch_call_args[1]['userId'] == 'me'
            
            mock_gmail_service.users().watch.assert_called_once()
            expected_topic_name = f"projects/{os.environ['GOOGLE_CLOUD_PROJECT_ID']}/topics/{os.environ['GOOGLE_PUBSUB_TOPIC_ID']}"
            watch_request = mock_gmail_service.users().watch.call_args[1]['body']
            assert watch_request['topicName'] == expected_topic_name
            assert watch_request['labelIds'] == ['INBOX']

    def test_stop_push_notifications(self, mock_build, mock_gmail_service):
        """Test stopping push notifications."""
        # Arrange
        mock_build.return_value = mock_gmail_service
        
        with patch('os.path.exists', return_value=True), \
             patch('src.gmail_service.gmail_client.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)
            client = GmailClient()
            
            # Act
            result = client.stop_push_notifications()
            
            # Assert
            assert result is True
            mock_gmail_service.users().stop.assert_called_once_with(userId=GMAIL_USER_ID) 