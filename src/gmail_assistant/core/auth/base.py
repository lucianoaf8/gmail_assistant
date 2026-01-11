"""
Base authentication module for Gmail Fetcher.
Provides common authentication patterns and utilities to eliminate code duplication.

Security: Implements rate limiting on authentication attempts (L-2 fix)
H-2 fix: Uses centralized AuthError from exceptions.py
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from gmail_assistant.core.exceptions import AuthError
from gmail_assistant.utils.error_handler import ErrorCategory, ErrorContext, ErrorHandler

from .credential_manager import SecureCredentialManager
from .rate_limiter import get_auth_rate_limiter

logger = logging.getLogger(__name__)

# H-2: Backward compatibility alias
AuthenticationError = AuthError


class AuthenticationBase(ABC):
    """
    Abstract base class for Gmail API authentication.
    Provides common authentication patterns and error handling.
    """

    def __init__(self, credentials_file: str = 'credentials.json',
                 required_scopes: list[str] | None = None):
        """
        Initialize authentication base.

        Args:
            credentials_file: Path to OAuth credentials file
            required_scopes: Required OAuth scopes
        """
        self.credentials_file = credentials_file
        self.required_scopes = required_scopes or ['https://www.googleapis.com/auth/gmail.readonly']
        self.credential_manager = SecureCredentialManager(credentials_file)
        self.error_handler = ErrorHandler()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Authentication state
        self._authenticated = False
        self._service = None
        self._user_info = None

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated and self._service is not None

    @property
    def service(self):
        """Get authenticated Gmail service."""
        if not self.is_authenticated and not self.authenticate():
            raise AuthenticationError("Failed to authenticate with Gmail API")
        return self._service

    @property
    def user_info(self) -> dict[str, Any] | None:
        """Get cached user information."""
        return self._user_info

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API with rate limiting (L-2 security fix).

        Returns:
            True if authentication successful, False otherwise
        """
        # Get rate limiter (L-2 fix)
        rate_limiter = get_auth_rate_limiter()

        # Check rate limit before attempting authentication
        if not rate_limiter.check_rate_limit(self.credentials_file):
            remaining = rate_limiter.get_lockout_remaining(self.credentials_file)
            self._handle_auth_failure(
                f"Authentication rate limited. Try again in {remaining} seconds."
            )
            return False

        try:
            self.logger.info("Starting Gmail API authentication")

            # Check if already authenticated
            if self.is_authenticated:
                self.logger.info("Already authenticated")
                return True

            # Perform authentication using credential manager
            success = self.credential_manager.authenticate()

            if success:
                self._service = self.credential_manager.get_service()
                self._authenticated = True

                # Validate OAuth scopes match required scopes (M-AUDIT-01 fix)
                required_scopes = self.get_required_scopes()
                scope_valid, missing_scopes = self.credential_manager.validate_scopes(
                    required_scopes
                )
                if not scope_valid:
                    self._handle_auth_failure(
                        f"OAuth scope mismatch. Missing scopes: {missing_scopes}. "
                        f"Please re-authenticate with the correct permissions."
                    )
                    # Clear invalid credentials
                    self.credential_manager.reset_credentials()
                    return False

                # Get user information
                self._user_info = self._fetch_user_info()

                # Record successful attempt (L-2 fix)
                rate_limiter.record_attempt(self.credentials_file, success=True)

                self.logger.info(f"Authentication successful for {self._user_info.get('email', 'unknown user')}")
                return True
            else:
                # Record failed attempt (L-2 fix)
                rate_limiter.record_attempt(self.credentials_file, success=False)
                remaining = rate_limiter.get_remaining_attempts(self.credentials_file)
                self._handle_auth_failure(
                    f"Credential manager authentication failed. "
                    f"{remaining} attempts remaining."
                )
                return False

        except Exception as e:
            # Record failed attempt (L-2 fix)
            rate_limiter.record_attempt(self.credentials_file, success=False)

            context = ErrorContext(
                operation="authenticate",
                additional_data={"credentials_file": self.credentials_file}
            )
            self.error_handler.handle_error(e, context)
            self._handle_auth_failure(f"Authentication error: {e}")
            return False

    def _fetch_user_info(self) -> dict[str, Any] | None:
        """Fetch user information from Gmail API."""
        try:
            if self._service:
                return self.credential_manager.get_user_info()
        except Exception as e:
            self.logger.warning(f"Failed to fetch user info: {e}")
        return None

    def _handle_auth_failure(self, message: str) -> None:
        """Handle authentication failure."""
        self._authenticated = False
        self._service = None
        self._user_info = None
        self.logger.error(message)

    def reset_authentication(self) -> bool:
        """
        Reset authentication and force re-authentication.

        Returns:
            True if reset successful, False otherwise
        """
        try:
            self.logger.info("Resetting authentication")

            # Clear current state
            self._authenticated = False
            self._service = None
            self._user_info = None

            # Reset credential manager
            success = self.credential_manager.reset_credentials()

            if success:
                self.logger.info("Authentication reset successful")
                return True
            else:
                self.logger.error("Failed to reset authentication")
                return False

        except Exception as e:
            context = ErrorContext(operation="reset_authentication")
            self.error_handler.handle_error(e, context)
            return False

    def validate_scopes(self) -> bool:
        """
        Validate that current authentication has required scopes.

        Returns:
            True if scopes are valid, False otherwise
        """
        try:
            if not self.is_authenticated:
                return False

            # Validate granted scopes against required scopes (M-AUDIT-01 fix)
            required_scopes = self.get_required_scopes()
            scope_valid, missing_scopes = self.credential_manager.validate_scopes(
                required_scopes
            )

            if not scope_valid:
                self.logger.warning(
                    f"Scope validation failed - missing scopes: {missing_scopes}"
                )
                return False

            # Additionally verify API access works
            user_info = self.credential_manager.get_user_info()
            if user_info:
                self.logger.info("Scope validation successful")
                return True
            else:
                self.logger.warning("Scope validation failed - cannot access user profile")
                return False

        except Exception as e:
            self.logger.error(f"Scope validation error: {e}")
            return False

    def get_authentication_status(self) -> dict[str, Any]:
        """
        Get detailed authentication status.

        Returns:
            Dictionary with authentication status information
        """
        return {
            'authenticated': self.is_authenticated,
            'credentials_file': self.credentials_file,
            'required_scopes': self.required_scopes,
            'user_email': self._user_info.get('email') if self._user_info else None,
            'messages_total': self._user_info.get('messages_total') if self._user_info else None,
            'service_available': self._service is not None
        }

    @abstractmethod
    def get_required_scopes(self) -> list[str]:
        """
        Get list of required OAuth scopes for this implementation.

        Returns:
            List of required scope strings
        """
        pass

    def check_credentials_file(self) -> bool:
        """
        Check if credentials file exists and is valid.

        Returns:
            True if credentials file is valid, False otherwise
        """
        try:
            credentials_path = Path(self.credentials_file)

            if not credentials_path.exists():
                self.logger.error(f"Credentials file not found: {credentials_path}")
                return False

            if not credentials_path.is_file():
                self.logger.error(f"Credentials path is not a file: {credentials_path}")
                return False

            if credentials_path.stat().st_size == 0:
                self.logger.error(f"Credentials file is empty: {credentials_path}")
                return False

            self.logger.info(f"Credentials file validation successful: {credentials_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error checking credentials file: {e}")
            return False

    def setup_authentication_recovery(self) -> None:
        """Setup automatic recovery for authentication errors."""
        def auth_recovery_handler(error):
            """Handle authentication recovery."""
            try:
                if error.category == ErrorCategory.AUTHENTICATION:
                    self.logger.info("Attempting authentication recovery")
                    return self.reset_authentication()
                return False
            except Exception as e:
                self.logger.error(f"Authentication recovery failed: {e}")
                return False

        # Register recovery handler
        self.error_handler.register_recovery_handler(
            ErrorCategory.AUTHENTICATION,
            auth_recovery_handler
        )


class ReadOnlyGmailAuth(AuthenticationBase):
    """Authentication for read-only Gmail operations."""

    def get_required_scopes(self) -> list[str]:
        """Get read-only Gmail scopes."""
        return ['https://www.googleapis.com/auth/gmail.readonly']


class GmailModifyAuth(AuthenticationBase):
    """Authentication for Gmail operations that modify data (delete, modify labels)."""

    def get_required_scopes(self) -> list[str]:
        """Get Gmail modify scopes."""
        return ['https://www.googleapis.com/auth/gmail.modify']


class FullGmailAuth(AuthenticationBase):
    """Authentication for full Gmail access."""

    def get_required_scopes(self) -> list[str]:
        """Get full Gmail access scopes."""
        return [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.compose'
        ]


class AuthenticationFactory:
    """Factory for creating appropriate authentication instances."""

    @staticmethod
    def create_auth(auth_type: str, credentials_file: str = 'credentials.json') -> AuthenticationBase:
        """
        Create authentication instance based on type.

        Args:
            auth_type: Type of authentication ('readonly', 'modify', 'full')
            credentials_file: Path to credentials file

        Returns:
            Authentication instance

        Raises:
            ValueError: If auth_type is invalid
        """
        auth_classes = {
            'readonly': ReadOnlyGmailAuth,
            'modify': GmailModifyAuth,
            'full': FullGmailAuth
        }

        if auth_type not in auth_classes:
            raise ValueError(f"Invalid auth type: {auth_type}. Must be one of: {list(auth_classes.keys())}")

        auth_class = auth_classes[auth_type]
        instance = auth_class(credentials_file)

        # Setup recovery
        instance.setup_authentication_recovery()

        return instance

    @staticmethod
    def get_auth_for_scopes(required_scopes: list[str],
                           credentials_file: str = 'credentials.json') -> AuthenticationBase:
        """
        Get authentication instance for specific scopes.

        Args:
            required_scopes: List of required OAuth scopes
            credentials_file: Path to credentials file

        Returns:
            Authentication instance
        """
        # Determine auth type based on scopes
        readonly_scopes = {'https://www.googleapis.com/auth/gmail.readonly'}
        modify_scopes = {'https://www.googleapis.com/auth/gmail.modify'}

        scope_set = set(required_scopes)

        if scope_set <= readonly_scopes:
            return AuthenticationFactory.create_auth('readonly', credentials_file)
        elif scope_set <= (readonly_scopes | modify_scopes):
            return AuthenticationFactory.create_auth('modify', credentials_file)
        else:
            return AuthenticationFactory.create_auth('full', credentials_file)


# Utility functions for common authentication patterns
def ensure_authenticated(auth_instance: AuthenticationBase) -> bool:
    """
    Ensure authentication instance is authenticated.

    Args:
        auth_instance: Authentication instance

    Returns:
        True if authenticated, False otherwise
    """
    if not auth_instance.is_authenticated:
        return auth_instance.authenticate()
    return True


def get_authenticated_service(auth_type: str = 'readonly',
                            credentials_file: str = 'credentials.json'):
    """
    Get authenticated Gmail service with error handling.

    Args:
        auth_type: Type of authentication
        credentials_file: Path to credentials file

    Returns:
        Authenticated Gmail service

    Raises:
        AuthenticationError: If authentication fails
    """
    auth = AuthenticationFactory.create_auth(auth_type, credentials_file)

    if not auth.authenticate():
        raise AuthenticationError(f"Failed to authenticate for {auth_type} access")

    return auth.service


def validate_authentication_setup(credentials_file: str = 'credentials.json') -> dict[str, Any]:
    """
    Validate authentication setup and return status.

    Args:
        credentials_file: Path to credentials file

    Returns:
        Dictionary with validation results
    """
    results = {
        'credentials_file_valid': False,
        'authentication_successful': False,
        'user_info': None,
        'errors': []
    }

    try:
        # Check credentials file
        auth = ReadOnlyGmailAuth(credentials_file)
        results['credentials_file_valid'] = auth.check_credentials_file()

        if results['credentials_file_valid']:
            # Test authentication
            if auth.authenticate():
                results['authentication_successful'] = True
                results['user_info'] = auth.user_info
            else:
                results['errors'].append("Authentication failed")
        else:
            results['errors'].append("Invalid credentials file")

    except Exception as e:
        results['errors'].append(f"Validation error: {e}")

    return results
