"""
Comprehensive tests for auth.py command module.
Tests authenticate, check_auth_status, and revoke_auth functions.
"""

from pathlib import Path
from unittest import mock

import pytest


class TestAuthenticate:
    """Tests for authenticate function."""

    def test_authenticate_missing_credentials(self, tmp_path):
        """Test authenticate raises error for missing credentials file."""
        from gmail_assistant.cli.commands.auth import authenticate
        from gmail_assistant.core.exceptions import AuthError

        nonexistent = tmp_path / "credentials.json"

        with pytest.raises(AuthError, match="not found"):
            authenticate(nonexistent)

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_authenticate_success(self, mock_manager_class, tmp_path):
        """Test successful authentication."""
        from gmail_assistant.cli.commands.auth import authenticate

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_manager = mock.MagicMock()
        mock_manager.authenticate.return_value = True
        mock_manager.get_user_info.return_value = {
            'email': 'test@example.com',
            'messages_total': 1000,
            'threads_total': 500
        }
        mock_manager_class.return_value = mock_manager

        result = authenticate(creds_path)

        assert result['success'] is True
        assert result['email'] == 'test@example.com'
        assert result['messages_total'] == 1000

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_authenticate_failure(self, mock_manager_class, tmp_path):
        """Test authentication failure."""
        from gmail_assistant.cli.commands.auth import authenticate
        from gmail_assistant.core.exceptions import AuthError

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_manager = mock.MagicMock()
        mock_manager.authenticate.return_value = False
        mock_manager_class.return_value = mock_manager

        with pytest.raises(AuthError, match="Authentication failed"):
            authenticate(creds_path)

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_authenticate_force_reauth(self, mock_manager_class, tmp_path):
        """Test force re-authentication clears existing credentials."""
        from gmail_assistant.cli.commands.auth import authenticate

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_manager = mock.MagicMock()
        mock_manager.authenticate.return_value = True
        mock_manager.get_user_info.return_value = None
        mock_manager_class.return_value = mock_manager

        authenticate(creds_path, force_reauth=True)

        mock_manager.reset_credentials.assert_called_once()

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_authenticate_no_user_info(self, mock_manager_class, tmp_path):
        """Test authenticate handles missing user info."""
        from gmail_assistant.cli.commands.auth import authenticate

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_manager = mock.MagicMock()
        mock_manager.authenticate.return_value = True
        mock_manager.get_user_info.return_value = None
        mock_manager_class.return_value = mock_manager

        result = authenticate(creds_path)

        assert result['success'] is True
        assert result['email'] is None


class TestCheckAuthStatus:
    """Tests for check_auth_status function."""

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_check_status_no_credentials(self, mock_manager_class, tmp_path):
        """Test status check with no stored credentials."""
        from gmail_assistant.cli.commands.auth import check_auth_status

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_manager = mock.MagicMock()
        mock_manager._load_credentials_securely.return_value = None
        mock_manager_class.return_value = mock_manager

        result = check_auth_status(creds_path)

        assert result['authenticated'] is False
        assert 'No credentials' in result['status']

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_check_status_valid_credentials(self, mock_manager_class, tmp_path):
        """Test status check with valid credentials."""
        from gmail_assistant.cli.commands.auth import check_auth_status

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_creds = mock.MagicMock()
        mock_creds.valid = True
        mock_manager = mock.MagicMock()
        mock_manager._load_credentials_securely.return_value = mock_creds
        mock_manager_class.return_value = mock_manager

        result = check_auth_status(creds_path)

        assert result['authenticated'] is True
        assert 'Valid' in result['status']

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_check_status_expired_credentials(self, mock_manager_class, tmp_path):
        """Test status check with expired but refreshable credentials."""
        from gmail_assistant.cli.commands.auth import check_auth_status

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_creds = mock.MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = 'refresh_token_here'
        mock_manager = mock.MagicMock()
        mock_manager._load_credentials_securely.return_value = mock_creds
        mock_manager_class.return_value = mock_manager

        result = check_auth_status(creds_path)

        assert result['authenticated'] is False
        assert 'expired' in result['status'].lower()
        assert result['refresh_available'] is True

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_check_status_invalid_credentials(self, mock_manager_class, tmp_path):
        """Test status check with invalid credentials."""
        from gmail_assistant.cli.commands.auth import check_auth_status

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_creds = mock.MagicMock()
        mock_creds.valid = False
        mock_creds.expired = False
        mock_manager = mock.MagicMock()
        mock_manager._load_credentials_securely.return_value = mock_creds
        mock_manager_class.return_value = mock_manager

        result = check_auth_status(creds_path)

        assert result['authenticated'] is False
        assert 'invalid' in result['status'].lower()


class TestRevokeAuth:
    """Tests for revoke_auth function."""

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_revoke_success(self, mock_manager_class):
        """Test successful credential revocation."""
        from gmail_assistant.cli.commands.auth import revoke_auth

        mock_manager = mock.MagicMock()
        mock_manager.reset_credentials.return_value = True
        mock_manager_class.return_value = mock_manager

        result = revoke_auth()

        assert result['success'] is True
        mock_manager.reset_credentials.assert_called_once()

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_revoke_failure(self, mock_manager_class):
        """Test failed credential revocation."""
        from gmail_assistant.cli.commands.auth import revoke_auth

        mock_manager = mock.MagicMock()
        mock_manager.reset_credentials.return_value = False
        mock_manager_class.return_value = mock_manager

        result = revoke_auth()

        assert result['success'] is False
        assert 'Failed' in result['message']


class TestAuthenticateEdgeCases:
    """Edge case tests for authentication."""

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_authenticate_partial_user_info(self, mock_manager_class, tmp_path):
        """Test authenticate handles partial user info using .get() defaults."""
        from gmail_assistant.cli.commands.auth import authenticate

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_manager = mock.MagicMock()
        mock_manager.authenticate.return_value = True
        mock_manager.get_user_info.return_value = {
            'email': 'test@example.com'
            # Missing messages_total and threads_total
        }
        mock_manager_class.return_value = mock_manager

        result = authenticate(creds_path)

        assert result['success'] is True
        assert result['email'] == 'test@example.com'
        # Messages_total returns None because dict.get() returns None for missing keys
        # unless a default is provided (which the source doesn't do)
        assert result.get('messages_total') is None or result.get('messages_total') == 0

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_authenticate_logs_credentials_path(self, mock_manager_class, tmp_path, capsys):
        """Test authenticate shows credentials path."""
        from gmail_assistant.cli.commands.auth import authenticate

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_manager = mock.MagicMock()
        mock_manager.authenticate.return_value = True
        mock_manager.get_user_info.return_value = {'email': 'test@example.com'}
        mock_manager_class.return_value = mock_manager

        authenticate(creds_path)

        captured = capsys.readouterr()
        assert str(creds_path) in captured.out

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    def test_check_status_expired_no_refresh(self, mock_manager_class, tmp_path):
        """Test status check with expired credentials but no refresh token."""
        from gmail_assistant.cli.commands.auth import check_auth_status

        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{}')

        mock_creds = mock.MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = None  # No refresh token
        mock_manager = mock.MagicMock()
        mock_manager._load_credentials_securely.return_value = mock_creds
        mock_manager_class.return_value = mock_manager

        result = check_auth_status(creds_path)

        assert result['authenticated'] is False
        assert 'invalid' in result['status'].lower()


class TestAuthModuleExports:
    """Tests for module exports."""

    def test_module_exports(self):
        """Test module has expected exports."""
        from gmail_assistant.cli.commands import auth

        assert hasattr(auth, 'authenticate')
        assert hasattr(auth, 'check_auth_status')
        assert hasattr(auth, 'revoke_auth')
        assert callable(auth.authenticate)
        assert callable(auth.check_auth_status)
        assert callable(auth.revoke_auth)

    def test_all_exports(self):
        """Test __all__ contains expected functions."""
        from gmail_assistant.cli.commands.auth import __all__

        assert 'authenticate' in __all__
        assert 'check_auth_status' in __all__
        assert 'revoke_auth' in __all__
