"""
Tests for the PubSub listener component.
"""
import pytest
from unittest.mock import patch, MagicMock, call, ANY
import json
import base64
import os
from concurrent.futures import Future

from tests.test_integration.fixtures import (
    mock_environment, mock_pubsub_listener, mock_app_components
)
from tests.mocks.data import (
    STANDARD_RECEIVED_MESSAGE, INVALID_JSON_RECEIVED_MESSAGE,
    MISSING_FIELDS_RECEIVED_MESSAGE, EMPTY_FIELDS_RECEIVED_MESSAGE,
    NON_GMAIL_RECEIVED_MESSAGE, NON_BASE64_RECEIVED_MESSAGE,
    EMPTY_DATA_RECEIVED_MESSAGE, EXTRA_FIELDS_RECEIVED_MESSAGE,
    SPECIAL_CHARS_RECEIVED_MESSAGE
)

from src.gmail_service.pubsub_listener import PubSubListener
from src.utils.exceptions import PubSubError

pytestmark = pytest.mark.asyncio

@pytest.mark.usefixtures("mock_environment")
class TestPubSubListener:
    """Tests for the PubSub listener component."""

    def test_initialization(self):
        """Test initializing the PubSub listener."""
        with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient') as mock_subscriber:
            # Configure the mock subscriber
            mock_client = MagicMock()
            mock_subscriber.return_value = mock_client
            
            # Mock the subscription path
            mock_client.subscription_path.return_value = "projects/test-project/subscriptions/test-sub"
            
            # Initialize the listener
            listener = PubSubListener(
                project_id="test-project",
                subscription_id="test-sub"
            )
            
            # Verify the initialization
            assert listener.project_id == "test-project"
            assert listener.subscription_id == "test-sub"
            assert listener.subscriber_client is mock_client
            assert listener.subscription_path == "projects/test-project/subscriptions/test-sub"
            
            # Verify the subscription path was called with the correct arguments
            mock_client.subscription_path.assert_called_once_with("test-project", "test-sub")

    def test_process_payload_standard(self):
        """Test processing a standard Pub/Sub message payload."""
        with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient'):
            listener = PubSubListener(
                project_id="test-project",
                subscription_id="test-sub"
            )
            
            # Process a standard message
            history_id = listener._process_payload(STANDARD_RECEIVED_MESSAGE)
            
            # Verify the result
            assert history_id == "12345"

    def test_process_payload_invalid_json(self):
        """Test processing a message with invalid JSON."""
        with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient'):
            listener = PubSubListener(
                project_id="test-project",
                subscription_id="test-sub"
            )
            
            # Process a message with invalid JSON
            history_id = listener._process_payload(INVALID_JSON_RECEIVED_MESSAGE)
            
            # Verify the result
            assert history_id is None

    def test_process_payload_missing_fields(self):
        """Test processing a message with missing required fields."""
        with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient'):
            listener = PubSubListener(
                project_id="test-project",
                subscription_id="test-sub"
            )
            
            # Process a message with missing fields
            history_id = listener._process_payload(MISSING_FIELDS_RECEIVED_MESSAGE)
            
            # Verify the result
            assert history_id is None

    def test_process_payload_empty_fields(self):
        """Test processing a message with empty required fields."""
        with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient'):
            listener = PubSubListener(
                project_id="test-project",
                subscription_id="test-sub"
            )
            
            # Process a message with empty fields
            history_id = listener._process_payload(EMPTY_FIELDS_RECEIVED_MESSAGE)
            
            # Verify the result - should still try to parse the empty string
            assert history_id == ""

    def test_process_payload_non_gmail(self):
        """Test processing a message from a non-Gmail source."""
        with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient'):
            listener = PubSubListener(
                project_id="test-project",
                subscription_id="test-sub"
            )
            
            # Process a non-Gmail message
            history_id = listener._process_payload(NON_GMAIL_RECEIVED_MESSAGE)
            
            # Verify the result - should handle any JSON, but this would not contain historyId
            assert history_id is None

    def test_process_payload_non_base64(self):
        """Test processing a message with non-base64 data."""
        with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient'):
            listener = PubSubListener(
                project_id="test-project",
                subscription_id="test-sub"
            )
            
            # Process a message with non-base64 data
            history_id = listener._process_payload(NON_BASE64_RECEIVED_MESSAGE)
            
            # Verify the result
            assert history_id is None

    def test_process_payload_empty_data(self):
        """Test processing a message with empty data."""
        with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient'):
            listener = PubSubListener(
                project_id="test-project",
                subscription_id="test-sub"
            )
            
            # Process a message with empty data
            history_id = listener._process_payload(EMPTY_DATA_RECEIVED_MESSAGE)
            
            # Verify the result
            assert history_id is None

    def test_process_payload_extra_fields(self):
        """Test processing a message with extra fields."""
        with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient'):
            listener = PubSubListener(
                project_id="test-project",
                subscription_id="test-sub"
            )
            
            # Process a message with extra fields
            history_id = listener._process_payload(EXTRA_FIELDS_RECEIVED_MESSAGE)
            
            # Verify the result - should extract the historyId correctly
            assert history_id == "12346"

    def test_process_payload_special_chars(self):
        """Test processing a message with special characters."""
        with patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient'):
            listener = PubSubListener(
                project_id="test-project",
                subscription_id="test-sub"
            )
            
            # Process a message with special characters
            history_id = listener._process_payload(SPECIAL_CHARS_RECEIVED_MESSAGE)
            
            # Verify the result - should handle special characters correctly
            assert history_id == "12347"

    def test_start_listening(self, mock_pubsub_listener):
        """Test starting the PubSub listener."""
        # Create a mock callback
        mock_callback = MagicMock()
        
        # Create a mock streaming pull future
        mock_future = MagicMock(spec=Future)
        # Configure the future to raise an exception on result() to end the blocking call
        mock_future.result.side_effect = KeyboardInterrupt("Testing end of listening")
        
        # Configure the subscribe method to return our future
        mock_pubsub_listener.subscriber_client.subscribe.return_value = mock_future
        
        # Start listening
        mock_pubsub_listener.start_listening(mock_callback)
        
        # Verify that subscribe was called
        mock_pubsub_listener.subscriber_client.subscribe.assert_called_once_with(
            mock_pubsub_listener.subscription_path, callback=ANY
        )
        
        # Verify that future.result() was called
        mock_future.result.assert_called_once()
        
        # Verify that future.cancel() was called
        mock_future.cancel.assert_called_once()
        
        # Verify that subscriber_client.close() was called
        mock_pubsub_listener.subscriber_client.close.assert_called_once()

    def test_message_handler(self, mock_pubsub_listener):
        """Test the message handler function created by start_listening."""
        # Extract the message handler function
        mock_callback = MagicMock()
        mock_pubsub_listener.subscriber_client.subscribe.return_value = MagicMock(spec=Future)
        
        # Call start_listening to get the message handler
        with patch.object(mock_pubsub_listener, '_process_payload', return_value="12345") as mock_process_payload:
            # Create a fake calling context to extract the handler
            def fake_subscribe(subscription_path, callback):
                fake_subscribe.handler = callback
                return MagicMock(spec=Future)
            
            # Replace subscribe with our fake
            mock_pubsub_listener.subscriber_client.subscribe.side_effect = fake_subscribe
            
            # Start listening - this will set fake_subscribe.handler
            try:
                mock_pubsub_listener.start_listening(mock_callback)
            except Exception:
                # The mock future might cause an exception - that's fine
                pass
            
            # Make sure we captured the handler
            assert hasattr(fake_subscribe, 'handler')
            
            # Create a mock message
            mock_message = MagicMock()
            mock_message.message_id = "test_message_id"
            
            # Call the handler
            fake_subscribe.handler(mock_message)
            
            # Verify process_payload was called
            mock_process_payload.assert_called_once_with(mock_message)
            
            # Verify callback was called with historyId
            mock_callback.assert_called_once_with("12345")
            
            # Verify message.ack was called
            mock_message.ack.assert_called_once()

    def test_message_handler_error(self, mock_pubsub_listener):
        """Test the message handler when an error occurs."""
        # Extract the message handler function
        mock_callback = MagicMock(side_effect=Exception("Test callback exception"))
        mock_pubsub_listener.subscriber_client.subscribe.return_value = MagicMock(spec=Future)
        
        # Call start_listening to get the message handler
        with patch.object(mock_pubsub_listener, '_process_payload', return_value="12345") as mock_process_payload:
            # Create a fake calling context to extract the handler
            def fake_subscribe(subscription_path, callback):
                fake_subscribe.handler = callback
                return MagicMock(spec=Future)
            
            # Replace subscribe with our fake
            mock_pubsub_listener.subscriber_client.subscribe.side_effect = fake_subscribe
            
            # Start listening - this will set fake_subscribe.handler
            try:
                mock_pubsub_listener.start_listening(mock_callback)
            except Exception:
                # The mock future might cause an exception - that's fine
                pass
            
            # Make sure we captured the handler
            assert hasattr(fake_subscribe, 'handler')
            
            # Create a mock message
            mock_message = MagicMock()
            mock_message.message_id = "test_message_id"
            
            # Call the handler - should not raise an exception to the caller
            fake_subscribe.handler(mock_message)
            
            # Verify process_payload was called
            mock_process_payload.assert_called_once_with(mock_message)
            
            # Verify callback was called with historyId
            mock_callback.assert_called_once_with("12345")
            
            # Verify message.nack was called (since callback failed)
            mock_message.nack.assert_called_once()

    def test_message_handler_null_history(self, mock_pubsub_listener):
        """Test the message handler when no history_id is returned."""
        # Extract the message handler function
        mock_callback = MagicMock()
        mock_pubsub_listener.subscriber_client.subscribe.return_value = MagicMock(spec=Future)
        
        # Call start_listening to get the message handler
        with patch.object(mock_pubsub_listener, '_process_payload', return_value=None) as mock_process_payload:
            # Create a fake calling context to extract the handler
            def fake_subscribe(subscription_path, callback):
                fake_subscribe.handler = callback
                return MagicMock(spec=Future)
            
            # Replace subscribe with our fake
            mock_pubsub_listener.subscriber_client.subscribe.side_effect = fake_subscribe
            
            # Start listening - this will set fake_subscribe.handler
            try:
                mock_pubsub_listener.start_listening(mock_callback)
            except Exception:
                # The mock future might cause an exception - that's fine
                pass
            
            # Make sure we captured the handler
            assert hasattr(fake_subscribe, 'handler')
            
            # Create a mock message
            mock_message = MagicMock()
            mock_message.message_id = "test_message_id"
            
            # Call the handler
            fake_subscribe.handler(mock_message)
            
            # Verify process_payload was called
            mock_process_payload.assert_called_once_with(mock_message)
            
            # Verify callback was NOT called (since history_id is None)
            mock_callback.assert_not_called()
            
            # Verify message.ack was called (even with bad payload)
            mock_message.ack.assert_called_once() 