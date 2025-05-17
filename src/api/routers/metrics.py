from fastapi import APIRouter, Depends, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest
)

from src.api.dependencies import get_api_key

# Define metrics
EMAILS_PROCESSED = Counter(
    "emails_processed_total",
    "Total number of emails processed",
    ["status", "is_urgent"]
)

EMAIL_PROCESSING_TIME = Histogram(
    "email_processing_seconds",
    "Time taken to process emails",
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf'))
)

GMAIL_REQUESTS = Counter(
    "gmail_requests_total",
    "Total number of Gmail API requests",
    ["status"]
)

SLACK_NOTIFICATIONS = Counter(
    "slack_notifications_total",
    "Total number of Slack notifications sent",
    ["status"]
)

AI_REQUESTS = Counter(
    "ai_requests_total",
    "Total number of AI service requests",
    ["status"]
)

ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Number of active connections to the API"
)

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    dependencies=[Depends(get_api_key)]
)

@router.get("", summary="Get Prometheus metrics")
async def get_metrics():
    """Return Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST) 