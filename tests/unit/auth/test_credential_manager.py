"""Unit tests for gmail_assistant.core.auth.credential_manager module."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from gmail_assistant.core.auth.credential_manager import SecureCredentialManager


@pytest.fixture
def mock_keyring():
    """Mock keyring module."""
    with patch("gmail_assistant.core.auth.credential_manager.keyring") as mock:
        yield mock


@pytest.fixture
def mock_credentials():
    """Create mock Google Credentials."""
    with patch(
        "gmail_assistant.core.auth.credential_manager.Credentials"
    ) as mock_creds:
        creds = Mock()
        creds.valid = True
        creds.expired = False
        creds.refresh_token = "refresh_token_123"
        creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        creds.to_json.return_value = json.dumps(
            {
                "token": "access_token_123",
                "refresh_token": "refresh_token_123",
                "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            }
        )

        mock_creds.from_authorized_user_info.return_value = creds
        yield mock_creds


@pytest.fixture
def mock_flow():
    """Mock OAuth flow."""
    with patch(
        "gmail_assistant.core.auth.credential_manager.InstalledAppFlow"
    ) as mock_flow:
        flow = Mock()
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.to_json.return_value = json.dumps({"token": "new_token"})
        mock_creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        flow.run_local_server.return_value = mock_creds

        mock_flow.from_client_secrets_file.return_value = flow
        yield mock_flow


@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service."""
    with patch("gmail_assistant.core.auth.credential_manager.build") as mock_build:
        service = Mock()
        profile_response = {
            "emailAddress": "test@gmail.com",
            "messagesTotal": 1000,
            "threadsTotal": 500,
        }
        service.users().getProfile().execute.return_value = profile_response

        mock_build.return_value = service
        yield mock_build


@pytest.mark.unit
class TestSecureCredentialManagerInit:
    """Test SecureCredentialManager initialization."""

    def test_init_default_credentials_file(self, mock_keyring):
        """Should initialize with default credentials file."""
        manager = SecureCredentialManager()

        assert manager.credentials_file == "credentials.json"
        assert manager.service is None
        assert manager._credentials is None

    def test_init_custom_credentials_file(self, mock_keyring):
        """Should initialize with custom credentials file."""
        manager = SecureCredentialManager("custom_creds.json")

        assert manager.credentials_file == "custom_creds.json"


@pytest.mark.unit
class TestStoreCredentialsSecurely:
    """Test _store_credentials_securely method."""

    def test_store_credentials_success(self, mock_keyring, mock_credentials):
        """Should store credentials in OS keyring successfully."""
        manager = SecureCredentialManager()
        creds = Mock()
        creds.to_json.return_value = '{"token": "test_token"}'

        result = manager._store_credentials_securely(creds)

        assert result is True
        mock_keyring.set_password.assert_called_once()

    def test_store_credentials_failure(self, mock_keyring):
        """Should return False when storing fails."""
        mock_keyring.set_password.side_effect = Exception("Keyring error")

        manager = SecureCredentialManager()
        creds = Mock()
        creds.to_json.return_value = '{"token": "test_token"}'

        result = manager._store_credentials_securely(creds)

        assert result is False


@pytest.mark.unit
class TestLoadCredentialsSecurely:
    """Test _load_credentials_securely method."""

    def test_load_credentials_success(self, mock_keyring, mock_credentials):
        """Should load credentials from keyring successfully."""
        mock_keyring.get_password.return_value = '{"token": "stored_token"}'

        manager = SecureCredentialManager()

        result = manager._load_credentials_securely()

        assert result is not None
        mock_keyring.get_password.assert_called_once()

    def test_load_credentials_not_found(self, mock_keyring, mock_credentials):
        """Should return None when credentials not found in keyring."""
        mock_keyring.get_password.return_value = None

        manager = SecureCredentialManager()

        result = manager._load_credentials_securely()

        assert result is None

    def test_load_credentials_failure(self, mock_keyring, mock_credentials):
        """Should return None when loading fails."""
        mock_keyring.get_password.side_effect = Exception("Keyring error")

        manager = SecureCredentialManager()

        result = manager._load_credentials_securely()

        assert result is None


@pytest.mark.unit
class TestClearCredentials:
    """Test _clear_credentials method."""

    def test_clear_credentials_success(self, mock_keyring):
        """Should clear credentials from keyring successfully."""
        manager = SecureCredentialManager()

        result = manager._clear_credentials()

        assert result is True
        mock_keyring.delete_password.assert_called_once()

    def test_clear_credentials_not_found(self, mock_keyring):
        """Should return True even when no credentials to clear."""
        # Mock PasswordDeleteError as an exception
        with patch("gmail_assistant.core.auth.credential_manager.keyring.errors") as mock_errors:
            mock_error = type('PasswordDeleteError', (Exception,), {})
            mock_errors.PasswordDeleteError = mock_error
            mock_keyring.errors = mock_errors
            mock_keyring.delete_password.side_effect = mock_error()

            manager = SecureCredentialManager()

            result = manager._clear_credentials()

            assert result is True

    def test_clear_credentials_failure(self, mock_keyring):
        """Should return False when clearing fails."""
        # Use a different exception type that's not PasswordDeleteError
        # Mock keyring.errors to avoid the catching issue
        with patch("gmail_assistant.core.auth.credential_manager.keyring.errors") as mock_errors:
            mock_errors.PasswordDeleteError = type('PasswordDeleteError', (Exception,), {})
            mock_keyring.errors = mock_errors
            mock_keyring.delete_password.side_effect = RuntimeError("Keyring error")

            manager = SecureCredentialManager()

            result = manager._clear_credentials()

            assert result is False


@pytest.mark.unit
class TestAuthenticate:
    """Test authenticate method."""

    def test_authenticate_with_stored_valid_credentials(
        self, mock_keyring, mock_credentials, mock_gmail_service
    ):
        """Should authenticate with stored valid credentials."""
        mock_keyring.get_password.return_value = json.dumps(
            {"token": "stored_token", "scopes": ["gmail.readonly"]}
        )

        creds = Mock()
        creds.valid = True
        creds.expired = False
        creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        mock_credentials.from_authorized_user_info.return_value = creds

        manager = SecureCredentialManager()

        result = manager.authenticate()

        assert result is True
        assert manager.service is not None
        assert manager._credentials is not None

    def test_authenticate_refresh_expired_credentials(
        self, mock_keyring, mock_credentials, mock_gmail_service
    ):
        """Should refresh expired credentials with valid refresh token."""
        mock_keyring.get_password.return_value = json.dumps({"token": "expired_token"})

        creds = Mock()
        creds.valid = False
        creds.expired = True
        creds.refresh_token = "refresh_token_123"
        creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        creds.to_json.return_value = json.dumps({"token": "refreshed_token"})

        with patch(
            "gmail_assistant.core.auth.credential_manager.Request"
        ) as mock_request:
            mock_credentials.from_authorized_user_info.return_value = creds

            manager = SecureCredentialManager()

            result = manager.authenticate()

            assert result is True
            creds.refresh.assert_called_once()
            mock_keyring.set_password.assert_called()

    def test_authenticate_refresh_failure(
        self, mock_keyring, mock_credentials, mock_flow, temp_dir, mock_gmail_service
    ):
        """Should run OAuth flow when refresh fails."""
        mock_keyring.get_password.return_value = json.dumps({"token": "expired_token"})

        creds = Mock()
        creds.valid = False
        creds.expired = True
        creds.refresh_token = "refresh_token_123"
        creds.refresh.side_effect = Exception("Refresh failed")

        mock_credentials.from_authorized_user_info.return_value = creds

        # Create credentials file
        creds_file = temp_dir / "credentials.json"
        creds_file.write_text(json.dumps({"installed": {"client_id": "test_id"}}))

        manager = SecureCredentialManager(str(creds_file))

        result = manager.authenticate()

        assert result is True
        mock_flow.from_client_secrets_file.assert_called()

    def test_authenticate_new_oauth_flow(
        self, mock_keyring, mock_credentials, mock_flow, temp_dir, mock_gmail_service
    ):
        """Should run OAuth flow for new authentication."""
        mock_keyring.get_password.return_value = None

        # Create credentials file
        creds_file = temp_dir / "credentials.json"
        creds_file.write_text(json.dumps({"installed": {"client_id": "test_id"}}))

        manager = SecureCredentialManager(str(creds_file))

        result = manager.authenticate()

        assert result is True
        mock_flow.from_client_secrets_file.assert_called_with(
            str(creds_file), ["https://www.googleapis.com/auth/gmail.readonly"]
        )

    def test_authenticate_missing_credentials_file(
        self, mock_keyring, mock_credentials
    ):
        """Should return False when credentials file is missing."""
        mock_keyring.get_password.return_value = None

        manager = SecureCredentialManager("nonexistent.json")

        result = manager.authenticate()

        assert result is False
        assert manager.service is None

    def test_authenticate_oauth_flow_failure(
        self, mock_keyring, mock_credentials, mock_flow, temp_dir
    ):
        """Should return False when OAuth flow fails."""
        mock_keyring.get_password.return_value = None
        mock_flow.from_client_secrets_file.side_effect = Exception("OAuth flow failed")

        # Create credentials file
        creds_file = temp_dir / "credentials.json"
        creds_file.write_text(json.dumps({"installed": {"client_id": "test_id"}}))

        manager = SecureCredentialManager(str(creds_file))

        result = manager.authenticate()

        assert result is False

    def test_authenticate_storage_failure_after_oauth(
        self, mock_keyring, mock_credentials, mock_flow, temp_dir, mock_gmail_service
    ):
        """Should return False when credential storage fails after OAuth."""
        mock_keyring.get_password.return_value = None
        mock_keyring.set_password.side_effect = Exception("Storage failed")

        # Create credentials file
        creds_file = temp_dir / "credentials.json"
        creds_file.write_text(json.dumps({"installed": {"client_id": "test_id"}}))

        manager = SecureCredentialManager(str(creds_file))

        result = manager.authenticate()

        assert result is False

    def test_authenticate_build_service_failure(
        self, mock_keyring, mock_credentials, mock_gmail_service
    ):
        """Should return False when building Gmail service fails."""
        mock_keyring.get_password.return_value = json.dumps({"token": "valid_token"})
        mock_gmail_service.side_effect = Exception("Service build failed")

        creds = Mock()
        creds.valid = True
        creds.expired = False
        mock_credentials.from_authorized_user_info.return_value = creds

        manager = SecureCredentialManager()

        result = manager.authenticate()

        assert result is False


@pytest.mark.unit
class TestGetService:
    """Test get_service method."""

    def test_get_service_already_authenticated(
        self, mock_keyring, mock_credentials, mock_gmail_service
    ):
        """Should return service when already authenticated."""
        mock_keyring.get_password.return_value = json.dumps({"token": "valid_token"})

        creds = Mock()
        creds.valid = True
        creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        mock_credentials.from_authorized_user_info.return_value = creds

        manager = SecureCredentialManager()
        manager.authenticate()

        service = manager.get_service()

        assert service is not None

    def test_get_service_needs_authentication(
        self, mock_keyring, mock_credentials, mock_gmail_service
    ):
        """Should authenticate and return service when not authenticated."""
        mock_keyring.get_password.return_value = json.dumps({"token": "valid_token"})

        creds = Mock()
        creds.valid = True
        creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        mock_credentials.from_authorized_user_info.return_value = creds

        manager = SecureCredentialManager()

        service = manager.get_service()

        assert service is not None

    def test_get_service_authentication_fails(self, mock_keyring, mock_credentials):
        """Should return None when authentication fails."""
        mock_keyring.get_password.return_value = None

        manager = SecureCredentialManager("nonexistent.json")

        service = manager.get_service()

        assert service is None


@pytest.mark.unit
class TestResetCredentials:
    """Test reset_credentials method."""

    def test_reset_credentials_success(self, mock_keyring):
        """Should reset credentials successfully."""
        manager = SecureCredentialManager()
        manager.service = Mock()

        result = manager.reset_credentials()

        assert result is True
        assert manager.service is None
        mock_keyring.delete_password.assert_called_once()

    def test_reset_credentials_clears_service(self, mock_keyring):
        """Should clear service reference when resetting."""
        manager = SecureCredentialManager()
        manager.service = Mock()

        manager.reset_credentials()

        assert manager.service is None


@pytest.mark.unit
class TestGetUserInfo:
    """Test get_user_info method."""

    def test_get_user_info_success(
        self, mock_keyring, mock_credentials, mock_gmail_service
    ):
        """Should return user information successfully."""
        mock_keyring.get_password.return_value = json.dumps({"token": "valid_token"})

        creds = Mock()
        creds.valid = True
        creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        mock_credentials.from_authorized_user_info.return_value = creds

        manager = SecureCredentialManager()
        manager.authenticate()

        user_info = manager.get_user_info()

        assert user_info is not None
        assert user_info["email"] == "test@gmail.com"
        assert user_info["messages_total"] == 1000
        assert user_info["threads_total"] == 500

    def test_get_user_info_not_authenticated(self, mock_keyring):
        """Should return None when not authenticated."""
        manager = SecureCredentialManager()

        user_info = manager.get_user_info()

        assert user_info is None

    def test_get_user_info_api_failure(
        self, mock_keyring, mock_credentials, mock_gmail_service
    ):
        """Should return None when API call fails."""
        mock_keyring.get_password.return_value = json.dumps({"token": "valid_token"})

        creds = Mock()
        creds.valid = True
        creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        mock_credentials.from_authorized_user_info.return_value = creds

        service = Mock()
        service.users().getProfile().execute.side_effect = Exception("API error")
        mock_gmail_service.return_value = service

        manager = SecureCredentialManager()
        manager.authenticate()

        user_info = manager.get_user_info()

        assert user_info is None


@pytest.mark.unit
class TestGetGrantedScopes:
    """Test get_granted_scopes method."""

    def test_get_granted_scopes_authenticated(
        self, mock_keyring, mock_credentials, mock_gmail_service
    ):
        """Should return granted scopes when authenticated."""
        mock_keyring.get_password.return_value = json.dumps({"token": "valid_token"})

        creds = Mock()
        creds.valid = True
        creds.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
        ]
        mock_credentials.from_authorized_user_info.return_value = creds

        manager = SecureCredentialManager()
        manager.authenticate()

        scopes = manager.get_granted_scopes()

        assert len(scopes) == 2
        assert "https://www.googleapis.com/auth/gmail.readonly" in scopes
        assert "https://www.googleapis.com/auth/gmail.modify" in scopes

    def test_get_granted_scopes_not_authenticated(self, mock_keyring):
        """Should return empty list when not authenticated."""
        manager = SecureCredentialManager()

        scopes = manager.get_granted_scopes()

        assert scopes == []


@pytest.mark.unit
class TestValidateScopes:
    """Test validate_scopes method."""

    def test_validate_scopes_all_present(
        self, mock_keyring, mock_credentials, mock_gmail_service
    ):
        """Should return True when all required scopes are granted."""
        mock_keyring.get_password.return_value = json.dumps({"token": "valid_token"})

        creds = Mock()
        creds.valid = True
        creds.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
        ]
        mock_credentials.from_authorized_user_info.return_value = creds

        manager = SecureCredentialManager()
        manager.authenticate()

        is_valid, missing = manager.validate_scopes(
            ["https://www.googleapis.com/auth/gmail.readonly"]
        )

        assert is_valid is True
        assert missing == []

    def test_validate_scopes_missing_some(
        self, mock_keyring, mock_credentials, mock_gmail_service
    ):
        """Should return False when some required scopes are missing."""
        mock_keyring.get_password.return_value = json.dumps({"token": "valid_token"})

        creds = Mock()
        creds.valid = True
        creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        mock_credentials.from_authorized_user_info.return_value = creds

        manager = SecureCredentialManager()
        manager.authenticate()

        is_valid, missing = manager.validate_scopes(
            [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.modify",
            ]
        )

        assert is_valid is False
        assert "https://www.googleapis.com/auth/gmail.modify" in missing

    def test_validate_scopes_not_authenticated(self, mock_keyring):
        """Should return False when not authenticated."""
        manager = SecureCredentialManager()

        is_valid, missing = manager.validate_scopes(
            ["https://www.googleapis.com/auth/gmail.readonly"]
        )

        assert is_valid is False
        assert "https://www.googleapis.com/auth/gmail.readonly" in missing
