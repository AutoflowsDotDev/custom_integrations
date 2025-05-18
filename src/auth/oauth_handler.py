"""
OAuth2 handlers for Google and Slack authentication.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError

# Path to store OAuth tokens
DATA_DIR = Path("/app/data") if os.path.exists("/app/data") else Path("./data")
DATA_DIR.mkdir(exist_ok=True)
TOKENS_DIR = DATA_DIR / "tokens"
TOKENS_DIR.mkdir(exist_ok=True)

# Google OAuth2 settings
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8501/google_callback")
GOOGLE_TOKEN_FILE = TOKENS_DIR / "google_token.json"
GOOGLE_AUTH_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/pubsub',
    'openid',
    'email',
    'profile'
]
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

# Slack OAuth2 settings
SLACK_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID", "")
SLACK_CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET", "")
SLACK_REDIRECT_URI = os.environ.get("SLACK_REDIRECT_URI", "http://localhost:8501/slack_callback")
SLACK_TOKEN_FILE = TOKENS_DIR / "slack_token.json"
SLACK_AUTH_SCOPES = [
    'chat:write',
    'channels:read',
    'channels:history',
    'chat:write.customize',
    'users:read'
]
SLACK_AUTH_URL = "https://slack.com/oauth/v2/authorize"
SLACK_TOKEN_URL = "https://slack.com/api/oauth.v2.access"
SLACK_USERINFO_URL = "https://slack.com/api/users.identity"

class OAuth2Handler:
    """Base class for OAuth2 handlers."""
    
    def __init__(self, 
                 client_id: str,
                 client_secret: str,
                 redirect_uri: str,
                 token_file: Path,
                 auth_url: str,
                 token_url: str,
                 scopes: List[str],
                 userinfo_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_file = token_file
        self.auth_url = auth_url
        self.token_url = token_url
        self.scopes = scopes
        self.userinfo_url = userinfo_url
        self.token = self._load_token()
        
    def _load_token(self) -> Optional[Dict[str, Any]]:
        """Load the OAuth2 token from file."""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return None
        return None
    
    def _save_token(self, token: Dict[str, Any]) -> None:
        """Save the OAuth2 token to file."""
        with open(self.token_file, 'w') as f:
            json.dump(token, f)
        self.token = token
    
    def get_authorization_url(self) -> Tuple[str, str]:
        """Get the authorization URL for the OAuth2 flow."""
        oauth_session = OAuth2Session(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=self.scopes
        )
        authorization_url, state = oauth_session.authorization_url(self.auth_url)
        return authorization_url, state
    
    def fetch_token(self, authorization_response: str, state: str) -> Dict[str, Any]:
        """Fetch the OAuth2 token using the authorization response."""
        oauth_session = OAuth2Session(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            state=state
        )
        token = oauth_session.fetch_token(
            token_url=self.token_url,
            authorization_response=authorization_response,
            client_secret=self.client_secret
        )
        self._save_token(token)
        return token
    
    def get_session(self) -> OAuth2Session:
        """Get an OAuth2 session with automatic token refresh."""
        def token_updater(token):
            self._save_token(token)
            
        session = OAuth2Session(
            client_id=self.client_id,
            token=self.token,
            auto_refresh_url=self.token_url,
            auto_refresh_kwargs={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            },
            token_updater=token_updater
        )
        return session
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get user information using the OAuth2 token."""
        if not self.token:
            return {}
            
        try:
            session = self.get_session()
            response = session.get(self.userinfo_url)
            return response.json()
        except TokenExpiredError:
            # Token refresh is handled automatically in the session
            session = self.get_session()
            response = session.get(self.userinfo_url)
            return response.json()
        except Exception as e:
            print(f"Error getting user info: {e}")
            return {}
    
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.token is not None
    
    def revoke_token(self) -> bool:
        """Revoke the OAuth2 token."""
        if self.token_file.exists():
            self.token_file.unlink()
        self.token = None
        return True


class GoogleOAuth2Handler(OAuth2Handler):
    """Google OAuth2 handler."""
    
    def __init__(self):
        super().__init__(
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            redirect_uri=GOOGLE_REDIRECT_URI,
            token_file=GOOGLE_TOKEN_FILE,
            auth_url=GOOGLE_AUTH_URL,
            token_url=GOOGLE_TOKEN_URL,
            scopes=GOOGLE_AUTH_SCOPES,
            userinfo_url=GOOGLE_USERINFO_URL
        )
    
    def get_credentials_dict(self) -> Dict[str, Any]:
        """Get Google API credentials dictionary for direct API use."""
        if not self.token:
            return {}
            
        return {
            'token': self.token.get('access_token'),
            'refresh_token': self.token.get('refresh_token'),
            'token_uri': GOOGLE_TOKEN_URL,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scopes': self.scopes
        }


class SlackOAuth2Handler(OAuth2Handler):
    """Slack OAuth2 handler."""
    
    def __init__(self):
        super().__init__(
            client_id=SLACK_CLIENT_ID,
            client_secret=SLACK_CLIENT_SECRET,
            redirect_uri=SLACK_REDIRECT_URI,
            token_file=SLACK_TOKEN_FILE,
            auth_url=SLACK_AUTH_URL,
            token_url=SLACK_TOKEN_URL,
            scopes=SLACK_AUTH_SCOPES,
            userinfo_url=SLACK_USERINFO_URL
        )
    
    def fetch_token(self, authorization_response: str, state: str) -> Dict[str, Any]:
        """Fetch the Slack OAuth2 token using the authorization response."""
        # Extract code from the authorization response
        code = authorization_response.split('code=')[1].split('&')[0]
        
        # Exchange code for token
        response = requests.post(
            self.token_url,
            data={
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri
            }
        )
        token_data = response.json()
        
        # Slack returns a nested structure, flatten it for consistency
        token = {
            'access_token': token_data.get('access_token', ''),
            'token_type': 'bearer',
            'scope': token_data.get('scope', ''),
            'team_id': token_data.get('team', {}).get('id', ''),
            'team_name': token_data.get('team', {}).get('name', ''),
            'user_id': token_data.get('authed_user', {}).get('id', ''),
            'bot_user_id': token_data.get('bot_user_id', '')
        }
        
        self._save_token(token)
        return token
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get user information from Slack."""
        if not self.token:
            return {}
            
        try:
            response = requests.get(
                self.userinfo_url,
                headers={
                    'Authorization': f"Bearer {self.token.get('access_token')}"
                }
            )
            data = response.json()
            if data.get('ok', False):
                return {
                    'user_id': data.get('user', {}).get('id', ''),
                    'name': data.get('user', {}).get('name', ''),
                    'email': data.get('user', {}).get('email', ''),
                    'team_id': data.get('team', {}).get('id', ''),
                    'team_name': data.get('team', {}).get('name', '')
                }
            return {}
        except Exception as e:
            print(f"Error getting Slack user info: {e}")
            return {}


# Global instances of the OAuth2 handlers
_google_auth_handler = None
_slack_auth_handler = None

def get_google_auth_handler() -> GoogleOAuth2Handler:
    """Get the global Google OAuth2 handler instance."""
    global _google_auth_handler
    if _google_auth_handler is None:
        _google_auth_handler = GoogleOAuth2Handler()
    return _google_auth_handler

def get_slack_auth_handler() -> SlackOAuth2Handler:
    """Get the global Slack OAuth2 handler instance."""
    global _slack_auth_handler
    if _slack_auth_handler is None:
        _slack_auth_handler = SlackOAuth2Handler()
    return _slack_auth_handler

def is_google_authenticated() -> bool:
    """Check if the user is authenticated with Google."""
    return get_google_auth_handler().is_authenticated()

def is_slack_authenticated() -> bool:
    """Check if the user is authenticated with Slack."""
    return get_slack_auth_handler().is_authenticated() 