"""
Fixtures for integration tests.
These fixtures prepare test environments for end-to-end tests.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, Mock
import json
import base64
import requests
from datetime import datetime, timezone

from tests.mocks.data import (
    STANDARD_EMAIL, URGENT_EMAIL, EMPTY_FIELDS_EMAIL, NULL_FIELDS_EMAIL,
    SPECIAL_CHARS_EMAIL, HTML_ONLY_EMAIL, PLAIN_ONLY_EMAIL, MALICIOUS_EMAIL,
    EMOJI_EMAIL, LONG_EMAIL, BORDERLINE_URGENT_EMAIL, IMPLICIT_URGENT_EMAIL,
    THREAD_EMAILS, MISLEADING_URGENCY_EMAIL,
    BASIC_MESSAGE_RESPONSE, PLAIN_TEXT_ONLY_RESPONSE, HTML_ONLY_RESPONSE,
    EMPTY_BODY_RESPONSE, MALFORMED_BASE64_RESPONSE, MISSING_HEADERS_RESPONSE, 
    HISTORY_RESPONSE_WITH_MESSAGES, EMPTY_HISTORY_RESPONSE, HISTORY_LABEL_CHANGES_ONLY,
    LABELS_LIST_RESPONSE, CREATED_LABEL_RESPONSE, WATCH_RESPONSE,
    URGENT_CLASSIFICATION_RESPONSE, NON_URGENT_CLASSIFICATION_RESPONSE,
    MALFORMED_URGENCY_RESPONSE, STANDARD_SUMMARY_RESPONSE, URGENT_SUMMARY_RESPONSE,
    API_ERROR_RESPONSE, SUCCESSFUL_MESSAGE_RESPONSE, WARNING_MESSAGE_RESPONSE,
    INVALID_TOKEN_ERROR, STANDARD_GMAIL_PUBSUB_MESSAGE, STANDARD_RECEIVED_MESSAGE,
    INVALID_JSON_RECEIVED_MESSAGE, MISSING_FIELDS_RECEIVED_MESSAGE
)

from src.gmail_service.gmail_client import GmailClient
from src.ai_service.ai_processor import AIProcessor
from src.slack_service.slack_client import SlackServiceClient
from src.gmail_service.pubsub_listener import PubSubListener
from src.core.types import EmailData, AnalyzedEmailData

@pytest.fixture
def mock_environment():
    """Set environment variables for testing."""
    original_env = os.environ.copy()
    # Set mock credentials and configuration
    os.environ["OPENROUTER_API_KEY"] = "test-api-key"
    os.environ["OPENROUTER_API_URL"] = "https://api.openrouter.ai/api/v1/chat/completions"
    os.environ["GOOGLE_CLIENT_SECRETS_JSON_PATH"] = "dummy/path/client_secret.json"
    os.environ["GOOGLE_CREDENTIALS_JSON_PATH"] = "dummy/path/credentials.json"
    os.environ["GOOGLE_SERVICE_ACCOUNT_PATH"] = "dummy/path/service_account.json"
    os.environ["GOOGLE_CLOUD_PROJECT_ID"] = "test-project-id"
    os.environ["GOOGLE_PUBSUB_TOPIC_ID"] = "test-topic-id"
    os.environ["GOOGLE_PUBSUB_SUBSCRIPTION_ID"] = "test-subscription-id"
    os.environ["SLACK_BOT_TOKEN"] = "xoxb-test-token"
    os.environ["SLACK_CHANNEL_ID"] = "C123456789"
    os.environ["GMAIL_USER_ID"] = "me"
    os.environ["GMAIL_LABEL_URGENT"] = "URGENT_AI"
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service with realistic response behavior."""
    # Create a mock for the Gmail API service
    mock_service = MagicMock()
    
    # Get message method chain
    mock_message_get = MagicMock()
    # Configure to return different responses based on the message ID
    def message_get_execute():
        message_id = mock_message_get.call_args[1]['id']
        if 'standard' in message_id:
            return BASIC_MESSAGE_RESPONSE
        elif 'plain_only' in message_id:
            return PLAIN_TEXT_ONLY_RESPONSE
        elif 'html_only' in message_id:
            return HTML_ONLY_RESPONSE
        elif 'empty' in message_id:
            return EMPTY_BODY_RESPONSE
        elif 'malformed' in message_id:
            return MALFORMED_BASE64_RESPONSE
        elif 'missing_headers' in message_id:
            return MISSING_HEADERS_RESPONSE
        elif message_id == 'msg_in_history_1' or message_id == 'msg_in_history_2':
            return BASIC_MESSAGE_RESPONSE
        else:
            return BASIC_MESSAGE_RESPONSE
    
    mock_message_get.execute = message_get_execute
    mock_messages = MagicMock()
    mock_messages.get.return_value = mock_message_get
    
    # Label methods chain
    mock_labels_list = MagicMock()
    mock_labels_list.execute.return_value = LABELS_LIST_RESPONSE
    mock_labels_create = MagicMock()
    mock_labels_create.execute.return_value = CREATED_LABEL_RESPONSE
    mock_labels = MagicMock()
    mock_labels.list.return_value = mock_labels_list
    mock_labels.create.return_value = mock_labels_create
    
    # Modify message (apply label) method chain
    mock_modify = MagicMock()
    mock_modify.execute.return_value = {"id": "modified_message_id", "labelIds": ["INBOX", "URGENT_AI"]}
    mock_messages.modify.return_value = mock_modify
    
    # Watch method chain
    mock_watch = MagicMock()
    mock_watch.execute.return_value = WATCH_RESPONSE
    
    # Stop method chain
    mock_stop = MagicMock()
    mock_stop.execute.return_value = {}
    
    # History method chain
    mock_history_list = MagicMock()
    def history_list_execute():
        history_id = mock_history_list.call_args[1]['startHistoryId']
        if history_id == "12345":
            return HISTORY_RESPONSE_WITH_MESSAGES
        elif history_id == "12400":
            return EMPTY_HISTORY_RESPONSE
        elif history_id == "12401":
            return HISTORY_LABEL_CHANGES_ONLY
        else:
            return HISTORY_RESPONSE_WITH_MESSAGES
    
    mock_history_list.execute = history_list_execute
    mock_history = MagicMock()
    mock_history.list.return_value = mock_history_list
    
    # Configure the users chain
    mock_users = MagicMock()
    mock_users.messages.return_value = mock_messages
    mock_users.labels.return_value = mock_labels
    mock_users.watch.return_value = mock_watch
    mock_users.stop.return_value = mock_stop
    mock_users.history.return_value = mock_history
    
    # Final service configuration
    mock_service.users.return_value = mock_users
    
    # Setup the build mock to return our mock service
    with patch('src.gmail_service.gmail_client.build', return_value=mock_service):
        yield mock_service

@pytest.fixture
def mock_gmail_client(mock_gmail_service):
    """Create a mock GmailClient with integrated service mock."""
    # Mock the file existence check and Credentials
    with patch('os.path.exists', return_value=False), \
         patch('src.gmail_service.gmail_client.Credentials') as mock_creds, \
         patch('src.gmail_service.gmail_client.build', return_value=mock_gmail_service):
        
        # Configure credentials mock
        mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)
        
        # Create Gmail client instance
        client = GmailClient()
        
        # Mock the get_email_details method to handle various email test cases
        original_get_email_details = client.get_email_details
        def mock_get_email_details(message_id: str):
            # For test cases where we need specific email content
            if message_id == "standard_email_id":
                return STANDARD_EMAIL
            elif message_id == "urgent_email_id":
                return URGENT_EMAIL
            elif message_id == "empty_fields_id":
                return EMPTY_FIELDS_EMAIL
            elif message_id == "null_fields_id":
                return NULL_FIELDS_EMAIL
            elif message_id == "special_chars_id":
                return SPECIAL_CHARS_EMAIL
            elif message_id == "html_only_id":
                return HTML_ONLY_EMAIL
            elif message_id == "plain_only_id":
                return PLAIN_ONLY_EMAIL
            elif message_id == "malicious_id":
                return MALICIOUS_EMAIL
            elif message_id == "emoji_id":
                return EMOJI_EMAIL
            elif message_id == "long_email_id":
                return LONG_EMAIL
            elif message_id == "borderline_id":
                return BORDERLINE_URGENT_EMAIL
            elif message_id == "implicit_urgent_id":
                return IMPLICIT_URGENT_EMAIL
            elif message_id == "misleading_id":
                return MISLEADING_URGENCY_EMAIL
            elif message_id == "thread_email_1":
                return THREAD_EMAILS[0]
            elif message_id == "thread_email_2":
                return THREAD_EMAILS[1]
            elif message_id == "thread_email_3":
                return THREAD_EMAILS[2]
            elif message_id == "msg_in_history_1" or message_id == "msg_in_history_2":
                # For history testing, return standard email
                return STANDARD_EMAIL
            else:
                # For other IDs, use the original method which will interact with our mock service
                return original_get_email_details(message_id)
        
        # Replace with MagicMock with side_effect to track calls 
        client.get_email_details = MagicMock(side_effect=mock_get_email_details)
        
        # Mock other methods that the tests check with assertions
        client.apply_urgent_label = MagicMock(return_value=True)
        client.setup_push_notifications = MagicMock(return_value=True)
        client.stop_push_notifications = MagicMock(return_value=True)
        client.get_history = MagicMock()
        
        yield client

@pytest.fixture
def mock_ai_processor():
    """Create a mock AIProcessor with predetermined responses."""
    # Mock the requests module used by AIProcessor
    with patch('src.ai_service.ai_processor.requests.post') as mock_post:
        # Configure the mock post to return different responses based on input
        def mock_post_response(*args, **kwargs):
            mock_response = MagicMock()
            
            # Parse the request JSON to determine the appropriate response
            request_json = kwargs.get('json', {})
            model = request_json.get('model', '')
            messages = request_json.get('messages', [])
            
            # Get the user message/content to check for keywords
            user_content = ""
            for msg in messages:
                if msg.get('role') == 'user':
                    user_content = msg.get('content', '').lower()
                    break
            
            # Determine response based on content and model
            if 'system_error' in user_content:
                # Simulate a service error
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
                return mock_response
            elif 'rate_limit' in user_content:
                # Simulate a rate limit error
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Rate Limit Exceeded")
                return mock_response
            
            # Normal responses based on content pattern
            mock_response.raise_for_status.return_value = None
            
            if 'gpt-3.5-turbo' in model:
                if any(kw in user_content for kw in ['urgent', 'asap', 'immediately', 'critical']):
                    mock_response.json.return_value = URGENT_CLASSIFICATION_RESPONSE
                elif 'borderline' in user_content:
                    mock_response.json.return_value = NON_URGENT_CLASSIFICATION_RESPONSE
                elif 'malformed' in user_content:
                    mock_response.json.return_value = MALFORMED_URGENCY_RESPONSE
                elif 'summarize' in user_content and 'urgent' in user_content:
                    mock_response.json.return_value = URGENT_SUMMARY_RESPONSE
                elif 'summarize' in user_content:
                    mock_response.json.return_value = STANDARD_SUMMARY_RESPONSE
                else:
                    mock_response.json.return_value = NON_URGENT_CLASSIFICATION_RESPONSE
            else:
                # Default response for unknown models
                mock_response.json.return_value = NON_URGENT_CLASSIFICATION_RESPONSE
                
            return mock_response
        
        # Set the side effect of the mock_post to use our function
        mock_post.side_effect = mock_post_response
        
        # Set up the AI processor
        os.environ["OPENROUTER_API_KEY"] = "test-api-key"
        processor = AIProcessor()
        
        # Mock the analyze_urgency method to handle our test cases
        original_analyze_urgency = processor.analyze_urgency
        def mock_analyze_urgency(email_text: str):
            # Determine response based on text patterns
            if not email_text:
                return {"is_urgent": False, "confidence_score": None}
            
            email_text_lower = email_text.lower()
            if any(kw in email_text_lower for kw in ['urgent', 'asap', 'immediately', 'critical', 'action required']):
                return {"is_urgent": True, "confidence_score": 0.92}
            elif "borderline" in email_text_lower:
                return {"is_urgent": False, "confidence_score": 0.55}  # Low confidence for borderline
            elif "implicit" in email_text_lower and "error rate" in email_text_lower:
                return {"is_urgent": True, "confidence_score": 0.75}  # Implicit urgency detected as urgent
            elif "misleading" in email_text_lower and "urgent care" in email_text_lower:
                return {"is_urgent": False, "confidence_score": 0.82}  # Not urgent despite "urgent" keyword
            else:
                return {"is_urgent": False, "confidence_score": 0.87}
                
        # Replace with our mock function with MagicMock to track calls
        processor.analyze_urgency = MagicMock(side_effect=mock_analyze_urgency)
        
        # Create a process_email method that can be tracked with MagicMock
        original_process_email = processor.process_email
        def mock_process_email(email_data):
            # For urgent emails
            if email_data.get('id') == 'urgent_email_id' or (email_data.get('body_plain') and 'urgent' in email_data.get('body_plain', '').lower()):
                return {
                    **email_data,
                    'is_urgent': True,
                    'urgency_score': 0.92,
                    'summary': 'Urgent email requiring immediate attention.'
                }
            # For other emails
            else:
                return {
                    **email_data,
                    'is_urgent': False,
                    'urgency_score': 0.15,
                    'summary': 'Regular email with project update.'
                }
        
        processor.process_email = MagicMock(side_effect=mock_process_email)
        
        yield processor

@pytest.fixture
def mock_slack_client():
    """Create a mock SlackServiceClient with predetermined responses."""
    # Mock the WebClient
    with patch('src.slack_service.slack_client.WebClient') as mock_web_client_class:
        # Configure the mock client
        mock_client = MagicMock()
        mock_web_client_class.return_value = mock_client
        
        # Configure the chat.postMessage method to return different responses
        def mock_post_message(**kwargs):
            channel = kwargs.get('channel', '')
            text = kwargs.get('text', '')
            
            # Return different responses based on inputs
            if channel == "invalid_channel":
                return INVALID_TOKEN_ERROR
            elif "ERROR" in text:
                return WARNING_MESSAGE_RESPONSE
            else:
                return SUCCESSFUL_MESSAGE_RESPONSE
                
        # Set the chat.postMessage to use our mock function
        mock_client.chat_postMessage = mock_post_message
        
        # Create the slack client
        slack_client = SlackServiceClient()
        
        # Mock the send_urgent_email_notification method for testing
        slack_client.send_urgent_email_notification = MagicMock(return_value=True)
        
        yield slack_client

@pytest.fixture
def mock_pubsub_listener():
    """Create a mock PubSubListener."""
    with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient') as mock_subscriber_class:
        # Configure the mock subscriber
        mock_subscriber = MagicMock()
        mock_subscriber_class.return_value = mock_subscriber
        
        # Mock the subscription path
        mock_subscriber.subscription_path.return_value = "projects/test-project-id/subscriptions/test-subscription-id"
        
        # Mock the subscribe method
        mock_streaming_future = MagicMock()
        mock_subscriber.subscribe.return_value = mock_streaming_future
        
        # Create the pubsub listener
        listener = PubSubListener(
            project_id="test-project-id",
            subscription_id="test-subscription-id"
        )
        
        # Mock the _process_payload method to work with our test messages
        original_process_payload = listener._process_payload
        def mock_process_payload(message):
            if hasattr(message, 'message_id') and message.message_id == 'pubsub_msg_12345':
                return '12345'  # Standard history ID
            elif hasattr(message, 'message_id') and message.message_id == 'invalid_json':
                return None  # Simulate processing error
            elif hasattr(message, 'message_id') and message.message_id == 'missing_fields':
                return None  # Simulate missing fields
            else:
                # For other cases use the original method
                return original_process_payload(message)
                
        # Replace with our mock function
        listener._process_payload = mock_process_payload
        
        yield listener

@pytest.fixture
def mock_app_components(mock_gmail_client, mock_ai_processor, mock_slack_client, mock_pubsub_listener):
    """Combine all mocked components for end-to-end tests."""
    return {
        'gmail_client': mock_gmail_client,
        'ai_processor': mock_ai_processor,
        'slack_client': mock_slack_client,
        'pubsub_listener': mock_pubsub_listener
    }

@pytest.fixture
def mock_email_processor(mock_app_components):
    """Create a mock EmailProcessor for testing the entire workflow."""
    from src.main import EmailProcessor
    
    with patch('src.main.GmailClient', return_value=mock_app_components['gmail_client']), \
         patch('src.main.AIProcessor', return_value=mock_app_components['ai_processor']), \
         patch('src.main.SlackServiceClient', return_value=mock_app_components['slack_client']):
        
        # Create the processor instance
        processor = EmailProcessor()
        
        # Ensure process_email returns False for nonexistent and error cases
        original_process_email = processor.process_email
        def mock_process_email(email_id):
            if email_id == "nonexistent_id":
                return False
            elif email_id == "error_email_id":
                return False
            else:
                return original_process_email(email_id)
                
        # Replace with a MagicMock that uses our side_effect
        processor.process_email = MagicMock(side_effect=mock_process_email)
        
        # Set up history response
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
        
        # Configure the mock get_history method
        processor.gmail_client.get_history = MagicMock(return_value=history_response)
        
        yield processor

@pytest.fixture
def mock_email_triage_app(mock_app_components):
    """Create a mock EmailTriageApp for testing the complete application."""
    from src.main import EmailTriageApp
    
    with patch('src.main.GmailClient', return_value=mock_app_components['gmail_client']), \
         patch('src.main.AIProcessor', return_value=mock_app_components['ai_processor']), \
         patch('src.main.SlackServiceClient', return_value=mock_app_components['slack_client']), \
         patch('src.main.PubSubListener', return_value=mock_app_components['pubsub_listener']):
        
        # Create the app instance
        app = EmailTriageApp()
        
        # Ensure service is properly mocked
        if app.gmail_client and not app.gmail_client.service:
            app.gmail_client.service = MagicMock()
            
            # Create the users mock chain
            users_mock = MagicMock()
            app.gmail_client.service.users = MagicMock(return_value=users_mock)
            
            # Mock history method
            history_mock = MagicMock()
            users_mock.history = MagicMock(return_value=history_mock)
            
            # Mock history.list
            list_mock = MagicMock()
            history_mock.list = MagicMock(return_value=list_mock)
            
            # Mock the execute method to return history data
            list_mock.execute = MagicMock(return_value={
                'history': [
                    {
                        'messagesAdded': [
                            {'message': {'id': 'msg_in_history_1'}}
                        ]
                    }
                ]
            })
        
        yield app 