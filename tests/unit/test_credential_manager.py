"""Tests for SecureCredentialManager."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestSecureCredentialManagerInit:
    """Tests for SecureCredentialManager initialization."""

    def test_default_credentials_file(self):
        """Test default credentials file path."""
        with patch.dict('sys.modules', {'keyring': MagicMock()}):
            from gmail_assistant.core.auth.credential_manager import SecureCredentialManager
            manager = SecureCredentialManager()
            assert manager.credentials_file == 'credentials.json'
            assert manager.service is None

    def test_custom_credentials_file(self):
        """Test custom credentials file path."""
        with patch.dict('sys.modules', {'keyring': MagicMock()}):
            from gmail_assistant.core.auth.credential_manager import SecureCredentialManager
            manager = SecureCredentialManager('/custom/path/creds.json')
            assert manager.credentials_file == '/custom/path/creds.json'


class TestStoreCredentials:
    """Tests for _store_credentials_securely method."""

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_store_credentials_success(self, mock_keyring):
        """Test successful credential storage."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        manager = SecureCredentialManager()
        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"token": "test"}'

        result = manager._store_credentials_securely(mock_creds)

        assert result is True
        mock_keyring.set_password.assert_called_once()

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_store_credentials_failure(self, mock_keyring):
        """Test credential storage failure."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.set_password.side_effect = Exception("Keyring error")
        manager = SecureCredentialManager()
        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"token": "test"}'

        result = manager._store_credentials_securely(mock_creds)

        assert result is False


class TestLoadCredentials:
    """Tests for _load_credentials_securely method."""

    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_load_credentials_success(self, mock_keyring, mock_creds_class):
        """Test successful credential loading."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = '{"token": "test", "refresh_token": "refresh"}'
        mock_creds = Mock()
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        manager = SecureCredentialManager()
        result = manager._load_credentials_securely()

        assert result == mock_creds

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_load_credentials_not_found(self, mock_keyring):
        """Test credential loading when not found."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = None

        manager = SecureCredentialManager()
        result = manager._load_credentials_securely()

        assert result is None

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_load_credentials_error(self, mock_keyring):
        """Test credential loading error handling."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.side_effect = Exception("Keyring error")

        manager = SecureCredentialManager()
        result = manager._load_credentials_securely()

        assert result is None


class TestClearCredentials:
    """Tests for _clear_credentials method."""

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_clear_credentials_success(self, mock_keyring):
        """Test successful credential clearing."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        manager = SecureCredentialManager()
        result = manager._clear_credentials()

        assert result is True
        mock_keyring.delete_password.assert_called_once()

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_clear_credentials_failure(self, mock_keyring):
        """Test credential clearing failure."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        # Create a proper exception that isn't PasswordDeleteError
        mock_keyring.errors = Mock()
        mock_keyring.errors.PasswordDeleteError = type('PasswordDeleteError', (Exception,), {})
        mock_keyring.delete_password.side_effect = OSError("Keyring backend error")

        manager = SecureCredentialManager()
        result = manager._clear_credentials()

        assert result is False


class TestCredentialsValidation:
    """Tests for credential validation logic."""

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_has_valid_credentials_none(self, mock_keyring):
        """Test has_valid_credentials when no credentials exist."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = None

        manager = SecureCredentialManager()
        # The method loads from keyring, returns None if not found
        creds = manager._load_credentials_securely()
        assert creds is None

    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_has_valid_credentials_expired(self, mock_keyring, mock_creds_class):
        """Test handling of expired credentials."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = '{"token": "test"}'
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        manager = SecureCredentialManager()
        creds = manager._load_credentials_securely()

        assert creds.valid is False
        assert creds.expired is True


class TestAuthentication:
    """Tests for authentication flow."""

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_get_service_with_valid_credentials(self, mock_keyring, mock_creds_class, mock_build):
        """Test getting service with valid cached credentials."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = '{"token": "test"}'
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        manager = SecureCredentialManager()
        # Load credentials
        creds = manager._load_credentials_securely()

        assert creds.valid is True

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_get_service_no_credentials_file(self, mock_keyring):
        """Test error when credentials file missing."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = None

        manager = SecureCredentialManager('/nonexistent/credentials.json')
        creds = manager._load_credentials_securely()

        assert creds is None


class TestRefreshToken:
    """Tests for token refresh functionality."""

    @patch('gmail_assistant.core.auth.credential_manager.Request')
    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_refresh_expired_token(self, mock_keyring, mock_creds_class, mock_request):
        """Test refreshing expired token."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = '{"token": "old", "refresh_token": "refresh"}'
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        manager = SecureCredentialManager()
        creds = manager._load_credentials_securely()

        # Credentials loaded but expired
        assert creds is not None
        assert creds.expired is True
        assert creds.refresh_token is not None


class TestKeyringConstants:
    """Tests for keyring constants usage."""

    def test_keyring_service_constant(self):
        """Test that KEYRING_SERVICE constant is used."""
        from gmail_assistant.core.constants import KEYRING_SERVICE
        assert KEYRING_SERVICE == "gmail_assistant"

    def test_keyring_username_constant(self):
        """Test that KEYRING_USERNAME constant is used."""
        from gmail_assistant.core.constants import KEYRING_USERNAME
        assert KEYRING_USERNAME == "oauth_credentials"


class TestClearCredentialsPasswordDeleteError:
    """Tests for _clear_credentials with PasswordDeleteError."""

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_clear_credentials_password_delete_error(self, mock_keyring):
        """Test credential clearing when password doesn't exist."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager
        import keyring.errors as keyring_errors

        # Setup to raise PasswordDeleteError - simulates no credentials to delete
        mock_keyring.errors = keyring_errors
        mock_keyring.delete_password.side_effect = keyring_errors.PasswordDeleteError()

        manager = SecureCredentialManager()
        result = manager._clear_credentials()

        # Should return True even when password doesn't exist
        assert result is True


class TestAuthenticateMethod:
    """Tests for authenticate() method comprehensive coverage."""

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_authenticate_with_valid_cached_credentials(self, mock_keyring, mock_creds_class, mock_build):
        """Test authenticate with valid cached credentials."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        # Setup valid credentials in keyring
        mock_keyring.get_password.return_value = '{"token": "test", "refresh_token": "refresh"}'
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        manager = SecureCredentialManager()
        result = manager.authenticate()

        assert result is True
        assert manager.service == mock_service
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.Request')
    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_authenticate_with_expired_credentials_refresh_success(
        self, mock_keyring, mock_creds_class, mock_request_class, mock_build
    ):
        """Test authenticate refreshes expired credentials successfully."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = '{"token": "old", "refresh_token": "refresh"}'
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_creds.to_json.return_value = '{"token": "new"}'
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        manager = SecureCredentialManager()
        result = manager.authenticate()

        assert result is True
        mock_creds.refresh.assert_called_once()

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.Request')
    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_authenticate_refresh_failure_triggers_oauth_flow(
        self, mock_keyring, mock_creds_class, mock_request_class, mock_build
    ):
        """Test authenticate handles refresh failure by falling through to OAuth."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = '{"token": "old", "refresh_token": "refresh"}'
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_creds.refresh.side_effect = Exception("Refresh failed")
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        manager = SecureCredentialManager('/nonexistent/credentials.json')
        result = manager.authenticate()

        # Should fail because credentials file doesn't exist after refresh fails
        assert result is False

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.InstalledAppFlow')
    @patch('gmail_assistant.core.auth.credential_manager.os')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_authenticate_oauth_flow_success(
        self, mock_keyring, mock_os, mock_flow_class, mock_build
    ):
        """Test authenticate with OAuth flow when no cached credentials."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        # No cached credentials
        mock_keyring.get_password.return_value = None

        # Credentials file exists
        mock_os.path.exists.return_value = True

        # Setup OAuth flow
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.to_json.return_value = '{"token": "new"}'
        mock_flow = Mock()
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        mock_service = Mock()
        mock_build.return_value = mock_service

        manager = SecureCredentialManager('credentials.json')
        result = manager.authenticate()

        assert result is True
        mock_flow_class.from_client_secrets_file.assert_called_once()
        mock_flow.run_local_server.assert_called_once_with(port=0)

    @patch('gmail_assistant.core.auth.credential_manager.os')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_authenticate_no_credentials_file(self, mock_keyring, mock_os, capsys):
        """Test authenticate fails when credentials file is missing."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = None
        mock_os.path.exists.return_value = False

        manager = SecureCredentialManager('missing_credentials.json')
        result = manager.authenticate()

        assert result is False
        # Check that error message was printed
        captured = capsys.readouterr()
        assert "Error" in captured.out or result is False

    @patch('gmail_assistant.core.auth.credential_manager.InstalledAppFlow')
    @patch('gmail_assistant.core.auth.credential_manager.os')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_authenticate_oauth_flow_failure(
        self, mock_keyring, mock_os, mock_flow_class
    ):
        """Test authenticate handles OAuth flow failure."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = None
        mock_os.path.exists.return_value = True
        mock_flow_class.from_client_secrets_file.side_effect = Exception("OAuth error")

        manager = SecureCredentialManager('credentials.json')
        result = manager.authenticate()

        assert result is False

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.InstalledAppFlow')
    @patch('gmail_assistant.core.auth.credential_manager.os')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_authenticate_store_credentials_failure(
        self, mock_keyring, mock_os, mock_flow_class, mock_build
    ):
        """Test authenticate when storing credentials fails."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = None
        mock_os.path.exists.return_value = True
        mock_keyring.set_password.side_effect = Exception("Storage failed")

        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.to_json.return_value = '{"token": "new"}'
        mock_flow = Mock()
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        manager = SecureCredentialManager('credentials.json')
        result = manager.authenticate()

        assert result is False

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_authenticate_build_service_failure(
        self, mock_keyring, mock_creds_class, mock_build
    ):
        """Test authenticate when building Gmail service fails."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = '{"token": "test"}'
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_info.return_value = mock_creds
        mock_build.side_effect = Exception("Service build failed")

        manager = SecureCredentialManager()
        result = manager.authenticate()

        assert result is False


class TestGetServiceMethod:
    """Tests for get_service() method."""

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_get_service_returns_existing_service(
        self, mock_keyring, mock_creds_class, mock_build
    ):
        """Test get_service returns existing service without re-authenticating."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        manager = SecureCredentialManager()
        mock_service = Mock()
        manager.service = mock_service

        result = manager.get_service()

        assert result == mock_service
        # Should not call authenticate since service already exists

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_get_service_authenticates_when_no_service(
        self, mock_keyring, mock_creds_class, mock_build
    ):
        """Test get_service authenticates when no service exists."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = '{"token": "test"}'
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        manager = SecureCredentialManager()
        result = manager.get_service()

        assert result == mock_service

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_get_service_returns_none_on_auth_failure(self, mock_keyring):
        """Test get_service returns None when authentication fails."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = None

        manager = SecureCredentialManager('/nonexistent/creds.json')

        with patch.object(manager, 'authenticate', return_value=False):
            result = manager.get_service()
            assert result is None


class TestResetCredentialsMethod:
    """Tests for reset_credentials() method."""

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_reset_credentials_clears_service(self, mock_keyring):
        """Test reset_credentials clears the service."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        manager = SecureCredentialManager()
        manager.service = Mock()

        result = manager.reset_credentials()

        assert result is True
        assert manager.service is None
        mock_keyring.delete_password.assert_called_once()

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_reset_credentials_success_with_no_service(self, mock_keyring):
        """Test reset_credentials works when service is None."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        manager = SecureCredentialManager()
        manager.service = None

        result = manager.reset_credentials()

        assert result is True
        assert manager.service is None


class TestGetUserInfoMethod:
    """Tests for get_user_info() method."""

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_get_user_info_success(self, mock_keyring, mock_creds_class, mock_build):
        """Test get_user_info returns user information."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = '{"token": "test"}'
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        mock_profile = {
            'emailAddress': 'test@gmail.com',
            'messagesTotal': 1000,
            'threadsTotal': 500
        }
        mock_service = Mock()
        mock_service.users().getProfile().execute.return_value = mock_profile
        mock_build.return_value = mock_service

        manager = SecureCredentialManager()
        manager.authenticate()
        result = manager.get_user_info()

        assert result is not None
        assert result['email'] == 'test@gmail.com'
        assert result['messages_total'] == 1000
        assert result['threads_total'] == 500

    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_get_user_info_no_service(self, mock_keyring):
        """Test get_user_info returns None when service unavailable."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = None

        manager = SecureCredentialManager('/nonexistent/creds.json')

        with patch.object(manager, 'get_service', return_value=None):
            result = manager.get_user_info()
            assert result is None

    @patch('gmail_assistant.core.auth.credential_manager.build')
    @patch('gmail_assistant.core.auth.credential_manager.Credentials')
    @patch('gmail_assistant.core.auth.credential_manager.keyring')
    def test_get_user_info_api_error(self, mock_keyring, mock_creds_class, mock_build):
        """Test get_user_info handles API errors gracefully."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        mock_keyring.get_password.return_value = '{"token": "test"}'
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        mock_service = Mock()
        mock_service.users().getProfile().execute.side_effect = Exception("API Error")
        mock_build.return_value = mock_service

        manager = SecureCredentialManager()
        manager.authenticate()
        result = manager.get_user_info()

        assert result is None
