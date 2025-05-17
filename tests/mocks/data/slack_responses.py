"""
Mock Slack API responses for testing.
This file contains synthetic responses from the Slack API covering various scenarios.
"""
from typing import Dict, List, Any
import time

# Standard successful response for posting a message
SUCCESSFUL_MESSAGE_RESPONSE = {
    "ok": True,
    "channel": "C123456789",
    "ts": "1612345678.123456",
    "message": {
        "text": ":rotating_light: *Urgent Email Received* :rotating_light:\n\n*From*: important@example.com\n*Subject*: URGENT: Action Required Immediately\n*Summary*: Urgent matter requiring immediate attention.",
        "user": "U987654321",
        "bot_id": "B12345678",
        "ts": "1612345678.123456",
        "team": "T12345678",
        "bot_profile": {
            "id": "B12345678",
            "app_id": "A12345678",
            "name": "Email Triage Bot",
            "icons": {
                "image_36": "https://example.com/bot_image_36.png",
                "image_48": "https://example.com/bot_image_48.png",
                "image_72": "https://example.com/bot_image_72.png"
            },
            "deleted": False,
            "updated": 1612345670,
            "team_id": "T12345678"
        },
        "type": "message",
        "subtype": "bot_message"
    }
}

# Response when message has been posted but with warnings
WARNING_MESSAGE_RESPONSE = {
    "ok": True,
    "channel": "C123456789",
    "ts": "1612345679.123456",
    "message": {
        "text": ":rotating_light: *Urgent Email Received* :rotating_light:\n\n*From*: important@example.com\n*Subject*: URGENT: Action Required Immediately\n*Summary*: Urgent matter requiring immediate attention.",
        "user": "U987654321",
        "bot_id": "B12345678",
        "ts": "1612345679.123456",
        "team": "T12345678"
    },
    "warning": "some_links_denied",
    "response_metadata": {
        "warnings": ["some_links_denied"]
    }
}

# Responses for various error scenarios

# Error: Invalid token
INVALID_TOKEN_ERROR = {
    "ok": False,
    "error": "invalid_auth",
    "warning": "invalid_auth",
    "response_metadata": {
        "warnings": ["invalid_auth"]
    }
}

# Error: Channel not found
CHANNEL_NOT_FOUND_ERROR = {
    "ok": False,
    "error": "channel_not_found",
    "warning": "channel_not_found",
    "response_metadata": {
        "warnings": ["channel_not_found"]
    }
}

# Error: Not in channel
NOT_IN_CHANNEL_ERROR = {
    "ok": False,
    "error": "not_in_channel",
    "warning": "not_in_channel",
    "response_metadata": {
        "warnings": ["not_in_channel"]
    }
}

# Error: Rate limited
RATE_LIMITED_ERROR = {
    "ok": False,
    "error": "ratelimited",
    "warning": "ratelimited",
    "response_metadata": {
        "warnings": ["ratelimited"]
    },
    "retry_after": 60
}

# Error: Message too long
MESSAGE_TOO_LONG_ERROR = {
    "ok": False,
    "error": "msg_too_long",
    "warning": "msg_too_long",
    "response_metadata": {
        "warnings": ["msg_too_long"]
    }
}

# Error: Restricted action (e.g., bot doesn't have permission)
RESTRICTED_ACTION_ERROR = {
    "ok": False,
    "error": "restricted_action",
    "warning": "restricted_action",
    "response_metadata": {
        "warnings": ["restricted_action"]
    }
}

# Error: Invalid arguments
INVALID_ARGS_ERROR = {
    "ok": False,
    "error": "invalid_arguments",
    "warning": "invalid_arguments",
    "response_metadata": {
        "warnings": ["invalid_arguments"]
    }
}

# Error: Message containing malicious links or content that violates Slack policies
INVALID_BLOCKS_ERROR = {
    "ok": False,
    "error": "invalid_blocks",
    "warning": "invalid_blocks",
    "response_metadata": {
        "warnings": ["invalid_blocks"]
    }
}

# Error: Unknown error
UNKNOWN_ERROR = {
    "ok": False,
    "error": "unknown_error",
    "warning": "unknown_error",
    "response_metadata": {
        "warnings": ["unknown_error"]
    }
}

# Responses for channel and user information

# Response for channels.info
CHANNEL_INFO_RESPONSE = {
    "ok": True,
    "channel": {
        "id": "C123456789",
        "name": "urgent-alerts",
        "is_channel": True,
        "is_group": False,
        "is_im": False,
        "created": 1612340000,
        "creator": "U987654321",
        "is_archived": False,
        "is_general": False,
        "unlinked": 0,
        "name_normalized": "urgent-alerts",
        "is_shared": False,
        "is_ext_shared": False,
        "is_org_shared": False,
        "pending_shared": [],
        "is_pending_ext_shared": False,
        "is_member": True,
        "is_private": False,
        "is_mpim": False,
        "last_read": "1612345678.123456",
        "latest": {
            "type": "message",
            "subtype": "bot_message",
            "text": "Latest message in the channel",
            "ts": "1612345678.123456",
            "username": "Email Triage Bot",
            "bot_id": "B12345678"
        },
        "unread_count": 0,
        "unread_count_display": 0,
        "members": ["U987654321", "U876543210"],
        "topic": {
            "value": "Urgent email notifications",
            "creator": "U987654321",
            "last_set": 1612340001
        },
        "purpose": {
            "value": "Channel for urgent email notifications requiring immediate attention",
            "creator": "U987654321",
            "last_set": 1612340002
        },
        "previous_names": ["alerts"]
    }
}

# Response for auth.test
AUTH_TEST_RESPONSE = {
    "ok": True,
    "url": "https://example.slack.com/",
    "team": "Example Team",
    "user": "Email Triage Bot",
    "team_id": "T12345678",
    "user_id": "U12345678",
    "bot_id": "B12345678",
    "is_enterprise_install": False
}

# Collection of responses for easy access
SLACK_RESPONSES = {
    'success': SUCCESSFUL_MESSAGE_RESPONSE,
    'warning': WARNING_MESSAGE_RESPONSE,
    'invalid_token': INVALID_TOKEN_ERROR,
    'channel_not_found': CHANNEL_NOT_FOUND_ERROR,
    'not_in_channel': NOT_IN_CHANNEL_ERROR,
    'rate_limited': RATE_LIMITED_ERROR,
    'message_too_long': MESSAGE_TOO_LONG_ERROR,
    'restricted_action': RESTRICTED_ACTION_ERROR,
    'invalid_args': INVALID_ARGS_ERROR,
    'invalid_blocks': INVALID_BLOCKS_ERROR,
    'unknown_error': UNKNOWN_ERROR,
    'channel_info': CHANNEL_INFO_RESPONSE,
    'auth_test': AUTH_TEST_RESPONSE
}

# Export for easy import in tests
__all__ = [
    'SUCCESSFUL_MESSAGE_RESPONSE',
    'WARNING_MESSAGE_RESPONSE',
    'INVALID_TOKEN_ERROR',
    'CHANNEL_NOT_FOUND_ERROR',
    'NOT_IN_CHANNEL_ERROR',
    'RATE_LIMITED_ERROR',
    'MESSAGE_TOO_LONG_ERROR',
    'RESTRICTED_ACTION_ERROR',
    'INVALID_ARGS_ERROR',
    'INVALID_BLOCKS_ERROR',
    'UNKNOWN_ERROR',
    'CHANNEL_INFO_RESPONSE',
    'AUTH_TEST_RESPONSE',
    'SLACK_RESPONSES'
] 