"""
End-to-end tests for the email processing flow.
"""
import pytest
from unittest.mock import patch, MagicMock, call
import logging
import os

from tests.test_integration.fixtures import (
    mock_environment, mock_gmail_service, mock_gmail_client, 
    mock_ai_processor, mock_slack_client, mock_pubsub_listener,
    mock_app_components, mock_email_processor, mock_email_triage_app
)

from src.main import EmailProcessor, EmailTriageApp, process_new_email
from tests.mocks.data import (
    STANDARD_EMAIL, URGENT_EMAIL, NULL_FIELDS_EMAIL,
    EMPTY_FIELDS_EMAIL, MALICIOUS_EMAIL, STANDARD_RECEIVED_MESSAGE
)

@pytest.mark.usefixtures("mock_environment")
class TestEmailProcessingFlow:
    """Tests for the end-to-end email processing flow."""

    def test_process_standard_email(self, mock_email_processor):
        """Test processing a standard (non-urgent) email."""
        # Process a standard email
        result = mock_email_processor.process_email("standard_email_id")
        
        # Verify the result is successful
        assert result is True

    def test_process_urgent_email(self, mock_email_processor, mock_app_components):
        """Test processing an urgent email triggers the correct actions."""
        # Get components to verify calls
        gmail_client = mock_app_components['gmail_client']
        slack_client = mock_app_components['slack_client']
        
        # Process an urgent email
        result = mock_email_processor.process_email("urgent_email_id")
        
        # Verify the result is successful
        assert result is True
        
        # Verify that the urgent label was applied
        gmail_client.apply_urgent_label.assert_called_once_with("urgent_email_id")
        
        # Verify that a Slack notification was sent
        assert slack_client.send_urgent_email_notification.call_count == 1
        # Get the call argument (should be an AnalyzedEmailData dict)
        call_args = slack_client.send_urgent_email_notification.call_args[0][0]
        assert call_args['is_urgent'] is True
        assert call_args['id'] == "urgent_email_id"

    def test_process_email_missing_fields(self, mock_email_processor):
        """Test processing an email with missing fields."""
        # Process an email with missing fields
        result = mock_email_processor.process_email("empty_fields_id")
        
        # Verify the result is successful (should handle missing fields gracefully)
        assert result is True

    def test_process_email_null_fields(self, mock_email_processor):
        """Test processing an email with None values for optional fields."""
        # Process an email with null fields
        result = mock_email_processor.process_email("null_fields_id")
        
        # Verify the result is successful (should handle null fields gracefully)
        assert result is True

    def test_process_malicious_email(self, mock_email_processor):
        """Test processing an email with potentially malicious content."""
        # Process an email with malicious content
        result = mock_email_processor.process_email("malicious_id")
        
        # Verify the result is successful (should sanitize/handle malicious content)
        assert result is True

    def test_process_nonexistent_email(self, mock_email_processor):
        """Test processing a non-existent email ID."""
        # Mock a failed get_email_details call
        mock_email_processor.gmail_client.get_email_details = MagicMock(return_value=None)
        
        # Process a non-existent email
        result = mock_email_processor.process_email("nonexistent_id")
        
        # Verify the result is False (indicating failure)
        assert result is False

    def test_process_email_with_exception(self, mock_email_processor, mock_app_components):
        """Test handling exceptions during email processing."""
        # Configure AI processor to raise an exception
        mock_app_components['ai_processor'].process_email = MagicMock(
            side_effect=Exception("Test exception")
        )
        
        # Process an email that will trigger the exception
        result = mock_email_processor.process_email("standard_email_id")
        
        # Verify the result is False (indicating failure)
        assert result is False

    def test_on_new_email_with_history(self, mock_email_processor, mock_app_components):
        """Test handling a new email notification with history data."""
        # Configure the get_history mock
        history_response = {
            'history': [
                {
                    'messagesAdded': [
                        {'message': {'id': 'msg_in_history_1'}},
                        {'message': {'id': 'msg_in_history_2'}}
                    ]
                }
            ]
        }
        mock_app_components['gmail_client'].get_history = MagicMock(return_value=history_response)
        
        # Process a new email notification via history ID
        mock_email_processor.on_new_email("12345")
        
        # Verify that process_email was called twice (once for each message)
        assert mock_email_processor.process_email.call_count == 2
        # Verify the specific message IDs that were processed
        mock_email_processor.process_email.assert_has_calls([
            call('msg_in_history_1'),
            call('msg_in_history_2')
        ])

    def test_on_new_email_empty_history(self, mock_email_processor, mock_app_components):
        """Test handling a notification with empty history."""
        # Configure the get_history mock to return empty history
        mock_app_components['gmail_client'].get_history = MagicMock(return_value={'history': []})
        
        # Process a notification with empty history
        mock_email_processor.on_new_email("12400")
        
        # Verify that process_email was not called
        mock_email_processor.process_email.assert_not_called()

    def test_on_new_email_no_history(self, mock_email_processor, mock_app_components):
        """Test handling a notification with no history response."""
        # Configure the get_history mock to return None
        mock_app_components['gmail_client'].get_history = MagicMock(return_value=None)
        
        # Process a notification with no history
        mock_email_processor.on_new_email("invalid_history")
        
        # Verify that process_email was not called
        mock_email_processor.process_email.assert_not_called()

    def test_on_new_email_with_exception(self, mock_email_processor, mock_app_components):
        """Test handling exceptions during notification processing."""
        # Configure the get_history mock to raise an exception
        mock_app_components['gmail_client'].get_history = MagicMock(
            side_effect=Exception("Test exception")
        )
        
        # Process a notification that will trigger the exception
        # This should not raise an exception to the test
        mock_email_processor.on_new_email("exception_history")
        
        # Verify that process_email was not called
        mock_email_processor.process_email.assert_not_called()

@pytest.mark.usefixtures("mock_environment")
class TestEmailTriageAppFlow:
    """Tests for the EmailTriageApp class covering the complete flow."""

    def test_app_initialization(self, mock_email_triage_app, mock_app_components):
        """Test that the app initializes correctly with all components."""
        # Verify that all components were initialized
        assert mock_email_triage_app.gmail_client is mock_app_components['gmail_client']
        assert mock_email_triage_app.ai_processor is mock_app_components['ai_processor']
        assert mock_email_triage_app.slack_client is mock_app_components['slack_client']
        assert mock_email_triage_app.pubsub_listener is mock_app_components['pubsub_listener']
        assert mock_email_triage_app._running is True

    def test_handle_new_email_notification(self, mock_email_triage_app, mock_app_components):
        """Test the main notification handler with a standard email."""
        # Configure the history_list mock
        mock_history_response = {
            'history': [
                {
                    'messagesAdded': [
                        {'message': {'id': 'msg_in_history_1'}}
                    ]
                }
            ]
        }
        history_list_mock = MagicMock()
        history_list_mock.execute.return_value = mock_history_response
        
        mock_history = MagicMock()
        mock_history.list.return_value = history_list_mock
        
        mock_app_components['gmail_client'].service.users().history.return_value = mock_history
        
        # Process a new email notification
        mock_email_triage_app._handle_new_email_notification("12345")
        
        # Verify that the history was requested
        mock_history.list.assert_called_once()
        
        # Verify that the email was processed (via get_email_details)
        mock_app_components['gmail_client'].get_email_details.assert_called_with('msg_in_history_1')
        
        # Verify that the AI processor was called
        mock_app_components['ai_processor'].process_email.assert_called_once()

    def test_handle_urgent_email_notification(self, mock_email_triage_app, mock_app_components):
        """Test the notification handler with an urgent email."""
        # Configure the history_list mock
        mock_history_response = {
            'history': [
                {
                    'messagesAdded': [
                        {'message': {'id': 'urgent_email_id'}}
                    ]
                }
            ]
        }
        history_list_mock = MagicMock()
        history_list_mock.execute.return_value = mock_history_response
        
        mock_history = MagicMock()
        mock_history.list.return_value = history_list_mock
        
        mock_app_components['gmail_client'].service.users().history.return_value = mock_history
        
        # Configure AI processor to classify as urgent
        def mock_process_email(email_data):
            return {
                **email_data,
                'is_urgent': True,
                'summary': 'Urgent test email requiring immediate attention.'
            }
        mock_app_components['ai_processor'].process_email.side_effect = mock_process_email
        
        # Process a new urgent email notification
        mock_email_triage_app._handle_new_email_notification("12345")
        
        # Verify that the urgent label was applied
        mock_app_components['gmail_client'].apply_urgent_label.assert_called_once_with('urgent_email_id')
        
        # Verify that a Slack notification was sent
        mock_app_components['slack_client'].send_urgent_email_notification.assert_called_once()

    def test_app_run_and_stop(self, mock_email_triage_app, mock_app_components):
        """Test the app's run and stop methods."""
        # Mock the pubsub listener
        mock_app_components['pubsub_listener'].start_listening = MagicMock()
        
        # Run the app in a way that doesn't block
        with patch('src.main.EmailTriageApp.stop') as mock_stop:
            # Configure the start_listening to call stop after setup
            def mock_start_listening(callback):
                # Verify callback is correct
                assert callback == mock_email_triage_app._handle_new_email_notification
                # Call stop to end the run method
                mock_email_triage_app.stop()
            
            mock_app_components['pubsub_listener'].start_listening.side_effect = mock_start_listening
            
            # Run the app
            mock_email_triage_app.run()
        
        # Verify setup_push_notifications was called
        mock_app_components['gmail_client'].setup_push_notifications.assert_called_once()
        
        # Verify start_listening was called
        mock_app_components['pubsub_listener'].start_listening.assert_called_once()
        
        # Now test the stop method directly
        mock_email_triage_app._running = True
        mock_email_triage_app.stop()
        
        # Verify the app is no longer running
        assert mock_email_triage_app._running is False
        # Verify stop_push_notifications was called
        mock_app_components['gmail_client'].stop_push_notifications.assert_called_once()

    def test_shutdown_handler(self, mock_email_triage_app):
        """Test the signal handler for shutdown."""
        # Mock the stop method
        mock_email_triage_app.stop = MagicMock()
        
        # Call the shutdown handler
        mock_email_triage_app.shutdown(15, None)  # 15 = SIGTERM
        
        # Verify stop was called
        mock_email_triage_app.stop.assert_called_once()

    def test_handle_notification_during_shutdown(self, mock_email_triage_app, mock_app_components):
        """Test handling notifications while shutting down."""
        # Set running to False to simulate shutdown
        mock_email_triage_app._running = False
        
        # Process a notification during shutdown
        mock_email_triage_app._handle_new_email_notification("12345")
        
        # Verify that no processing occurred
        mock_app_components['gmail_client'].service.users().history.list.assert_not_called()

    def test_handle_notification_without_gmail_client(self, mock_email_triage_app):
        """Test handling notifications without a valid Gmail client."""
        # Set Gmail client service to None
        mock_email_triage_app.gmail_client.service = None
        
        # Process a notification without a valid Gmail client
        mock_email_triage_app._handle_new_email_notification("12345")
        
        # No error should be raised

def test_direct_process_new_email_function(mock_app_components):
    """Test the standalone process_new_email function."""
    # Patch the imports in the process_new_email function's module
    with patch('src.main.GmailClient', return_value=mock_app_components['gmail_client']), \
         patch('src.main.AIProcessor', return_value=mock_app_components['ai_processor']), \
         patch('src.main.SlackServiceClient', return_value=mock_app_components['slack_client']), \
         patch('src.main.get_logger') as mock_get_logger:
        
        # Configure mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Call the function directly
        result = process_new_email("urgent_email_id")
        
        # Verify the function behaved correctly
        assert result is True
        mock_app_components['gmail_client'].get_email_details.assert_called_with("urgent_email_id")
        mock_app_components['ai_processor'].process_email.assert_called_once()
        mock_app_components['gmail_client'].apply_urgent_label.assert_called_with("urgent_email_id")
        mock_app_components['slack_client'].send_urgent_email_notification.assert_called_once() 