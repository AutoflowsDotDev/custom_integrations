#!/usr/bin/env python
"""
Streamlit Dashboard Runner for Email Triage Workflow
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_data_directory():
    """Make sure the data directory exists."""
    data_dir = Path("/app/data") if os.path.exists("/app/data") else Path("./data")
    data_dir.mkdir(exist_ok=True)
    return data_dir

def main():
    """Run the Streamlit dashboard."""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Dashboard file path
    dashboard_path = script_dir / "dashboard.py"
    
    # Ensure data directory exists
    data_dir = ensure_data_directory()
    
    # Set default Streamlit port
    port = os.environ.get("DASHBOARD_PORT", "8501")
    
    # Set up command to run Streamlit
    cmd = [
        "streamlit", "run", 
        str(dashboard_path),
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--browser.serverAddress", os.environ.get("FLY_APP_NAME", "localhost"),
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--server.headless", "true"
    ]
    
    print(f"Starting dashboard on port {port}...")
    
    try:
        # Run Streamlit
        process = subprocess.Popen(cmd)
        process.wait()
    except KeyboardInterrupt:
        print("Dashboard stopped.")
    except Exception as e:
        print(f"Error running dashboard: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 