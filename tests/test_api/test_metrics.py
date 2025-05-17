"""Tests for the metrics API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.api.app import app
from src.api.routers.metrics import (
    EMAILS_PROCESSED,
    EMAIL_PROCESSING_TIME,
    GMAIL_REQUESTS,
    SLACK_NOTIFICATIONS,
    AI_REQUESTS,
    ACTIVE_CONNECTIONS
)


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


def test_metrics_endpoint(test_client):
    """Test that metrics endpoint returns Prometheus metrics."""
    # Add some metrics
    EMAILS_PROCESSED.labels(status="success", is_urgent="true").inc()
    GMAIL_REQUESTS.labels(status="success").inc(2)
    EMAIL_PROCESSING_TIME.observe(1.5)
    SLACK_NOTIFICATIONS.labels(status="success").inc()
    AI_REQUESTS.labels(status="success").inc()
    ACTIVE_CONNECTIONS.set(5)
    
    response = test_client.get("/api/v1/metrics")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    
    # Check for metric presence in response text
    metrics_text = response.text
    assert "emails_processed_total" in metrics_text
    assert "email_processing_seconds" in metrics_text
    assert "gmail_requests_total" in metrics_text
    assert "slack_notifications_total" in metrics_text
    assert "ai_requests_total" in metrics_text
    assert "active_connections" in metrics_text 