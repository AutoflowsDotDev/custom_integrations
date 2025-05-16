"""Tests for the pubsub_listener module."""
import json
import base64
from unittest.mock import patch, MagicMock, call

import pytest
from google.cloud.pubsub_v1.types import ReceivedMessage

from src.gmail_service.pubsub_listener import PubSubListener


@pytest.fixture
def mock_pubsub_subscriber():
    """Create a mock Pub/Sub subscriber client."""
    mock_subscriber = MagicMock()
    mock_subscriber.subscription_path.return_value = "projects/test-project/subscriptions/test-subscription"
    return mock_subscriber


@pytest.fixture
def mock_pubsub_message():
    """Create a mock Pub/Sub message."""
    # Create message data (simulating Gmail notification)
    data = {
        'emailAddress': 'user@example.com',
        'historyId': '12345'
    }
    # Instead of raw bytes, wrap the encoded data in a MagicMock so that tests can
    # conveniently override the behaviour of ``decode`` via
    # ``mock_pubsub_message.data.decode.return_value`` without running into an
    # ``AttributeError`` (the built-in ``bytes.decode`` method is implemented in C
    # and therefore does not allow attribute assignment).

    encoded_data = base64.b64encode(json.dumps(data).encode('utf-8'))

    # Create mock message
    message = MagicMock(spec=ReceivedMessage)
    message.message_id = 'test-message-id'

    # Wrap encoded_data in a MagicMock with a configurable ``decode`` method
    data_mock = MagicMock(name='data')
    data_mock.decode.return_value = encoded_data.decode('utf-8')
    message.data = data_mock
    message.ack = MagicMock()
    message.nack = MagicMock()
    
    return message


@pytest.fixture
def mock_invalid_pubsub_message():
    """Create a mock Pub/Sub message with invalid data."""
    # Create invalid data that doesn't parse as JSON
    encoded_data = base64.b64encode(b'This is not valid JSON')

    # Create mock message
    message = MagicMock(spec=ReceivedMessage)
    message.message_id = 'invalid-message-id'

    data_mock = MagicMock(name='data')
    data_mock.decode.return_value = encoded_data.decode('utf-8')
    message.data = data_mock
    message.ack = MagicMock()
    message.nack = MagicMock()
    
    return message


class TestPubSubListener:
    """Tests for the PubSubListener class."""

    @patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient')
    def test_init(self, mock_subscriber_client):
        """Test PubSubListener initialization."""
        # Arrange
        mock_subscriber_client.return_value = MagicMock()
        mock_subscriber_client.return_value.subscription_path.return_value = "projects/test-project/subscriptions/test-subscription"
        
        # Act
        listener = PubSubListener("test-project", "test-subscription")
        
        # Assert
        assert listener.project_id == "test-project"
        assert listener.subscription_id == "test-subscription"
        assert listener.subscription_path == "projects/test-project/subscriptions/test-subscription"
        mock_subscriber_client.return_value.subscription_path.assert_called_once_with("test-project", "test-subscription")

    @patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient')
    def test_process_payload_valid(self, mock_subscriber_client, mock_pubsub_message):
        """Test processing a valid Pub/Sub message payload."""
        # Arrange
        mock_subscriber_client.return_value = MagicMock()
        listener = PubSubListener("test-project", "test-subscription")
        
        # Ensure the mock_pubsub_message returns the right data
        mock_pubsub_message.data.decode.return_value = '{"emailAddress": "user@example.com", "historyId": "12345"}'
        
        # Act
        history_id = listener._process_payload(mock_pubsub_message)
        
        # Assert
        assert history_id == "12345"

    @patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient')
    def test_process_payload_invalid_json(self, mock_subscriber_client, mock_invalid_pubsub_message):
        """Test processing a Pub/Sub message with invalid JSON payload."""
        # Arrange
        mock_subscriber_client.return_value = MagicMock()
        listener = PubSubListener("test-project", "test-subscription")
        
        # Act
        history_id = listener._process_payload(mock_invalid_pubsub_message)
        
        # Assert
        assert history_id is None

    @patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient')
    def test_process_payload_missing_fields(self, mock_subscriber_client):
        """Test processing a Pub/Sub message with missing required fields."""
        # Arrange
        mock_subscriber_client.return_value = MagicMock()
        listener = PubSubListener("test-project", "test-subscription")
        
        # Create message with missing historyId
        data = {'emailAddress': 'user@example.com'}  # No historyId
        # Instead of raw bytes, wrap the encoded data in a MagicMock so that tests can
        # conveniently override the behaviour of ``decode`` via
        # ``mock_pubsub_message.data.decode.return_value`` without running into an
        # ``AttributeError`` (the built-in ``bytes.decode`` method is implemented in C
        # and therefore does not allow attribute assignment).

        encoded_data = base64.b64encode(json.dumps(data).encode('utf-8'))

        # Create mock message
        message = MagicMock(spec=ReceivedMessage)
        message.message_id = 'test-message-id'

        # Wrap encoded_data in a MagicMock with a configurable ``decode`` method
        data_mock = MagicMock(name='data')
        data_mock.decode.return_value = encoded_data.decode('utf-8')
        message.data = data_mock
        
        # Act
        history_id = listener._process_payload(message)
        
        # Assert
        assert history_id is None

    @patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient')
    def test_start_listening_callback_success(self, mock_subscriber_client, mock_pubsub_message):
        """Test that the listener correctly calls the callback with history ID."""
        # Arrange
        mock_subscriber = MagicMock()
        mock_subscriber_client.return_value = mock_subscriber
        
        # Setup streaming pull future
        mock_future = MagicMock()
        mock_subscriber.subscribe.return_value = mock_future
        
        # Create test callback
        mock_callback = MagicMock()
        
        # Create the listener
        listener = PubSubListener("test-project", "test-subscription")
        
        # Ensure the mock_pubsub_message returns valid data
        mock_pubsub_message.data.decode.return_value = '{"emailAddress": "user@example.com", "historyId": "12345"}'
        
        # Act - need to simulate message handler call since we can't directly test it
        # Extract the callback function from the subscribe call
        def side_effect(*args, **kwargs):
            # Call the callback with our test message
            callback_func = kwargs.get('callback')
            callback_func(mock_pubsub_message)
            return mock_future
        
        mock_subscriber.subscribe.side_effect = side_effect
        
        # This will trigger message_handler via our side_effect
        listener.start_listening(mock_callback)
        
        # Assert
        mock_subscriber.subscribe.assert_called_once()
        mock_callback.assert_called_once_with("12345")
        mock_pubsub_message.ack.assert_called_once()
        mock_pubsub_message.nack.assert_not_called()

    @patch('src.gmail_service.pubsub_listener.pubsub_v1.SubscriberClient')
    def test_start_listening_callback_exception(self, mock_subscriber_client, mock_pubsub_message):
        """Test that the listener handles exceptions in the callback."""
        # Arrange
        mock_subscriber = MagicMock()
        mock_subscriber_client.return_value = mock_subscriber
        
        # Setup streaming pull future
        mock_future = MagicMock()
        mock_subscriber.subscribe.return_value = mock_future
        
        # Create test callback that raises an exception
        mock_callback = MagicMock(side_effect=Exception("Test exception"))
        
        # Create the listener
        listener = PubSubListener("test-project", "test-subscription")
        
        # Ensure the mock_pubsub_message returns valid data
        mock_pubsub_message.data.decode.return_value = '{"emailAddress": "user@example.com", "historyId": "12345"}'
        
        # Act - need to simulate message handler call since we can't directly test it
        # Extract the callback function from the subscribe call
        def side_effect(*args, **kwargs):
            # Call the callback with our test message
            callback_func = kwargs.get('callback')
            callback_func(mock_pubsub_message)
            return mock_future
        
        mock_subscriber.subscribe.side_effect = side_effect
        
        # This will trigger message_handler via our side_effect
        listener.start_listening(mock_callback)
        
        # Assert
        mock_subscriber.subscribe.assert_called_once()
        mock_callback.assert_called_once_with("12345")
        mock_pubsub_message.nack.assert_called_once()  # Should nack on exception
        mock_pubsub_message.ack.assert_not_called() 