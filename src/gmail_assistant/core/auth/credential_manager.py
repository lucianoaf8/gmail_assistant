"""
Secure credential management for Gmail Fetcher using OS keyring.
Replaces plain text token storage with encrypted OS-level storage.
"""

import json
import os

import keyring
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from gmail_assistant.core.constants import KEYRING_SERVICE, KEYRING_USERNAME

# Import centralized constants
from gmail_assistant.core.constants import SCOPES_READONLY as SCOPES
from gmail_assistant.utils.secure_logger import SecureLogger

logger = SecureLogger(__name__)


class SecureCredentialManager:
    """Manages Gmail API credentials using secure OS keyring storage."""

    def __init__(self, credentials_file: str = 'credentials.json'):
        """
        Initialize credential manager.

        Args:
            credentials_file: Path to OAuth client credentials file
        """
        self.credentials_file = credentials_file
        self.service = None
        self._credentials: Credentials | None = None

    def _store_credentials_securely(self, creds: Credentials) -> bool:
        """
        Store credentials in OS keyring.

        Args:
            creds: OAuth credentials to store

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            credentials_json = creds.to_json()
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, credentials_json)
            logger.info("Credentials stored securely in OS keyring")
            return True
        except Exception as e:
            logger.error(f"Failed to store credentials securely: {e}")
            return False

    def _load_credentials_securely(self) -> Credentials | None:
        """
        Load credentials from OS keyring.

        Returns:
            Credentials object if found, None otherwise
        """
        try:
            credentials_json = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if credentials_json:
                creds = Credentials.from_authorized_user_info(
                    json.loads(credentials_json), SCOPES
                )
                logger.info("Credentials loaded from OS keyring")
                return creds
            else:
                logger.info("No credentials found in OS keyring")
                return None
        except Exception as e:
            logger.error(f"Failed to load credentials from keyring: {e}")
            return None

    def _clear_credentials(self) -> bool:
        """
        Clear stored credentials from keyring.

        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
            logger.info("Credentials cleared from OS keyring")
            return True
        except keyring.errors.PasswordDeleteError:
            logger.info("No credentials found to clear")
            return True
        except Exception as e:
            logger.error(f"Failed to clear credentials: {e}")
            return False

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using secure credential storage.

        Returns:
            True if authentication successful, False otherwise
        """
        creds = None

        # Try to load existing credentials from keyring
        creds = self._load_credentials_securely()

        # Check if credentials are valid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Credentials refreshed successfully")
                    # Store refreshed credentials
                    self._store_credentials_securely(creds)
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                # Need to run OAuth flow
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Credentials file not found: {self.credentials_file}")
                    print(f"❌ Error: {self.credentials_file} not found!")
                    print("📋 Setup Instructions:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a new project or select existing")
                    print("3. Enable Gmail API")
                    print("4. Create OAuth 2.0 credentials (Desktop application)")
                    print("5. Download as 'credentials.json'")
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                    logger.info("OAuth flow completed successfully")

                    # Store new credentials securely
                    if not self._store_credentials_securely(creds):
                        logger.warning("Failed to store credentials securely")
                        return False

                except Exception as e:
                    logger.error(f"OAuth flow failed: {e}")
                    return False

        # Build Gmail service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            self._credentials = creds  # Store for scope validation
            logger.info("Gmail service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            return False

    def get_service(self):
        """
        Get authenticated Gmail service.

        Returns:
            Gmail service object if authenticated, None otherwise
        """
        if not self.service and not self.authenticate():
            return None
        return self.service

    def reset_credentials(self) -> bool:
        """
        Clear stored credentials and force re-authentication.

        Returns:
            True if reset successful, False otherwise
        """
        logger.info("Resetting credentials")
        self.service = None
        return self._clear_credentials()

    def get_user_info(self) -> dict | None:
        """
        Get authenticated user information for validation.

        Returns:
            User profile information if available, None otherwise
        """
        service = self.get_service()
        if not service:
            return None

        try:
            profile = service.users().getProfile(userId='me').execute()
            return {
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal')
            }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    def get_granted_scopes(self) -> list[str]:
        """
        Get the OAuth scopes granted by the authorization server.

        Returns:
            List of granted scope strings, empty list if not authenticated
        """
        if self._credentials and self._credentials.scopes:
            return list(self._credentials.scopes)
        return []

    def validate_scopes(self, required_scopes: list[str]) -> tuple[bool, list[str]]:
        """
        Validate that granted scopes include all required scopes.

        Args:
            required_scopes: List of required OAuth scopes

        Returns:
            Tuple of (is_valid, missing_scopes)
        """
        granted = set(self.get_granted_scopes())
        required = set(required_scopes)
        missing = required - granted

        if missing:
            logger.warning(
                f"Scope validation failed. Missing scopes: {missing}"
            )
            return False, list(missing)

        logger.info("Scope validation successful")
        return True, []
