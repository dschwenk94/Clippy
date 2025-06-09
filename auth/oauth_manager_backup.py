"""
OAuth flow management for Google/YouTube authentication
"""

import os
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from flask import current_app, session, request
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from .models import User, UserSession
from .token_manager import token_manager

logger = logging.getLogger(__name__)


class OAuthManager:
    """Manages OAuth authentication flow for YouTube"""
    
    # OAuth scopes required for YouTube upload and user info
    OAUTH_SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email'
    ]
    
    def __init__(self, client_secrets_file: str = None):
        """Initialize OAuth manager"""
        self.client_secrets_file = client_secrets_file or 'client_secrets.json'
        self._flow = None
    
    def create_flow(self, redirect_uri: str = None) -> Flow:
        """Create OAuth flow instance"""
        if not os.path.exists(self.client_secrets_file):
            raise FileNotFoundError(
                f"OAuth credentials file not found: {self.client_secrets_file}. "
                "Please ensure client_secrets.json exists."
            )
        
        flow = Flow.from_client_secrets_file(
            self.client_secrets_file,
            scopes=self.OAUTH_SCOPES
        )
        
        if redirect_uri:
            flow.redirect_uri = redirect_uri
        
        return flow
    
    def get_authorization_url(self, redirect_uri: str, state: str = None) -> tuple:
        """Get OAuth authorization URL"""
        flow = self.create_flow(redirect_uri)
        
        if not state:
            state = secrets.token_urlsafe(32)
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Force consent to ensure refresh token
        )
        
        return authorization_url, state
    
    def handle_oauth_callback(self, authorization_response: str, 
                            state: str, redirect_uri: str) -> Optional[User]:
        """Handle OAuth callback and create/update user"""
        try:
            # For local development, allow insecure transport
            import os
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            
            # Create flow and exchange code for tokens
            flow = self.create_flow(redirect_uri)
            
            # Handle scope mismatch by updating flow scopes to match what Google returns
            # Google automatically adds 'openid' scope
            flow.oauth2session.scope = None  # This tells the session to not validate scopes
            
            try:
                flow.fetch_token(authorization_response=authorization_response)
            except Exception as token_error:
                logger.error(f"Token fetch error: {token_error}")
                # Try alternative approach: manually extract the code
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(authorization_response)
                code = parse_qs(parsed.query).get('code', [None])[0]
                if code:
                    flow.fetch_token(code=code)
                else:
                    raise token_error
            
            credentials = flow.credentials
            logger.info(f"Got credentials with token: {bool(credentials.token)}")
            
            # Get user info from Google
            user_info = self._get_google_user_info(credentials)
            if not user_info:
                logger.error("Failed to get user info from Google")
                return None
            
            logger.info(f"Got user info: {user_info.get('email')}")
            
            # Create or update user
            user = self._create_or_update_user(user_info, credentials)
            
            if user:
                # Create session
                self._create_user_session(user)
                logger.info(f"User {user.email} authenticated successfully")
            else:
                logger.error("Failed to create/update user")
            
            return user
            
        except Exception as e:
            logger.error(f"OAuth callback failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_google_user_info(self, credentials: Credentials) -> Optional[dict]:
        """Get user information from Google"""
        try:
            # Build OAuth2 service to get user info
            oauth2_service = build('oauth2', 'v2', credentials=credentials)
            user_info = oauth2_service.userinfo().get().execute()
            
            return {
                'google_id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture_url': user_info.get('picture')
            }
        except Exception as e:
            logger.error(f"Failed to get Google user info: {e}")
            return None
    
    def _create_or_update_user(self, user_info: dict, credentials: Credentials) -> Optional[User]:
        """Create new user or update existing user with tokens"""
        try:
            # Prepare tokens for storage
            tokens = {
                'refresh_token': credentials.refresh_token,
                'access_token': credentials.token,
                'expires_in': getattr(credentials, 'expires_in', 3600)
            }
            
            encrypted_refresh, encrypted_access, expires_at = \
                token_manager.prepare_tokens_for_storage(tokens)
            
            # Check if user exists
            user = User.get_by_google_id(user_info['google_id'])
            
            if user:
                # Update existing user
                user.email = user_info['email']
                user.name = user_info['name']
                user.picture_url = user_info['picture_url']
                user.refresh_token = encrypted_refresh or user.refresh_token  # Keep existing if no new one
                user.access_token = encrypted_access
                user.token_expires_at = expires_at
                user.last_login = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    google_id=user_info['google_id'],
                    email=user_info['email'],
                    name=user_info['name'],
                    picture_url=user_info['picture_url'],
                    refresh_token=encrypted_refresh,
                    access_token=encrypted_access,
                    token_expires_at=expires_at,
                    last_login=datetime.utcnow()
                )
            
            if user.save():
                return user
            else:
                logger.error("Failed to save user to database")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create/update user: {e}")
            return None
    
    def _create_user_session(self, user: User):
        """Create session for authenticated user"""
        # Generate session token
        session_token = token_manager.generate_session_token()
        
        # Set expiry (7 days as configured)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Get request info
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Create session in database
        UserSession.create_session(
            user_id=user.id,
            session_token=session_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Set Flask session
        session['user_id'] = user.id
        session['session_token'] = session_token
        session.permanent = True
    
    def get_youtube_service(self, user: User):
        """Get YouTube service for a user"""
        try:
            # Get decrypted tokens
            tokens = token_manager.get_decrypted_tokens(user)
            if not tokens:
                logger.error("No tokens available for user")
                return None
            
            # Create credentials
            creds = Credentials(
                token=tokens.get('access_token'),
                refresh_token=tokens['refresh_token'],
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self._get_client_id(),
                client_secret=self._get_client_secret()
            )
            
            # Refresh if needed
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    
                    # Update tokens in database
                    encrypted_access = token_manager.encrypt_token(creds.token)
                    expires_at = datetime.utcnow() + timedelta(seconds=3600)
                    
                    user.access_token = encrypted_access
                    user.token_expires_at = expires_at
                    user.save()
            
            # Build YouTube service
            return build('youtube', 'v3', credentials=creds)
            
        except Exception as e:
            logger.error(f"Failed to get YouTube service: {e}")
            return None
    
    def _get_client_id(self) -> str:
        """Get client ID from secrets file"""
        import json
        with open(self.client_secrets_file, 'r') as f:
            secrets = json.load(f)
            return secrets.get('web', {}).get('client_id', '')
    
    def _get_client_secret(self) -> str:
        """Get client secret from secrets file"""
        import json
        with open(self.client_secrets_file, 'r') as f:
            secrets = json.load(f)
            return secrets.get('web', {}).get('client_secret', '')
    
    def revoke_user_credentials(self, user: User) -> bool:
        """Revoke user's OAuth credentials"""
        try:
            tokens = token_manager.get_decrypted_tokens(user)
            if not tokens:
                return True  # Already revoked
            
            # Revoke token with Google
            import requests
            response = requests.post(
                'https://oauth2.googleapis.com/revoke',
                params={'token': tokens['refresh_token']},
                headers={'content-type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                # Clear tokens in database
                user.refresh_token = None
                user.access_token = None
                user.token_expires_at = None
                user.save()
                
                logger.info(f"Revoked credentials for user {user.email}")
                return True
            else:
                logger.error(f"Failed to revoke token: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to revoke credentials: {e}")
            return False


# Global OAuth manager instance
oauth_manager = OAuthManager()
