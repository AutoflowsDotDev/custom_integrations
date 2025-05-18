import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
from datetime import datetime, timedelta
import time
import random  # For demo data, remove in production
import sqlite3
import psutil
from pathlib import Path
import requests
import re

# Configure page
st.set_page_config(
    page_title="Email Triage Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #424242;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
    }
    .metric-delta {
        font-size: 0.9rem;
        font-weight: 500;
    }
    .section-header {
        font-size: 1.5rem;
        color: #424242;
        margin: 2rem 0 1rem 0;
    }
    .chart-container {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/email.png", width=80)
    st.title("Email Triage Dashboard")
    st.markdown("---")
    
    # Date range filter
    st.subheader("Filters")
    date_range = st.selectbox(
        "Time Period",
        options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        index=1
    )

    # Refresh rate
    refresh_rate = st.slider(
        "Refresh Rate (seconds)",
        min_value=0,
        max_value=300,
        value=60,
        step=10
    )
    
    if refresh_rate > 0:
        st.info(f"Dashboard refreshes every {refresh_rate} seconds")
    
    st.markdown("---")
    st.markdown("""
    **Data Sources**
    - Email Processing Logs
    - API Usage Metrics
    - System Performance
    """)
    
    # Add environment info
    st.markdown("---")
    st.caption(f"Environment: {'Production' if os.getenv('FLY_APP_NAME') else 'Development'}")
    st.caption(f"Version: 1.0.0")

# Helper functions
def get_database_connection():
    """Connect to the SQLite database"""
    data_dir = Path("/app/data") if os.path.exists("/app/data") else Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "email_triage.db"
    
    # Create the database and tables if they don't exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
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

def get_log_data():
    """Extract metrics from log files"""
    log_data = []
    log_dir = Path("/app/logs") if os.path.exists("/app/logs") else Path("./logs")
    
    if not log_dir.exists():
        return []
    
    # Look for log files
    log_files = list(log_dir.glob("*.log"))
    
    for log_file in log_files:
        if not log_file.exists():
            continue
            
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    # Look for lines containing email processing information
                    if "processed email" in line.lower():
                        log_data.append(line.strip())
        except Exception as e:
            st.warning(f"Could not read log file {log_file}: {str(e)}")
    
    return log_data

def get_api_metrics():
    """Get API metrics from Prometheus metrics endpoint"""
    api_metrics = {}
    
    try:
        # Try to get metrics from the API server's metrics endpoint
        api_url = "http://localhost:8000/metrics"
        response = requests.get(api_url, timeout=2)
        
        if response.status_code == 200:
            # Parse prometheus metrics
            for line in response.text.split('\n'):
                if line.startswith('api_'):
                    parts = line.split(' ')
                    if len(parts) >= 2:
                        name = parts[0]
                        value = float(parts[1])
                        api_metrics[name] = value
    except Exception as e:
        st.warning(f"Could not get API metrics: {str(e)}")
    
    return api_metrics

def parse_log_data(log_data):
    """Parse log data for email processing information"""
    email_counts = {}
    urgent_counts = {}
    action_counts = {}
    info_counts = {}
    response_times = {}
    
    for line in log_data:
        try:
            # Extract date (assumes ISO format date at start of line)
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
            if date_match:
                date = date_match.group(0)
                
                # Increment total emails for the date
                if "processed email" in line.lower():
                    email_counts[date] = email_counts.get(date, 0) + 1
                
                # Categorize emails based on priority
                if "urgent" in line.lower():
                    urgent_counts[date] = urgent_counts.get(date, 0) + 1
                elif "action required" in line.lower():
                    action_counts[date] = action_counts.get(date, 0) + 1
                elif "informational" in line.lower():
                    info_counts[date] = info_counts.get(date, 0) + 1
                
                # Extract response time if available
                time_match = re.search(r'response time: (\d+\.?\d*)', line)
                if time_match:
                    time_val = float(time_match.group(1))
                    if date in response_times:
                        response_times[date].append(time_val)
                    else:
                        response_times[date] = [time_val]
        except Exception as e:
            st.warning(f"Error parsing log line: {str(e)}")
    
    return email_counts, urgent_counts, action_counts, info_counts, response_times

def get_real_data():
    """Get real data from the database and other sources"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Initialize with empty values
    daily_df = pd.DataFrame()
    current_stats = {
        'total_emails': 0,
        'emails_today': 0,
        'avg_response_time': 0,
        'success_rate': 100.0  # Default to 100%
    }
    classification_df = pd.DataFrame({
        'category': ['Urgent', 'Action Required', 'Informational'],
        'count': [0, 0, 0]
    })
    system_metrics = {
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'api_success_rate': 100.0,
        'api_calls_per_min': 0
    }
    
    try:
        # Get email metrics from database
        cursor.execute('''
        SELECT date, SUM(emails_processed), SUM(urgent), SUM(action_required), 
               SUM(informational), AVG(avg_response_time_min)
        FROM email_metrics
        GROUP BY date
        ORDER BY date
        LIMIT 30
        ''')
        results = cursor.fetchall()
        
        if results:
            daily_df = pd.DataFrame(results, columns=[
                'date', 'emails_processed', 'urgent', 'action_required', 
                'informational', 'avg_response_time_min'
            ])
        
        # If no database results, try to parse log files
        if daily_df.empty:
            log_data = get_log_data()
            if log_data:
                email_counts, urgent_counts, action_counts, info_counts, response_times = parse_log_data(log_data)
                
                # Convert to DataFrame
                dates = sorted(list(email_counts.keys()))
                emails_processed = [email_counts.get(date, 0) for date in dates]
                urgent = [urgent_counts.get(date, 0) for date in dates]
                action_required = [action_counts.get(date, 0) for date in dates]
                informational = [info_counts.get(date, 0) for date in dates]
                avg_response_time = []
                
                for date in dates:
                    if date in response_times and response_times[date]:
                        avg_response_time.append(sum(response_times[date]) / len(response_times[date]))
                    else:
                        avg_response_time.append(0)
                
                daily_df = pd.DataFrame({
                    'date': dates,
                    'emails_processed': emails_processed,
                    'urgent': urgent,
                    'action_required': action_required,
                    'informational': informational,
                    'avg_response_time_min': avg_response_time
                })
        
        # If we still have no data, fall back to mock data with a warning
        if daily_df.empty:
            st.warning("No email processing data found. Using mock data for demonstration.")
            # Generate mock data (same as before but marked as mock)
            return get_mock_data(is_mock=True)
        
        # Calculate aggregate statistics
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Total emails processed
        current_stats['total_emails'] = daily_df['emails_processed'].sum()
        
        # Emails processed today
        today_df = daily_df[daily_df['date'] == today]
        current_stats['emails_today'] = today_df['emails_processed'].sum() if not today_df.empty else 0
        
        # Average response time
        current_stats['avg_response_time'] = daily_df['avg_response_time_min'].mean()
        
        # Get API metrics
        api_metrics = get_api_metrics()
        if api_metrics:
            if 'api_success_rate' in api_metrics:
                system_metrics['api_success_rate'] = api_metrics['api_success_rate']
            if 'api_requests_per_minute' in api_metrics:
                system_metrics['api_calls_per_min'] = api_metrics['api_requests_per_minute']
        
        # Calculate success rate from API metrics or database
        cursor.execute('''
        SELECT COUNT(*) FROM api_metrics WHERE status_code < 400
        ''')
        success_count = cursor.fetchone()[0] or 0
        
        cursor.execute('''
        SELECT COUNT(*) FROM api_metrics
        ''')
        total_count = cursor.fetchone()[0] or 0
        
        if total_count > 0:
            current_stats['success_rate'] = (success_count / total_count) * 100
        
        # Get classification breakdown
        total_urgent = daily_df['urgent'].sum()
        total_action = daily_df['action_required'].sum()
        total_info = daily_df['informational'].sum()
        
        classification_df = pd.DataFrame({
            'category': ['Urgent', 'Action Required', 'Informational'],
            'count': [total_urgent, total_action, total_info]
        })
        
        # System metrics are already collected with psutil above
        
    except Exception as e:
        st.error(f"Error retrieving real data: {str(e)}")
        # Fall back to mock data
        return get_mock_data(is_mock=True)
    finally:
        conn.close()
    
    return daily_df, current_stats, classification_df, system_metrics

def get_mock_data(is_mock=False):
    """Generate mock data for demonstration"""
    if is_mock:
        st.warning("Using mock data for demonstration purposes")
    
    # Mock email processing data
    now = datetime.now()
    dates = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
    dates.reverse()
    
    emails_processed = [random.randint(20, 100) for _ in range(30)]
    urgent_emails = [int(x * random.uniform(0.1, 0.3)) for x in emails_processed]
    action_required = [int(x * random.uniform(0.4, 0.7)) for x in emails_processed]
    informational = [emails_processed[i] - urgent_emails[i] - action_required[i] for i in range(30)]
    
    response_times = [random.uniform(1, 10) for _ in range(30)]
    
    # Create dataframes
    daily_df = pd.DataFrame({
        'date': dates,
        'emails_processed': emails_processed,
        'urgent': urgent_emails,
        'action_required': action_required, 
        'informational': informational,
        'avg_response_time_min': response_times
    })
    
    # Current stats
    current_stats = {
        'total_emails': sum(emails_processed),
        'emails_today': emails_processed[-1],
        'avg_response_time': sum(response_times) / len(response_times),
        'success_rate': random.uniform(0.95, 0.99) * 100
    }
    
    # Classification breakdown
    classification_data = {
        'category': ['Urgent', 'Action Required', 'Informational'],
        'count': [sum(urgent_emails), sum(action_required), sum(informational)]
    }
    classification_df = pd.DataFrame(classification_data)
    
    # System metrics
    system_metrics = {
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'api_success_rate': random.uniform(98, 100),
        'api_calls_per_min': random.randint(5, 30)
    }
    
    return daily_df, current_stats, classification_df, system_metrics

# Main dashboard
st.markdown('<h1 class="main-header">Email Triage Workflow Dashboard</h1>', unsafe_allow_html=True)

# Placeholder for last refresh timestamp
refresh_placeholder = st.empty()

# Main function to update dashboard
def update_dashboard():
    # Get data (real or fallback to mock)
    try:
        daily_df, current_stats, classification_df, system_metrics = get_real_data()
        
        # Update refresh timestamp
        refresh_placeholder.markdown(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Overview metrics
        st.markdown('<h2 class="section-header">📊 Overview</h2>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<p class="metric-title">Total Emails Processed</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">{current_stats["total_emails"]:,}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<p class="metric-title">Emails Today</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">{current_stats["emails_today"]}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<p class="metric-title">Avg Response Time</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">{current_stats["avg_response_time"]:.1f} min</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<p class="metric-title">Success Rate</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">{current_stats["success_rate"]:.1f}%</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Email Triage Metrics
        st.markdown('<h2 class="section-header">📧 Email Classification</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart of email categories
            fig = px.pie(
                classification_df, 
                values='count', 
                names='category',
                color='category',
                color_discrete_map={
                    'Urgent': '#FF6B6B',
                    'Action Required': '#4ECDC4',
                    'Informational': '#45B7D1'
                },
                title="Email Classification Breakdown"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # Bar chart of daily email volume by category
            fig = px.bar(
                daily_df.tail(7),
                x='date',
                y=['urgent', 'action_required', 'informational'],
                title="Daily Email Volume (Last 7 Days)",
                labels={'value': 'Count', 'date': 'Date', 'variable': 'Category'},
                color_discrete_map={
                    'urgent': '#FF6B6B',
                    'action_required': '#4ECDC4',
                    'informational': '#45B7D1'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Time Series Data
        st.markdown('<h2 class="section-header">📈 Time Series Analysis</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Line chart of emails processed over time
            fig = px.line(
                daily_df,
                x='date',
                y='emails_processed',
                title="Emails Processed Over Time",
                labels={'emails_processed': 'Count', 'date': 'Date'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # Line chart of response time over time
            fig = px.line(
                daily_df,
                x='date',
                y='avg_response_time_min',
                title="Average Response Time (minutes)",
                labels={'avg_response_time_min': 'Minutes', 'date': 'Date'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # System Performance Metrics
        st.markdown('<h2 class="section-header">⚙️ System Performance</h2>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CPU Usage
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=system_metrics['cpu_usage'],
                title={'text': "CPU Usage"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#1E88E5"},
                    'steps': [
                        {'range': [0, 50], 'color': "#EDFFF2"},
                        {'range': [50, 75], 'color': "#FFE77A"},
                        {'range': [75, 100], 'color': "#FFCAC8"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # Memory Usage
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=system_metrics['memory_usage'],
                title={'text': "Memory Usage"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#4ECDC4"},
                    'steps': [
                        {'range': [0, 50], 'color': "#EDFFF2"},
                        {'range': [50, 75], 'color': "#FFE77A"},
                        {'range': [75, 100], 'color': "#FFCAC8"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
            
        with col3:
            # Disk Usage
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=system_metrics['disk_usage'],
                title={'text': "Disk Usage"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#FF6B6B"},
                    'steps': [
                        {'range': [0, 50], 'color': "#EDFFF2"},
                        {'range': [50, 75], 'color': "#FFE77A"},
                        {'range': [75, 100], 'color': "#FFCAC8"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        # API Metrics
        st.markdown('<h2 class="section-header">🌐 API Performance</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<p class="metric-title">API Success Rate</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">{system_metrics["api_success_rate"]:.2f}%</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<p class="metric-title">API Calls per Minute</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">{system_metrics["api_calls_per_min"]}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"An error occurred while updating the dashboard: {str(e)}")

# Run the dashboard update function
update_dashboard()

# Auto-refresh logic
if refresh_rate > 0:
    refresh_button = st.empty()
    refresh_button.button("Refresh Now")
    
    # Create an auto-refresh mechanism
    st.markdown(
        f"""
        <script>
            var refreshRate = {refresh_rate * 1000};
            setInterval(function() {{
                window.location.reload();
            }}, refreshRate);
        </script>
        """,
        unsafe_allow_html=True
    )

# Footer
st.markdown("---")
st.caption("© 2025 Email Triage Workflow | Data is refreshed automatically") 