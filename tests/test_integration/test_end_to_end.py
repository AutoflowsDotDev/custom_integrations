"""End-to-end tests for the full application workflow."""
import pytest
from unittest.mock import patch, MagicMock, call

from src.main import EmailProcessor
from src.gmail_service.pubsub_listener import PubSubListener


class TestEndToEndWorkflow:
    """Tests for the complete end-to-end workflow."""
    
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
        mock_urgent_email_data,
        mock_analyzed_urgent_email_data,
        mock_pubsub_message
    ):
        """Test the complete workflow from PubSub message to Slack notification for an urgent email."""
        # Arrange
        # Set up Gmail Client
        mock_gmail_client = mock_gmail_client_class.return_value
        mock_gmail_client.get_email_details.return_value = mock_urgent_email_data
        
        # Configure mock history response with one urgent email
        history_response = {
            'history': [
                {
                    'messagesAdded': [
                        {'message': {'id': 'urgent123'}}
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
        mock_slack_client.send_urgent_email_notification.return_value = True
        
        # Ensure the mock_pubsub_message returns valid data
        mock_pubsub_message.data.decode.return_value = '{"emailAddress": "user@example.com", "historyId": "12345"}'
        
        # Set up PubSub Listener with callback capture
        def setup_pubsub_with_callback(processor):
            listener = PubSubListener("test-project", "test-subscription")
            
            with patch.object(listener, '_process_payload', return_value="12345"):
                listener.start_listening(processor.on_new_email)
                
                # Extract the callback that was passed to subscribe
                subscriber_instance = mock_subscriber_client.return_value
                callback = subscriber_instance.subscribe.call_args[1]['callback']
                
                # Manually trigger the callback with our test message
                callback(mock_pubsub_message)
                
                return listener
        
        # Act
        processor = EmailProcessor()
        with patch.object(processor, 'process_email', wraps=processor.process_email) as mock_process:
            # Start the workflow
            listener = setup_pubsub_with_callback(processor)
            
            # Assert
            # Verify PubSub message was processed
            mock_pubsub_message.ack.assert_called_once()
            
            # Verify Gmail history was fetched
            mock_gmail_client.get_history.assert_called_once()
            
            # Verify email was processed
            mock_process.assert_called_once_with('urgent123')
            
            # Verify email details were fetched
            mock_gmail_client.get_email_details.assert_called_once_with('urgent123')
            
            # Verify AI processing
            mock_ai_processor.process_email.assert_called_once_with(mock_urgent_email_data)
            
            # Verify urgent label was applied
            mock_gmail_client.apply_urgent_label.assert_called_once_with('urgent123')
            
            # Verify Slack notification was sent
            mock_slack_client.send_urgent_email_notification.assert_called_once_with(mock_analyzed_urgent_email_data)
    
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
        
        # Set up PubSub Listener with callback capture
        def setup_pubsub_with_callback(processor):
            listener = PubSubListener("test-project", "test-subscription")
            listener.start_listening(processor.on_new_email)
            
            # Extract the callback that was passed to subscribe
            subscriber_instance = mock_subscriber_client.return_value
            callback = subscriber_instance.subscribe.call_args[1]['callback']
            
            # Manually trigger the callback with our test message
            callback(mock_pubsub_message)
            
            return listener
        
        # Act
        processor = EmailProcessor()
        with patch.object(processor, 'process_email', wraps=processor.process_email) as mock_process:
            # Start the workflow
            listener = setup_pubsub_with_callback(processor)
            
            # Assert
            # Verify PubSub message was processed
            mock_pubsub_message.ack.assert_called_once()
            
            # Verify Gmail history was fetched
            mock_gmail_client.get_history.assert_called_once()
            
            # Verify email was processed
            mock_process.assert_called_once_with('test123')
            
            # Verify email details were fetched
            mock_gmail_client.get_email_details.assert_called_once_with('test123')
            
            # Verify AI processing
            mock_ai_processor.process_email.assert_called_once_with(mock_email_data)
            
            # Verify no urgent label was applied
            mock_gmail_client.apply_urgent_label.assert_not_called()
            
            # Verify no Slack notification was sent
            mock_slack_client.send_urgent_email_notification.assert_not_called() 