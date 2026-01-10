"""
Test M-1: Path Traversal Protection
Validates enhanced path validation with URL decoding and symlink resolution.
"""
import pytest
from pathlib import Path
import tempfile
import os


class TestPathTraversalValidation:
    """Tests for path traversal protection (M-1 fix)."""

    def test_basic_traversal_blocked(self):
        """Verify basic path traversal attempts are blocked."""
        from gmail_assistant.utils.input_validator import validate_file_path

        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "data/../../../secrets",
            "./../../sensitive",
        ]

        for path in traversal_paths:
            with pytest.raises(Exception) as exc_info:
                validate_file_path(path)
            assert "traversal" in str(exc_info.value).lower() or \
                   "invalid" in str(exc_info.value).lower()

    def test_url_encoded_traversal_blocked(self):
        """Verify URL-encoded traversal attempts are detected."""
        from gmail_assistant.utils.input_validator import validate_file_path

        encoded_paths = [
            "%2e%2e%2f%2e%2e%2fetc/passwd",  # ../..
            "%2e%2e/%2e%2e/secrets",
            "..%2f..%2f..%2fwindows",
            "%2e%2e%5c%2e%2e%5cwindows",  # ..\..
        ]

        for path in encoded_paths:
            with pytest.raises(Exception):
                validate_file_path(path)

    def test_double_encoded_traversal_blocked(self):
        """Verify double-URL-encoded traversal is detected."""
        from gmail_assistant.utils.input_validator import validate_file_path

        double_encoded = [
            "%252e%252e%252f",  # %2e%2e%2f
            "..%252f..%252f",
        ]

        for path in double_encoded:
            with pytest.raises(Exception):
                validate_file_path(path)

    def test_allowed_base_enforcement(self):
        """Verify allowed_base parameter restricts paths."""
        from gmail_assistant.utils.input_validator import validate_file_path

        with tempfile.TemporaryDirectory() as tmpdir:
            allowed = Path(tmpdir) / "allowed"
            allowed.mkdir()

            # Valid path within allowed base
            valid_file = allowed / "test.txt"
            valid_file.touch()

            result = validate_file_path(str(valid_file), allowed_base=allowed)
            assert result == valid_file

    def test_symlink_resolution(self):
        """Verify symlinks are resolved before validation."""
        from gmail_assistant.utils.input_validator import validate_file_path

        with tempfile.TemporaryDirectory() as tmpdir:
            allowed = Path(tmpdir) / "allowed"
            allowed.mkdir()

            outside = Path(tmpdir) / "outside"
            outside.mkdir()
            secret = outside / "secret.txt"
            secret.write_text("sensitive data")

            # Create symlink from allowed to outside
            symlink = allowed / "escape"
            try:
                symlink.symlink_to(outside)

                # Should block path that escapes via symlink
                with pytest.raises(Exception):
                    validate_file_path(
                        str(symlink / "secret.txt"),
                        allowed_base=allowed
                    )
            except OSError:
                # Symlink creation may require elevated privileges on Windows
                pytest.skip("Symlink creation requires elevated privileges")

    def test_null_byte_injection_blocked(self):
        """Verify null byte injection is blocked."""
        from gmail_assistant.utils.input_validator import validate_file_path

        null_paths = [
            "file.txt\x00.exe",
            "data\x00../secret",
        ]

        for path in null_paths:
            with pytest.raises(Exception):
                validate_file_path(path)


class TestValidPathOperations:
    """Tests for valid path handling."""

    def test_valid_relative_paths(self):
        """Verify valid relative paths are accepted."""
        from gmail_assistant.utils.input_validator import validate_file_path

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)

            valid = Path("subdir")
            valid.mkdir()
            file = valid / "test.txt"
            file.touch()

            result = validate_file_path(str(file))
            assert result.exists()

    def test_valid_absolute_paths(self):
        """Verify valid absolute paths are accepted."""
        from gmail_assistant.utils.input_validator import validate_file_path

        with tempfile.TemporaryDirectory() as tmpdir:
            file = Path(tmpdir) / "test.txt"
            file.touch()

            result = validate_file_path(str(file))
            assert result == file.resolve()
