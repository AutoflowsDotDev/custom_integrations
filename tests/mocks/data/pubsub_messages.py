"""
Mock Google Cloud Pub/Sub messages for testing.
This file contains synthetic Pub/Sub messages for simulating Gmail push notifications.
"""
from typing import Dict, List, Any
import json
import base64
from datetime import datetime, timezone

# Standard Gmail notification Pub/Sub message
STANDARD_GMAIL_PUBSUB_DATA = json.dumps({
    'emailAddress': 'user@example.com',
    'historyId': '12345'
}).encode('utf-8')

STANDARD_GMAIL_PUBSUB_MESSAGE = {
    'data': base64.b64encode(STANDARD_GMAIL_PUBSUB_DATA),
    'attributes': {
        'origin': 'gmail',
        'timestamp': str(int(datetime.now(timezone.utc).timestamp()))
    },
    'message_id': 'pubsub_msg_12345',
    'publish_time': datetime.now(timezone.utc).isoformat()
}

# Message with very large history ID
LARGE_HISTORY_ID_DATA = json.dumps({
    'emailAddress': 'user@example.com',
    'historyId': '999999999999999'
}).encode('utf-8')

LARGE_HISTORY_ID_MESSAGE = {
    'data': base64.b64encode(LARGE_HISTORY_ID_DATA),
    'attributes': {
        'origin': 'gmail',
        'timestamp': str(int(datetime.now(timezone.utc).timestamp()))
    },
    'message_id': 'pubsub_msg_12346',
    'publish_time': datetime.now(timezone.utc).isoformat()
}

# Message with invalid/malformed JSON data
INVALID_JSON_MESSAGE = {
    'data': base64.b64encode('{emailAddress: user@example.com, historyId: 12345}'.encode('utf-8')),  # Invalid JSON
    'attributes': {
        'origin': 'gmail',
        'timestamp': str(int(datetime.now(timezone.utc).timestamp()))
    },
    'message_id': 'pubsub_msg_12347',
    'publish_time': datetime.now(timezone.utc).isoformat()
}

# Message with missing required fields
MISSING_FIELDS_DATA = json.dumps({
    'emailAddress': 'user@example.com'
    # Missing historyId
}).encode('utf-8')

MISSING_FIELDS_MESSAGE = {
    'data': base64.b64encode(MISSING_FIELDS_DATA),
    'attributes': {
        'origin': 'gmail',
        'timestamp': str(int(datetime.now(timezone.utc).timestamp()))
    },
    'message_id': 'pubsub_msg_12348',
    'publish_time': datetime.now(timezone.utc).isoformat()
}

# Message with empty fields
EMPTY_FIELDS_DATA = json.dumps({
    'emailAddress': '',
    'historyId': ''
}).encode('utf-8')

EMPTY_FIELDS_MESSAGE = {
    'data': base64.b64encode(EMPTY_FIELDS_DATA),
    'attributes': {
        'origin': 'gmail',
        'timestamp': str(int(datetime.now(timezone.utc).timestamp()))
    },
    'message_id': 'pubsub_msg_12349',
    'publish_time': datetime.now(timezone.utc).isoformat()
}

# Message with non-Gmail origin (should be ignored)
NON_GMAIL_DATA = json.dumps({
    'someOtherService': 'data',
    'actionId': '67890'
}).encode('utf-8')

NON_GMAIL_MESSAGE = {
    'data': base64.b64encode(NON_GMAIL_DATA),
    'attributes': {
        'origin': 'other-service',
        'timestamp': str(int(datetime.now(timezone.utc).timestamp()))
    },
    'message_id': 'pubsub_msg_12350',
    'publish_time': datetime.now(timezone.utc).isoformat()
}

# Message with non-base64 data
NON_BASE64_MESSAGE = {
    'data': 'This is not base64 encoded data'.encode('utf-8'),  # Ensure it's bytes
    'attributes': {
        'origin': 'gmail',
        'timestamp': str(int(datetime.now(timezone.utc).timestamp()))
    },
    'message_id': 'pubsub_msg_12351',
    'publish_time': datetime.now(timezone.utc).isoformat()
}

# Message with empty data
EMPTY_DATA_MESSAGE = {
    'data': b'',  # Ensure it's bytes
    'attributes': {
        'origin': 'gmail',
        'timestamp': str(int(datetime.now(timezone.utc).timestamp()))
    },
    'message_id': 'pubsub_msg_12352',
    'publish_time': datetime.now(timezone.utc).isoformat()
}

# Message with extra unexpected fields (should be handled gracefully)
EXTRA_FIELDS_DATA = json.dumps({
    'emailAddress': 'user@example.com',
    'historyId': '12346',
    'extraField1': 'value1',
    'extraField2': 'value2',
    'nestedExtra': {
        'nested1': 'value1',
        'nested2': 'value2'
    }
}).encode('utf-8')

EXTRA_FIELDS_MESSAGE = {
    'data': base64.b64encode(EXTRA_FIELDS_DATA),
    'attributes': {
        'origin': 'gmail',
        'timestamp': str(int(datetime.now(timezone.utc).timestamp())),
        'extra_attribute': 'value'
    },
    'message_id': 'pubsub_msg_12353',
    'publish_time': datetime.now(timezone.utc).isoformat()
}

# Message with special characters in email address
SPECIAL_CHARS_DATA = json.dumps({
    'emailAddress': 'user+special.chars_123@example.com',
    'historyId': '12347'
}).encode('utf-8')

SPECIAL_CHARS_MESSAGE = {
    'data': base64.b64encode(SPECIAL_CHARS_DATA),
    'attributes': {
        'origin': 'gmail',
        'timestamp': str(int(datetime.now(timezone.utc).timestamp()))
    },
    'message_id': 'pubsub_msg_12354',
    'publish_time': datetime.now(timezone.utc).isoformat()
}

# Create objects that can be used with the mocked Pub/Sub ReceivedMessage class
def create_pubsub_received_message(msg_dict):
    """Create a mock ReceivedMessage object from a message dictionary."""
    class MockReceivedMessage:
        def __init__(self, message_dict):
            self.message_id = message_dict.get('message_id', '')
            # Ensure data is bytes, not string
            data = message_dict.get('data', b'')
            self.data = data if isinstance(data, bytes) else str(data).encode('utf-8')
            self.attributes = message_dict.get('attributes', {})
            self.publish_time = message_dict.get('publish_time', '')
            self.ack = lambda: None  # Mock function that does nothing
            self.nack = lambda: None  # Mock function that does nothing
            
    return MockReceivedMessage(msg_dict)

# Create received message objects
STANDARD_RECEIVED_MESSAGE = create_pubsub_received_message(STANDARD_GMAIL_PUBSUB_MESSAGE)
LARGE_HISTORY_ID_RECEIVED_MESSAGE = create_pubsub_received_message(LARGE_HISTORY_ID_MESSAGE)
INVALID_JSON_RECEIVED_MESSAGE = create_pubsub_received_message(INVALID_JSON_MESSAGE)
MISSING_FIELDS_RECEIVED_MESSAGE = create_pubsub_received_message(MISSING_FIELDS_MESSAGE)
EMPTY_FIELDS_RECEIVED_MESSAGE = create_pubsub_received_message(EMPTY_FIELDS_MESSAGE)
NON_GMAIL_RECEIVED_MESSAGE = create_pubsub_received_message(NON_GMAIL_MESSAGE)
NON_BASE64_RECEIVED_MESSAGE = create_pubsub_received_message(NON_BASE64_MESSAGE)
EMPTY_DATA_RECEIVED_MESSAGE = create_pubsub_received_message(EMPTY_DATA_MESSAGE)
EXTRA_FIELDS_RECEIVED_MESSAGE = create_pubsub_received_message(EXTRA_FIELDS_MESSAGE)
SPECIAL_CHARS_RECEIVED_MESSAGE = create_pubsub_received_message(SPECIAL_CHARS_MESSAGE)

# Collection of dictionaries for easy access
PUBSUB_MESSAGES = {
    'standard': STANDARD_GMAIL_PUBSUB_MESSAGE,
    'large_history_id': LARGE_HISTORY_ID_MESSAGE,
    'invalid_json': INVALID_JSON_MESSAGE,
    'missing_fields': MISSING_FIELDS_MESSAGE,
    'empty_fields': EMPTY_FIELDS_MESSAGE,
    'non_gmail': NON_GMAIL_MESSAGE,
    'non_base64': NON_BASE64_MESSAGE,
    'empty_data': EMPTY_DATA_MESSAGE,
    'extra_fields': EXTRA_FIELDS_MESSAGE,
    'special_chars': SPECIAL_CHARS_MESSAGE
}

# Collection of ReceivedMessage objects for easy access
RECEIVED_MESSAGES = {
    'standard': STANDARD_RECEIVED_MESSAGE,
    'large_history_id': LARGE_HISTORY_ID_RECEIVED_MESSAGE,
    'invalid_json': INVALID_JSON_RECEIVED_MESSAGE,
    'missing_fields': MISSING_FIELDS_RECEIVED_MESSAGE,
    'empty_fields': EMPTY_FIELDS_RECEIVED_MESSAGE,
    'non_gmail': NON_GMAIL_RECEIVED_MESSAGE,
    'non_base64': NON_BASE64_RECEIVED_MESSAGE,
    'empty_data': EMPTY_DATA_RECEIVED_MESSAGE,
    'extra_fields': EXTRA_FIELDS_RECEIVED_MESSAGE,
    'special_chars': SPECIAL_CHARS_RECEIVED_MESSAGE
}

# Export for easy import in tests
__all__ = [
    'STANDARD_GMAIL_PUBSUB_DATA',
    'STANDARD_GMAIL_PUBSUB_MESSAGE',
    'LARGE_HISTORY_ID_DATA',
    'LARGE_HISTORY_ID_MESSAGE',
    'INVALID_JSON_MESSAGE',
    'MISSING_FIELDS_DATA',
    'MISSING_FIELDS_MESSAGE',
    'EMPTY_FIELDS_DATA',
    'EMPTY_FIELDS_MESSAGE',
    'NON_GMAIL_DATA',
    'NON_GMAIL_MESSAGE',
    'NON_BASE64_MESSAGE',
    'EMPTY_DATA_MESSAGE',
    'EXTRA_FIELDS_DATA',
    'EXTRA_FIELDS_MESSAGE',
    'SPECIAL_CHARS_DATA',
    'SPECIAL_CHARS_MESSAGE',
    'STANDARD_RECEIVED_MESSAGE',
    'LARGE_HISTORY_ID_RECEIVED_MESSAGE',
    'INVALID_JSON_RECEIVED_MESSAGE',
    'MISSING_FIELDS_RECEIVED_MESSAGE',
    'EMPTY_FIELDS_RECEIVED_MESSAGE',
    'NON_GMAIL_RECEIVED_MESSAGE',
    'NON_BASE64_RECEIVED_MESSAGE',
    'EMPTY_DATA_RECEIVED_MESSAGE',
    'EXTRA_FIELDS_RECEIVED_MESSAGE',
    'SPECIAL_CHARS_RECEIVED_MESSAGE',
    'PUBSUB_MESSAGES',
    'RECEIVED_MESSAGES',
    'create_pubsub_received_message'
] 