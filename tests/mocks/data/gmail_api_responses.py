"""
Mock Gmail API responses for testing.
This file contains synthetic responses from the Gmail API covering various scenarios.
"""
from typing import Dict, List, Any
import base64
import json
from datetime import datetime, timezone, timedelta

# Basic message response
BASIC_MESSAGE_RESPONSE = {
    'id': 'msg_123',
    'threadId': 'thread_123',
    'labelIds': ['INBOX', 'UNREAD'],
    'snippet': 'This is a snippet of the email content...',
    'payload': {
        'mimeType': 'multipart/alternative',
        'headers': [
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'To', 'value': 'recipient@example.com'},
            {'name': 'Subject', 'value': 'Test Subject'},
            {'name': 'Date', 'value': 'Wed, 5 Jun 2024 10:30:00 +0000 (UTC)'},
        ],
        'parts': [
            {
                'mimeType': 'text/plain',
                'body': {
                    'data': base64.urlsafe_b64encode('This is the plain text body.'.encode()).decode(),
                    'size': 28
                }
            },
            {
                'mimeType': 'text/html',
                'body': {
                    'data': base64.urlsafe_b64encode('<div>This is the HTML body.</div>'.encode()).decode(),
                    'size': 33
                }
            }
        ]
    },
    'sizeEstimate': 1024,
    'historyId': '12345'
}

# Message with only plain text (no HTML)
PLAIN_TEXT_ONLY_RESPONSE = {
    'id': 'msg_plain_123',
    'threadId': 'thread_plain_123',
    'labelIds': ['INBOX'],
    'snippet': 'This is a plain text email...',
    'payload': {
        'mimeType': 'text/plain',
        'headers': [
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'To', 'value': 'recipient@example.com'},
            {'name': 'Subject', 'value': 'Plain Text Only'},
            {'name': 'Date', 'value': 'Wed, 5 Jun 2024 09:30:00 +0000 (UTC)'},
        ],
        'body': {
            'data': base64.urlsafe_b64encode('This is a plain text only email.\nNo HTML part is included.'.encode()).decode(),
            'size': 55
        }
    },
    'sizeEstimate': 512,
    'historyId': '12346'
}

# Message with only HTML (no plain text)
HTML_ONLY_RESPONSE = {
    'id': 'msg_html_123',
    'threadId': 'thread_html_123',
    'labelIds': ['INBOX'],
    'snippet': 'This is an HTML email...',
    'payload': {
        'mimeType': 'text/html',
        'headers': [
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'To', 'value': 'recipient@example.com'},
            {'name': 'Subject', 'value': 'HTML Only'},
            {'name': 'Date', 'value': 'Wed, 5 Jun 2024 08:30:00 +0000 (UTC)'},
        ],
        'body': {
            'data': base64.urlsafe_b64encode('<div>This is an HTML only email. <strong>No plain text is included.</strong></div>'.encode()).decode(),
            'size': 72
        }
    },
    'sizeEstimate': 512,
    'historyId': '12347'
}

# Message with missing headers
MISSING_HEADERS_RESPONSE = {
    'id': 'msg_missing_headers_123',
    'threadId': 'thread_missing_headers_123',
    'labelIds': ['INBOX'],
    'snippet': 'Email with missing headers...',
    'payload': {
        'mimeType': 'multipart/alternative',
        'headers': [
            # Missing Subject and From headers
            {'name': 'To', 'value': 'recipient@example.com'},
            {'name': 'Date', 'value': 'Wed, 5 Jun 2024 07:30:00 +0000 (UTC)'},
        ],
        'parts': [
            {
                'mimeType': 'text/plain',
                'body': {
                    'data': base64.urlsafe_b64encode('This email has missing headers.'.encode()).decode(),
                    'size': 30
                }
            }
        ]
    },
    'sizeEstimate': 256,
    'historyId': '12348'
}

# Message with invalid date format
INVALID_DATE_RESPONSE = {
    'id': 'msg_invalid_date_123',
    'threadId': 'thread_invalid_date_123',
    'labelIds': ['INBOX'],
    'snippet': 'Email with invalid date format...',
    'payload': {
        'mimeType': 'multipart/alternative',
        'headers': [
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'To', 'value': 'recipient@example.com'},
            {'name': 'Subject', 'value': 'Invalid Date Format'},
            {'name': 'Date', 'value': 'Invalid Date Format'},  # Invalid date format
        ],
        'parts': [
            {
                'mimeType': 'text/plain',
                'body': {
                    'data': base64.urlsafe_b64encode('This email has an invalid date format.'.encode()).decode(),
                    'size': 38
                }
            }
        ]
    },
    'sizeEstimate': 256,
    'historyId': '12349'
}

# Message with empty body parts
EMPTY_BODY_RESPONSE = {
    'id': 'msg_empty_body_123',
    'threadId': 'thread_empty_body_123',
    'labelIds': ['INBOX'],
    'snippet': '',
    'payload': {
        'mimeType': 'multipart/alternative',
        'headers': [
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'To', 'value': 'recipient@example.com'},
            {'name': 'Subject', 'value': 'Empty Body'},
            {'name': 'Date', 'value': 'Wed, 5 Jun 2024 06:30:00 +0000 (UTC)'},
        ],
        'parts': [
            {
                'mimeType': 'text/plain',
                'body': {
                    'data': '',  # Empty data
                    'size': 0
                }
            },
            {
                'mimeType': 'text/html',
                'body': {
                    'data': '',  # Empty data
                    'size': 0
                }
            }
        ]
    },
    'sizeEstimate': 128,
    'historyId': '12350'
}

# Message with oversized HTML content
OVERSIZED_HTML_RESPONSE = {
    'id': 'msg_oversized_html_123',
    'threadId': 'thread_oversized_html_123',
    'labelIds': ['INBOX'],
    'snippet': 'Email with oversized HTML content...',
    'payload': {
        'mimeType': 'multipart/alternative',
        'headers': [
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'To', 'value': 'recipient@example.com'},
            {'name': 'Subject', 'value': 'Oversized HTML Content'},
            {'name': 'Date', 'value': 'Wed, 5 Jun 2024 05:30:00 +0000 (UTC)'},
        ],
        'parts': [
            {
                'mimeType': 'text/plain',
                'body': {
                    'data': base64.urlsafe_b64encode('This is the plain text version of an email with a very large HTML body.'.encode()).decode(),
                    'size': 66
                }
            },
            {
                'mimeType': 'text/html',
                'body': {
                    'data': base64.urlsafe_b64encode(('<div>This is an email with oversized HTML content. ' + 'A' * 50000 + '</div>').encode()).decode(),
                    'size': 50056
                }
            }
        ]
    },
    'sizeEstimate': 51200,
    'historyId': '12351'
}

# Message with unusual MIME types
UNUSUAL_MIME_TYPES_RESPONSE = {
    'id': 'msg_unusual_mime_123',
    'threadId': 'thread_unusual_mime_123',
    'labelIds': ['INBOX'],
    'snippet': 'Email with unusual MIME types...',
    'payload': {
        'mimeType': 'multipart/mixed',
        'headers': [
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'To', 'value': 'recipient@example.com'},
            {'name': 'Subject', 'value': 'Unusual MIME Types'},
            {'name': 'Date', 'value': 'Wed, 5 Jun 2024 04:30:00 +0000 (UTC)'},
        ],
        'parts': [
            {
                'mimeType': 'text/x-custom-format',  # Unusual MIME type
                'body': {
                    'data': base64.urlsafe_b64encode('This is a custom formatted text.'.encode()).decode(),
                    'size': 31
                }
            },
            {
                'mimeType': 'application/x-custom-app',  # Unusual MIME type
                'body': {
                    'data': base64.urlsafe_b64encode('Custom application data.'.encode()).decode(),
                    'size': 23
                }
            }
        ]
    },
    'sizeEstimate': 512,
    'historyId': '12352'
}

# Message with base64 encoding issues (malformed base64 data)
MALFORMED_BASE64_RESPONSE = {
    'id': 'msg_malformed_base64_123',
    'threadId': 'thread_malformed_base64_123',
    'labelIds': ['INBOX'],
    'snippet': 'Email with malformed base64 encoding...',
    'payload': {
        'mimeType': 'multipart/alternative',
        'headers': [
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'To', 'value': 'recipient@example.com'},
            {'name': 'Subject', 'value': 'Malformed Base64 Encoding'},
            {'name': 'Date', 'value': 'Wed, 5 Jun 2024 03:30:00 +0000 (UTC)'},
        ],
        'parts': [
            {
                'mimeType': 'text/plain',
                'body': {
                    'data': 'This is not valid base64 data!!!',  # Malformed base64 data
                    'size': 30
                }
            }
        ]
    },
    'sizeEstimate': 256,
    'historyId': '12353'
}

# History response with new messages
HISTORY_RESPONSE_WITH_MESSAGES = {
    'history': [
        {
            'id': 'hist_123',
            'messages': [
                {'id': 'msg_in_history_1'}
            ],
            'messagesAdded': [
                {
                    'message': {
                        'id': 'msg_in_history_1',
                        'threadId': 'thread_in_history_1',
                        'labelIds': ['INBOX', 'UNREAD']
                    }
                },
                {
                    'message': {
                        'id': 'msg_in_history_2',
                        'threadId': 'thread_in_history_2',
                        'labelIds': ['INBOX', 'UNREAD']
                    }
                }
            ]
        }
    ],
    'historyId': '12400'
}

# Empty history response (no new messages)
EMPTY_HISTORY_RESPONSE = {
    'history': [],
    'historyId': '12400'
}

# Response with only label changes (no new messages)
HISTORY_LABEL_CHANGES_ONLY = {
    'history': [
        {
            'id': 'hist_124',
            'labelsAdded': [
                {
                    'message': {
                        'id': 'msg_label_change_1',
                        'threadId': 'thread_label_change_1',
                        'labelIds': ['INBOX', 'UNREAD', 'IMPORTANT']
                    },
                    'labelIds': ['IMPORTANT']
                }
            ],
            'labelsRemoved': [
                {
                    'message': {
                        'id': 'msg_label_change_2',
                        'threadId': 'thread_label_change_2',
                        'labelIds': ['INBOX']
                    },
                    'labelIds': ['UNREAD']
                }
            ]
        }
    ],
    'historyId': '12401'
}

# History response with mixed changes (new messages and label changes)
HISTORY_MIXED_CHANGES = {
    'history': [
        {
            'id': 'hist_125',
            'messagesAdded': [
                {
                    'message': {
                        'id': 'msg_mixed_1',
                        'threadId': 'thread_mixed_1',
                        'labelIds': ['INBOX', 'UNREAD']
                    }
                }
            ],
            'labelsAdded': [
                {
                    'message': {
                        'id': 'msg_mixed_2',
                        'threadId': 'thread_mixed_2',
                        'labelIds': ['INBOX', 'UNREAD', 'IMPORTANT']
                    },
                    'labelIds': ['IMPORTANT']
                }
            ]
        }
    ],
    'historyId': '12402'
}

# Labels list response
LABELS_LIST_RESPONSE = {
    'labels': [
        {
            'id': 'INBOX',
            'name': 'INBOX',
            'type': 'system',
            'messageListVisibility': 'show',
            'labelListVisibility': 'labelShow',
            'messagesTotal': 253,
            'messagesUnread': 17,
            'threadsTotal': 207,
            'threadsUnread': 17
        },
        {
            'id': 'IMPORTANT',
            'name': 'IMPORTANT',
            'type': 'system',
            'messageListVisibility': 'hide',
            'labelListVisibility': 'labelShow',
            'messagesTotal': 126,
            'messagesUnread': 0,
            'threadsTotal': 80,
            'threadsUnread': 0
        },
        {
            'id': 'SENT',
            'name': 'SENT',
            'type': 'system',
            'messageListVisibility': 'hide',
            'labelListVisibility': 'labelShow',
            'messagesTotal': 89,
            'messagesUnread': 0,
            'threadsTotal': 76,
            'threadsUnread': 0
        },
        {
            'id': 'Label_123',
            'name': 'URGENT_AI',
            'type': 'user',
            'messageListVisibility': 'show',
            'labelListVisibility': 'labelShow',
            'messagesTotal': 3,
            'messagesUnread': 0,
            'threadsTotal': 3,
            'threadsUnread': 0
        }
    ]
}

# Created label response
CREATED_LABEL_RESPONSE = {
    'id': 'Label_456',
    'name': 'URGENT_AI',
    'type': 'user',
    'messageListVisibility': 'show',
    'labelListVisibility': 'labelShow'
}

# Watch response (for push notifications)
WATCH_RESPONSE = {
    'historyId': '12345',
    'expiration': str(int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp() * 1000))  # One week from now
}

# Collection of responses for easy access
API_RESPONSES = {
    'basic_message': BASIC_MESSAGE_RESPONSE,
    'plain_text_only': PLAIN_TEXT_ONLY_RESPONSE,
    'html_only': HTML_ONLY_RESPONSE,
    'missing_headers': MISSING_HEADERS_RESPONSE,
    'invalid_date': INVALID_DATE_RESPONSE,
    'empty_body': EMPTY_BODY_RESPONSE,
    'oversized_html': OVERSIZED_HTML_RESPONSE,
    'unusual_mime_types': UNUSUAL_MIME_TYPES_RESPONSE,
    'malformed_base64': MALFORMED_BASE64_RESPONSE,
    'history_with_messages': HISTORY_RESPONSE_WITH_MESSAGES,
    'empty_history': EMPTY_HISTORY_RESPONSE,
    'history_label_changes': HISTORY_LABEL_CHANGES_ONLY,
    'history_mixed_changes': HISTORY_MIXED_CHANGES,
    'labels_list': LABELS_LIST_RESPONSE,
    'created_label': CREATED_LABEL_RESPONSE,
    'watch': WATCH_RESPONSE
}

# Export for easy import in tests
__all__ = [
    'BASIC_MESSAGE_RESPONSE',
    'PLAIN_TEXT_ONLY_RESPONSE',
    'HTML_ONLY_RESPONSE',
    'MISSING_HEADERS_RESPONSE',
    'INVALID_DATE_RESPONSE',
    'EMPTY_BODY_RESPONSE',
    'OVERSIZED_HTML_RESPONSE',
    'UNUSUAL_MIME_TYPES_RESPONSE',
    'MALFORMED_BASE64_RESPONSE',
    'HISTORY_RESPONSE_WITH_MESSAGES',
    'EMPTY_HISTORY_RESPONSE',
    'HISTORY_LABEL_CHANGES_ONLY',
    'HISTORY_MIXED_CHANGES',
    'LABELS_LIST_RESPONSE',
    'CREATED_LABEL_RESPONSE',
    'WATCH_RESPONSE',
    'API_RESPONSES'
] 