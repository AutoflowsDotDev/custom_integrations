#!/bin/bash
set -e

# Create data directory
mkdir -p /app/data

# Start the application
echo "Starting API server..."
exec python src/api_server.py --host 0.0.0.0 --port 8000 