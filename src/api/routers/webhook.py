import json
import base64
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Any, Dict

from src.api.models import ProcessHistoryResponse
from src.api.dependencies import (
    get_api_key,
    get_gmail_client,
    get_ai_processor,
    get_slack_client
)
from src.api.routers.email import process_history
from src.api.routers.metrics import GMAIL_REQUESTS
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/webhook",
    tags=["webhook"]
)

@router.post(
    "/pubsub", 
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive Gmail PubSub push notification",
    description="Handle PubSub push notification from Gmail watch"
)
async def pubsub_push(
    request: Request,
    gmail_client = Depends(get_gmail_client),
    ai_processor = Depends(get_ai_processor),
    slack_client = Depends(get_slack_client)
):
    """
    Handle PubSub push notification from Gmail watch.
    This endpoint receives push notifications from Google Cloud Pub/Sub
    when changes occur in the Gmail mailbox.
    """
    try:
        # Get request body
        payload = await request.json()
        logger.info(f"Received PubSub push notification: {payload}")
        
        # Extract and decode message data
        if "message" not in payload:
            logger.error("Invalid PubSub notification: 'message' not found in payload")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PubSub notification"
            )
        
        message = payload["message"]
        if "data" not in message:
            logger.error("Invalid PubSub message: 'data' not found in message")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PubSub message"
            )
        
        # Decode base64 encoded message data
        data_encoded = message["data"]
        try:
            data_decoded = base64.b64decode(data_encoded).decode("utf-8")
            data = json.loads(data_decoded)
        except Exception as e:
            logger.error(f"Error decoding message data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error decoding message data"
            )
        
        logger.info(f"Decoded PubSub message data: {data}")
        
        # Extract historyId from data
        if "historyId" not in data:
            logger.error("historyId not found in message data")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="historyId not found in message data"
            )
        
        history_id = data["historyId"]
        logger.info(f"Processing history ID: {history_id}")
        
        # Process history using the existing endpoint logic
        from src.api.models import ProcessHistoryRequest
        history_request = ProcessHistoryRequest(history_id=history_id)
        response = await process_history(
            request=history_request,
            gmail_client=gmail_client,
            ai_processor=ai_processor,
            slack_client=slack_client
        )
        
        return {"status": "success", "message": "PubSub notification processed successfully"}
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing request body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )
    except KeyError as e:
        logger.error(f"Missing required field in request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required field: {str(e)}"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error processing PubSub notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        ) 