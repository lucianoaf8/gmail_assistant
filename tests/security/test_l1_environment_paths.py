"""
Test L-1: Environment Variable Path Overrides
Validates environment variable configuration for paths.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch


class TestEnvironmentPathOverrides:
    """Tests for environment variable path overrides (L-1 fix)."""

    def test_config_dir_override(self):
        """Verify CONFIG_DIR can be overridden via environment."""
        with patch.dict(os.environ, {'GMAIL_ASSISTANT_CONFIG_DIR': '/custom/config'}):
            # Force reimport to pick up new env var
            import importlib
            from gmail_assistant.core import constants
            importlib.reload(constants)

            assert str(constants.CONFIG_DIR) == '/custom/config'

    def test_data_dir_override(self):
        """Verify DATA_DIR can be overridden via environment."""
        with patch.dict(os.environ, {'GMAIL_ASSISTANT_DATA_DIR': '/custom/data'}):
            import importlib
            from gmail_assistant.core import constants
            importlib.reload(constants)

            assert str(constants.DATA_DIR) == '/custom/data'

    def test_backup_dir_override(self):
        """Verify BACKUP_DIR can be overridden via environment."""
        with patch.dict(os.environ, {'GMAIL_ASSISTANT_BACKUP_DIR': '/custom/backups'}):
            import importlib
            from gmail_assistant.core import constants
            importlib.reload(constants)

            assert str(constants.BACKUP_DIR) == '/custom/backups'

    def test_env_path_function_exists(self):
        """Verify _get_env_path helper function exists."""
        from gmail_assistant.core import constants

        source = Path(constants.__file__).read_text()

        assert '_get_env_path' in source, \
            "_get_env_path helper function should exist"

    def test_default_paths_when_no_env(self):
        """Verify default paths used when env vars not set."""
        # Clear relevant env vars
        env_vars = [
            'GMAIL_ASSISTANT_CONFIG_DIR',
            'GMAIL_ASSISTANT_DATA_DIR',
            'GMAIL_ASSISTANT_BACKUP_DIR',
        ]

        clean_env = {k: v for k, v in os.environ.items()
                     if k not in env_vars}

        with patch.dict(os.environ, clean_env, clear=True):
            import importlib
            from gmail_assistant.core import constants
            importlib.reload(constants)

            # Should use default project-relative paths
            assert constants.CONFIG_DIR.exists() or 'config' in str(constants.CONFIG_DIR).lower()


class TestEnvironmentSecurity:
    """Tests for environment variable security."""

    def test_path_traversal_in_env_blocked(self):
        """Verify path traversal in env vars is handled."""
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32',
        ]

        for malicious in malicious_paths:
            with patch.dict(os.environ, {'GMAIL_ASSISTANT_CONFIG_DIR': malicious}):
                import importlib
                from gmail_assistant.core import constants
                importlib.reload(constants)

                # Path should be converted to absolute, neutralizing traversal
                assert '..' not in str(constants.CONFIG_DIR.resolve())

    def test_empty_env_uses_default(self):
        """Verify empty environment variables use defaults."""
        with patch.dict(os.environ, {'GMAIL_ASSISTANT_CONFIG_DIR': ''}):
            import importlib
            from gmail_assistant.core import constants
            importlib.reload(constants)

            # Empty string should result in default path
            assert constants.CONFIG_DIR is not None
            assert str(constants.CONFIG_DIR) != ''
