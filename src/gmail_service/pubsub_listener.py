import json
import base64
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import Callable, Optional
import os

from google.cloud import pubsub_v1
from google.oauth2.service_account import Credentials as ServiceAccountCredentials # For PubSub

from src.core.config import (
    GOOGLE_CLOUD_PROJECT_ID,
    GOOGLE_PUBSUB_SUBSCRIPTION_ID,
    # GOOGLE_APPLICATION_CREDENTIALS # Assuming this is set in environment for pubsub client
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PubSubListener:
    """Listens to a Google Cloud Pub/Sub subscription for Gmail notifications."""

    def __init__(self, project_id: str, subscription_id: str):
        self.project_id = project_id
        self.subscription_id = subscription_id
        # TODO: Explore if specific credentials needed or if GOOGLE_APPLICATION_CREDENTIALS is enough
        # If running in an environment where ADC (Application Default Credentials) is configured
        # (e.g., on Google Cloud services like GCE, GKE, Cloud Functions), 
        # explicitly passing credentials might not be necessary for the Pub/Sub client.
        # credentials = ServiceAccountCredentials.from_service_account_file(SERVICE_ACCOUNT_KEY_PATH)
        # self.subscriber_client = pubsub_v1.SubscriberClient(credentials=credentials)
        self.subscriber_client = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber_client.subscription_path(
            self.project_id, self.subscription_id
        )

    def _process_payload(self, message: pubsub_v1.types.ReceivedMessage) -> Optional[str]:
        """Processes the Pub/Sub message payload to extract the Gmail message ID."""
        try:
            # The actual message from Gmail is in the 'data' field, Base64-encoded JSON.
            # It contains emailAddress and historyId.
            # We are interested in the new emails, which typically means processing history records
            # or directly getting message IDs if the notification format allows.
            # For `watch` on `users`, the notification data is a JSON string:
            # { "emailAddress": "user@example.com", "historyId": "1234567890" }
            
            notification_data_str = message.data.decode("utf-8")
            logger.debug(f"Received raw Pub/Sub message data: {notification_data_str}")
            
            notification_payload = json.loads(notification_data_str)
            email_address = notification_payload.get("emailAddress")
            history_id = notification_payload.get("historyId")

            if not email_address or not history_id:
                logger.warning(f"Received Pub/Sub message without emailAddress or historyId: {notification_payload}")
                return None

            logger.info(f"Received notification for {email_address} with history ID: {history_id}")
            
            # IMPORTANT: The push notification from users.watch() gives a historyId.
            # You need to use users.history.list with this historyId to find new messageIds.
            # This is a simplification for now, assuming a more direct way or that the callback
            # will handle history processing to get individual message IDs.
            # For the purpose of this listener, we might not have the message ID directly.
            # The calling code (e.g., the main workflow) will need to use the historyId
            # with the Gmail API to get new message IDs.
            # However, if the Pub/Sub message *was* a direct message_id (e.g. from a different setup),
            # this is where you'd extract it. For now, we pass the historyId.
            
            # Returning historyId for further processing by GmailClient. 
            # The orchestrator will call a method like `gmail_client.get_new_messages_from_history(history_id)`
            return history_id 

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode Pub/Sub message data: {message.data}. Error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing Pub/Sub message: {e}")
            return None

    def start_listening(self, callback: Callable[[str], None]) -> None:
        """Starts listening for messages and calls the callback with the history ID."""
        
        def message_handler(message: pubsub_v1.types.ReceivedMessage) -> None:
            logger.info(f"Received Pub/Sub message ID: {message.message_id}")
            history_id = self._process_payload(message)
            if history_id:
                try:
                    callback(history_id) # Pass history_id to the main processing logic
                    message.ack() # Acknowledge after successful processing by callback
                    logger.info(f"Acknowledged Pub/Sub message for history_id: {history_id}")
                except Exception as e:
                    logger.error(f"Callback failed for history_id {history_id}: {e}. Message will be nacked.")
                    message.nack() # Negative acknowledgment
            else:
                logger.warning(f"No valid history_id extracted from message {message.message_id}. Acknowledging to remove from queue.")
                message.ack() # Acknowledge even if payload is bad to prevent re-delivery loops

        streaming_pull_future = self.subscriber_client.subscribe(
            self.subscription_path, callback=message_handler
        )
        logger.info(f"Listening for messages on {self.subscription_path}...")

        try:
            # Keep the main thread alive while the subscriber is running in background threads.
            # Timeout can be set, or it can run indefinitely.
            streaming_pull_future.result() # Blocking call, add timeout if needed for graceful shutdown
        except FuturesTimeoutError:
            logger.info("Listening timeout reached.")
            streaming_pull_future.cancel()
            streaming_pull_future.result() # Block until the shutdown is complete
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt detected. Shutting down listener...")
            streaming_pull_future.cancel()
            streaming_pull_future.result() # Ensure graceful shutdown
        except Exception as e:
            logger.error(f"An unexpected error occurred in the listener: {e}")
            streaming_pull_future.cancel()
            streaming_pull_future.result() # Ensure graceful shutdown
        finally:
            self.subscriber_client.close()
            logger.info("Pub/Sub listener shut down.")

# Example usage (for testing - requires a Pub/Sub subscription to be set up and messages published)
def _test_callback(history_id: str):
    print(f"Test Callback: Received history ID: {history_id}")
    # In a real scenario, this callback would trigger email fetching and AI processing.

if __name__ == '__main__':
    # Ensure GOOGLE_APPLICATION_CREDENTIALS is set in your environment
    # pointing to your service account key JSON file that has Pub/Sub Subscriber role.
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
        print("Please set it to the path of your GCP service account key JSON file.")
    else:
        print(f"Using GCP credentials from: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        listener = PubSubListener(
            project_id=GOOGLE_CLOUD_PROJECT_ID,
            subscription_id=GOOGLE_PUBSUB_SUBSCRIPTION_ID
        )
        print(f"Attempting to listen on project '{GOOGLE_CLOUD_PROJECT_ID}' subscription '{GOOGLE_PUBSUB_SUBSCRIPTION_ID}'")
        try:
            listener.start_listening(_test_callback)
        except Exception as e:
            print(f"Failed to start listener: {e}") 