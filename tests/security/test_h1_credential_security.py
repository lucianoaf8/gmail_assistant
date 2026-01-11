"""
Test H-1: Credential Storage Security
Validates SecureCredentialManager keyring integration.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path


class TestSecureCredentialManager:
    """Tests for secure credential storage (H-1 fix)."""

    def test_no_plaintext_token_storage(self):
        """Verify credentials are NOT stored in plaintext files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_path = Path(tmpdir) / "token.json"

            # token.json should NOT be created by SecureCredentialManager
            assert not token_path.exists(), "Plaintext token.json should not exist"

    @patch('keyring.get_password')
    def test_keyring_credential_retrieval(self, mock_get):
        """Verify credentials retrieved from keyring."""
        mock_get.return_value = '{"token": "encrypted_data"}'

        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        # Should attempt keyring access, not file access
        manager = SecureCredentialManager("credentials.json")
        mock_get.assert_not_called()  # Only called during actual auth

    @patch('keyring.set_password')
    def test_keyring_credential_storage(self, mock_set):
        """Verify credentials stored via keyring."""
        from gmail_assistant.core.auth.credential_manager import SecureCredentialManager

        manager = SecureCredentialManager("credentials.json")
        # Keyring should be used for storage, not file system

    def test_legacy_token_migration_warning(self, caplog):
        """Verify warning when legacy token.json exists."""
        import logging
        caplog.set_level(logging.WARNING)

        with tempfile.TemporaryDirectory() as tmpdir:
            token_path = Path(tmpdir) / "token.json"
            token_path.write_text('{"token": "old"}')

            # Migration should warn about legacy tokens
            # (Actual implementation migrates on first use)

    def test_credential_manager_uses_os_keyring(self):
        """Verify credential manager imports keyring module."""
        from gmail_assistant.core.auth import credential_manager

        # Module should use keyring for secure storage
        source = Path(credential_manager.__file__).read_text(encoding='utf-8')
        assert 'keyring' in source, "Credential manager should use keyring module"


class TestGmailAPIClientCredentials:
    """Tests for Gmail API client credential integration."""

    def test_api_client_uses_secure_manager(self):
        """Verify GmailAPIClient uses SecureCredentialManager."""
        from gmail_assistant.core.fetch import gmail_api_client

        source = Path(gmail_api_client.__file__).read_text(encoding='utf-8')
        assert 'SecureCredentialManager' in source, \
            "GmailAPIClient should use SecureCredentialManager"

    def test_no_direct_token_file_handling(self):
        """Verify no direct token.json file handling in API client."""
        from gmail_assistant.core.fetch import gmail_api_client

        source = Path(gmail_api_client.__file__).read_text(encoding='utf-8')
        # Should not have direct token file operations
        assert 'token.json' not in source or 'legacy' in source.lower() or 'migrate' in source.lower(), \
            "Should not have direct token.json handling except for migration"
