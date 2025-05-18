#!/bin/bash
set -e

# Create data directory
mkdir -p /app/data

# Determine what to run
if [ "$1" = "dashboard" ]; then
    # Start the dashboard
    echo "Starting Streamlit dashboard..."
    exec python /app/src/run_dashboard.py
elif [ "$1" = "api" ]; then
    # Start the API server
    echo "Starting API server..."
    exec python src/api_server.py --host 0.0.0.0 --port 8000
else
    # Default: start both in parallel
    echo "Starting API server and dashboard..."
    
    # Start API server in background
    python src/api_server.py --host 0.0.0.0 --port 8000 &
    API_PID=$!
    
    # Start dashboard in background
    python /app/src/run_dashboard.py &
    DASHBOARD_PID=$!
    
    # Function to handle graceful shutdown
    function handle_shutdown {
        echo "Shutting down services..."
        kill -TERM $API_PID 2>/dev/null || true
        kill -TERM $DASHBOARD_PID 2>/dev/null || true
        wait
        echo "All services terminated."
        exit 0
    }
    
    # Trap SIGTERM and SIGINT
    trap handle_shutdown SIGTERM SIGINT
    
    # Wait for either process to exit
    wait -n $API_PID $DASHBOARD_PID
    
    # If we got here, one of the processes exited
    # Check if API server is still running
    if kill -0 $API_PID 2>/dev/null; then
        echo "Dashboard exited, shutting down API server..."
        kill -TERM $API_PID
    else
        echo "API server exited, shutting down dashboard..."
        kill -TERM $DASHBOARD_PID
    fi
    
    # Wait for all processes to finish
    wait
    
    echo "All services stopped."
fi 