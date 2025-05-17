import time
import platform
import psutil
from fastapi import APIRouter, Depends

from src.api.models import ServiceHealthResponse, ServiceStatus
from src.api.dependencies import (
    get_gmail_client, 
    get_ai_processor, 
    get_slack_client
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Store start time for uptime calculation
START_TIME = time.time()
VERSION = "0.1.0"

router = APIRouter(tags=["health"])

@router.get("/health", response_model=ServiceHealthResponse)
async def health_check():
    """
    Check the health of the service and its dependencies.
    """
    logger.info("Health check requested")
    
    services_status = {
        "system": ServiceStatus.OK,
        "gmail": ServiceStatus.OK,
        "ai": ServiceStatus.OK,
        "slack": ServiceStatus.OK,
    }
    
    # Check system health (basic example)
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 90 or memory_percent > 90:
            services_status["system"] = ServiceStatus.DEGRADED
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        services_status["system"] = ServiceStatus.DEGRADED
    
    # Check Gmail service (optional)
    try:
        gmail_client = await get_gmail_client()
        # Simple test or just initialization check
    except Exception as e:
        logger.error(f"Gmail service unavailable: {e}")
        services_status["gmail"] = ServiceStatus.UNAVAILABLE
    
    # Check AI service (optional)
    try:
        ai_processor = await get_ai_processor()
        # Simple test or just initialization check
    except Exception as e:
        logger.error(f"AI service unavailable: {e}")
        services_status["ai"] = ServiceStatus.UNAVAILABLE
    
    # Check Slack service (optional)
    try:
        slack_client = await get_slack_client()
        # Simple test or just initialization check
    except Exception as e:
        logger.error(f"Slack service unavailable: {e}")
        services_status["slack"] = ServiceStatus.UNAVAILABLE
    
    # Determine overall status
    overall_status = ServiceStatus.OK
    if ServiceStatus.UNAVAILABLE in services_status.values():
        overall_status = ServiceStatus.DEGRADED
    if services_status["system"] == ServiceStatus.DEGRADED:
        overall_status = ServiceStatus.DEGRADED
    if (services_status["gmail"] == ServiceStatus.UNAVAILABLE and 
        services_status["ai"] == ServiceStatus.UNAVAILABLE and 
        services_status["slack"] == ServiceStatus.UNAVAILABLE):
        overall_status = ServiceStatus.UNAVAILABLE
    
    return ServiceHealthResponse(
        status=overall_status,
        uptime=time.time() - START_TIME,
        version=VERSION,
        services=services_status,
        message=f"Running on {platform.system()} {platform.release()}"
    ) 