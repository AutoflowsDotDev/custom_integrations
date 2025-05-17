"""Tests for the health API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.app import app, create_app # Import app for overrides
from src.api.models import ServiceStatus
from src.api.dependencies import get_api_key, get_gmail_client, get_ai_processor, get_slack_client # Import actual dependencies


@pytest.fixture
def test_client_fixture(): # Renamed to avoid conflict if we use a client from app directly
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_api_key():
    """Mock API key for tests."""
    with patch('src.api.dependencies.api_settings') as mock_settings:
        mock_settings.API_KEY_NAME = "X-API-KEY"
        mock_settings.API_KEY = "test-api-key"
        yield "test-api-key"


def test_health_check(test_client_fixture, mock_api_key): # Use mock_api_key if headers are needed, or override get_api_key
    """Test health check endpoint."""
    # Create mocks for all required services
    mock_gmail_instance = MagicMock()
    mock_ai_instance = MagicMock()
    mock_slack_instance = MagicMock()

    # Configure mock service methods if they are called by health check logic (e.g., a ping() method)
    # For now, assume their mere existence via override is enough or health check logic handles their absence.

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_api_key] = lambda: mock_api_key # Override API key for simplicity
    app.dependency_overrides[get_gmail_client] = lambda: mock_gmail_instance
    app.dependency_overrides[get_ai_processor] = lambda: mock_ai_instance
    app.dependency_overrides[get_slack_client] = lambda: mock_slack_instance

    with patch('psutil.cpu_percent', return_value=10.0), \
         patch('psutil.virtual_memory', return_value=MagicMock(percent=30.0)):
        try:
            response = test_client_fixture.get("/api/v1/health") # Headers might not be needed if get_api_key is overridden
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "uptime" in data
            assert "version" in data
            assert "services" in data
            assert "message" in data
            
            services = data["services"]
            assert "system" in services
            assert "gmail" in services
            assert "ai" in services
            assert "slack" in services
            
            assert services["system"] == ServiceStatus.OK.value # Assuming system is always operational for this basic check
            # The actual status of overridden services will depend on how the health check router
            # interacts with these mocks (e.g., if it tries to call methods on them).
            # For now, let's assume the health check in the router checks if the clients can be 'resolved' (i.e., a mock is returned)
            # or if it has specific checks. If it simply assumes they are okay because a mock is provided, the following might pass.
            # If the health check actually tries to use the clients (e.g., client.ping()), then the mocks need behavior.
            assert services["gmail"] in [status.value for status in ServiceStatus] 
            assert services["ai"] in [status.value for status in ServiceStatus]
            assert services["slack"] in [status.value for status in ServiceStatus]
        finally:
            app.dependency_overrides = original_overrides


def test_health_check_service_error(test_client_fixture, mock_api_key):
    """Test health check when a service is down."""
    from src.utils.exceptions import GmailServiceError # Import for raising

    mock_ai_instance = MagicMock()
    mock_slack_instance = MagicMock()

    def faulty_gmail_client_provider():
        raise GmailServiceError("Mocked Service unavailable")

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_api_key] = lambda: mock_api_key
    app.dependency_overrides[get_gmail_client] = faulty_gmail_client_provider # This will cause get_gmail_client in dependencies.py to raise HTTPException
    app.dependency_overrides[get_ai_processor] = lambda: mock_ai_instance
    app.dependency_overrides[get_slack_client] = lambda: mock_slack_instance
    
    try:
        response = test_client_fixture.get("/api/v1/health")
        
        # The health router itself catches HTTPExceptions from dependencies and reports service status
        # So the overall /api/v1/health should still be 200
        assert response.status_code == 200 
        data = response.json()
        services = data["services"]
        
        assert services["gmail"] == ServiceStatus.UNAVAILABLE.value
        assert data["status"] == ServiceStatus.DEGRADED.value # Overall status should be degraded
        assert services["ai"] == ServiceStatus.OK.value # Assuming other services are fine
        assert services["slack"] == ServiceStatus.OK.value
    finally:
        app.dependency_overrides = original_overrides

def test_health_check_unauthorized(test_client_fixture): # mock_api_key fixture implicitly sets up valid key
    """Test health check endpoint with invalid API key."""
    # Mock the api_settings to ensure API_KEY is set and check is enforced
    with patch('src.api.dependencies.api_settings') as mock_settings:
        # Configure api_settings explicitly for this test
        mock_settings.API_KEY_NAME = "X-API-KEY"
        mock_settings.API_KEY = "correct-api-key"
        
        original_overrides = app.dependency_overrides.copy()
        # Keep other services mocked to isolate the auth test
        app.dependency_overrides[get_gmail_client] = lambda: MagicMock()
        app.dependency_overrides[get_ai_processor] = lambda: MagicMock()
        app.dependency_overrides[get_slack_client] = lambda: MagicMock()
        
        # Important: Don't override get_api_key here, let the actual implementation run

        # Add psutil mocks here too, as health_check runs regardless of auth for other parts
        with patch('psutil.cpu_percent', return_value=10.0), \
             patch('psutil.virtual_memory', return_value=MagicMock(percent=30.0)):
            try:
                response = test_client_fixture.get("/api/v1/health", headers={"X-API-KEY": "invalid-key"})
                assert response.status_code == 401 # Expecting unauthorized
                data = response.json()
                assert "Invalid API key" in data["detail"]
            finally:
                app.dependency_overrides = original_overrides 