#!/bin/bash

# Run API Tests Script
set -e

echo "=== Running API Tests ==="

# Ensure we have pytest and pytest-asyncio
echo "Checking for test dependencies..."
pip install -r requirements.txt pytest-asyncio pytest-cov

# Set environment variables for testing
export API_KEY=test-api-key
export GOOGLE_SERVICE_ACCOUNT_PATH=dummy/path/service_account.json

# Create logs directory if it doesn't exist
mkdir -p logs

# Run API tests with coverage
echo "Running API tests..."
cd tests && python -m pytest test_api -v --cov=src.api --cov-report=term-missing

echo "=== Tests completed ===" 