"""Tests for the slack_client module."""
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest
from slack_sdk.errors import SlackApiError

from src.slack_service.slack_client import SlackServiceClient
from src.core.config import SLACK_CHANNEL_ID


@pytest.fixture
def mock_slack_client():
    """Mock the Slack WebClient."""
    with patch('src.slack_service.slack_client.WebClient') as mock_web_client:
        mock_instance = MagicMock()
        mock_web_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_analyzed_urgent_email_data():
    """Create a mock of analyzed urgent email data."""
    return {
        'id': 'urgent123',
        'thread_id': 'urgentthread123',
        'subject': 'URGENT: Action Required Immediately',
        'sender': 'important@example.com',
        'received_timestamp': datetime.now(),
        'is_urgent': True,
        'confidence_score': 0.95,
        'summary': 'Urgent matter requiring immediate attention and response.'
    }


class TestSlackServiceClient:
    """Tests for the SlackServiceClient class."""

    def test_init_with_valid_token(self, mock_slack_client):
        """Test initialization with a valid bot token."""
        # Arrange & Act
        client = SlackServiceClient(token="xoxb-valid-token")
        
        # Assert
        assert client.client == mock_slack_client

    def test_init_with_invalid_token_format(self, mock_slack_client):
        """Test initialization with an invalid token format."""
        # Act (should log a warning but not fail)
        with patch('src.slack_service.slack_client.logger.warning') as mock_warn:
            client = SlackServiceClient(token="invalid-token-format")
            
            # Assert
            assert client.client == mock_slack_client
            mock_warn.assert_called_once()
            # Check that warning contains expected text
            assert "token might be missing or invalid" in mock_warn.call_args[0][0]

    def test_format_notification_text(self, mock_slack_client, mock_analyzed_urgent_email_data):
        """Test formatting of notification text."""
        # Arrange
        client = SlackServiceClient()
        
        # Act
        notification_text = client._format_notification_text(mock_analyzed_urgent_email_data)
        
        # Assert
        assert ":rotating_light:" in notification_text
        assert "*From*: important@example.com" in notification_text
        assert "*Subject*: URGENT: Action Required Immediately" in notification_text
        assert "*Summary*: Urgent matter requiring immediate attention and response." in notification_text
        assert "View Email" in notification_text
        assert f"ID: {mock_analyzed_urgent_email_data['id']}" in notification_text

    def test_send_urgent_email_notification_success(self, mock_slack_client, mock_analyzed_urgent_email_data):
        """Test successful sending of urgent email notification."""
        # Arrange
        mock_slack_client.chat_postMessage.return_value = {"ok": True, "ts": "1234.5678"}
        client = SlackServiceClient()
        
        # Act
        result = client.send_urgent_email_notification(mock_analyzed_urgent_email_data)
        
        # Assert
        assert result is True
        mock_slack_client.chat_postMessage.assert_called_once()
        # Channel should be passed
        assert mock_slack_client.chat_postMessage.call_args[1]["channel"] == SLACK_CHANNEL_ID
        # Text should include formatted notification
        text = mock_slack_client.chat_postMessage.call_args[1]["text"]
        assert "URGENT: Action Required Immediately" in text

    def test_send_urgent_email_notification_api_failure(self, mock_slack_client, mock_analyzed_urgent_email_data):
        """Test handling of Slack API errors."""
        # Arrange
        mock_slack_client.chat_postMessage.return_value = {"ok": False, "error": "channel_not_found"}
        client = SlackServiceClient()
        
        # Act
        with patch('src.slack_service.slack_client.logger.error') as mock_error:
            result = client.send_urgent_email_notification(mock_analyzed_urgent_email_data)
            
            # Assert
            assert result is False
            mock_error.assert_called_once()
            assert "channel_not_found" in mock_error.call_args[0][0]

    def test_send_urgent_email_notification_api_exception(self, mock_slack_client, mock_analyzed_urgent_email_data):
        """Test handling of Slack API exceptions."""
        # Arrange
        slack_error_response = {'ok': False, 'error': 'invalid_auth'}
        error_message = "The request to the Slack API failed."
        mock_slack_client.chat_postMessage.side_effect = SlackApiError(
            message=error_message,
            response=MagicMock(data=slack_error_response)
        )
        client = SlackServiceClient()
        
        # Act
        with patch('src.slack_service.slack_client.logger.error') as mock_error:
            result = client.send_urgent_email_notification(mock_analyzed_urgent_email_data)
            
            # Assert
            assert result is False
            mock_error.assert_called_once()
            # Check that some kind of error message was logged
            assert "Slack API error" in mock_error.call_args[0][0]

    def test_send_urgent_email_notification_missing_channel(self, mock_slack_client, mock_analyzed_urgent_email_data):
        """Test sending notification with a missing channel."""
        # Arrange
        client = SlackServiceClient()
        
        # Act
        with patch('src.slack_service.slack_client.logger.error') as mock_error:
            result = client.send_urgent_email_notification(mock_analyzed_urgent_email_data, channel="")
            
            # Assert
            assert result is False
            mock_error.assert_called_once()
            assert "channel ID is not configured" in mock_error.call_args[0][0]
            mock_slack_client.chat_postMessage.assert_not_called() 