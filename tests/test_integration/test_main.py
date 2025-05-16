"""Integration tests for the main application workflow."""
import pytest
from unittest.mock import patch, MagicMock, call

from src.main import process_new_email, EmailProcessor
from src.core.types import EmailData, AnalyzedEmailData


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