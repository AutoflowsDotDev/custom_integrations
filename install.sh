#!/bin/bash

# Email Triage Workflow API Installation Script
set -e

echo "=== Email Triage Workflow API Installation ==="
echo "This script will install and configure the Email Triage Workflow API."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Docker and/or Docker Compose not found. Please install them first."
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Create necessary directories
mkdir -p secrets logs

# Setup environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example"
    cp .env.example .env
    echo "Please edit the .env file with your actual configuration values."
    echo "At minimum, you need to set:"
    echo "- API_KEY"
    echo "- GOOGLE_CLOUD_PROJECT_ID"
    echo "- GOOGLE_PUBSUB_TOPIC_ID"
    echo "- GOOGLE_PUBSUB_SUBSCRIPTION_ID"
    echo "- SLACK_BOT_TOKEN"
    echo "- SLACK_CHANNEL_ID"
    echo "- OPENAI_API_KEY or OPENROUTER_API_KEY"
    read -p "Press Enter to continue after editing the .env file..."
else
    echo ".env file already exists, skipping creation."
fi

# Check for Google API credentials
echo "Checking for Google API credentials..."
if [ ! -f secrets/client_secret.json ] || [ ! -f secrets/credentials.json ] || [ ! -f secrets/service_account.json ]; then
    echo "Please place the following files in the 'secrets' directory:"
    echo "- client_secret.json (OAuth 2.0 client secrets)"
    echo "- credentials.json (OAuth 2.0 tokens)"
    echo "- service_account.json (Service account key file)"
    read -p "Press Enter to continue after adding the necessary files..."
else
    echo "Google API credentials found."
fi

# Build and start the Docker containers
echo "Building and starting Docker containers..."
docker-compose up -d --build

echo "=== Installation completed ==="
echo "The Email Triage Workflow API is now running at http://localhost:8000"
echo "API documentation is available at http://localhost:8000/api/v1/docs"
echo "Health status is available at http://localhost:8000/api/v1/health"
echo ""
echo "To view logs:"
echo "docker-compose logs -f"
echo ""
echo "To stop the service:"
echo "docker-compose down" 