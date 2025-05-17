import os.path
import base64
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from src.core.config import (
    GOOGLE_CLIENT_SECRETS_JSON_PATH,
    GOOGLE_CREDENTIALS_JSON_PATH,
    GOOGLE_SERVICE_ACCOUNT_PATH,
    GMAIL_USER_ID,
    GMAIL_LABEL_URGENT,
    GOOGLE_PUBSUB_TOPIC_ID,
    GOOGLE_CLOUD_PROJECT_ID
)
from src.core.types import EmailData
from src.utils.logger import get_logger
from src.utils.exceptions import (
    GmailServiceError,
    GmailAuthenticationError,
    GmailAPIError,
    MessageProcessingError
)

logger = get_logger(__name__)

# If modifying these SCOPES, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly', # Read emails
    'https://www.googleapis.com/auth/gmail.modify',   # Modify emails (e.g., add labels)
    'https://www.googleapis.com/auth/pubsub'          # For Pub/Sub push notifications
]

class GmailClient:
    """Handles interactions with the Gmail API."""
    def __init__(self) -> None:
        # Check for service account first, otherwise fall back to OAuth
        self.service: Optional[Resource] = self._get_service_account_gmail_service() or self._get_oauth_gmail_service()
        self.urgent_label_id: Optional[str] = None
        if self.service:
            self.urgent_label_id = self._get_or_create_label(GMAIL_LABEL_URGENT)

    def _get_service_account_gmail_service(self) -> Optional[Resource]:
        """Authenticates using a service account and returns the Gmail API service client.
        This is the recommended approach for server deployments.
        """
        if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_PATH):
            logger.info(f"Service account file not found at: {GOOGLE_SERVICE_ACCOUNT_PATH}. Will try OAuth flow.")
            return None

        try:
            # Create credentials for delegated user using service account
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_PATH,
                scopes=SCOPES
            )
            
            # Important: The service account must have domain-wide delegation enabled
            # and be granted access to impersonate users in your organization
            delegated_credentials = credentials.with_subject(GMAIL_USER_ID)
            
            # Build the Gmail service
            service = build('gmail', 'v1', credentials=delegated_credentials)
            logger.info("Gmail API service built successfully using service account authentication.")
            return service
        except FileNotFoundError as e:
            error_msg = f"Service account file not found: {e}"
            logger.error(error_msg)
            raise GmailAuthenticationError(error_msg) from e
        except PermissionError as e:
            error_msg = f"Permission error accessing service account file: {e}"
            logger.error(error_msg)
            raise GmailAuthenticationError(error_msg) from e
        except HttpError as e:
            error_msg = f"Gmail API HTTP error during service account auth: {e}"
            logger.error(error_msg)
            raise GmailAPIError(error_msg) from e
        except Exception as e:
            error_msg = f"Error authenticating with service account: {e}"
            logger.error(error_msg)
            raise GmailAuthenticationError(error_msg) from e

    def _get_oauth_gmail_service(self) -> Optional[Resource]:
        """Authenticates using OAuth user flow and returns the Gmail API service client.
        This is less secure for server deployments but useful for desktop applications.
        """
        creds = None
        if os.path.exists(GOOGLE_CREDENTIALS_JSON_PATH):
            try:
                creds = Credentials.from_authorized_user_file(GOOGLE_CREDENTIALS_JSON_PATH, SCOPES)
            except Exception as e:
                logger.error(f"Failed to load credentials from {GOOGLE_CREDENTIALS_JSON_PATH}: {e}")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None # Force re-authentication
            else:
                if not os.path.exists(GOOGLE_CLIENT_SECRETS_JSON_PATH):
                    logger.error(f"Client secrets file not found at: {GOOGLE_CLIENT_SECRETS_JSON_PATH}")
                    logger.error("Please download it from Google Cloud Console and place it correctly.")
                    return None
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        GOOGLE_CLIENT_SECRETS_JSON_PATH, SCOPES)
                    # Ensure the redirect_uri is http://localhost:port for installed apps
                    # For server-side apps, you might need a different flow or configuration
                    creds = flow.run_local_server(port=0) 
                except Exception as e:
                    logger.error(f"Failed to run OAuth flow: {e}")
                    return None
            
            if creds:
                try:
                    with open(GOOGLE_CREDENTIALS_JSON_PATH, 'w') as token_file:
                        token_file.write(creds.to_json())
                    logger.info(f"Credentials saved to {GOOGLE_CREDENTIALS_JSON_PATH}")
                except Exception as e:
                    logger.error(f"Failed to save credentials to {GOOGLE_CREDENTIALS_JSON_PATH}: {e}")
        
        if not creds:
            logger.error("Failed to obtain valid credentials.")
            return None

        try:
            service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API service built successfully.")
            return service
        except HttpError as error:
            logger.error(f'An API error occurred: {error}')
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while building Gmail service: {e}")
            return None

    def _get_or_create_label(self, label_name: str) -> Optional[str]:
        """Gets the ID of a label by name, creating it if it doesn't exist."""
        if not self.service:
            return None
        try:
            results = self.service.users().labels().list(userId=GMAIL_USER_ID).execute()
            labels = results.get('labels', [])
            for label in labels:
                if label['name'] == label_name:
                    logger.info(f"Label '{label_name}' found with ID: {label['id']}")
                    return label['id']
            
            # Label not found, create it
            label_body = {'name': label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
            created_label = self.service.users().labels().create(userId=GMAIL_USER_ID, body=label_body).execute()
            logger.info(f"Label '{label_name}' created with ID: {created_label['id']}")
            return created_label['id']
        except HttpError as error:
            logger.error(f"An API error occurred while getting/creating label '{label_name}': {error}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with label '{label_name}': {e}")
            return None

        def get_email_details(self, message_id: str) -> Optional[EmailData]:        """Fetches details of a specific email."""        if not self.service:            error_msg = "Gmail service is not initialized"            logger.error(error_msg)            raise GmailServiceError(error_msg)                    try:            # Requesting full format to get all parts, including plain text and HTML            # Also requesting headers to extract sender, subject, and date            message = self.service.users().messages().get(userId=GMAIL_USER_ID, id=message_id, format='full').execute()                        payload = message.get('payload', {})            headers = payload.get('headers', [])                        subject = None            sender = None            date_str = None            for header in headers:                name = header.get('name', '').lower()                if name == 'subject':                    subject = header.get('value')                elif name == 'from':                    sender = header.get('value')                elif name == 'date':                    date_str = header.get('value')                        # Parse date string to datetime object (simplified, robust parsing might be needed)            try:                # Example: "Wed, 5 Jun 2024 10:30:00 +0000 (UTC)" or similar                # This parsing is basic. For robustness, consider `dateutil.parser`                if date_str:                    received_timestamp = datetime.strptime(date_str.split(' (')[0], '%a, %d %b %Y %H:%M:%S %z')                else:                    received_timestamp = datetime.now(timezone.utc)            except (ValueError, TypeError) as e:                logger.warning(f"Could not parse date string '{date_str}': {e}. Using current UTC time.")                received_timestamp = datetime.now(timezone.utc)            body_plain: Optional[str] = None            body_html: Optional[str] = None            parts = payload.get('parts', [])            if parts:                for part in parts:                    mime_type = part.get('mimeType', '')                    if mime_type == 'text/plain':                        data = part.get('body', {}).get('data')                        if data:                            body_plain = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')                    elif mime_type == 'text/html':                        data = part.get('body', {}).get('data')                        if data:                            body_html = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')                    if body_plain and body_html: # Prefer plain if both found early                        break             else: # No parts, body might be directly in payload                data = payload.get('body', {}).get('data')                mime_type = payload.get('mimeType', '')                if data:                    decoded_data = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')                    if mime_type == 'text/plain':                        body_plain = decoded_data                    elif mime_type == 'text/html':                        body_html = decoded_data                        # Fallback if specific content types not found but there is some primary body            if not body_plain and not body_html and payload.get('body',{}).get('data'):                data = payload.get('body',{}).get('data')                body_plain = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')                logger.info(f"Using main payload body for message {message_id} as plain text was not explicitly found.")            email_data: EmailData = {                'id': message.get('id', message_id),                'thread_id': message.get('threadId', ''),                'subject': subject,                'sender': sender,                'body_plain': body_plain,                'body_html': body_html,                'received_timestamp': received_timestamp,                'snippet': message.get('snippet')            }            return email_data        except HttpError as e:            error_msg = f'Gmail API error occurred while fetching email {message_id}: {e}'            logger.error(error_msg)            raise GmailAPIError(error_msg) from e        except ValueError as e:            error_msg = f"Value error processing email {message_id}: {e}"            logger.error(error_msg)            raise MessageProcessingError(error_msg) from e        except Exception as e:            error_msg = f"Unexpected error fetching email {message_id}: {e}"            logger.error(error_msg)            raise MessageProcessingError(error_msg) from e

    def apply_urgent_label(self, message_id: str) -> bool:
        """Applies the 'URGENT_AI' label to a message."""
        if not self.service or not self.urgent_label_id:
            logger.error("Service or urgent_label_id not initialized.")
            return False
        try:
            modify_request = {
                'addLabelIds': [self.urgent_label_id],
                'removeLabelIds': []
            }
            self.service.users().messages().modify(
                userId=GMAIL_USER_ID, id=message_id, body=modify_request).execute()
            logger.info(f"Applied urgent label to message {message_id}")
            return True
        except HttpError as error:
            logger.error(f'An API error occurred while applying label to {message_id}: {error}')
            return False
        except Exception as e:
            logger.error(f"Unexpected error applying label to {message_id}: {e}")
            return False

    def setup_push_notifications(self) -> bool:
        """Sets up push notifications for new emails using Google Cloud Pub/Sub."""
        if not self.service:
            logger.error("Gmail service not initialized. Cannot set up push notifications.")
            return False
        
        # Construct the full topic name – fetch the *current* environment variables
        # in case they have been altered at runtime (e.g., within unit tests).
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID", GOOGLE_CLOUD_PROJECT_ID)
        topic_id = os.getenv("GOOGLE_PUBSUB_TOPIC_ID", GOOGLE_PUBSUB_TOPIC_ID)

        topic_name = f"projects/{project_id}/topics/{topic_id}"
        
        watch_request = {
            'labelIds': ['INBOX'],  # Only watch for new emails in the INBOX
            'topicName': topic_name
        }
        
        try:
            # Check if a watch is already active on the topic to avoid duplicates, or stop existing one.
            # Gmail API docs mention that calling watch() again on the same topic effectively renews it.
            response = self.service.users().watch(userId=GMAIL_USER_ID, body=watch_request).execute()
            logger.info(f"Successfully set up watch on topic {topic_name}. History ID: {response.get('historyId')}")
            logger.info(f"Notifications will expire on: {datetime.fromtimestamp(int(response.get('expiration')) / 1000)}")
            return True
        except HttpError as error:
            logger.error(f'An API error occurred while setting up push notifications: {error}')
            # Common error: Topic not found or permissions issue.
            # Ensure the Gmail service account has Pub/Sub Publisher role on the topic, 
            # and the Pub/Sub topic exists in the specified project.
            # Also ensure the domain is verified for push notifications if using a service account from a different domain.
            if error.resp.status == 400 and 'topicName Leasing Not Enabled' in str(error.content):
                logger.error("Error: Topic leasing not enabled. This might be a permission issue or the topic doesn't exist.")
            elif error.resp.status == 403:
                 logger.error("Error: 403 Forbidden. Ensure the service account has permissions for Pub/Sub and Gmail API is enabled.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during push notification setup: {e}")
            return False

    def stop_push_notifications(self) -> bool:
        """Stops push notifications for the user's mailbox."""
        if not self.service:
            logger.error("Gmail service not initialized. Cannot stop push notifications.")
            return False
        try:
            self.service.users().stop(userId=GMAIL_USER_ID).execute()
            logger.info("Successfully stopped push notifications.")
            return True
        except HttpError as error:
            logger.error(f'An API error occurred while stopping push notifications: {error}')
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while stopping push notifications: {e}")
            return False

    def get_history(self, history_id: str) -> Optional[Dict[str, Any]]:
        """Get email history starting from the specified history ID.
        
        Args:
            history_id: The ID to start the history from
            
        Returns:
            A dictionary containing the history information, or None if an error occurred
        """
        if not self.service:
            logger.error("Gmail service not initialized. Cannot get history.")
            return None
            
        try:
            history_response = self.service.users().history().list(
                userId=GMAIL_USER_ID,
                startHistoryId=history_id,
                historyTypes=['messageAdded']
            ).execute()
            
            return history_response
        except HttpError as error:
            logger.error(f"An API error occurred while getting history for ID {history_id}: {error}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting history for ID {history_id}: {e}")
            return None

# Example Usage (for testing purposes)
if __name__ == '__main__':
    gmail_client = GmailClient()
    if gmail_client.service:
        logger.info(f"Urgent label ID: {gmail_client.urgent_label_id}")
        
        # 1. Test setting up push notifications
        # print("\nAttempting to set up push notifications...")
        # if gmail_client.setup_push_notifications():
        #     print("Push notifications set up successfully.")
        # else:
        #     print("Failed to set up push notifications.")

        # 2. To test fetching an email, you'll need a message ID from your inbox.
        #    You can list messages first (not implemented here to keep it focused).
        # test_message_id = 'YOUR_TEST_MESSAGE_ID' 
        # if test_message_id != 'YOUR_TEST_MESSAGE_ID':
        #     print(f"\nFetching email with ID: {test_message_id}...")
        #     email = gmail_client.get_email_details(test_message_id)
        #     if email:
        #         print(f"Subject: {email.get('subject')}")
        #         print(f"Sender: {email.get('sender')}")
        #         print(f"Body (plain): {email.get('body_plain', '')[:200]}...")
        #         # 3. Test applying a label
        #         print(f"\nApplying urgent label to {test_message_id}...")
        #         if gmail_client.apply_urgent_label(test_message_id):
        #             print("Urgent label applied.")
        #         else:
        #             print("Failed to apply urgent label.")
        #     else:
        #         print("Failed to fetch email.")
        # else:
        # print("Skipping email fetch/label test as no message ID was provided.")

        # 4. Test stopping push notifications
        # print("\nAttempting to stop push notifications...")
        # if gmail_client.stop_push_notifications():
        #     print("Push notifications stopped successfully.")
        # else:
        #     print("Failed to stop push notifications.")
    else:
        logger.error("Gmail client service could not be initialized.") 