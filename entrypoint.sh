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
elif [ "$1" = "metrics-collector" ]; then
    # Run the metrics collector once
    echo "Running metrics collector..."
    exec python src/metrics_collector.py
elif [ "$1" = "metrics-collector-daemon" ]; then
    # Run the metrics collector on a schedule
    echo "Starting metrics collector daemon..."
    
    # Make the script executable
    chmod +x /app/src/metrics_collector.py
    
    # Create a cron job to run the metrics collector every 5 minutes
    echo "*/5 * * * * /usr/local/bin/python /app/src/metrics_collector.py >> /app/data/metrics_collector.log 2>&1" > /tmp/crontab
    crontab /tmp/crontab
    rm /tmp/crontab
    
    # Start cron and keep container running
    cron
    
    # Run once immediately
    python /app/src/metrics_collector.py
    
    # Keep container running
    tail -f /dev/null
else
    # Default: start everything in parallel
    echo "Starting API server, dashboard, and metrics collector..."
    
    # Start API server in background
    python src/api_server.py --host 0.0.0.0 --port 8000 &
    API_PID=$!
    
    # Start dashboard in background
    python /app/src/run_dashboard.py &
    DASHBOARD_PID=$!
    
    # Set up metrics collector cron job
    echo "Setting up metrics collector..."
    chmod +x /app/src/metrics_collector.py
    echo "*/5 * * * * /usr/local/bin/python /app/src/metrics_collector.py >> /app/data/metrics_collector.log 2>&1" > /tmp/crontab
    crontab /tmp/crontab
    rm /tmp/crontab
    
    # Start cron
    cron
    
    # Run metrics collector once immediately
    python /app/src/metrics_collector.py &
    
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