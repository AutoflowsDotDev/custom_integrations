"""Tests for metrics endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.app import app
from src.api.routers.metrics import (
    EMAILS_PROCESSED,
    GMAIL_REQUESTS,
    EMAIL_PROCESSING_TIME,
    SLACK_NOTIFICATIONS,
    AI_REQUESTS,
    ACTIVE_CONNECTIONS
)


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_api_key():
    """Mock API key for tests."""
    with patch('src.api.dependencies.api_settings') as mock_settings:
        mock_settings.API_KEY_NAME = "X-API-KEY"
        mock_settings.API_KEY = "test-api-key"
        yield "test-api-key"


def test_metrics_endpoint(test_client):
    """Test that metrics endpoint returns Prometheus metrics."""
    # Mock process collector to avoid bytes vs string error
    with patch('prometheus_client.process_collector.ProcessCollector.collect', return_value=[]), \
         patch('src.gmail_service.gmail_client.GmailClient.__init__', return_value=None), \
         patch('src.ai_service.ai_processor.AIProcessor.__init__', return_value=None), \
         patch('src.slack_service.slack_client.SlackServiceClient.__init__', return_value=None), \
         patch('src.api.dependencies.get_api_key', return_value="test-api-key"), \
         patch('src.api.dependencies.get_gmail_client', return_value=MagicMock()), \
         patch('src.api.dependencies.get_ai_processor', return_value=MagicMock()), \
         patch('src.api.dependencies.get_slack_client', return_value=MagicMock()):
        
        # Add some metrics
        EMAILS_PROCESSED.labels(status="success", is_urgent="true").inc()
        GMAIL_REQUESTS.labels(status="success").inc(2)
        EMAIL_PROCESSING_TIME.observe(1.5)
        SLACK_NOTIFICATIONS.labels(status="success").inc()
        AI_REQUESTS.labels(status="success").inc()
        ACTIVE_CONNECTIONS.set(5)
        
        response = test_client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        
        # Check for metric names in the response
        metric_text = response.text
        assert "emails_processed_total" in metric_text
        assert "gmail_requests_total" in metric_text
        assert "email_processing_seconds" in metric_text
        assert "slack_notifications_total" in metric_text
        assert "ai_requests_total" in metric_text
        assert "active_connections" in metric_text 