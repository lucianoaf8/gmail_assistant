"""Unit tests for gmail_assistant.core.auth.base module."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from gmail_assistant.core.auth.base import (
    AuthenticationBase,
    AuthenticationError,
    AuthenticationFactory,
    FullGmailAuth,
    GmailModifyAuth,
    ReadOnlyGmailAuth,
    ensure_authenticated,
    get_authenticated_service,
    validate_authentication_setup,
)
from gmail_assistant.core.exceptions import AuthError


@pytest.fixture
def mock_credential_manager():
    """Create a mock SecureCredentialManager."""
    with patch("gmail_assistant.core.auth.base.SecureCredentialManager") as mock:
        manager = Mock()
        manager.authenticate.return_value = True
        manager.get_service.return_value = Mock()
        manager.get_user_info.return_value = {
            "email": "test@gmail.com",
            "messages_total": 1000,
        }
        manager.validate_scopes.return_value = (True, [])
        manager.reset_credentials.return_value = True
        mock.return_value = manager
        yield mock


@pytest.fixture
def mock_rate_limiter():
    """Create a mock authentication rate limiter."""
    with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as mock:
        limiter = Mock()
        limiter.check_rate_limit.return_value = True
        limiter.record_attempt.return_value = None
        limiter.get_remaining_attempts.return_value = 5
        limiter.get_lockout_remaining.return_value = 0
        mock.return_value = limiter
        yield limiter


@pytest.mark.unit
class TestAuthenticationBase:
    """Test AuthenticationBase abstract class."""

    def test_init_with_defaults(self, mock_credential_manager):
        """Should initialize with default credentials file and scopes."""
        auth = ReadOnlyGmailAuth()

        assert auth.credentials_file == "credentials.json"
        assert auth.required_scopes == ["https://www.googleapis.com/auth/gmail.readonly"]
        assert not auth._authenticated
        assert auth._service is None
        assert auth._user_info is None

    def test_init_with_custom_credentials(self, mock_credential_manager):
        """Should initialize with custom credentials file."""
        auth = ReadOnlyGmailAuth(credentials_file="custom_creds.json")

        assert auth.credentials_file == "custom_creds.json"

    def test_init_with_custom_scopes(self, mock_credential_manager):
        """Should initialize with custom required scopes."""
        custom_scopes = ["https://www.googleapis.com/auth/gmail.modify"]
        auth = ReadOnlyGmailAuth(required_scopes=custom_scopes)

        assert auth.required_scopes == custom_scopes

    def test_is_authenticated_false_initially(self, mock_credential_manager):
        """Should return False when not authenticated."""
        auth = ReadOnlyGmailAuth()

        assert not auth.is_authenticated

    def test_is_authenticated_true_after_auth(
        self, mock_credential_manager, mock_rate_limiter
    ):
        """Should return True after successful authentication."""
        auth = ReadOnlyGmailAuth()
        auth.authenticate()

        assert auth.is_authenticated

    def test_service_property_triggers_auth(
        self, mock_credential_manager, mock_rate_limiter
    ):
        """Service property should trigger authentication if not authenticated."""
        auth = ReadOnlyGmailAuth()

        service = auth.service

        assert service is not None
        assert auth.is_authenticated

    def test_service_property_raises_on_auth_failure(self, mock_credential_manager):
        """Service property should raise AuthenticationError on auth failure."""
        mock_credential_manager.return_value.authenticate.return_value = False

        with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as rate_mock:
            rate_mock.return_value.check_rate_limit.return_value = True
            rate_mock.return_value.record_attempt.return_value = None

            auth = ReadOnlyGmailAuth()

            with pytest.raises(AuthenticationError):
                _ = auth.service

    def test_user_info_property_returns_cached_info(
        self, mock_credential_manager, mock_rate_limiter
    ):
        """Should return cached user information."""
        auth = ReadOnlyGmailAuth()
        auth.authenticate()

        assert auth.user_info is not None
        assert auth.user_info["email"] == "test@gmail.com"


@pytest.mark.unit
class TestAuthenticate:
    """Test authenticate method."""

    def test_authenticate_success(self, mock_credential_manager, mock_rate_limiter):
        """Should authenticate successfully."""
        auth = ReadOnlyGmailAuth()

        result = auth.authenticate()

        assert result is True
        assert auth.is_authenticated
        mock_rate_limiter.record_attempt.assert_called_with(
            auth.credentials_file, success=True
        )

    def test_authenticate_already_authenticated(
        self, mock_credential_manager, mock_rate_limiter
    ):
        """Should return True if already authenticated."""
        auth = ReadOnlyGmailAuth()
        auth.authenticate()

        # Second authentication should skip
        result = auth.authenticate()

        assert result is True

    def test_authenticate_rate_limited(self, mock_credential_manager):
        """Should fail authentication when rate limited."""
        with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as rate_mock:
            limiter = Mock()
            limiter.check_rate_limit.return_value = False
            limiter.get_lockout_remaining.return_value = 900
            rate_mock.return_value = limiter

            auth = ReadOnlyGmailAuth()

            result = auth.authenticate()

            assert result is False
            assert not auth.is_authenticated

    def test_authenticate_credential_manager_failure(
        self, mock_credential_manager, mock_rate_limiter
    ):
        """Should fail when credential manager authentication fails."""
        mock_credential_manager.return_value.authenticate.return_value = False

        auth = ReadOnlyGmailAuth()

        result = auth.authenticate()

        assert result is False
        assert not auth.is_authenticated
        mock_rate_limiter.record_attempt.assert_called_with(
            auth.credentials_file, success=False
        )

    def test_authenticate_scope_mismatch(self, mock_credential_manager, mock_rate_limiter):
        """Should fail when OAuth scopes don't match required scopes."""
        mock_credential_manager.return_value.validate_scopes.return_value = (
            False,
            ["missing.scope"],
        )

        auth = ReadOnlyGmailAuth()

        result = auth.authenticate()

        assert result is False
        assert not auth.is_authenticated
        mock_credential_manager.return_value.reset_credentials.assert_called_once()

    def test_authenticate_handles_exception(self, mock_credential_manager):
        """Should handle exceptions during authentication gracefully."""
        mock_credential_manager.return_value.authenticate.side_effect = Exception(
            "Test error"
        )

        with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as rate_mock:
            limiter = Mock()
            limiter.check_rate_limit.return_value = True
            limiter.record_attempt.return_value = None
            rate_mock.return_value = limiter

            auth = ReadOnlyGmailAuth()

            result = auth.authenticate()

            assert result is False
            assert not auth.is_authenticated


@pytest.mark.unit
class TestResetAuthentication:
    """Test reset_authentication method."""

    def test_reset_authentication_success(self, mock_credential_manager):
        """Should reset authentication successfully."""
        auth = ReadOnlyGmailAuth()

        result = auth.reset_authentication()

        assert result is True
        assert not auth.is_authenticated
        assert auth._service is None
        assert auth._user_info is None
        mock_credential_manager.return_value.reset_credentials.assert_called_once()

    def test_reset_authentication_failure(self, mock_credential_manager):
        """Should return False when reset fails."""
        mock_credential_manager.return_value.reset_credentials.return_value = False

        auth = ReadOnlyGmailAuth()

        result = auth.reset_authentication()

        assert result is False

    def test_reset_authentication_handles_exception(self, mock_credential_manager):
        """Should handle exceptions during reset gracefully."""
        mock_credential_manager.return_value.reset_credentials.side_effect = Exception(
            "Test error"
        )

        auth = ReadOnlyGmailAuth()

        result = auth.reset_authentication()

        assert result is False


@pytest.mark.unit
class TestValidateScopes:
    """Test validate_scopes method."""

    def test_validate_scopes_success(
        self, mock_credential_manager, mock_rate_limiter
    ):
        """Should validate scopes successfully."""
        auth = ReadOnlyGmailAuth()
        auth.authenticate()

        result = auth.validate_scopes()

        assert result is True

    def test_validate_scopes_not_authenticated(self, mock_credential_manager):
        """Should return False when not authenticated."""
        auth = ReadOnlyGmailAuth()

        result = auth.validate_scopes()

        assert result is False

    def test_validate_scopes_missing_scopes(
        self, mock_credential_manager, mock_rate_limiter
    ):
        """Should return False when scopes are missing."""
        mock_credential_manager.return_value.validate_scopes.return_value = (
            False,
            ["missing.scope"],
        )

        auth = ReadOnlyGmailAuth()
        auth.authenticate()

        result = auth.validate_scopes()

        assert result is False

    def test_validate_scopes_no_user_info(
        self, mock_credential_manager, mock_rate_limiter
    ):
        """Should return False when user info cannot be fetched."""
        mock_credential_manager.return_value.get_user_info.return_value = None

        auth = ReadOnlyGmailAuth()
        auth.authenticate()

        result = auth.validate_scopes()

        assert result is False


@pytest.mark.unit
class TestCheckCredentialsFile:
    """Test check_credentials_file method."""

    def test_check_credentials_file_exists(self, mock_credential_manager, temp_dir):
        """Should return True when credentials file exists."""
        creds_file = temp_dir / "credentials.json"
        creds_file.write_text('{"test": "data"}')

        auth = ReadOnlyGmailAuth(credentials_file=str(creds_file))

        result = auth.check_credentials_file()

        assert result is True

    def test_check_credentials_file_not_found(self, mock_credential_manager):
        """Should return False when credentials file doesn't exist."""
        auth = ReadOnlyGmailAuth(credentials_file="nonexistent.json")

        result = auth.check_credentials_file()

        assert result is False

    def test_check_credentials_file_is_directory(
        self, mock_credential_manager, temp_dir
    ):
        """Should return False when credentials path is a directory."""
        auth = ReadOnlyGmailAuth(credentials_file=str(temp_dir))

        result = auth.check_credentials_file()

        assert result is False

    def test_check_credentials_file_empty(self, mock_credential_manager, temp_dir):
        """Should return False when credentials file is empty."""
        creds_file = temp_dir / "empty_creds.json"
        creds_file.write_text("")

        auth = ReadOnlyGmailAuth(credentials_file=str(creds_file))

        result = auth.check_credentials_file()

        assert result is False


@pytest.mark.unit
class TestAuthenticationStatus:
    """Test get_authentication_status method."""

    def test_get_authentication_status_not_authenticated(self, mock_credential_manager):
        """Should return status for unauthenticated instance."""
        auth = ReadOnlyGmailAuth()

        status = auth.get_authentication_status()

        assert status["authenticated"] is False
        assert status["credentials_file"] == "credentials.json"
        assert status["user_email"] is None
        assert status["service_available"] is False

    def test_get_authentication_status_authenticated(
        self, mock_credential_manager, mock_rate_limiter
    ):
        """Should return status for authenticated instance."""
        auth = ReadOnlyGmailAuth()
        auth.authenticate()

        status = auth.get_authentication_status()

        assert status["authenticated"] is True
        assert status["user_email"] == "test@gmail.com"
        assert status["messages_total"] == 1000
        assert status["service_available"] is True


@pytest.mark.unit
class TestReadOnlyGmailAuth:
    """Test ReadOnlyGmailAuth class."""

    def test_get_required_scopes(self, mock_credential_manager):
        """Should return read-only Gmail scopes."""
        auth = ReadOnlyGmailAuth()

        scopes = auth.get_required_scopes()

        assert scopes == ["https://www.googleapis.com/auth/gmail.readonly"]


@pytest.mark.unit
class TestGmailModifyAuth:
    """Test GmailModifyAuth class."""

    def test_get_required_scopes(self, mock_credential_manager):
        """Should return Gmail modify scopes."""
        auth = GmailModifyAuth()

        scopes = auth.get_required_scopes()

        assert scopes == ["https://www.googleapis.com/auth/gmail.modify"]


@pytest.mark.unit
class TestFullGmailAuth:
    """Test FullGmailAuth class."""

    def test_get_required_scopes(self, mock_credential_manager):
        """Should return full Gmail access scopes."""
        auth = FullGmailAuth()

        scopes = auth.get_required_scopes()

        expected_scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.compose",
        ]
        assert scopes == expected_scopes


@pytest.mark.unit
class TestAuthenticationFactory:
    """Test AuthenticationFactory class."""

    def test_create_auth_readonly(self, mock_credential_manager):
        """Should create ReadOnlyGmailAuth instance."""
        auth = AuthenticationFactory.create_auth("readonly")

        assert isinstance(auth, ReadOnlyGmailAuth)

    def test_create_auth_modify(self, mock_credential_manager):
        """Should create GmailModifyAuth instance."""
        auth = AuthenticationFactory.create_auth("modify")

        assert isinstance(auth, GmailModifyAuth)

    def test_create_auth_full(self, mock_credential_manager):
        """Should create FullGmailAuth instance."""
        auth = AuthenticationFactory.create_auth("full")

        assert isinstance(auth, FullGmailAuth)

    def test_create_auth_invalid_type(self, mock_credential_manager):
        """Should raise ValueError for invalid auth type."""
        with pytest.raises(ValueError, match="Invalid auth type"):
            AuthenticationFactory.create_auth("invalid")

    def test_create_auth_with_credentials_file(self, mock_credential_manager):
        """Should create auth with custom credentials file."""
        auth = AuthenticationFactory.create_auth(
            "readonly", credentials_file="custom.json"
        )

        assert auth.credentials_file == "custom.json"

    def test_get_auth_for_scopes_readonly(self, mock_credential_manager):
        """Should return ReadOnlyGmailAuth for readonly scopes."""
        scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

        auth = AuthenticationFactory.get_auth_for_scopes(scopes)

        assert isinstance(auth, ReadOnlyGmailAuth)

    def test_get_auth_for_scopes_modify(self, mock_credential_manager):
        """Should return GmailModifyAuth for modify scopes."""
        scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
        ]

        auth = AuthenticationFactory.get_auth_for_scopes(scopes)

        assert isinstance(auth, GmailModifyAuth)

    def test_get_auth_for_scopes_full(self, mock_credential_manager):
        """Should return FullGmailAuth for full access scopes."""
        scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.compose",
        ]

        auth = AuthenticationFactory.get_auth_for_scopes(scopes)

        assert isinstance(auth, FullGmailAuth)


@pytest.mark.unit
class TestUtilityFunctions:
    """Test utility functions."""

    def test_ensure_authenticated_already_authenticated(self, mock_credential_manager):
        """Should return True when already authenticated."""
        with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as rate_mock:
            rate_mock.return_value.check_rate_limit.return_value = True
            rate_mock.return_value.record_attempt.return_value = None

            auth = ReadOnlyGmailAuth()
            auth.authenticate()

            result = ensure_authenticated(auth)

            assert result is True

    def test_ensure_authenticated_needs_auth(self, mock_credential_manager):
        """Should authenticate when not authenticated."""
        with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as rate_mock:
            rate_mock.return_value.check_rate_limit.return_value = True
            rate_mock.return_value.record_attempt.return_value = None

            auth = ReadOnlyGmailAuth()

            result = ensure_authenticated(auth)

            assert result is True
            assert auth.is_authenticated

    def test_get_authenticated_service_success(self, mock_credential_manager):
        """Should return authenticated service."""
        with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as rate_mock:
            rate_mock.return_value.check_rate_limit.return_value = True
            rate_mock.return_value.record_attempt.return_value = None

            service = get_authenticated_service("readonly")

            assert service is not None

    def test_get_authenticated_service_failure(self, mock_credential_manager):
        """Should raise AuthenticationError when authentication fails."""
        mock_credential_manager.return_value.authenticate.return_value = False

        with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as rate_mock:
            rate_mock.return_value.check_rate_limit.return_value = True
            rate_mock.return_value.record_attempt.return_value = None

            with pytest.raises(AuthenticationError):
                get_authenticated_service("readonly")

    def test_validate_authentication_setup_valid(
        self, mock_credential_manager, temp_dir
    ):
        """Should validate authentication setup successfully."""
        creds_file = temp_dir / "credentials.json"
        creds_file.write_text('{"test": "data"}')

        with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as rate_mock:
            rate_mock.return_value.check_rate_limit.return_value = True
            rate_mock.return_value.record_attempt.return_value = None

            results = validate_authentication_setup(str(creds_file))

            assert results["credentials_file_valid"] is True
            assert results["authentication_successful"] is True
            assert results["user_info"] is not None
            assert len(results["errors"]) == 0

    def test_validate_authentication_setup_invalid_file(self, mock_credential_manager):
        """Should return errors when credentials file is invalid."""
        with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as rate_mock:
            rate_mock.return_value.check_rate_limit.return_value = True

            results = validate_authentication_setup("nonexistent.json")

            assert results["credentials_file_valid"] is False
            assert results["authentication_successful"] is False
            assert len(results["errors"]) > 0

    def test_validate_authentication_setup_auth_failure(self, mock_credential_manager, temp_dir):
        """Should return errors when authentication fails."""
        # Create a valid credentials file
        creds_file = temp_dir / "credentials.json"
        creds_file.write_text('{"test": "data"}')

        mock_credential_manager.return_value.authenticate.return_value = False

        with patch("gmail_assistant.core.auth.base.get_auth_rate_limiter") as rate_mock:
            rate_mock.return_value.check_rate_limit.return_value = True
            rate_mock.return_value.record_attempt.return_value = None

            results = validate_authentication_setup(str(creds_file))

            assert results["credentials_file_valid"] is True
            assert "Authentication failed" in results["errors"]


@pytest.mark.unit
class TestAuthenticationRecovery:
    """Test authentication recovery functionality."""

    def test_setup_authentication_recovery(self, mock_credential_manager):
        """Should setup authentication recovery handler."""
        auth = ReadOnlyGmailAuth()

        auth.setup_authentication_recovery()

        # Verify error handler was configured
        # (actual testing would require inspecting the error handler's registered handlers)
        assert auth.error_handler is not None
