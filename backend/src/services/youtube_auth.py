"""
YouTube OAuth Authentication Manager
Handles token refresh and credential management
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv, set_key

load_dotenv()

# OAuth scopes needed for YouTube Data API
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# File paths
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token.json"


class YouTubeAuthManager:
    """Manages YouTube OAuth tokens with automatic refresh"""

    def __init__(self):
        self.credentials = None
        self.load_credentials()

    def load_credentials(self) -> bool:
        """
        Load credentials from token.json or environment variables

        Returns:
            bool: True if credentials loaded successfully
        """
        # Try loading from token.json first
        if Path(TOKEN_FILE).exists():
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    TOKEN_FILE,
                    SCOPES
                )
                print("   ✅ Loaded credentials from token.json")
                return True
            except Exception as e:
                print(f"   ⚠️  Error loading token.json: {e}")

        # Try loading from environment variables
        access_token = os.getenv('YOUTUBE_OAUTH_TOKEN')
        refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')

        if access_token:
            self.credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv('YOUTUBE_CLIENT_ID'),
                client_secret=os.getenv('YOUTUBE_CLIENT_SECRET'),
                scopes=SCOPES
            )
            print("   ✅ Loaded credentials from environment")
            return True

        print("   ⚠️  No credentials found")
        return False

    def get_valid_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary

        Returns:
            str: Valid access token or None if failed
        """
        # If no credentials, try to load them
        if not self.credentials:
            if not self.load_credentials():
                print("   ❌ No credentials available")
                return None

        # Refresh token if expired
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                print("   🔄 Token expired, refreshing...")
                self.credentials.refresh(Request())
                self.save_credentials()
                print("   ✅ Token refreshed successfully")
                return self.credentials.token
            except Exception as e:
                print(f"   ❌ Token refresh failed: {e}")
                print("   ℹ️  Please run: python get_youtube_oauth_token.py")
                return None

        # Check if token is valid
        if self.credentials and self.credentials.valid:
            return self.credentials.token

        # Token is invalid and can't be refreshed
        print("   ❌ Token is invalid and cannot be refreshed")
        print("   ℹ️  Please run: python get_youtube_oauth_token.py")
        return None

    def save_credentials(self):
        """Save credentials to token.json"""
        try:
            with open(TOKEN_FILE, 'w') as token:
                token.write(self.credentials.to_json())

            # Also update .env file
            env_file = Path('.env')
            if env_file.exists():
                set_key(env_file, 'YOUTUBE_OAUTH_TOKEN', self.credentials.token)
                if self.credentials.refresh_token:
                    set_key(env_file, 'YOUTUBE_REFRESH_TOKEN', self.credentials.refresh_token)

            print("   ✅ Credentials saved")
        except Exception as e:
            print(f"   ⚠️  Error saving credentials: {e}")

    def authenticate_new(self) -> bool:
        """
        Perform new OAuth authentication flow

        Returns:
            bool: True if successful
        """
        if not Path(CLIENT_SECRETS_FILE).exists():
            print("❌ client_secrets.json not found!")
            print("Please run: python get_youtube_oauth_token.py")
            return False

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                SCOPES
            )

            self.credentials = flow.run_local_server(
                port=8080,
                prompt='consent',
                success_message='Authorization successful! You can close this window.'
            )

            self.save_credentials()
            print("✅ Authentication successful")
            return True

        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False


def get_youtube_token() -> Optional[str]:
    """
    Convenience function to get a valid YouTube OAuth token

    Returns:
        str: Valid access token or None
    """
    auth_manager = YouTubeAuthManager()
    return auth_manager.get_valid_token()
