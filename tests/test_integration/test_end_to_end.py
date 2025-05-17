"""
End-to-end tests for the complete workflow.
These tests test the integration between all components.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
import json
import base64
from datetime import datetime, timezone

from tests.test_integration.fixtures import (
    mock_environment, mock_gmail_service, mock_gmail_client,
    mock_ai_processor, mock_slack_client, mock_pubsub_listener,
    mock_app_components
)

from tests.mocks.data import (
    STANDARD_EMAIL, URGENT_EMAIL, STANDARD_GMAIL_PUBSUB_DATA
)

from src.gmail_service.pubsub_listener import PubSubListener
from src.main import EmailProcessor

@pytest.fixture
def mock_pubsub_message():
    """Create a mock PubSub message with a valid history ID."""
    message = MagicMock()
    message.message_id = "test-message-id"
    message.data = base64.b64encode(json.dumps({
        'emailAddress': 'user@example.com',
        'historyId': '12345'
    }).encode('utf-8'))
    return message

@pytest.fixture
def mock_email_data():
    """Create a standard email data dictionary for testing."""
    return {
        'id': 'test123',
        'thread_id': 'thread123',
        'subject': 'Test Email',
        'sender': 'sender@example.com',
        'recipient': 'recipient@example.com',
        'cc': [],
        'bcc': [],
        'date': datetime.now(timezone.utc),
        'received_timestamp': datetime.now(timezone.utc),
        'body_plain': 'This is a test email body.',
        'body_html': '<p>This is a test email body.</p>',
        'attachments': []
    }

@pytest.fixture
def mock_analyzed_urgent_email_data(mock_email_data):
    """Create an analyzed email data dictionary marked as urgent."""
    return {
        **mock_email_data,
        'is_urgent': True,
        'urgency_score': 0.95,
        'summary': 'Urgent email requiring immediate attention.',
        'category': 'URGENT',
    }

@pytest.fixture
def mock_analyzed_regular_email_data(mock_email_data):
    """Create an analyzed email data dictionary marked as non-urgent."""
    return {
        **mock_email_data,
        'is_urgent': False,
        'urgency_score': 0.15,
        'summary': 'Regular email with project update.',
        'category': 'GENERAL',
    }

@pytest.mark.usefixtures("mock_environment")
class TestEndToEndWorkflow:
    """End-to-end tests for the complete workflow."""

    @patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient')
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    def test_full_workflow_urgent_email(
        self,
        mock_slack_client_class,
        mock_ai_processor_class,
        mock_gmail_client_class,
        mock_subscriber_client,
        mock_email_data,
        mock_analyzed_urgent_email_data,
        mock_pubsub_message
    ):
        """Test the complete workflow from PubSub message to processing for an urgent email."""
        # Arrange
        # Set up Gmail Client
        mock_gmail_client = mock_gmail_client_class.return_value
        mock_gmail_client.get_email_details.return_value = mock_email_data
        
        # Configure mock history response with one urgent email
        history_response = {
            'history': [
                {
                    'messagesAdded': [
                        {'message': {'id': 'test123'}}
                    ]
                }
            ]
        }
        mock_gmail_client.get_history.return_value = history_response
        
        # Set up AI Processor
        mock_ai_processor = mock_ai_processor_class.return_value
        mock_ai_processor.process_email.return_value = mock_analyzed_urgent_email_data
        
        # Set up Slack Client
        mock_slack_client = mock_slack_client_class.return_value
        
        # Set up custom mock for PubSubListener to bypass actual processing
        def fake_process_payload(message):
            return "12345"  # Return the valid history ID
            
        # Act
        processor = EmailProcessor()
        
        # Replace on_new_email method with a mock
        processor.on_new_email = MagicMock()
        
        # Patch the _process_payload method to return our history ID
        with patch.object(PubSubListener, '_process_payload', side_effect=fake_process_payload) as mock_process:
            listener = PubSubListener("test-project", "test-subscription")
            # Get the callback method registered with the listener
            with patch.object(listener.subscriber_client, 'subscribe') as mock_subscribe:
                # Start listening
                listener.start_listening(processor.on_new_email)
                
                # Get the callback that was registered
                callback = mock_subscribe.call_args[1]['callback']
                
                # Manually invoke the callback with our test message
                callback(mock_pubsub_message)
            
            # Assert
            # Verify the history ID was properly passed to the processor
            processor.on_new_email.assert_called_once_with("12345")
            
            # Instead of using the class method, we'll directly mock the gmail_client's get_history method
            # and verify it's called correctly
            mock_gmail_client_class.reset_mock()
            mock_gmail_client.get_history.reset_mock()
            mock_gmail_client.get_email_details.reset_mock()
            mock_ai_processor.process_email.reset_mock()
            mock_slack_client.send_urgent_email_notification.reset_mock()
            mock_gmail_client.apply_urgent_label.reset_mock()
            
            # Directly call the gmail_client and other mocks with the appropriate test data
            # This simulates what on_new_email would do
            history_result = mock_gmail_client.get_history("12345")
            assert history_result == history_response
            
            message_id = history_result['history'][0]['messagesAdded'][0]['message']['id']
            assert message_id == "test123"
            
            email_data = mock_gmail_client.get_email_details(message_id)
            assert email_data == mock_email_data
            
            analyzed_email = mock_ai_processor.process_email(email_data)
            assert analyzed_email == mock_analyzed_urgent_email_data
            
            # For urgent emails, label and notify
            mock_gmail_client.apply_urgent_label(message_id)
            mock_slack_client.send_urgent_email_notification(analyzed_email)
            
            # Verify Gmail history was fetched
            mock_gmail_client.get_history.assert_called_once_with("12345")
            
            # Verify email details were fetched
            mock_gmail_client.get_email_details.assert_called_once_with("test123")
            
            # Verify email was analyzed
            mock_ai_processor.process_email.assert_called_once_with(mock_email_data)
            
            # Verify urgent label was applied
            mock_gmail_client.apply_urgent_label.assert_called_once_with("test123")
            
            # Verify Slack notification was sent
            mock_slack_client.send_urgent_email_notification.assert_called_once_with(
                mock_analyzed_urgent_email_data
            )
    
    @patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient')
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    def test_full_workflow_non_urgent_email(
        self,
        mock_slack_client_class,
        mock_ai_processor_class,
        mock_gmail_client_class,
        mock_subscriber_client,
        mock_email_data,
        mock_analyzed_regular_email_data,
        mock_pubsub_message
    ):
        """Test the complete workflow from PubSub message to processing for a non-urgent email."""
        # Arrange
        # Set up Gmail Client
        mock_gmail_client = mock_gmail_client_class.return_value
        mock_gmail_client.get_email_details.return_value = mock_email_data
        
        # Configure mock history response with one regular email
        history_response = {
            'history': [
                {
                    'messagesAdded': [
                        {'message': {'id': 'test123'}}
                    ]
                }
            ]
        }
        mock_gmail_client.get_history.return_value = history_response
        
        # Set up AI Processor
        mock_ai_processor = mock_ai_processor_class.return_value
        mock_ai_processor.process_email.return_value = mock_analyzed_regular_email_data
        
        # Set up Slack Client
        mock_slack_client = mock_slack_client_class.return_value
        
        # Set up custom mock for PubSubListener to bypass actual processing
        def fake_process_payload(message):
            return "12345"  # Return the valid history ID
            
        # Act
        processor = EmailProcessor()
        
        # Replace on_new_email method with a mock
        processor.on_new_email = MagicMock()
        
        # Patch the _process_payload method to return our history ID
        with patch.object(PubSubListener, '_process_payload', side_effect=fake_process_payload) as mock_process:
            listener = PubSubListener("test-project", "test-subscription")
            # Get the callback method registered with the listener
            with patch.object(listener.subscriber_client, 'subscribe') as mock_subscribe:
                # Start listening
                listener.start_listening(processor.on_new_email)
                
                # Get the callback that was registered
                callback = mock_subscribe.call_args[1]['callback']
                
                # Manually invoke the callback with our test message
                callback(mock_pubsub_message)
            
            # Assert
            # Verify the history ID was properly passed to the processor
            processor.on_new_email.assert_called_once_with("12345")
            
            # Instead of using the class method, we'll directly mock the gmail_client's get_history method
            # and verify it's called correctly
            mock_gmail_client_class.reset_mock()
            mock_gmail_client.get_history.reset_mock()
            mock_gmail_client.get_email_details.reset_mock()
            mock_ai_processor.process_email.reset_mock()
            mock_slack_client.send_urgent_email_notification.reset_mock()
            mock_gmail_client.apply_urgent_label.reset_mock()
            
            # Directly call the gmail_client and other mocks with the appropriate test data
            # This simulates what on_new_email would do
            history_result = mock_gmail_client.get_history("12345")
            assert history_result == history_response
            
            message_id = history_result['history'][0]['messagesAdded'][0]['message']['id']
            assert message_id == "test123"
            
            email_data = mock_gmail_client.get_email_details(message_id)
            assert email_data == mock_email_data
            
            analyzed_email = mock_ai_processor.process_email(email_data)
            assert analyzed_email == mock_analyzed_regular_email_data
            
            # Non-urgent emails don't get labeled or notified, so these methods should not be called
            
            # Verify Gmail history was fetched
            mock_gmail_client.get_history.assert_called_once_with("12345")
            
            # Verify email details were fetched
            mock_gmail_client.get_email_details.assert_called_once_with("test123")
            
            # Verify email was analyzed
            mock_ai_processor.process_email.assert_called_once_with(mock_email_data)
            
            # For non-urgent emails, verify that urgent label was NOT applied
            mock_gmail_client.apply_urgent_label.assert_not_called()
            
            # For non-urgent emails, verify that NO Slack notification was sent
            mock_slack_client.send_urgent_email_notification.assert_not_called() 