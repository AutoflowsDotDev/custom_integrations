from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest
)

router = APIRouter(tags=["metrics"])

# Define metrics
EMAILS_PROCESSED = Counter(
    "emails_processed_total",
    "Total number of emails processed",
    ["status", "is_urgent"]
)

EMAIL_PROCESSING_TIME = Histogram(
    "email_processing_seconds",
    "Time spent processing emails",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
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
    "Number of active connections"
)

@router.get("/metrics")
async def metrics():
    """
    Expose Prometheus metrics.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST) 