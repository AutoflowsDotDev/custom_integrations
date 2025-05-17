"""Integration tests for the main application workflow."""
import pytest
from unittest.mock import patch, MagicMock, call

from src.main import process_new_email, EmailProcessor, EmailTriageApp
from src.core.types import EmailData, AnalyzedEmailData
from src.utils.exceptions import (
    GmailServiceError, AIServiceError, SlackServiceError, 
    EmailTriageError, GmailAPIError, MessageProcessingError,
    PubSubError
)


class TestMainWorkflow:
    """Tests for the main application workflow."""
    
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    def test_process_new_email_urgent(self, mock_slack_client_class, mock_ai_processor_class, mock_gmail_client_class, mock_urgent_email_data, mock_analyzed_urgent_email_data):
        """Test processing of a new urgent email."""
        # Arrange
        mock_gmail_client = mock_gmail_client_class.return_value
        mock_ai_processor = mock_ai_processor_class.return_value
        mock_slack_client = mock_slack_client_class.return_value
        
        # Configure mocks
        mock_gmail_client.get_email_details.return_value = mock_urgent_email_data
        mock_ai_processor.process_email.return_value = mock_analyzed_urgent_email_data
        mock_gmail_client.apply_urgent_label.return_value = True
        mock_slack_client.send_urgent_email_notification.return_value = True
        
        # Act
        result = process_new_email("urgent123")
        
        # Assert
        assert result is True
        mock_gmail_client.get_email_details.assert_called_once_with("urgent123")
        mock_ai_processor.process_email.assert_called_once_with(mock_urgent_email_data)
        mock_gmail_client.apply_urgent_label.assert_called_once_with("urgent123")
        mock_slack_client.send_urgent_email_notification.assert_called_once_with(mock_analyzed_urgent_email_data)
    
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    def test_process_new_email_non_urgent(self, mock_slack_client_class, mock_ai_processor_class, mock_gmail_client_class, mock_email_data, mock_analyzed_regular_email_data):
        """Test processing of a new non-urgent email."""
        # Arrange
        mock_gmail_client = mock_gmail_client_class.return_value
        mock_ai_processor = mock_ai_processor_class.return_value
        mock_slack_client = mock_slack_client_class.return_value
        
        # Configure mocks
        mock_gmail_client.get_email_details.return_value = mock_email_data
        mock_ai_processor.process_email.return_value = mock_analyzed_regular_email_data
        
        # Act
        result = process_new_email("test123")
        
        # Assert
        assert result is True
        mock_gmail_client.get_email_details.assert_called_once_with("test123")
        mock_ai_processor.process_email.assert_called_once_with(mock_email_data)
        mock_gmail_client.apply_urgent_label.assert_not_called()
        mock_slack_client.send_urgent_email_notification.assert_not_called()
    
    @patch('src.main.GmailClient')
    def test_process_new_email_not_found(self, mock_gmail_client_class):
        """Test processing when email is not found."""
        # Arrange
        mock_gmail_client = mock_gmail_client_class.return_value
        mock_gmail_client.get_email_details.return_value = None
        
        # Act
        result = process_new_email("missing123")
        
        # Assert
        assert result is False
        mock_gmail_client.get_email_details.assert_called_once_with("missing123")
    
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    def test_email_processor_on_new_email(self, mock_slack_client_class, mock_ai_processor_class, mock_gmail_client_class):
        """Test EmailProcessor's on_new_email callback."""
        # Arrange
        mock_gmail_client = mock_gmail_client_class.return_value
        
        # Configure mock history response
        history_response = {
            'history': [
                {
                    'messagesAdded': [
                        {'message': {'id': 'email1'}},
                        {'message': {'id': 'email2'}}
                    ]
                }
            ]
        }
        mock_gmail_client.get_history.return_value = history_response
        
        # Create processor with mocked process_email function
        processor = EmailProcessor()
        processor.process_email = MagicMock(return_value=True)
        
        # Act
        processor.on_new_email("12345")
        
        # Assert
        assert processor.process_email.call_count == 2
        processor.process_email.assert_has_calls([
            call('email1'),
            call('email2')
        ])
    
    @patch('src.main.GmailClient')
    def test_email_processor_on_new_email_no_messages(self, mock_gmail_client_class):
        """Test EmailProcessor's on_new_email callback with no new messages."""
        # Arrange
        mock_gmail_client = mock_gmail_client_class.return_value
        
        # Configure mock history with no messages
        mock_gmail_client.get_history.return_value = {'history': []}
        
        # Create processor with mocked process_email function
        processor = EmailProcessor()
        processor.process_email = MagicMock()
        
        # Act
        processor.on_new_email("12345")
        
        # Assert
        processor.process_email.assert_not_called()
    
    @patch('src.main.GmailClient')
    def test_email_processor_on_new_email_history_error(self, mock_gmail_client_class):
        """Test EmailProcessor's on_new_email callback with history retrieval error."""
        # Arrange
        mock_gmail_client = mock_gmail_client_class.return_value
        mock_gmail_client.get_history.return_value = None
        
        # Create processor with mocked process_email function
        processor = EmailProcessor()
        processor.process_email = MagicMock()
        
        # Act
        processor.on_new_email("12345")
        
        # Assert
        processor.process_email.assert_not_called()
        
    @patch('src.main.GmailClient')
    def test_email_processor_uninitialized_client(self, mock_gmail_client_class):
        """Test EmailProcessor's on_new_email callback with uninitialized client."""
        # Set gmail_client to None
        processor = EmailProcessor()
        processor.gmail_client = None
        processor.process_email = MagicMock()
        
        # Act
        processor.on_new_email("12345")
        
        # Assert
        processor.process_email.assert_not_called()
        
    @patch('src.main.GmailClient')
    def test_email_processor_with_gmail_api_error(self, mock_gmail_client_class):
        """Test EmailProcessor's on_new_email callback when a Gmail API error occurs."""
        # Arrange
        mock_gmail_client = mock_gmail_client_class.return_value
        mock_gmail_client.get_history.side_effect = GmailAPIError("API error")
        
        # Create processor
        processor = EmailProcessor()
        processor.process_email = MagicMock()
        
        # Act
        processor.on_new_email("12345")
        
        # Assert
        processor.process_email.assert_not_called()
        
    @patch('src.main.GmailClient')
    def test_email_processor_with_gmail_service_error(self, mock_gmail_client_class):
        """Test EmailProcessor's on_new_email callback when a Gmail service error occurs."""
        # Arrange
        mock_gmail_client = mock_gmail_client_class.return_value
        mock_gmail_client.get_history.side_effect = GmailServiceError("Service error")
        
        # Create processor
        processor = EmailProcessor()
        processor.process_email = MagicMock()
        
        # Act
        processor.on_new_email("12345")
        
        # Assert
        processor.process_email.assert_not_called()
        
    @patch('src.main.process_new_email')
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    def test_process_new_email_with_gmail_service_error(self, mock_slack, mock_ai, mock_gmail, mock_process_email):
        """Test process_new_email function when Gmail service error occurs."""
        # Arrange
        mock_gmail.return_value.get_email_details.side_effect = GmailServiceError("Gmail error")
        
        # Act
        result = process_new_email("email123")
        
        # Assert
        assert result is False
        
    @patch('src.main.process_new_email')
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    def test_process_new_email_with_ai_service_error(self, mock_slack, mock_ai, mock_gmail, mock_process_email, mock_email_data):
        """Test process_new_email function when AI service error occurs."""
        # Arrange
        mock_gmail.return_value.get_email_details.return_value = mock_email_data
        mock_ai.return_value.process_email.side_effect = AIServiceError("AI error")
        
        # Act
        result = process_new_email("email123")
        
        # Assert
        assert result is False
        
    @patch('src.main.process_new_email')
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    def test_process_new_email_with_slack_service_error(self, mock_slack, mock_ai, mock_gmail, mock_process_email, mock_email_data, mock_analyzed_urgent_email_data):
        """Test process_new_email function when Slack service error occurs."""
        # Arrange
        mock_gmail.return_value.get_email_details.return_value = mock_email_data
        mock_ai.return_value.process_email.return_value = mock_analyzed_urgent_email_data
        mock_gmail.return_value.apply_urgent_label.return_value = True
        mock_slack.return_value.send_urgent_email_notification.side_effect = SlackServiceError("Slack error")
        
        # Act
        result = process_new_email("email123")
        
        # Assert
        assert result is False
        
    @patch('src.main.process_new_email')
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    def test_process_new_email_with_email_triage_error(self, mock_slack, mock_ai, mock_gmail, mock_process_email, mock_email_data):
        """Test process_new_email function when email triage error occurs."""
        # Arrange
        mock_gmail.return_value.get_email_details.return_value = mock_email_data
        mock_ai.return_value.process_email.side_effect = EmailTriageError("Triage error")
        
        # Act
        result = process_new_email("email123")
        
        # Assert
        assert result is False
        
    @patch('src.main.process_new_email')
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    def test_process_new_email_with_generic_exception(self, mock_slack, mock_ai, mock_gmail, mock_process_email, mock_email_data):
        """Test process_new_email function when unexpected exception occurs."""
        # Arrange
        mock_gmail.return_value.get_email_details.return_value = mock_email_data
        mock_ai.return_value.process_email.side_effect = Exception("Unexpected error")
        
        # Act
        result = process_new_email("email123")
        
        # Assert
        assert result is False


class TestEmailTriageApp:
    """Tests for the EmailTriageApp class."""
    
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    @patch('src.main.signal.signal')
    def test_init_successful(self, mock_signal, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test successful initialization of EmailTriageApp."""
        # Act
        app = EmailTriageApp()
        
        # Assert
        assert app._running is True
        assert app.gmail_client is mock_gmail.return_value
        assert app.ai_processor is mock_ai.return_value
        assert app.slack_client is mock_slack.return_value
        assert app.pubsub_listener is mock_pubsub.return_value
        mock_signal.assert_called()
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    @patch('src.main.sys.exit')
    def test_init_gmail_service_error(self, mock_exit, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test EmailTriageApp init when Gmail service error occurs."""
        # Arrange
        mock_gmail.side_effect = GmailServiceError("Gmail service error")
        
        # Act
        EmailTriageApp()
        
        # Assert
        mock_exit.assert_called_once_with(1)
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    @patch('src.main.sys.exit')
    def test_init_ai_service_error(self, mock_exit, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test EmailTriageApp init when AI service error occurs."""
        # Arrange
        mock_ai.side_effect = AIServiceError("AI service error")
        
        # Act
        EmailTriageApp()
        
        # Assert
        mock_exit.assert_called_once_with(1)
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    @patch('src.main.sys.exit')
    def test_init_slack_service_error(self, mock_exit, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test EmailTriageApp init when Slack service error occurs."""
        # Arrange
        mock_slack.side_effect = SlackServiceError("Slack service error")
        
        # Act
        EmailTriageApp()
        
        # Assert
        mock_exit.assert_called_once_with(1)
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    @patch('src.main.sys.exit')
    def test_init_pubsub_error(self, mock_exit, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test EmailTriageApp init when PubSub error occurs."""
        # Arrange
        mock_pubsub.side_effect = PubSubError("PubSub error")
        
        # Act
        EmailTriageApp()
        
        # Assert
        mock_exit.assert_called_once_with(1)
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    def test_handle_new_email_notification_success(self, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test _handle_new_email_notification with successful processing."""
        # Arrange
        app = EmailTriageApp()
        app._running = True
        
        # Set up mock data
        history_response = {
            'history': [
                {
                    'messagesAdded': [
                        {'message': {'id': 'msg1'}}
                    ]
                }
            ]
        }
        mock_email_data = {'id': 'msg1', 'subject': 'Test'}
        
        # Configure mocks
        mock_gmail.return_value.service.users().history().list().execute.return_value = history_response
        mock_gmail.return_value.get_email_details.return_value = mock_email_data
        mock_ai.return_value.process_email.return_value = {'is_urgent': False, 'summary': 'Test summary'}
        
        # Act
        app._handle_new_email_notification('12345')
        
        # Assert
        mock_gmail.return_value.service.users().history().list().execute.assert_called_once()
        mock_gmail.return_value.get_email_details.assert_called_once_with('msg1')
        mock_ai.return_value.process_email.assert_called_once_with(mock_email_data)
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    def test_handle_new_email_notification_urgent(self, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test _handle_new_email_notification with urgent email."""
        # Arrange
        app = EmailTriageApp()
        app._running = True
        
        # Set up mock data
        history_response = {
            'history': [
                {
                    'messagesAdded': [
                        {'message': {'id': 'msg1'}}
                    ]
                }
            ]
        }
        mock_email_data = {'id': 'msg1', 'subject': 'Urgent Test'}
        
        # Configure mocks
        mock_gmail.return_value.service.users().history().list().execute.return_value = history_response
        mock_gmail.return_value.get_email_details.return_value = mock_email_data
        mock_ai.return_value.process_email.return_value = {'is_urgent': True, 'summary': 'Urgent test summary'}
        mock_gmail.return_value.apply_urgent_label.return_value = True
        mock_slack.return_value.send_urgent_email_notification.return_value = True
        
        # Act
        app._handle_new_email_notification('12345')
        
        # Assert
        mock_gmail.return_value.service.users().history().list().execute.assert_called_once()
        mock_gmail.return_value.get_email_details.assert_called_once_with('msg1')
        mock_ai.return_value.process_email.assert_called_once()
        mock_gmail.return_value.apply_urgent_label.assert_called_once_with('msg1')
        mock_slack.return_value.send_urgent_email_notification.assert_called_once()
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    def test_handle_new_email_notification_shutting_down(self, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test _handle_new_email_notification when app is shutting down."""
        # Arrange
        app = EmailTriageApp()
        app._running = False
        
        # Act
        app._handle_new_email_notification('12345')
        
        # Assert
        mock_gmail.return_value.service.users().history().list.assert_not_called()
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    def test_handle_new_email_notification_no_client(self, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test _handle_new_email_notification when gmail client is missing."""
        # Arrange
        app = EmailTriageApp()
        app._running = True
        app.gmail_client = None
        
        # Act
        app._handle_new_email_notification('12345')
        
        # Assert - should handle gracefully without errors
        pass
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    def test_run_successful(self, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test run method with successful setup."""
        # Arrange
        app = EmailTriageApp()
        mock_gmail.return_value.setup_push_notifications.return_value = True
        
        # Act
        app.run()
        
        # Assert
        mock_gmail.return_value.setup_push_notifications.assert_called_once()
        mock_pubsub.return_value.start_listening.assert_called_once_with(app._handle_new_email_notification)
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    def test_run_setup_failed(self, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test run method when push notification setup fails."""
        # Arrange
        app = EmailTriageApp()
        mock_gmail.return_value.setup_push_notifications.return_value = False
        
        # Act
        app.run()
        
        # Assert
        mock_gmail.return_value.setup_push_notifications.assert_called_once()
        mock_pubsub.return_value.start_listening.assert_called_once_with(app._handle_new_email_notification)
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    def test_run_no_gmail_client(self, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test run method when Gmail client is not initialized."""
        # Arrange
        app = EmailTriageApp()
        app.gmail_client = None
        
        # Act
        app.run()
        
        # Assert
        mock_pubsub.return_value.start_listening.assert_not_called()
        
    @patch('src.main.GmailClient')
    @patch('src.main.AIProcessor')
    @patch('src.main.SlackServiceClient')
    @patch('src.main.PubSubListener')
    def test_shutdown(self, mock_pubsub, mock_slack, mock_ai, mock_gmail):
        """Test shutdown method."""
        # Arrange
        app = EmailTriageApp()
        app._running = True
        mock_gmail.return_value.stop_push_notifications.return_value = True
        
        # Act
        app.shutdown(None, None)  # Normally called by signal handler
        
        # Assert
        assert app._running is False
        mock_gmail.return_value.stop_push_notifications.assert_called_once() 