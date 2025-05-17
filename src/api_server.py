import os
import argparse
import uvicorn
from dotenv import load_dotenv

from src.utils.logger import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Email Triage API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--ssl-keyfile", help="SSL key file")
    parser.add_argument("--ssl-certfile", help="SSL certificate file")
    
    args = parser.parse_args()
    
    # Setup UVicorn config
    uvicorn_config = {
        "app": "src.api.app:app",
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "workers": args.workers,
    }
    
    # Add SSL if specified
    if args.ssl_keyfile and args.ssl_certfile:
        uvicorn_config["ssl_keyfile"] = args.ssl_keyfile
        uvicorn_config["ssl_certfile"] = args.ssl_certfile
    
    logger.info(f"Starting API server at http://{args.host}:{args.port}")
    
    try:
        uvicorn.run(**uvicorn_config)
    except Exception as e:
        logger.critical(f"Failed to start server: {e}", exc_info=True)
        exit(1) 