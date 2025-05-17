import time
import platform
import psutil
from fastapi import APIRouter, Depends
from typing import Dict

from src.api.models import ServiceHealthResponse, ServiceStatus
from src.api.dependencies import (
    get_gmail_client, 
    get_ai_processor, 
    get_slack_client,
    get_api_key
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Store start time for uptime calculation
START_TIME = time.time()
VERSION = "0.1.0"

router = APIRouter(
    prefix="/health",
    tags=["health"],
    dependencies=[Depends(get_api_key)]
)

@router.get("", response_model=ServiceHealthResponse)
async def health_check():
    """
    Check the health of the service and its dependencies.
    """
    logger.info("Health check requested")
    
    services_status: Dict[str, ServiceStatus] = {
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
        if not gmail_client or not gmail_client.service:
            logger.warning("Gmail client not available for health check.")
            services_status["gmail"] = ServiceStatus.UNAVAILABLE
            services_status["system"] = ServiceStatus.DEGRADED # Gmail is a critical dependency
    except Exception as e:
        logger.error(f"Gmail service unavailable: {e}")
        services_status["gmail"] = ServiceStatus.UNAVAILABLE
    
    # Check AI service (optional)
    try:
        ai_processor = await get_ai_processor()
        if not ai_processor:
            logger.warning("AI processor not available for health check.")
            services_status["ai"] = ServiceStatus.UNAVAILABLE
            services_status["system"] = ServiceStatus.DEGRADED # AI processor is a critical dependency
    except Exception as e:
        logger.error(f"AI service unavailable: {e}")
        services_status["ai"] = ServiceStatus.UNAVAILABLE
    
    # Check Slack service (optional)
    try:
        slack_client = await get_slack_client()
        if not slack_client:
            logger.warning("Slack client not available for health check.")
            services_status["slack"] = ServiceStatus.UNAVAILABLE
            # Slack might not be critical for core email processing, depends on requirements
            # services_status["system"] = ServiceStatus.DEGRADED 
    except Exception as e:
        logger.error(f"Slack service unavailable: {e}")
        services_status["slack"] = ServiceStatus.UNAVAILABLE
    
    # Determine overall status
    overall_status = ServiceStatus.OK
    # Check if any service is unavailable or system is degraded
    if ServiceStatus.UNAVAILABLE in services_status.values() or services_status["system"] == ServiceStatus.DEGRADED:
        overall_status = ServiceStatus.DEGRADED

    # More specific: if all critical external services are down, system is unavailable
    # This is a simplified check. A more robust system might have a concept of critical vs. non-critical dependencies.
    critical_dependencies_down = (
        services_status["gmail"] == ServiceStatus.UNAVAILABLE and
        services_status["ai"] == ServiceStatus.UNAVAILABLE # Assuming AI is also critical
        # services_status["slack"] == ServiceStatus.UNAVAILABLE # Slack might not make the whole system unavailable
    )

    if critical_dependencies_down and services_status["system"] != ServiceStatus.OK:
        overall_status = ServiceStatus.UNAVAILABLE # Or if system is also unavailable
    elif ServiceStatus.UNAVAILABLE in services_status.values(): # If any service is unavailable, overall is degraded
        overall_status = ServiceStatus.DEGRADED
    elif services_status["system"] != ServiceStatus.OK: # If system itself is degraded (e.g. due to a critical dep)
        overall_status = ServiceStatus.DEGRADED

    return ServiceHealthResponse(
        status=overall_status,
        uptime=time.time() - START_TIME,
        version=VERSION,
        services=services_status,
        message=f"Running on {platform.system()} {platform.release()}"
    ) 