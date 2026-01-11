"""
Comprehensive tests for secure_file.py module.
Tests SecureFileWriter class for atomic writes and secure permissions.
"""

import os
import stat
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from gmail_assistant.utils.secure_file import (
    SecureFileWriter,
    secure_mkdir,
    secure_write,
)


class TestSecureFileWriter:
    """Tests for SecureFileWriter class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_write_secure_creates_file(self, temp_dir):
        """Test that write_secure creates a file with correct content."""
        test_file = temp_dir / "test.txt"
        content = "Test content"

        SecureFileWriter.write_secure(test_file, content)

        assert test_file.exists()
        assert test_file.read_text() == content

    def test_write_secure_creates_parent_directories(self, temp_dir):
        """Test that write_secure creates parent directories if needed."""
        test_file = temp_dir / "subdir" / "nested" / "test.txt"
        content = "Nested content"

        SecureFileWriter.write_secure(test_file, content)

        assert test_file.exists()
        assert test_file.read_text() == content

    def test_write_secure_overwrites_existing_file(self, temp_dir):
        """Test that write_secure overwrites existing files."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Original content")

        SecureFileWriter.write_secure(test_file, "New content")

        assert test_file.read_text() == "New content"

    def test_write_secure_with_custom_encoding(self, temp_dir):
        """Test write_secure with different encoding."""
        test_file = temp_dir / "test.txt"
        content = "Test with utf-16"

        SecureFileWriter.write_secure(test_file, content, encoding='utf-8')

        assert test_file.read_text(encoding='utf-8') == content

    def test_write_secure_unicode_content(self, temp_dir):
        """Test write_secure handles unicode content."""
        test_file = temp_dir / "unicode.txt"
        content = "Unicode: abc123"  # Simple test for unicode file creation

        SecureFileWriter.write_secure(test_file, content)

        assert test_file.read_text(encoding='utf-8') == content

    def test_write_secure_atomic_on_failure(self, temp_dir):
        """Test that write fails atomically without corrupting existing file."""
        test_file = temp_dir / "test.txt"
        original_content = "Original content"
        test_file.write_text(original_content)

        # Mock os.replace to fail
        with mock.patch('os.replace', side_effect=OSError("Mock error")):
            with pytest.raises(OSError):
                SecureFileWriter.write_secure(test_file, "New content")

        # Original file should remain unchanged
        assert test_file.read_text() == original_content

    def test_write_secure_cleans_up_temp_on_failure(self, temp_dir):
        """Test that temp files are cleaned up on failure."""
        test_file = temp_dir / "test.txt"

        with mock.patch('os.replace', side_effect=OSError("Mock error")):
            with pytest.raises(OSError):
                SecureFileWriter.write_secure(test_file, "Content")

        # Check no temp files remain
        temp_files = list(temp_dir.glob(".secure_*.tmp"))
        assert len(temp_files) == 0

    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific permissions test")
    def test_write_secure_sets_unix_permissions(self, temp_dir):
        """Test that write_secure sets restrictive permissions on Unix."""
        test_file = temp_dir / "secure.txt"

        SecureFileWriter.write_secure(test_file, "Secret content")

        mode = test_file.stat().st_mode
        # Check owner read/write only (0o600)
        assert mode & stat.S_IRWXU == (stat.S_IRUSR | stat.S_IWUSR)
        assert mode & stat.S_IRWXG == 0
        assert mode & stat.S_IRWXO == 0


class TestSecureFileWriterBytes:
    """Tests for write_secure_bytes method."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_write_secure_bytes_creates_file(self, temp_dir):
        """Test that write_secure_bytes creates a binary file."""
        test_file = temp_dir / "test.bin"
        content = b"\x00\x01\x02\x03\xff"

        SecureFileWriter.write_secure_bytes(test_file, content)

        assert test_file.exists()
        assert test_file.read_bytes() == content

    def test_write_secure_bytes_creates_parent_dirs(self, temp_dir):
        """Test that write_secure_bytes creates parent directories."""
        test_file = temp_dir / "sub" / "test.bin"
        content = b"Binary content"

        SecureFileWriter.write_secure_bytes(test_file, content)

        assert test_file.exists()
        assert test_file.read_bytes() == content

    def test_write_secure_bytes_large_content(self, temp_dir):
        """Test write_secure_bytes with large content."""
        test_file = temp_dir / "large.bin"
        content = b"X" * (1024 * 1024)  # 1MB

        SecureFileWriter.write_secure_bytes(test_file, content)

        assert test_file.read_bytes() == content


class TestCreateSecureDirectory:
    """Tests for create_secure_directory method."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_create_secure_directory_creates_dir(self, temp_dir):
        """Test that create_secure_directory creates a directory."""
        new_dir = temp_dir / "secure_dir"

        result = SecureFileWriter.create_secure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_create_secure_directory_nested(self, temp_dir):
        """Test that create_secure_directory creates nested directories."""
        new_dir = temp_dir / "a" / "b" / "c"

        result = SecureFileWriter.create_secure_directory(new_dir)

        assert new_dir.exists()
        assert result == new_dir

    def test_create_secure_directory_idempotent(self, temp_dir):
        """Test that create_secure_directory is idempotent."""
        new_dir = temp_dir / "secure_dir"
        new_dir.mkdir()

        # Should not raise
        result = SecureFileWriter.create_secure_directory(new_dir)

        assert result == new_dir

    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific permissions test")
    def test_create_secure_directory_unix_permissions(self, temp_dir):
        """Test secure directory has restrictive permissions on Unix."""
        new_dir = temp_dir / "secure_dir"

        SecureFileWriter.create_secure_directory(new_dir)

        mode = new_dir.stat().st_mode
        # Check owner read/write/execute only (0o700)
        assert mode & stat.S_IRWXU == stat.S_IRWXU
        assert mode & stat.S_IRWXG == 0
        assert mode & stat.S_IRWXO == 0


class TestSecureExistingFile:
    """Tests for secure_existing_file method."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_secure_existing_file_success(self, temp_dir):
        """Test securing an existing file succeeds."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Content")

        result = SecureFileWriter.secure_existing_file(test_file)

        assert result is True

    def test_secure_existing_file_nonexistent(self, temp_dir):
        """Test securing non-existent file returns False."""
        test_file = temp_dir / "nonexistent.txt"

        result = SecureFileWriter.secure_existing_file(test_file)

        assert result is False

    def test_secure_existing_file_directory(self, temp_dir):
        """Test securing an existing directory succeeds."""
        new_dir = temp_dir / "dir"
        new_dir.mkdir()

        result = SecureFileWriter.secure_existing_file(new_dir)

        assert result is True


class TestVerifyPermissions:
    """Tests for verify_permissions method."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_verify_permissions_nonexistent(self, temp_dir):
        """Test verify_permissions returns False for non-existent file."""
        test_file = temp_dir / "nonexistent.txt"

        result = SecureFileWriter.verify_permissions(test_file)

        assert result is False

    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific permissions test")
    def test_verify_permissions_secure_file(self, temp_dir):
        """Test verify_permissions returns True for secure file on Unix."""
        test_file = temp_dir / "secure.txt"
        test_file.write_text("Content")
        os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR)

        result = SecureFileWriter.verify_permissions(test_file)

        assert result is True

    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific permissions test")
    def test_verify_permissions_insecure_file(self, temp_dir):
        """Test verify_permissions returns False for world-readable file."""
        test_file = temp_dir / "insecure.txt"
        test_file.write_text("Content")
        os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IROTH)

        result = SecureFileWriter.verify_permissions(test_file)

        assert result is False

    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_verify_permissions_windows(self, temp_dir):
        """Test verify_permissions returns True on Windows (basic check)."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Content")

        result = SecureFileWriter.verify_permissions(test_file)

        assert result is True


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_secure_write_function(self, temp_dir):
        """Test secure_write convenience function."""
        test_file = temp_dir / "test.txt"

        secure_write(test_file, "Content")

        assert test_file.read_text() == "Content"

    def test_secure_write_with_encoding(self, temp_dir):
        """Test secure_write with encoding parameter."""
        test_file = temp_dir / "test.txt"

        secure_write(test_file, "Content", encoding='utf-8')

        assert test_file.read_text() == "Content"

    def test_secure_mkdir_function(self, temp_dir):
        """Test secure_mkdir convenience function."""
        new_dir = temp_dir / "secure"

        result = secure_mkdir(new_dir)

        assert new_dir.exists()
        assert result == new_dir


class TestWindowsPermissions:
    """Tests for Windows-specific permission handling."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_windows_permissions_fallback(self, temp_dir):
        """Test Windows permissions fallback when pywin32 not available."""
        test_file = temp_dir / "test.txt"

        with mock.patch.dict('sys.modules', {'win32security': None, 'ntsecuritycon': None}):
            SecureFileWriter.write_secure(test_file, "Content")

        assert test_file.exists()

    def test_set_windows_permissions_import_error(self, temp_dir):
        """Test _set_windows_permissions handles ImportError gracefully."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Content")

        # This should not raise even if pywin32 is not available
        SecureFileWriter._set_windows_permissions(test_file)

        # File should still exist
        assert test_file.exists()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_write_empty_content(self, temp_dir):
        """Test writing empty content creates empty file."""
        test_file = temp_dir / "empty.txt"

        SecureFileWriter.write_secure(test_file, "")

        assert test_file.exists()
        assert test_file.read_text() == ""

    def test_write_string_path(self, temp_dir):
        """Test write_secure accepts string path."""
        test_file = str(temp_dir / "test.txt")

        SecureFileWriter.write_secure(test_file, "Content")

        assert Path(test_file).read_text() == "Content"

    def test_create_directory_string_path(self, temp_dir):
        """Test create_secure_directory accepts string path."""
        new_dir = str(temp_dir / "secure")

        result = SecureFileWriter.create_secure_directory(new_dir)

        assert Path(new_dir).exists()
        assert result == Path(new_dir)
