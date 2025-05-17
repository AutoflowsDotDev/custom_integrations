import time
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from src.api.models import (
    EmailProcessRequest,
    EmailProcessResponse,
    ProcessHistoryRequest,
    ProcessHistoryResponse
)
from src.api.dependencies import (
    get_api_key,
    get_gmail_client,
    get_ai_processor,
    get_slack_client
)
from src.api.routers.metrics import (
    EMAILS_PROCESSED,
    EMAIL_PROCESSING_TIME,
    GMAIL_REQUESTS,
    SLACK_NOTIFICATIONS,
    AI_REQUESTS
)
from src.utils.exceptions import (
    GmailServiceError,
    AIServiceError,
    SlackServiceError,
    EmailTriageError,
    GmailAPIError,
    MessageProcessingError
)
from src.utils.logger import get_logger
from src.gmail_service.gmail_client import GmailClient
from src.ai_service.ai_processor import AIProcessor
from src.slack_service.slack_client import SlackServiceClient
from src.core.config import GMAIL_USER_ID

logger = get_logger(__name__)

router = APIRouter(
    prefix="/emails",
    tags=["emails"],
    dependencies=[Depends(get_api_key)]
)

@router.post(
    "/process", 
    response_model=EmailProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process a single email",
    description="Process a single email by ID and perform AI analysis and actions"
)
async def process_email(
    request: EmailProcessRequest,
    gmail_client: GmailClient = Depends(get_gmail_client),
    ai_processor: AIProcessor = Depends(get_ai_processor),
    slack_client: SlackServiceClient = Depends(get_slack_client)
):
    """
    Process a single email by ID.
    """
    email_id = request.email_id
    logger.info(f"API request to process email ID: {email_id}")
    
    start_time = time.time()
    try:
        # Get email details
        logger.set_step("get_email_details")
        GMAIL_REQUESTS.labels(status="started").inc()
        email_data = gmail_client.get_email_details(email_id)
        GMAIL_REQUESTS.labels(status="success").inc()
        
        if not email_data:
            EMAILS_PROCESSED.labels(status="failed", is_urgent="unknown").inc()
            logger.warning(f"Could not retrieve details for email ID: {email_id}")
            return EmailProcessResponse(
                success=False,
                email_id=email_id,
                message="Email not found or could not be retrieved"
            )
        
        # Analyze the email
        logger.set_step("analyze_email")
        AI_REQUESTS.labels(status="started").inc()
        analyzed_email = ai_processor.process_email(email_data)
        AI_REQUESTS.labels(status="success").inc()
        
        is_urgent = analyzed_email.get('is_urgent', False)
        
        # If urgent, apply label and send notification
        if is_urgent:
            logger.set_step("handle_urgent_email")
            
            # Apply urgent label
            GMAIL_REQUESTS.labels(status="started").inc()
            gmail_client.apply_urgent_label(email_id)
            GMAIL_REQUESTS.labels(status="success").inc()
            
            # Send Slack notification
            SLACK_NOTIFICATIONS.labels(status="started").inc()
            slack_client.send_urgent_email_notification(analyzed_email)
            SLACK_NOTIFICATIONS.labels(status="success").inc()
            
            logger.info(f"Email {email_id} processed as urgent")
            EMAILS_PROCESSED.labels(status="success", is_urgent="true").inc()
        else:
            logger.info(f"Email {email_id} processed as non-urgent")
            EMAILS_PROCESSED.labels(status="success", is_urgent="false").inc()
        
        processing_time = time.time() - start_time
        EMAIL_PROCESSING_TIME.observe(processing_time)
        
        return EmailProcessResponse(
            success=True,
            email_id=email_id,
            is_urgent=is_urgent,
            message=f"Email processed successfully in {processing_time:.2f} seconds"
        )
    
    except GmailServiceError as e:
        GMAIL_REQUESTS.labels(status="error").inc()
        EMAILS_PROCESSED.labels(status="failed", is_urgent="unknown").inc()
        logger.error(f"Gmail service error while processing email {email_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gmail service error: {str(e)}"
        )
    except AIServiceError as e:
        AI_REQUESTS.labels(status="error").inc()
        EMAILS_PROCESSED.labels(status="failed", is_urgent="unknown").inc()
        logger.error(f"AI service error while processing email {email_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}"
        )
    except SlackServiceError as e:
        SLACK_NOTIFICATIONS.labels(status="error").inc()
        EMAILS_PROCESSED.labels(status="failed", is_urgent="true").inc()
        logger.error(f"Slack service error while processing email {email_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Slack service error: {str(e)}"
        )
    except EmailTriageError as e:
        EMAILS_PROCESSED.labels(status="failed", is_urgent="unknown").inc()
        logger.error(f"Email triage error while processing email {email_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email processing error: {str(e)}"
        )
    except Exception as e:
        EMAILS_PROCESSED.labels(status="failed", is_urgent="unknown").inc()
        logger.error(f"Unexpected error processing email {email_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the email"
        )

@router.post(
    "/history", 
    response_model=ProcessHistoryResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process Gmail history",
    description="Process Gmail history updates and handle new emails"
)
async def process_history(
    request: ProcessHistoryRequest,
    gmail_client: GmailClient = Depends(get_gmail_client),
    ai_processor: AIProcessor = Depends(get_ai_processor),
    slack_client: SlackServiceClient = Depends(get_slack_client)
):
    """
    Process Gmail history updates.
    """
    history_id = request.history_id
    logger.info(f"API request to process Gmail history ID: {history_id}")
    
    try:
        # Get history records
        logger.set_step("get_history_records")
        GMAIL_REQUESTS.labels(status="started").inc()
        history_response = gmail_client.get_history(history_id)
        GMAIL_REQUESTS.labels(status="success").inc()
        
        if not history_response:
            logger.warning(f"No history found for history ID: {history_id}")
            return ProcessHistoryResponse(
                success=True,
                history_id=history_id,
                processed_emails=0,
                message="No history records found for the provided ID"
            )
        
        # Extract message IDs from history
        logger.set_step("extract_message_ids")
        message_ids = []
        for history_record in history_response.get('history', []):
            for msg_added in history_record.get('messagesAdded', []):
                msg_id = msg_added.get('message', {}).get('id')
                if msg_id and msg_id not in message_ids:  # Avoid duplicates
                    message_ids.append(msg_id)
        
        logger.info(f"Extracted {len(message_ids)} message ID(s) from history")
        
        # Process each message
        processed_count = 0
        logger.set_step("process_messages")
        for msg_id in message_ids:
            try:
                # Similar processing logic as in process_email endpoint
                email_data = gmail_client.get_email_details(msg_id)
                if not email_data:
                    continue
                
                analyzed_email = ai_processor.process_email(email_data)
                
                if analyzed_email.get('is_urgent', False):
                    gmail_client.apply_urgent_label(msg_id)
                    slack_client.send_urgent_email_notification(analyzed_email)
                    EMAILS_PROCESSED.labels(status="success", is_urgent="true").inc()
                else:
                    EMAILS_PROCESSED.labels(status="success", is_urgent="false").inc()
                
                processed_count += 1
            except (GmailServiceError, AIServiceError, SlackServiceError) as e:
                logger.error(f"Service error processing message {msg_id}: {e}")
                EMAILS_PROCESSED.labels(status="failed", is_urgent="unknown").inc()
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing message {msg_id}: {e}", exc_info=True)
                EMAILS_PROCESSED.labels(status="failed", is_urgent="unknown").inc()
                continue
        
        response_message = f"Processed {processed_count} emails from history update"
        if processed_count == 0 and not message_ids: # Check if no messages were even found to process
            # If history_response was valid but yielded no new message_ids from the start
            if history_response and not history_response.get('history'):
                 response_message = "No new messages found in history records."
            elif not history_response : # if get_history returned None or empty from the start
                 response_message = "No history records found for the provided ID or no new messages."
            # If message_ids were initially present but all failed to process, the original message is fine
            # however, if there were no message_ids to begin with, it means no new messages.
            elif not message_ids: # This covers the case where history was processed, but no messages were added.
                response_message = "No new messages found to process."


        return ProcessHistoryResponse(
            success=True,
            history_id=history_id,
            processed_emails=processed_count,
            message=response_message
        )
    
    except GmailAPIError as e:
        GMAIL_REQUESTS.labels(status="error").inc()
        logger.error(f"Gmail API error while processing history {history_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gmail API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error processing history {history_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the history"
        ) 