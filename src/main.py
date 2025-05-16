import time
import signal
import sys
from typing import Optional, List, Dict, Any
import json # For decoding Pub/Sub message data
import base64 # For decoding Pub/Sub message data
from googleapiclient.errors import HttpError # Add this import

from src.core.config import (
    GOOGLE_CLOUD_PROJECT_ID,
    GOOGLE_PUBSUB_SUBSCRIPTION_ID,
    GMAIL_USER_ID
)
from src.core.types import EmailData, AnalyzedEmailData
from src.utils.logger import get_logger
from src.gmail_service.gmail_client import GmailClient
from src.gmail_service.pubsub_listener import PubSubListener
from src.ai_service.ai_processor import AIProcessor
from src.slack_service.slack_client import SlackServiceClient

logger = get_logger(__name__)

def process_new_email(email_id: str) -> bool:
    """Process a new email given its ID.
    
    Args:
        email_id: The ID of the email to process
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        gmail_client = GmailClient()
        ai_processor = AIProcessor()
        slack_client = SlackServiceClient()
        
        # Get email details
        email_data = gmail_client.get_email_details(email_id)
        if not email_data:
            logger.warning(f"Could not retrieve details for email ID: {email_id}")
            return False
            
        # Analyze the email
        analyzed_email = ai_processor.process_email(email_data)
        
        # If urgent, apply label and send notification
        if analyzed_email['is_urgent']:
            gmail_client.apply_urgent_label(email_id)
            slack_client.send_urgent_email_notification(analyzed_email)
            
        return True
    except Exception as e:
        logger.error(f"Error processing email {email_id}: {e}")
        return False

class EmailProcessor:
    """Handles the processing of emails."""
    
    def __init__(self) -> None:
        """Initialize the email processor."""
        self.gmail_client = GmailClient()
        self.ai_processor = AIProcessor()
        self.slack_client = SlackServiceClient()
        
    def process_email(self, email_id: str) -> bool:
        """Process a single email.
        
        Args:
            email_id: The ID of the email to process
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        return process_new_email(email_id)
        
    def on_new_email(self, history_id: str) -> None:
        """Handle a new email notification from PubSub.
        
        Args:
            history_id: The history ID from the notification
        """
        if not self.gmail_client:
            logger.error("Gmail client is not initialized.")
            return
            
        try:
            # Get history records
            history_response = self.gmail_client.get_history(history_id)
            if not history_response:
                logger.warning(f"No history found for history ID: {history_id}")
                return
                
            # Extract message IDs from history
            message_ids = []
            for history_record in history_response.get('history', []):
                for msg_added in history_record.get('messagesAdded', []):
                    msg_id = msg_added.get('message', {}).get('id')
                    if msg_id:
                        message_ids.append(msg_id)
                        
            # Process each message
            for msg_id in message_ids:
                self.process_email(msg_id)
                
        except Exception as e:
            logger.error(f"Error processing history {history_id}: {e}")

class EmailTriageApp:
    """Orchestrates the email triage workflow."""

    def __init__(self) -> None:
        logger.info("Initializing Email Triage Application...")
        try:
            self.gmail_client = GmailClient()
            self.ai_processor = AIProcessor()
            self.slack_client = SlackServiceClient()
            self.pubsub_listener = PubSubListener(
                project_id=GOOGLE_CLOUD_PROJECT_ID,
                subscription_id=GOOGLE_PUBSUB_SUBSCRIPTION_ID
            )
            self._running = True
            signal.signal(signal.SIGINT, self.shutdown)
            signal.signal(signal.SIGTERM, self.shutdown)
            logger.info("Email Triage Application initialized successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize EmailTriageApp: {e}", exc_info=True)
            sys.exit(1)

    def _handle_new_email_notification(self, history_id: str) -> None:
        """Callback function to handle new email notifications from Pub/Sub."""
        if not self._running:
            logger.info("Application is shutting down. Ignoring new email notification.")
            return

        logger.info(f"Received new email notification with History ID: {history_id}")
        if not self.gmail_client or not self.gmail_client.service:
            logger.error("Gmail client not available. Cannot process email.")
            return

        try:
            # Use history.list to get new messages since the last known historyId
            # This requires storing and updating the last historyId processed.
            # For simplicity, this example will fetch the most recent message if history.list is complex.
            # A more robust solution would be needed here.
            
            # Conceptual: Fetch new message IDs from history_id
            # This is a simplified approach. A robust implementation needs to handle history records properly.
            # It might involve listing history and extracting messageAdded events.
            history_response = self.gmail_client.service.users().history().list(
                userId=GMAIL_USER_ID, 
                startHistoryId=history_id,
                historyTypes=['messageAdded'] 
            ).execute()
            
            history_records = history_response.get('history', [])
            if not history_records:
                logger.info(f"No new message history found for history_id: {history_id}")
                # It might be that this history_id only contains other types of changes (e.g. label modifications)
                # or it's the very first history_id from watch setup with no prior messages.
                return

            message_ids_to_process: List[str] = []
            for record in history_records:
                messages_added = record.get('messagesAdded', [])
                for msg_added_info in messages_added:
                    msg_id = msg_added_info.get('message', {}).get('id')
                    if msg_id and msg_id not in message_ids_to_process: # Avoid duplicates from same batch
                        message_ids_to_process.append(msg_id)
            
            if not message_ids_to_process:
                logger.info(f"No new messages extracted from history for history_id: {history_id}")
                return

            logger.info(f"Extracted {len(message_ids_to_process)} new message ID(s) from history: {message_ids_to_process}")

            for message_id in message_ids_to_process:
                logger.info(f"Processing message ID: {message_id}")
                email_data: Optional[EmailData] = self.gmail_client.get_email_details(message_id)

                if not email_data:
                    logger.warning(f"Could not retrieve details for email ID: {message_id}. Skipping.")
                    continue

                logger.debug(f"Email data for {message_id}: Subject - '{email_data.get('subject')}'")

                analyzed_email: AnalyzedEmailData = self.ai_processor.process_email(email_data)
                logger.info(f"AI Analysis for {message_id}: Urgent - {analyzed_email['is_urgent']}, Summary - '{analyzed_email['summary'][:50]}...'")

                if analyzed_email['is_urgent']:
                    logger.info(f"Email {message_id} is urgent. Applying label and sending Slack notification.")
                    label_success = self.gmail_client.apply_urgent_label(message_id)
                    if label_success:
                        logger.info(f"Successfully applied urgent label to {message_id}.")
                    else:
                        logger.error(f"Failed to apply urgent label to {message_id}.")
                    
                    slack_success = self.slack_client.send_urgent_email_notification(analyzed_email)
                    if slack_success:
                        logger.info(f"Successfully sent Slack notification for {message_id}.")
                    else:
                        logger.error(f"Failed to send Slack notification for {message_id}.")
                else:
                    logger.info(f"Email {message_id} is not urgent. No further action.")
            
        except HttpError as e:
            logger.error(f"Gmail API error while processing history for {history_id}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to process email notification for History ID {history_id}: {e}", exc_info=True)

    def run(self) -> None:
        """Starts the email triage application.
        Sets up Gmail push notifications and starts the Pub/Sub listener.
        """
        if not self.gmail_client or not self.gmail_client.service:
            logger.critical("Gmail client is not initialized. Application cannot start.")
            return

        logger.info("Starting Email Triage Application workflow...")
        
        # 1. Setup Gmail Push Notifications
        # This should ideally be done once, or renewed periodically. 
        # For a long-running service, you might do this at startup.
        if self.gmail_client.setup_push_notifications():
            logger.info("Gmail push notifications set up successfully.")
        else:
            logger.error("Failed to set up Gmail push notifications. The application might not receive new emails.")
            # Depending on the desired robustness, you might choose to exit or try to periodically retry setup.
            # For now, we'll continue and let the listener try, but it likely won't get messages.

        # 2. Start Pub/Sub Listener
        # This will block until an error or KeyboardInterrupt
        try:
            self.pubsub_listener.start_listening(self._handle_new_email_notification)
        except Exception as e:
            logger.critical(f"Pub/Sub listener failed critically: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self) -> None:
        """Stops the application components gracefully."""
        if not self._running:
            return # Already stopping or stopped
        
        self._running = False
        logger.info("Shutting down Email Triage Application...")

        # Stop Pub/Sub listener (it should handle its own shutdown on future.cancel())
        # The listener's future.cancel() is called in its own exception/finally blocks.
        # We might not need explicit stop here if listener manages its lifecycle fully.
        # However, if the listener is in a separate thread not managed by future, you'd signal it.

        # Stop Gmail push notifications (optional, they expire anyway but good practice)
        if self.gmail_client and self.gmail_client.service:
            logger.info("Attempting to stop Gmail push notifications...")
            if self.gmail_client.stop_push_notifications():
                logger.info("Gmail push notifications stopped.")
            else:
                logger.warning("Failed to stop Gmail push notifications. They will expire automatically.")
        
        logger.info("Email Triage Application shut down complete.")
        sys.exit(0) # Clean exit

    def shutdown(self, signum, frame):
        """Signal handler for graceful shutdown."""
        logger.warning(f"Signal {signum} received, initiating shutdown...")
        self.stop()

if __name__ == "__main__":
    app = EmailTriageApp()
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user (KeyboardInterrupt).")
        app.stop()
    except Exception as e:
        logger.critical(f"Unhandled exception in main application run: {e}", exc_info=True)
        # Attempt a graceful shutdown if app object exists
        if 'app' in locals() and hasattr(app, 'stop'):
            app.stop()
        sys.exit(1) 