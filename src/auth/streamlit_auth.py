"""
Streamlit authentication for OAuth2 single sign-on.
"""

import os
import json
import streamlit as st
from typing import Tuple, Dict, Any, Optional
from urllib.parse import urlencode

from .oauth_handler import (
    get_google_auth_handler,
    get_slack_auth_handler,
    is_google_authenticated,
    is_slack_authenticated
)

# Constants
SESSION_KEY = "auth_state"
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8501")


def init_auth_session() -> None:
    """Initialize the authentication session state if not already present."""
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = {
            "google_state": None,
            "slack_state": None,
            "is_authenticated": False,
            "current_user": None,
            "login_error": None
        }


def logout() -> None:
    """Log out the current user by revoking tokens and resetting session state."""
    google_auth = get_google_auth_handler()
    slack_auth = get_slack_auth_handler()
    
    # Revoke tokens
    google_auth.revoke_token()
    slack_auth.revoke_token()
    
    # Reset session state
    st.session_state[SESSION_KEY] = {
        "google_state": None,
        "slack_state": None,
        "is_authenticated": False,
        "current_user": None,
        "login_error": None
    }
    
    # Refresh the page to show login again
    st.rerun()


def handle_oauth_callback(service: str, current_url: str) -> None:
    """Handle OAuth callback responses.
    
    Args:
        service: Either 'google' or 'slack'
        current_url: The current URL with query parameters
    """
    # Get the appropriate auth handler
    if service == "google":
        auth_handler = get_google_auth_handler()
        state_key = "google_state"
    elif service == "slack":
        auth_handler = get_slack_auth_handler()
        state_key = "slack_state"
    else:
        st.error(f"Unknown service: {service}")
        return
    
    # Process the callback
    try:
        # Get the state from session
        state = st.session_state[SESSION_KEY].get(state_key)
        
        # Fetch token
        token = auth_handler.fetch_token(current_url, state)
        
        # Get user info
        user_info = auth_handler.get_user_info()
        
        # Update session state
        st.session_state[SESSION_KEY]["is_authenticated"] = True
        st.session_state[SESSION_KEY]["current_user"] = {
            "service": service,
            "info": user_info
        }
        
        st.success(f"Successfully authenticated with {service.capitalize()}")
        
    except Exception as e:
        st.session_state[SESSION_KEY]["login_error"] = f"Authentication failed: {str(e)}"
        st.error(f"Authentication failed: {str(e)}")


def render_login_page() -> bool:
    """Render the login page with OAuth options.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    init_auth_session()
    
    # Check if already authenticated
    if is_google_authenticated() or is_slack_authenticated():
        st.session_state[SESSION_KEY]["is_authenticated"] = True
        
        # Update current user info if not already set
        if not st.session_state[SESSION_KEY]["current_user"]:
            if is_google_authenticated():
                user_info = get_google_auth_handler().get_user_info()
                st.session_state[SESSION_KEY]["current_user"] = {
                    "service": "google",
                    "info": user_info
                }
            elif is_slack_authenticated():
                user_info = get_slack_auth_handler().get_user_info()
                st.session_state[SESSION_KEY]["current_user"] = {
                    "service": "slack",
                    "info": user_info
                }
                
        return True
    
    # Check for OAuth callbacks in URL
    query_params = st.query_params
    if "code" in query_params:
        # Determine which service this is for
        if "state" in query_params and query_params.get("state", "") == st.session_state[SESSION_KEY].get("google_state"):
            handle_oauth_callback("google", st.get_current_page_name())
            # Remove query params
            st.query_params.clear()
            return is_google_authenticated()
        elif "state" in query_params and query_params.get("state", "") == st.session_state[SESSION_KEY].get("slack_state"):
            handle_oauth_callback("slack", st.get_current_page_name())
            # Remove query params
            st.query_params.clear()
            return is_slack_authenticated()
    
    # Display login options
    st.markdown("# Sign In")
    st.markdown("Please sign in to access the Email Triage Workflow Dashboard.")
    
    # Check for login errors
    if st.session_state[SESSION_KEY].get("login_error"):
        st.error(st.session_state[SESSION_KEY]["login_error"])
        st.session_state[SESSION_KEY]["login_error"] = None
    
    # Create columns for buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Sign in with Google", type="primary", use_container_width=True):
            google_auth = get_google_auth_handler()
            auth_url, state = google_auth.get_authorization_url()
            st.session_state[SESSION_KEY]["google_state"] = state
            st.switch_page(auth_url)  # Redirect to Google login
    
    with col2:
        if st.button("Sign in with Slack", type="primary", use_container_width=True):
            slack_auth = get_slack_auth_handler()
            auth_url, state = slack_auth.get_authorization_url()
            st.session_state[SESSION_KEY]["slack_state"] = state
            st.switch_page(auth_url)  # Redirect to Slack login
    
    # Add space and a separator
    st.markdown("---")
    
    # Show info about the app
    st.markdown("""
    ### About Email Triage Workflow
    
    This dashboard provides metrics and insights for the Email Triage Workflow system.
    
    #### Features:
    - Real-time email processing statistics
    - Performance monitoring
    - System health overview
    
    Please sign in to continue.
    """)
    
    return False


def render_user_menu() -> None:
    """Render the user menu in the sidebar."""
    if not st.session_state[SESSION_KEY].get("is_authenticated"):
        return
        
    user_info = st.session_state[SESSION_KEY].get("current_user", {}).get("info", {})
    service = st.session_state[SESSION_KEY].get("current_user", {}).get("service", "Unknown")
    
    # Get user display info based on service
    if service == "google":
        name = user_info.get("name", "Unknown User")
        email = user_info.get("email", "")
        profile_icon = "👤"  # Default icon
    elif service == "slack":
        name = user_info.get("name", "Unknown User")
        email = user_info.get("email", "")
        profile_icon = "👤"  # Default icon
    else:
        name = "Unknown User"
        email = ""
        profile_icon = "👤"
    
    # Create an expander for user menu
    with st.sidebar:
        st.markdown("---")
        user_menu = st.expander(f"{profile_icon} {name}")
        with user_menu:
            st.write(f"**Name:** {name}")
            if email:
                st.write(f"**Email:** {email}")
            st.write(f"**Service:** {service.capitalize()}")
            if st.button("Sign Out", key="signout"):
                logout()
                

def require_auth(func):
    """Decorator that requires authentication before running a function."""
    def wrapper(*args, **kwargs):
        is_auth = render_login_page()
        if is_auth:
            # User is authenticated, render the function
            return func(*args, **kwargs)
        # User is not authenticated, login page already shown
        return None
    return wrapper 