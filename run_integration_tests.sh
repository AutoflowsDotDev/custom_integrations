#!/usr/bin/env bash

set -e

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the integration tests with coverage
echo "Running integration tests with coverage..."
python -m pytest tests/test_integration -v --cov=src

# Generate coverage report
echo "Generating coverage report..."
python -m coverage html
python -m coverage report

echo "Integration tests completed." 