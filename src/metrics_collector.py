#!/usr/bin/env python
"""
Metrics Collector for Email Triage Workflow

This script collects metrics from the email triage workflow and stores them in a SQLite database.
It should be run periodically to keep the metrics up to date.
"""
import os
import sys
import sqlite3
import logging
import time
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import requests
from typing import Dict, List, Tuple, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Database path
DATA_DIR = Path("/app/data") if os.path.exists("/app/data") else Path("./data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "email_triage.db"

# Log directory
LOG_DIR = Path("/app/logs") if os.path.exists("/app/logs") else Path("./logs")

# API endpoints
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_METRICS_URL = f"{API_BASE_URL}/metrics"
API_HEALTH_URL = f"{API_BASE_URL}/api/v1/health"

def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    
    # Create tables if they don't exist
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        date TEXT,
        emails_processed INTEGER,
        urgent INTEGER,
        action_required INTEGER,
        informational INTEGER,
        avg_response_time_min REAL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        endpoint TEXT,
        status_code INTEGER,
        response_time_ms REAL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        cpu_percent REAL,
        memory_percent REAL,
        disk_percent REAL
    )
    ''')
    
    conn.commit()
    return conn

def collect_email_metrics_from_logs() -> Dict[str, Dict[str, Any]]:
    """Collect email metrics from log files."""
    metrics_by_date = {}
    
    if not LOG_DIR.exists():
        logger.warning(f"Log directory {LOG_DIR} does not exist")
        return metrics_by_date
    
    # Get all log files
    log_files = list(LOG_DIR.glob("*.log"))
    if not log_files:
        logger.warning(f"No log files found in {LOG_DIR}")
        return metrics_by_date
    
    # Process each log file
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    # Look for log entries about processing emails
                    if "processed email" in line.lower():
                        # Extract date (assumes ISO format date at start of line)
                        date_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
                        if not date_match:
                            continue
                            
                        date = date_match.group(0)
                        
                        # Initialize metrics for this date if not exists
                        if date not in metrics_by_date:
                            metrics_by_date[date] = {
                                'emails_processed': 0,
                                'urgent': 0,
                                'action_required': 0,
                                'informational': 0,
                                'response_times': []
                            }
                        
                        # Increment email count
                        metrics_by_date[date]['emails_processed'] += 1
                        
                        # Determine email category
                        if "urgent" in line.lower():
                            metrics_by_date[date]['urgent'] += 1
                        elif "action required" in line.lower():
                            metrics_by_date[date]['action_required'] += 1
                        else:
                            metrics_by_date[date]['informational'] += 1
                        
                        # Extract response time if available
                        time_match = re.search(r'response time: (\d+\.?\d*)', line)
                        if time_match:
                            time_val = float(time_match.group(1))
                            metrics_by_date[date]['response_times'].append(time_val)
        except Exception as e:
            logger.error(f"Error processing log file {log_file}: {e}")
    
    # Calculate average response times
    for date, metrics in metrics_by_date.items():
        if metrics['response_times']:
            metrics['avg_response_time_min'] = sum(metrics['response_times']) / len(metrics['response_times'])
        else:
            metrics['avg_response_time_min'] = 0
        
        # Remove the raw response times list, we just need the average
        del metrics['response_times']
    
    return metrics_by_date

def collect_api_metrics() -> List[Dict[str, Any]]:
    """Collect metrics from the API server."""
    api_metrics = []
    
    # Test the API health endpoint
    try:
        start_time = time.time()
        response = requests.get(API_HEALTH_URL, timeout=5)
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        api_metrics.append({
            'endpoint': '/api/v1/health',
            'status_code': response.status_code,
            'response_time_ms': response_time
        })
        
        logger.info(f"API health check: status={response.status_code}, response_time={response_time:.2f}ms")
    except Exception as e:
        logger.error(f"Error checking API health: {e}")
    
    # Try to get metrics from the Prometheus metrics endpoint
    try:
        response = requests.get(API_METRICS_URL, timeout=5)
        if response.status_code == 200:
            # Parse Prometheus metrics format, but we don't use them directly
            # We're just recording that we successfully accessed the endpoint
            api_metrics.append({
                'endpoint': '/metrics',
                'status_code': response.status_code,
                'response_time_ms': 0
            })
    except Exception as e:
        logger.error(f"Error getting API metrics: {e}")
    
    return api_metrics

def collect_system_metrics() -> Dict[str, float]:
    """Collect system metrics."""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent
    }

def store_metrics(conn: sqlite3.Connection,
                  email_metrics: Dict[str, Dict[str, Any]],
                  api_metrics: List[Dict[str, Any]],
                  system_metrics: Dict[str, float]) -> None:
    """Store collected metrics in the database."""
    cursor = conn.cursor()
    
    # Store email metrics
    for date, metrics in email_metrics.items():
        cursor.execute('''
        INSERT INTO email_metrics (date, emails_processed, urgent, action_required, informational, avg_response_time_min)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            date,
            metrics['emails_processed'],
            metrics['urgent'],
            metrics['action_required'],
            metrics['informational'],
            metrics['avg_response_time_min']
        ))
    
    # Store API metrics
    for metric in api_metrics:
        cursor.execute('''
        INSERT INTO api_metrics (endpoint, status_code, response_time_ms)
        VALUES (?, ?, ?)
        ''', (
            metric['endpoint'],
            metric['status_code'],
            metric['response_time_ms']
        ))
    
    # Store system metrics
    cursor.execute('''
    INSERT INTO system_metrics (cpu_percent, memory_percent, disk_percent)
    VALUES (?, ?, ?)
    ''', (
        system_metrics['cpu_percent'],
        system_metrics['memory_percent'],
        system_metrics['disk_percent']
    ))
    
    conn.commit()

def main():
    """Main function to collect and store metrics."""
    logger.info("Starting metrics collection")
    
    try:
        # Connect to the database
        conn = get_db_connection()
        
        # Collect metrics
        email_metrics = collect_email_metrics_from_logs()
        api_metrics = collect_api_metrics()
        system_metrics = collect_system_metrics()
        
        # Store metrics
        store_metrics(conn, email_metrics, api_metrics, system_metrics)
        
        # Log summary
        total_emails = sum(m['emails_processed'] for m in email_metrics.values())
        logger.info(f"Metrics collection completed: {len(email_metrics)} dates, {total_emails} emails, {len(api_metrics)} API calls")
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 