#!/bin/bash
set -e

# Function to mount data directories from local to the volumes
setup_directories() {
  # Create any missing directories
  mkdir -p /app/data /app/logs /app/secrets
}

# Handle different process types
case "$1" in
  app_main)
    setup_directories
    echo "Starting main application process..."
    exec python src/api_server.py --host 0.0.0.0 --port 8000
    ;;
  app_secrets)
    setup_directories
    echo "Starting secrets process..."
    # This is just a placeholder process to mount the secrets volume
    # In a real scenario, you might run a separate service here
    exec tail -f /dev/null
    ;;
  app_logs)
    setup_directories
    echo "Starting logs process..."
    # This is just a placeholder process to mount the logs volume
    # In a real scenario, you might run a log collector here
    exec tail -f /dev/null
    ;;
  *)
    # Default to running whatever command was passed
    exec "$@"
    ;;
esac 