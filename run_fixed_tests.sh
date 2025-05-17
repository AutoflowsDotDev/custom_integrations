#!/bin/bash

# Run Fixed Tests Script
set -e

echo "=== Running Fixed Tests ==="

# Testing environment setup
export PYTHONPATH=$(pwd)
export API_KEY=test-api-key

# Create temp service account files
mkdir -p dummy/path
echo '{"type":"service_account"}' > dummy/path/service_account.json
echo '{"type":"client_secret"}' > dummy/path/client_secret.json
echo '{"type":"credentials"}' > dummy/path/credentials.json

# Run App tests
echo "Running App tests"
python -m pytest tests/test_api/test_app.py::test_root_endpoint -v
python -m pytest tests/test_api/test_app.py::test_app_creation_with_error -v

# Run API key dependency tests
echo "Running API dependency tests"
python -m pytest tests/test_api/test_dependencies.py::test_get_api_key_valid -v
python -m pytest tests/test_api/test_dependencies.py::test_get_api_key_invalid -v
python -m pytest tests/test_api/test_dependencies.py::test_get_api_key_none -v
python -m pytest tests/test_api/test_dependencies.py::test_get_api_key_disabled -v

# Run Health tests
echo "Running Health tests"
python -m pytest tests/test_api/test_health.py::test_health_check -v
python -m pytest tests/test_api/test_health.py::test_health_check_service_error -v
python -m pytest tests/test_api/test_health.py::test_health_check_unauthorized -v

# Run Metrics tests
echo "Running Metrics tests"
python -m pytest tests/test_api/test_metrics.py::test_metrics_endpoint -v

# Clean up
rm -rf dummy

echo "=== Tests completed ===" 