from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.core.config import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID
from src.core.types import AnalyzedEmailData, SlackMessage
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SlackServiceClient:
    """Handles interactions with the Slack API."""

    def __init__(self, token: str = SLACK_BOT_TOKEN):
        self.client = WebClient(token=token)
        if not token or not token.startswith("xoxb-"):
            logger.warning("Slack bot token might be missing or invalid. Ensure it starts with 'xoxb-'.")

    def _format_notification_text(self, email_data: AnalyzedEmailData) -> str:
        """Formats the email data into a readable Slack message."""
        subject = email_data.get('subject', 'N/A')
        sender = email_data.get('sender', 'N/A')
        summary = email_data.get('summary', 'N/A')
        email_id = email_data.get('id', 'N/A')
        
        # Construct a simple link to the email if possible (generic, may not work for all clients without deep linking)
        # For a more robust link, you might need to construct it based on mail.google.com/mail/u/0/#inbox/message_id
        # This requires knowing the user's Gmail interface structure.
        gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{email_data.get('thread_id', email_id)}" 
        # Using thread_id if available for better linking to the conversation

        text = (
            f":rotating_light: *Urgent Email Received* :rotating_light:\n\n"
            f"*From*: {sender}\n"
            f"*Subject*: {subject}\n"
            f"*Summary*: {summary}\n\n"
            f"<{gmail_link}|View Email> (ID: {email_id})"
        )
        return text

    def send_urgent_email_notification(self, email_data: AnalyzedEmailData, channel: str = SLACK_CHANNEL_ID) -> bool:
        """Sends a notification about an urgent email to the specified Slack channel."""
        if not channel:
            logger.error("Slack channel ID is not configured. Cannot send notification.")
            return False
        
        message_text = self._format_notification_text(email_data)
        
        slack_message: SlackMessage = {
            'channel': channel,
            'text': message_text
        }
        
        try:
            response = self.client.chat_postMessage(**slack_message)
            if response.get("ok"):
                logger.info(f"Sent urgent email notification to Slack channel {channel} for email ID {email_data.get('id')}")
                return True
            else:
                logger.error(f"Slack API error while sending notification: {response.get('error')}")
                return False
        except SlackApiError as e:
            logger.error(f"Slack API error (exception) while sending notification: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Slack notification: {e}")
            return False

# Example Usage:
if __name__ == '__main__':
    # This example assumes you have a valid SLACK_BOT_TOKEN and SLACK_CHANNEL_ID in your .env file
    # And that AnalyzedEmailData is available or mocked
    from datetime import datetime
    mock_email: AnalyzedEmailData = {
        'id': 'test_email_123',
        'thread_id': 'test_thread_456',
        'subject': 'URGENT: Action Required Immediately!',
        'sender': 'important.client@example.com',
        'body_plain': 'This is a test urgent email body. Please review the attached document and respond ASAP.',
        'body_html': '<p>This is a test urgent email body. Please review the attached document and respond ASAP.</p>',
        'received_timestamp': datetime.now(),
        'snippet': 'This is a test urgent email.',
        'is_urgent': True,
        'summary': 'An urgent action is required regarding a document that needs immediate review and response.'
    }

    slack_client = SlackServiceClient()
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        print("Please set SLACK_BOT_TOKEN and SLACK_CHANNEL_ID in your .env file to run this example.")
    else:
        print(f"Attempting to send Slack notification to channel {SLACK_CHANNEL_ID}...")
        success = slack_client.send_urgent_email_notification(mock_email)
        if success:
            print("Slack notification sent successfully (check the channel).")
        else:
            print("Failed to send Slack notification.") 