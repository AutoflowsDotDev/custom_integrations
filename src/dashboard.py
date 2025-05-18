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
    conn = sqlite3.connect(db_path)
    return conn

def get_mock_data():
    """Generate mock data for demonstration"""
    # In production, replace this with actual database queries
    
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
    # Get data (mock or real)
    try:
        daily_df, current_stats, classification_df, system_metrics = get_mock_data()
        
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