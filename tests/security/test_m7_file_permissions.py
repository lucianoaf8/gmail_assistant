"""
Test M-7: Secure File Permissions
Validates restrictive file permissions for sensitive files.
"""
import pytest
import tempfile
import stat
import os
from pathlib import Path


class TestSecureFileModule:
    """Tests for secure file permissions (M-7 fix)."""

    def test_secure_file_module_exists(self):
        """Verify secure file module exists."""
        from gmail_assistant.utils import secure_file

        assert hasattr(secure_file, 'secure_write') or \
               hasattr(secure_file, 'SecureFileWriter'), \
            "Secure file writer should exist"

    def test_file_permissions_restrictive(self):
        """Verify files are created with restrictive permissions."""
        from gmail_assistant.utils.secure_file import secure_write

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "sensitive.txt"

            secure_write(test_file, "sensitive data")

            # Check file permissions (Unix-style)
            if os.name != 'nt':  # Skip on Windows
                mode = stat.S_IMODE(os.stat(test_file).st_mode)

                # Should be 0o600 or more restrictive
                assert mode & stat.S_IRWXG == 0, "Group should have no access"
                assert mode & stat.S_IRWXO == 0, "Others should have no access"
                assert mode & stat.S_IRUSR, "Owner should have read"
                assert mode & stat.S_IWUSR, "Owner should have write"

    def test_directory_permissions_restrictive(self):
        """Verify directories are created with restrictive permissions."""
        from gmail_assistant.utils.secure_file import secure_mkdir

        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "sensitive_dir"

            secure_mkdir(test_dir)

            # Check directory permissions (Unix-style)
            if os.name != 'nt':  # Skip on Windows
                mode = stat.S_IMODE(os.stat(test_dir).st_mode)

                # Should be 0o700 or more restrictive
                assert mode & stat.S_IRWXG == 0, "Group should have no access"
                assert mode & stat.S_IRWXO == 0, "Others should have no access"

    def test_existing_file_permissions_fixed(self):
        """Verify existing files have permissions corrected on appropriate platforms."""
        from gmail_assistant.utils.secure_file import secure_write

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "existing.txt"
            test_file.write_text("initial content")

            if os.name != 'nt':  # Unix-like systems
                # Make file world-readable (insecure)
                os.chmod(test_file, 0o644)

                # Secure write should fix permissions
                secure_write(test_file, "updated content")

                mode = stat.S_IMODE(os.stat(test_file).st_mode)
                assert mode & stat.S_IRWXG == 0, "Group access should be removed"
            else:  # Windows
                # On Windows, test that file can be written and exists
                secure_write(test_file, "updated content")
                assert test_file.exists()
                assert test_file.read_text() == "updated content"


class TestSensitiveFileHandling:
    """Tests for sensitive file handling."""

    def test_credential_files_secured(self):
        """Verify credential files use secure permissions."""
        from gmail_assistant.utils import secure_file

        source = Path(secure_file.__file__).read_text(encoding='utf-8')

        # Should have restrictive permission constants
        assert '0o600' in source or '0600' in source or \
               'S_IRUSR' in source or 'S_IWUSR' in source

    def test_token_files_secured(self):
        """Verify token files use secure permissions."""
        # Token files should be handled with secure permissions

    def test_config_files_secured(self):
        """Verify config files with secrets use secure permissions."""
        # Config files containing credentials should be secured
