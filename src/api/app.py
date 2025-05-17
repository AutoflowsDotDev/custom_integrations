from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import time
import platform
import socket

from src.api.config import api_settings
from src.api.routers import health, metrics, email, webhook
from src.api.dependencies import get_api_key
from src.core.config import validate_config
from src.utils.logger import get_logger
from src.api.routers.metrics import ACTIVE_CONNECTIONS

logger = get_logger(__name__)

def create_app() -> FastAPI:
    """Create the FastAPI application."""
    try:
        # Validate configuration
        validate_config()
    except Exception as e:
        logger.critical(f"Configuration validation error: {e}")
        # Ensure we re-raise the exception for proper error handling
        raise Exception(f"Configuration error: {str(e)}")

    app = FastAPI(
        title=api_settings.PROJECT_NAME,
        description=api_settings.DESCRIPTION,
        version=api_settings.VERSION,
        docs_url=None,  # Disable default docs
        redoc_url=None,  # Disable default redoc
        openapi_url="/api/v1/openapi.json"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.CORS_ORIGINS,
        allow_credentials=api_settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=api_settings.CORS_ALLOW_METHODS,
        allow_headers=api_settings.CORS_ALLOW_HEADERS,
    )

    # Add middleware to track active connections
    @app.middleware("http")
    async def connection_middleware(request, call_next):
        ACTIVE_CONNECTIONS.inc()
        start_time = time.time()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            process_time = time.time() - start_time
            if response is not None:
                response.headers["X-Process-Time"] = str(process_time)
            ACTIVE_CONNECTIONS.dec()

    # Custom OpenAPI and docs endpoints with API key protection if enabled
    @app.get("/api/v1/docs", include_in_schema=False)
    async def custom_swagger_ui_html(api_key: str = Depends(get_api_key)):
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{api_settings.PROJECT_NAME} - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )

    @app.get("/api/v1/redoc", include_in_schema=False)
    async def custom_redoc_html(api_key: str = Depends(get_api_key)):
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{api_settings.PROJECT_NAME} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        )

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        hostname = socket.gethostname()
        return JSONResponse(
            content={
                "status": "online",
                "service": api_settings.PROJECT_NAME,
                "version": api_settings.VERSION,
                "hostname": hostname,
                "environment": "development" if api_settings.DEBUG else "production",
                "documentation": "/api/v1/docs"
            }
        )

    # Include routers
    app.include_router(health.router, prefix=api_settings.API_V1_PREFIX)
    app.include_router(metrics.router, prefix=api_settings.API_V1_PREFIX)
    app.include_router(email.router, prefix=api_settings.API_V1_PREFIX)
    app.include_router(webhook.router, prefix=api_settings.API_V1_PREFIX)

    # Log application startup
    logger.info(
        f"Application {api_settings.PROJECT_NAME} v{api_settings.VERSION} started on {platform.system()} {platform.release()}"
    )

    return app

app = create_app() 