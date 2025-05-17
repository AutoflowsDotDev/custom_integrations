"""Tests for the main FastAPI application."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.app import app, create_app


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


def test_app_creation():
    """Test that the app is created correctly."""
    with patch('src.core.config.validate_config'):
        test_app = create_app()
        assert test_app is not None
        assert test_app.title == "Email Triage API"
        # Check that routers are included
        routes = [route.path for route in test_app.routes]
        assert "/api/v1/health" in routes
        assert "/api/v1/metrics" in routes
        assert "/api/v1/emails/process" in routes
        assert "/api/v1/emails/history" in routes
        assert "/api/v1/webhook/pubsub" in routes


def test_app_creation_with_error():
    """Test that app creation handles errors correctly."""
    with patch('src.core.config.validate_config', side_effect=Exception("Test error")), \
         pytest.raises(Exception) as excinfo:
        create_app()
    assert "Test error" in str(excinfo.value)


def test_root_endpoint(test_client):
    """Test the root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "online"
    assert "service" in data
    assert "version" in data
    assert "hostname" in data
    assert "environment" in data
    assert "documentation" in data


def test_docs_endpoint(test_client):
    """Test the docs endpoint."""
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"):
        response = test_client.get("/api/v1/docs")
        assert response.status_code == 200
        content_type = response.headers.get("content-type")
        assert "text/html" in content_type
        # Check for swagger UI content
        html_content = response.text
        assert "swagger-ui" in html_content


def test_redoc_endpoint(test_client):
    """Test the redoc endpoint."""
    with patch('src.api.dependencies.get_api_key', return_value="test-api-key"):
        response = test_client.get("/api/v1/redoc")
        assert response.status_code == 200
        content_type = response.headers.get("content-type")
        assert "text/html" in content_type
        # Check for redoc content
        html_content = response.text
        assert "redoc" in html_content


def test_openapi_schema(test_client):
    """Test the OpenAPI schema endpoint."""
    response = test_client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    
    # Check that our endpoints are in the schema
    paths = schema["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/metrics" in paths
    assert "/api/v1/emails/process" in paths
    assert "/api/v1/emails/history" in paths
    assert "/api/v1/webhook/pubsub" in paths


def test_middleware_process_time_header(test_client):
    """Test that the middleware adds X-Process-Time header."""
    response = test_client.get("/")
    assert "x-process-time" in response.headers
    
    # X-Process-Time should be a float
    process_time = float(response.headers["x-process-time"])
    assert process_time >= 0 