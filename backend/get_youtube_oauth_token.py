#!/usr/bin/env python3
"""
YouTube OAuth Token Generator

This script helps you generate an OAuth 2.0 access token for YouTube Data API.
The token is required to update video descriptions.

Prerequisites:
1. Google Cloud Project with YouTube Data API v3 enabled
2. OAuth 2.0 Client ID credentials (Desktop application type)
3. Download the credentials JSON file

Setup:
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Application type: Desktop app)
3. Download the client configuration JSON
4. Save it as 'client_secrets.json' in this directory

Usage:
    python get_youtube_oauth_token.py

This will open a browser for authentication and save the token to .env file
"""

import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv, set_key

# OAuth scopes needed for YouTube Data API
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

# Client secrets file path
CLIENT_SECRETS_FILE = "client_secrets.json"


def check_client_secrets():
    """Check if client secrets file exists"""
    if not Path(CLIENT_SECRETS_FILE).exists():
        print("❌ Error: client_secrets.json not found!")
        print()
        print("Please follow these steps:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 Client ID (Application type: Desktop app)")
        print("3. Download the JSON file")
        print("4. Save it as 'client_secrets.json' in this directory")
        print()
        return False
    return True


def get_oauth_token():
    """
    Generate OAuth 2.0 token using installed app flow

    Returns:
        str: Access token
    """
    if not check_client_secrets():
        return None

    print("Starting OAuth flow...")
    print("A browser window will open for authentication.")
    print()

    # Create the flow using the client secrets file
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES
    )

    # Run the OAuth flow
    credentials = flow.run_local_server(
        port=8080,
        prompt='consent',
        success_message='Authorization successful! You can close this window.'
    )

    print()
    print("✅ Successfully authenticated!")
    print()
    print("Access Token:")
    print(credentials.token)
    print()
    print("Token Type:", credentials.token_uri)
    print("Expires at:", credentials.expiry)
    print()

    # Save token to .env file
    env_file = Path('.env')
    if env_file.exists():
        set_key(env_file, 'YOUTUBE_OAUTH_TOKEN', credentials.token)
        print("✅ Token saved to .env file as YOUTUBE_OAUTH_TOKEN")
    else:
        print("⚠️  No .env file found. Creating one...")
        with open('.env', 'w') as f:
            f.write(f'YOUTUBE_OAUTH_TOKEN={credentials.token}\n')
        print("✅ Created .env file with token")

    print()
    print("Note: This token will expire. You may need to regenerate it periodically.")
    print("Typical expiration time: 1 hour")
    print()

    # Optionally save refresh token if available
    if credentials.refresh_token:
        set_key(env_file, 'YOUTUBE_REFRESH_TOKEN', credentials.refresh_token)
        print("✅ Refresh token also saved (can be used to get new access tokens)")

    return credentials.token


def main():
    """Main execution"""
    print("=" * 70)
    print("YouTube OAuth Token Generator")
    print("=" * 70)
    print()

    token = get_oauth_token()

    if token:
        print()
        print("You can now use the update_youtube_descriptions.py script with:")
        print("  python update_youtube_descriptions.py --execute")
        print()
        print("Or manually set the token:")
        print(f'  export YOUTUBE_OAUTH_TOKEN="{token}"')
        print()
        return 0
    else:
        print("Failed to get OAuth token")
        return 1


if __name__ == "__main__":
    exit(main())
