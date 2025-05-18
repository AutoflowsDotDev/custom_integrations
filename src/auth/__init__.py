"""
Authentication module for email triage workflow.
Provides OAuth2 authentication for Google and Slack services.
"""

from .oauth_handler import (
    GoogleOAuth2Handler,
    SlackOAuth2Handler,
    get_google_auth_handler,
    get_slack_auth_handler,
    is_google_authenticated,
    is_slack_authenticated,
) 