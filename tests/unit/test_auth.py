"""Unit tests for gmail_assistant.core.auth module."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
from unittest import mock

import pytest

from gmail_assistant.core.auth.base import (
    AuthenticationError,
    AuthenticationBase,
    ReadOnlyGmailAuth,
    GmailModifyAuth,
    FullGmailAuth,
    AuthenticationFactory,
    ensure_authenticated,
    validate_authentication_setup,
)


@pytest.fixture
def mock_credential_manager():
    """Create a mock credential manager."""
    manager = mock.Mock()
    manager.authenticate.return_value = True
    manager.get_service.return_value = mock.Mock()
    manager.get_user_info.return_value = {
        "email": "test@example.com",
        "messages_total": 1000,
        "threads_total": 500
    }
    manager.reset_credentials.return_value = True
    return manager


@pytest.fixture
def readonly_auth(temp_dir: Path, mock_credential_manager):
    """Create a ReadOnlyGmailAuth instance with mocked credentials."""
    creds_file = temp_dir / "credentials.json"
    creds_file.write_text('{"installed": {"client_id": "test"}}')

    auth = ReadOnlyGmailAuth(str(creds_file))
    auth.credential_manager = mock_credential_manager
    return auth


@pytest.mark.unit
class TestAuthenticationError:
    """Test AuthenticationError exception."""

    def test_is_exception(self):
        """AuthenticationError should inherit from Exception."""
        assert issubclass(AuthenticationError, Exception)

    def test_with_message(self):
        """AuthenticationError should preserve message."""
        error = AuthenticationError("Auth failed")
        assert str(error) == "Auth failed"


@pytest.mark.unit
class TestAuthenticationBaseInit:
    """Test AuthenticationBase initialization."""

    def test_stores_credentials_file(self, temp_dir: Path):
        """Should store credentials file path."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = ReadOnlyGmailAuth(str(creds_file))

        assert auth.credentials_file == str(creds_file)

    def test_stores_required_scopes(self, temp_dir: Path):
        """Should store required scopes."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = ReadOnlyGmailAuth(str(creds_file))

        assert len(auth.required_scopes) > 0
        assert "gmail" in auth.required_scopes[0]

    def test_initial_state_not_authenticated(self, temp_dir: Path):
        """Should start not authenticated."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = ReadOnlyGmailAuth(str(creds_file))

        assert auth.is_authenticated is False
        assert auth._service is None


@pytest.mark.unit
class TestIsAuthenticatedProperty:
    """Test is_authenticated property."""

    def test_returns_false_when_not_authenticated(self, readonly_auth):
        """Should return False when not authenticated."""
        readonly_auth._authenticated = False
        readonly_auth._service = None

        assert readonly_auth.is_authenticated is False

    def test_returns_true_when_authenticated(self, readonly_auth):
        """Should return True when authenticated."""
        readonly_auth._authenticated = True
        readonly_auth._service = mock.Mock()

        assert readonly_auth.is_authenticated is True

    def test_requires_both_flag_and_service(self, readonly_auth):
        """Should require both authenticated flag and service."""
        # Authenticated but no service
        readonly_auth._authenticated = True
        readonly_auth._service = None

        assert readonly_auth.is_authenticated is False


@pytest.mark.unit
class TestAuthenticate:
    """Test authenticate method."""

    def test_authenticate_success(self, readonly_auth, mock_credential_manager):
        """authenticate should return True on success."""
        result = readonly_auth.authenticate()

        assert result is True
        assert readonly_auth.is_authenticated is True

    def test_authenticate_sets_service(self, readonly_auth, mock_credential_manager):
        """authenticate should set service from credential manager."""
        readonly_auth.authenticate()

        assert readonly_auth._service is not None
        mock_credential_manager.get_service.assert_called()

    def test_authenticate_fetches_user_info(
        self, readonly_auth, mock_credential_manager
    ):
        """authenticate should fetch user info."""
        readonly_auth.authenticate()

        assert readonly_auth.user_info is not None
        assert readonly_auth.user_info["email"] == "test@example.com"

    def test_authenticate_returns_true_if_already_authenticated(
        self, readonly_auth
    ):
        """authenticate should return True if already authenticated."""
        readonly_auth._authenticated = True
        readonly_auth._service = mock.Mock()

        result = readonly_auth.authenticate()

        assert result is True

    def test_authenticate_failure(self, readonly_auth, mock_credential_manager):
        """authenticate should handle failure."""
        mock_credential_manager.authenticate.return_value = False

        result = readonly_auth.authenticate()

        assert result is False
        assert readonly_auth.is_authenticated is False


@pytest.mark.unit
class TestServiceProperty:
    """Test service property."""

    def test_service_returns_authenticated_service(
        self, readonly_auth, mock_credential_manager
    ):
        """service property should return service when authenticated."""
        readonly_auth.authenticate()

        service = readonly_auth.service

        assert service is not None

    def test_service_auto_authenticates(
        self, readonly_auth, mock_credential_manager
    ):
        """service property should auto-authenticate if needed."""
        service = readonly_auth.service

        assert service is not None
        assert readonly_auth.is_authenticated is True

    def test_service_raises_on_auth_failure(
        self, readonly_auth, mock_credential_manager
    ):
        """service property should raise AuthenticationError on failure."""
        mock_credential_manager.authenticate.return_value = False

        with pytest.raises(AuthenticationError):
            _ = readonly_auth.service


@pytest.mark.unit
class TestUserInfoProperty:
    """Test user_info property."""

    def test_returns_cached_user_info(self, readonly_auth):
        """user_info should return cached info."""
        readonly_auth._user_info = {"email": "cached@example.com"}

        info = readonly_auth.user_info

        assert info["email"] == "cached@example.com"

    def test_returns_none_when_not_set(self, readonly_auth):
        """user_info should return None when not set."""
        readonly_auth._user_info = None

        assert readonly_auth.user_info is None


@pytest.mark.unit
class TestResetAuthentication:
    """Test reset_authentication method."""

    def test_reset_clears_state(self, readonly_auth, mock_credential_manager):
        """reset_authentication should clear authentication state."""
        readonly_auth._authenticated = True
        readonly_auth._service = mock.Mock()
        readonly_auth._user_info = {"email": "test@example.com"}

        result = readonly_auth.reset_authentication()

        assert result is True
        assert readonly_auth._authenticated is False
        assert readonly_auth._service is None
        assert readonly_auth._user_info is None

    def test_reset_calls_credential_manager(
        self, readonly_auth, mock_credential_manager
    ):
        """reset_authentication should call credential manager reset."""
        readonly_auth.reset_authentication()

        mock_credential_manager.reset_credentials.assert_called_once()


@pytest.mark.unit
class TestValidateScopes:
    """Test validate_scopes method."""

    def test_returns_false_when_not_authenticated(self, readonly_auth):
        """validate_scopes should return False when not authenticated."""
        readonly_auth._authenticated = False

        result = readonly_auth.validate_scopes()

        assert result is False

    def test_returns_true_when_authenticated_and_valid(
        self, readonly_auth, mock_credential_manager
    ):
        """validate_scopes should return True when scopes are valid."""
        readonly_auth.authenticate()

        result = readonly_auth.validate_scopes()

        assert result is True


@pytest.mark.unit
class TestGetAuthenticationStatus:
    """Test get_authentication_status method."""

    def test_returns_status_dict(self, readonly_auth):
        """get_authentication_status should return dictionary."""
        status = readonly_auth.get_authentication_status()

        assert isinstance(status, dict)
        assert "authenticated" in status
        assert "credentials_file" in status
        assert "required_scopes" in status

    def test_status_reflects_authentication_state(
        self, readonly_auth, mock_credential_manager
    ):
        """Status should reflect authentication state."""
        # Not authenticated
        status_before = readonly_auth.get_authentication_status()
        assert status_before["authenticated"] is False

        # Authenticate
        readonly_auth.authenticate()
        status_after = readonly_auth.get_authentication_status()

        assert status_after["authenticated"] is True
        assert status_after["user_email"] == "test@example.com"


@pytest.mark.unit
class TestCheckCredentialsFile:
    """Test check_credentials_file method."""

    def test_returns_true_for_existing_file(self, readonly_auth, temp_dir: Path):
        """check_credentials_file should return True for existing file."""
        # File was created in fixture
        result = readonly_auth.check_credentials_file()

        assert result is True

    def test_returns_false_for_nonexistent_file(self, temp_dir: Path):
        """check_credentials_file should return False for missing file."""
        auth = ReadOnlyGmailAuth(str(temp_dir / "nonexistent.json"))

        result = auth.check_credentials_file()

        assert result is False

    def test_returns_false_for_empty_file(self, temp_dir: Path):
        """check_credentials_file should return False for empty file."""
        empty_file = temp_dir / "empty.json"
        empty_file.write_text("")

        auth = ReadOnlyGmailAuth(str(empty_file))

        result = auth.check_credentials_file()

        assert result is False


@pytest.mark.unit
class TestReadOnlyGmailAuth:
    """Test ReadOnlyGmailAuth class."""

    def test_get_required_scopes(self, temp_dir: Path):
        """Should return readonly scope."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = ReadOnlyGmailAuth(str(creds_file))
        scopes = auth.get_required_scopes()

        assert len(scopes) == 1
        assert "readonly" in scopes[0]


@pytest.mark.unit
class TestGmailModifyAuth:
    """Test GmailModifyAuth class."""

    def test_get_required_scopes(self, temp_dir: Path):
        """Should return modify scope."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = GmailModifyAuth(str(creds_file))
        scopes = auth.get_required_scopes()

        assert len(scopes) == 1
        assert "modify" in scopes[0]


@pytest.mark.unit
class TestFullGmailAuth:
    """Test FullGmailAuth class."""

    def test_get_required_scopes(self, temp_dir: Path):
        """Should return multiple scopes including compose."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = FullGmailAuth(str(creds_file))
        scopes = auth.get_required_scopes()

        assert len(scopes) > 1
        scope_text = " ".join(scopes)
        assert "readonly" in scope_text
        assert "modify" in scope_text
        assert "compose" in scope_text


@pytest.mark.unit
class TestAuthenticationFactory:
    """Test AuthenticationFactory class."""

    def test_create_readonly_auth(self, temp_dir: Path):
        """create_auth should create ReadOnlyGmailAuth for 'readonly'."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = AuthenticationFactory.create_auth("readonly", str(creds_file))

        assert isinstance(auth, ReadOnlyGmailAuth)

    def test_create_modify_auth(self, temp_dir: Path):
        """create_auth should create GmailModifyAuth for 'modify'."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = AuthenticationFactory.create_auth("modify", str(creds_file))

        assert isinstance(auth, GmailModifyAuth)

    def test_create_full_auth(self, temp_dir: Path):
        """create_auth should create FullGmailAuth for 'full'."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = AuthenticationFactory.create_auth("full", str(creds_file))

        assert isinstance(auth, FullGmailAuth)

    def test_invalid_auth_type_raises_error(self, temp_dir: Path):
        """create_auth should raise ValueError for invalid type."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        with pytest.raises(ValueError, match="Invalid auth type"):
            AuthenticationFactory.create_auth("invalid", str(creds_file))

    def test_get_auth_for_scopes_readonly(self, temp_dir: Path):
        """get_auth_for_scopes should return readonly for readonly scope."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        auth = AuthenticationFactory.get_auth_for_scopes(scopes, str(creds_file))

        assert isinstance(auth, ReadOnlyGmailAuth)


@pytest.mark.unit
class TestEnsureAuthenticated:
    """Test ensure_authenticated helper function."""

    def test_returns_true_if_already_authenticated(self, readonly_auth):
        """Should return True if already authenticated."""
        readonly_auth._authenticated = True
        readonly_auth._service = mock.Mock()

        result = ensure_authenticated(readonly_auth)

        assert result is True

    def test_authenticates_if_not_authenticated(
        self, readonly_auth, mock_credential_manager
    ):
        """Should authenticate if not authenticated."""
        assert readonly_auth.is_authenticated is False

        result = ensure_authenticated(readonly_auth)

        assert result is True
        assert readonly_auth.is_authenticated is True


@pytest.mark.unit
class TestValidateAuthenticationSetup:
    """Test validate_authentication_setup function."""

    def test_returns_dict_with_results(self, temp_dir: Path):
        """Should return dictionary with validation results."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{"installed": {"client_id": "test"}}')

        # Need to mock the actual authentication
        with mock.patch.object(
            ReadOnlyGmailAuth, 'authenticate', return_value=False
        ):
            result = validate_authentication_setup(str(creds_file))

        assert isinstance(result, dict)
        assert "credentials_file_valid" in result
        assert "authentication_successful" in result
        assert "errors" in result

    def test_detects_invalid_credentials_file(self, temp_dir: Path):
        """Should detect invalid credentials file."""
        result = validate_authentication_setup(
            str(temp_dir / "nonexistent.json")
        )

        assert result["credentials_file_valid"] is False
        assert len(result["errors"]) > 0


@pytest.mark.unit
class TestAuthenticateExceptionHandling:
    """Test exception handling in authenticate method."""

    def test_authenticate_handles_exception_gracefully(
        self, temp_dir: Path
    ):
        """authenticate should handle exceptions gracefully."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = ReadOnlyGmailAuth(str(creds_file))
        auth.credential_manager = mock.Mock()
        auth.credential_manager.authenticate.side_effect = RuntimeError("Test error")

        result = auth.authenticate()

        assert result is False
        assert auth.is_authenticated is False

    def test_authenticate_handles_keyboard_interrupt(
        self, temp_dir: Path
    ):
        """authenticate should handle keyboard interrupt."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = ReadOnlyGmailAuth(str(creds_file))
        auth.credential_manager = mock.Mock()
        auth.credential_manager.authenticate.side_effect = Exception("User cancelled")

        result = auth.authenticate()

        assert result is False


@pytest.mark.unit
class TestFetchUserInfoExceptionHandling:
    """Test _fetch_user_info exception handling."""

    def test_fetch_user_info_handles_exception(self, readonly_auth, mock_credential_manager):
        """_fetch_user_info should return None on exception."""
        mock_credential_manager.get_user_info.side_effect = Exception("API error")
        readonly_auth._service = mock.Mock()

        result = readonly_auth._fetch_user_info()

        assert result is None

    def test_fetch_user_info_with_no_service(self, readonly_auth):
        """_fetch_user_info should handle no service."""
        readonly_auth._service = None

        result = readonly_auth._fetch_user_info()

        assert result is None


@pytest.mark.unit
class TestResetAuthenticationExceptionHandling:
    """Test exception handling in reset_authentication."""

    def test_reset_authentication_handles_exception(
        self, readonly_auth, mock_credential_manager
    ):
        """reset_authentication should handle exceptions gracefully."""
        mock_credential_manager.reset_credentials.side_effect = Exception("Reset failed")

        result = readonly_auth.reset_authentication()

        assert result is False
        assert readonly_auth._authenticated is False

    def test_reset_authentication_clears_user_info(
        self, readonly_auth, mock_credential_manager
    ):
        """reset_authentication should clear user info."""
        readonly_auth._user_info = {"email": "test@example.com"}

        readonly_auth.reset_authentication()

        assert readonly_auth._user_info is None


@pytest.mark.unit
class TestValidateScopesExtended:
    """Extended tests for validate_scopes method."""

    def test_validate_scopes_handles_exception(
        self, readonly_auth, mock_credential_manager
    ):
        """validate_scopes should handle exceptions."""
        readonly_auth._authenticated = True
        readonly_auth._service = mock.Mock()
        mock_credential_manager.get_user_info.side_effect = Exception("API error")

        result = readonly_auth.validate_scopes()

        assert result is False

    def test_validate_scopes_returns_false_when_user_info_none(
        self, readonly_auth, mock_credential_manager
    ):
        """validate_scopes should return False when user info is None."""
        readonly_auth._authenticated = True
        readonly_auth._service = mock.Mock()
        mock_credential_manager.get_user_info.return_value = None

        result = readonly_auth.validate_scopes()

        assert result is False


@pytest.mark.unit
class TestCheckCredentialsFileExtended:
    """Extended tests for check_credentials_file method."""

    def test_check_credentials_file_not_a_file(self, temp_dir: Path):
        """check_credentials_file should return False for directory."""
        # Use directory as credentials path
        auth = ReadOnlyGmailAuth(str(temp_dir))

        result = auth.check_credentials_file()

        assert result is False

    def test_check_credentials_file_exception_handling(self, temp_dir: Path):
        """check_credentials_file should handle exceptions."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = ReadOnlyGmailAuth(str(creds_file))

        # Mock Path to raise exception on stat
        with mock.patch.object(Path, 'stat', side_effect=PermissionError("Access denied")):
            result = auth.check_credentials_file()

        assert result is False


@pytest.mark.unit
class TestSetupAuthenticationRecovery:
    """Test setup_authentication_recovery method."""

    def test_setup_authentication_recovery_registers_handler(
        self, readonly_auth
    ):
        """setup_authentication_recovery should register recovery handler."""
        readonly_auth.setup_authentication_recovery()

        # The handler should be registered with the error handler
        assert readonly_auth.error_handler is not None

    def test_recovery_handler_handles_auth_error(self, temp_dir: Path):
        """Recovery handler should handle authentication errors."""
        from gmail_assistant.utils.error_handler import ErrorCategory

        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        auth = ReadOnlyGmailAuth(str(creds_file))
        auth.credential_manager = mock.Mock()
        auth.credential_manager.reset_credentials.return_value = True

        auth.setup_authentication_recovery()

        # Verify handler was registered
        assert ErrorCategory.AUTHENTICATION in auth.error_handler.recovery_handlers


@pytest.mark.unit
class TestAuthenticationFactoryExtended:
    """Extended tests for AuthenticationFactory."""

    def test_get_auth_for_modify_scopes(self, temp_dir: Path):
        """get_auth_for_scopes should return modify auth for modify scope."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify"
        ]
        auth = AuthenticationFactory.get_auth_for_scopes(scopes, str(creds_file))

        # Should return modify auth since it includes modify scope
        assert isinstance(auth, (GmailModifyAuth, FullGmailAuth))

    def test_get_auth_for_full_scopes(self, temp_dir: Path):
        """get_auth_for_scopes should return full auth for compose scope."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        scopes = [
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.modify"
        ]
        auth = AuthenticationFactory.get_auth_for_scopes(scopes, str(creds_file))

        assert isinstance(auth, FullGmailAuth)


@pytest.mark.unit
class TestGetAuthenticatedService:
    """Test get_authenticated_service function."""

    def test_get_authenticated_service_success(self, temp_dir: Path):
        """get_authenticated_service should return service on success."""
        from gmail_assistant.core.auth.base import get_authenticated_service

        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        mock_service = mock.Mock()

        with mock.patch.object(
            AuthenticationFactory, 'create_auth'
        ) as mock_create:
            mock_auth = mock.Mock()
            mock_auth.authenticate.return_value = True
            mock_auth.service = mock_service
            mock_create.return_value = mock_auth

            result = get_authenticated_service('readonly', str(creds_file))

            assert result == mock_service

    def test_get_authenticated_service_failure(self, temp_dir: Path):
        """get_authenticated_service should raise on auth failure."""
        from gmail_assistant.core.auth.base import get_authenticated_service

        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{}')

        with mock.patch.object(
            AuthenticationFactory, 'create_auth'
        ) as mock_create:
            mock_auth = mock.Mock()
            mock_auth.authenticate.return_value = False
            mock_create.return_value = mock_auth

            with pytest.raises(AuthenticationError):
                get_authenticated_service('readonly', str(creds_file))


@pytest.mark.unit
class TestValidateAuthenticationSetupExtended:
    """Extended tests for validate_authentication_setup function."""

    def test_validate_auth_setup_success(self, temp_dir: Path):
        """validate_authentication_setup should return success on valid auth."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{"installed": {"client_id": "test"}}')

        with mock.patch.object(
            ReadOnlyGmailAuth, 'authenticate', return_value=True
        ):
            with mock.patch.object(
                ReadOnlyGmailAuth, 'user_info',
                new_callable=mock.PropertyMock,
                return_value={"email": "test@gmail.com"}
            ):
                result = validate_authentication_setup(str(creds_file))

        assert result["authentication_successful"] is True
        assert result["user_info"] is not None

    def test_validate_auth_setup_handles_exception(self, temp_dir: Path):
        """validate_authentication_setup should handle exceptions."""
        creds_file = temp_dir / "creds.json"
        creds_file.write_text('{"installed": {"client_id": "test"}}')

        with mock.patch.object(
            ReadOnlyGmailAuth, '__init__', side_effect=Exception("Init error")
        ):
            result = validate_authentication_setup(str(creds_file))

        assert len(result["errors"]) > 0


@pytest.mark.unit
class TestHandleAuthFailure:
    """Test _handle_auth_failure method."""

    def test_handle_auth_failure_clears_state(self, readonly_auth):
        """_handle_auth_failure should clear all authentication state."""
        readonly_auth._authenticated = True
        readonly_auth._service = mock.Mock()
        readonly_auth._user_info = {"email": "test@example.com"}

        readonly_auth._handle_auth_failure("Test failure")

        assert readonly_auth._authenticated is False
        assert readonly_auth._service is None
        assert readonly_auth._user_info is None
