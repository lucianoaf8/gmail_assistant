"""
Comprehensive tests for manifest.py module.
Tests ManifestManager class for backup integrity verification.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

from gmail_assistant.utils.manifest import (
    BackupManifest,
    FileEntry,
    ManifestManager,
    VerificationResult,
)


class TestFileEntry:
    """Tests for FileEntry dataclass."""

    def test_file_entry_creation(self):
        """Test creating a FileEntry."""
        entry = FileEntry(
            path="2024/01/email.eml",
            size_bytes=1024,
            sha256="abc123",
            modified_at="2024-01-01T12:00:00",
            gmail_id="msg123",
            content_type="eml"
        )
        assert entry.path == "2024/01/email.eml"
        assert entry.size_bytes == 1024
        assert entry.sha256 == "abc123"
        assert entry.gmail_id == "msg123"
        assert entry.content_type == "eml"

    def test_file_entry_to_dict(self):
        """Test FileEntry.to_dict serialization."""
        entry = FileEntry(
            path="test.eml",
            size_bytes=512,
            sha256="def456",
            modified_at="2024-01-15T10:30:00"
        )
        result = entry.to_dict()
        assert result["path"] == "test.eml"
        assert result["size_bytes"] == 512
        assert result["sha256"] == "def456"

    def test_file_entry_from_dict(self):
        """Test FileEntry.from_dict deserialization."""
        data = {
            "path": "test.eml",
            "size_bytes": 1024,
            "sha256": "abc123",
            "modified_at": "2024-01-01T12:00:00",
            "gmail_id": None,
            "content_type": None
        }
        entry = FileEntry.from_dict(data)
        assert entry.path == "test.eml"
        assert entry.size_bytes == 1024

    def test_file_entry_optional_fields(self):
        """Test FileEntry with None optional fields."""
        entry = FileEntry(
            path="test.eml",
            size_bytes=100,
            sha256="hash",
            modified_at="2024-01-01T00:00:00"
        )
        assert entry.gmail_id is None
        assert entry.content_type is None


class TestBackupManifest:
    """Tests for BackupManifest dataclass."""

    def test_manifest_default_values(self):
        """Test BackupManifest default values."""
        manifest = BackupManifest()
        assert manifest.version == "1.0"
        assert manifest.total_files == 0
        assert manifest.total_size_bytes == 0
        assert manifest.files == []
        assert manifest.metadata == {}

    def test_manifest_post_init_sets_dates(self):
        """Test __post_init__ sets created_at and updated_at."""
        manifest = BackupManifest()
        assert manifest.created_at != ""
        assert manifest.updated_at != ""

    def test_manifest_to_dict(self):
        """Test BackupManifest.to_dict serialization."""
        manifest = BackupManifest(
            backup_directory="/backup",
            total_files=5,
            total_size_bytes=10240
        )
        result = manifest.to_dict()
        assert result["version"] == "1.0"
        assert result["backup_directory"] == "/backup"
        assert result["total_files"] == 5
        assert result["total_size_bytes"] == 10240

    def test_manifest_to_dict_with_files(self):
        """Test manifest serialization includes files."""
        entry = FileEntry(
            path="test.eml",
            size_bytes=100,
            sha256="abc",
            modified_at="2024-01-01T00:00:00"
        )
        manifest = BackupManifest(files=[entry])
        result = manifest.to_dict()
        assert len(result["files"]) == 1
        assert result["files"][0]["path"] == "test.eml"

    def test_manifest_from_dict(self):
        """Test BackupManifest.from_dict deserialization."""
        data = {
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "backup_directory": "/backup",
            "total_files": 3,
            "total_size_bytes": 5000,
            "files": [
                {
                    "path": "file.eml",
                    "size_bytes": 100,
                    "sha256": "hash",
                    "modified_at": "2024-01-01T00:00:00",
                    "gmail_id": None,
                    "content_type": None
                }
            ],
            "metadata": {"source": "gmail"}
        }
        manifest = BackupManifest.from_dict(data)
        assert manifest.backup_directory == "/backup"
        assert manifest.total_files == 3
        assert len(manifest.files) == 1


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_verification_result_defaults(self):
        """Test VerificationResult default values."""
        result = VerificationResult()
        assert result.verified == 0
        assert result.missing == []
        assert result.corrupted == []
        assert result.extra == []
        assert result.errors == []

    def test_is_valid_empty(self):
        """Test is_valid returns True when no issues."""
        result = VerificationResult(verified=10)
        assert result.is_valid is True

    def test_is_valid_with_missing(self):
        """Test is_valid returns False when files missing."""
        result = VerificationResult(missing=["file1.eml"])
        assert result.is_valid is False

    def test_is_valid_with_corrupted(self):
        """Test is_valid returns False when files corrupted."""
        result = VerificationResult(corrupted=[{"path": "file.eml"}])
        assert result.is_valid is False

    def test_to_dict(self):
        """Test VerificationResult.to_dict serialization."""
        result = VerificationResult(
            verified=5,
            missing=["a.eml"],
            extra=["b.eml"]
        )
        data = result.to_dict()
        assert data["verified"] == 5
        assert data["missing"] == ["a.eml"]
        assert data["extra"] == ["b.eml"]
        assert "is_valid" in data


class TestManifestManager:
    """Tests for ManifestManager class."""

    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_backup_dir):
        """Create ManifestManager instance."""
        return ManifestManager(temp_backup_dir)

    def test_manager_init(self, temp_backup_dir):
        """Test ManifestManager initialization."""
        manager = ManifestManager(temp_backup_dir)
        assert manager.backup_dir == temp_backup_dir
        assert manager.manifest_path == temp_backup_dir / "backup_manifest.json"

    def test_create_manifest_empty_dir(self, manager, temp_backup_dir):
        """Test creating manifest for empty directory."""
        manifest = manager.create_manifest()
        assert manifest.total_files == 0
        assert manifest.backup_directory == str(temp_backup_dir)

    def test_create_manifest_with_files(self, manager, temp_backup_dir):
        """Test creating manifest with files."""
        # Create test files
        eml_file = temp_backup_dir / "test.eml"
        eml_file.write_text("Email content")
        md_file = temp_backup_dir / "test.md"
        md_file.write_text("Markdown content")

        manifest = manager.create_manifest()
        assert manifest.total_files == 2

    def test_create_manifest_custom_patterns(self, manager, temp_backup_dir):
        """Test creating manifest with custom file patterns."""
        # Create test file
        txt_file = temp_backup_dir / "test.txt"
        txt_file.write_text("Text content")

        manifest = manager.create_manifest(file_patterns=["**/*.txt"])
        assert manifest.total_files == 1

    def test_create_manifest_with_metadata(self, manager, temp_backup_dir):
        """Test creating manifest with custom metadata."""
        metadata = {"source": "gmail", "user": "test@example.com"}
        manifest = manager.create_manifest(metadata=metadata)
        assert manifest.metadata == metadata

    def test_save_and_load_manifest(self, manager, temp_backup_dir):
        """Test saving and loading manifest."""
        # Create and save
        manifest = BackupManifest(
            backup_directory=str(temp_backup_dir),
            total_files=5
        )
        manager.save_manifest(manifest)

        # Load
        loaded = manager.load_manifest()
        assert loaded is not None
        assert loaded.total_files == 5

    def test_load_manifest_not_exists(self, manager):
        """Test loading manifest that doesn't exist returns None."""
        result = manager.load_manifest()
        assert result is None

    def test_calculate_sha256(self, manager, temp_backup_dir):
        """Test SHA-256 calculation."""
        test_file = temp_backup_dir / "test.txt"
        test_file.write_text("Hello, World!")

        sha256 = manager._calculate_sha256(test_file)
        # Known SHA-256 for "Hello, World!"
        assert len(sha256) == 64
        assert all(c in '0123456789abcdef' for c in sha256)

    def test_extract_gmail_id(self, manager):
        """Test Gmail ID extraction from filename."""
        path = Path("2024-01-01_120000_subject_1234567890abcdef.eml")
        gmail_id = manager._extract_gmail_id(path)
        assert gmail_id == "1234567890abcdef"

    def test_extract_gmail_id_no_match(self, manager):
        """Test Gmail ID extraction returns None for non-matching filename."""
        path = Path("simple_file.eml")
        gmail_id = manager._extract_gmail_id(path)
        assert gmail_id is None


class TestManifestVerification:
    """Tests for manifest verification functionality."""

    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_backup_dir):
        """Create ManifestManager instance."""
        return ManifestManager(temp_backup_dir)

    def test_verify_no_manifest(self, manager):
        """Test verification when no manifest exists."""
        result = manager.verify_integrity()
        assert "No manifest found" in result.errors[0]

    def test_verify_all_files_present(self, manager, temp_backup_dir):
        """Test verification when all files are present."""
        # Create test file
        test_file = temp_backup_dir / "test.eml"
        test_file.write_text("Content")

        # Create manifest
        manager.create_manifest()

        # Verify
        result = manager.verify_integrity()
        assert result.verified == 1
        assert result.is_valid is True

    def test_verify_missing_file(self, manager, temp_backup_dir):
        """Test verification detects missing file."""
        # Create test file and manifest
        test_file = temp_backup_dir / "test.eml"
        test_file.write_text("Content")
        manager.create_manifest()

        # Delete file
        test_file.unlink()

        # Verify
        result = manager.verify_integrity()
        assert len(result.missing) == 1
        assert result.is_valid is False

    def test_verify_corrupted_file(self, manager, temp_backup_dir):
        """Test verification detects corrupted file."""
        # Create test file and manifest
        test_file = temp_backup_dir / "test.eml"
        test_file.write_text("Original content")
        manager.create_manifest()

        # Modify file
        test_file.write_text("Modified content")

        # Verify
        result = manager.verify_integrity()
        assert len(result.corrupted) == 1
        assert result.is_valid is False

    def test_verify_extra_files(self, manager, temp_backup_dir):
        """Test verification detects extra files."""
        # Create manifest (empty)
        manager.create_manifest()

        # Add new file
        new_file = temp_backup_dir / "new.eml"
        new_file.write_text("New content")

        # Verify
        result = manager.verify_integrity()
        assert len(result.extra) == 1


class TestManifestUpdate:
    """Tests for manifest update functionality."""

    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_backup_dir):
        """Create ManifestManager instance."""
        return ManifestManager(temp_backup_dir)

    def test_update_manifest_auto_discover(self, manager, temp_backup_dir):
        """Test update manifest auto-discovers new files."""
        # Create initial manifest
        manager.create_manifest()

        # Add new file
        new_file = temp_backup_dir / "new.eml"
        new_file.write_text("New content")

        # Update
        updated = manager.update_manifest()
        assert updated.total_files == 1

    def test_update_manifest_explicit_files(self, manager, temp_backup_dir):
        """Test update manifest with explicit file list."""
        # Create initial manifest
        manager.create_manifest()

        # Add new file
        new_file = temp_backup_dir / "explicit.eml"
        new_file.write_text("Content")

        # Update with explicit list
        updated = manager.update_manifest(new_files=[new_file])
        assert updated.total_files == 1

    def test_update_manifest_no_duplicates(self, manager, temp_backup_dir):
        """Test update manifest doesn't add duplicates."""
        # Create file and manifest
        test_file = temp_backup_dir / "test.eml"
        test_file.write_text("Content")
        manager.create_manifest()

        # Try to update with same file
        updated = manager.update_manifest(new_files=[test_file])
        assert updated.total_files == 1


class TestManifestUtilities:
    """Tests for manifest utility functions."""

    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_backup_dir):
        """Create ManifestManager instance."""
        return ManifestManager(temp_backup_dir)

    def test_get_file_entry(self, manager, temp_backup_dir):
        """Test getting file entry by path."""
        # Create file and manifest
        test_file = temp_backup_dir / "test.eml"
        test_file.write_text("Content")
        manager.create_manifest()

        # Get entry
        entry = manager.get_file_entry("test.eml")
        assert entry is not None
        assert entry.path == "test.eml"

    def test_get_file_entry_not_found(self, manager, temp_backup_dir):
        """Test getting non-existent file entry returns None."""
        manager.create_manifest()
        entry = manager.get_file_entry("nonexistent.eml")
        assert entry is None

    def test_get_stats(self, manager, temp_backup_dir):
        """Test getting manifest statistics."""
        # Create files and manifest
        eml_file = temp_backup_dir / "test.eml"
        eml_file.write_text("Email content")
        md_file = temp_backup_dir / "test.md"
        md_file.write_text("Markdown content")
        manager.create_manifest()

        # Get stats
        stats = manager.get_stats()
        assert stats["total_files"] == 2
        assert "by_content_type" in stats

    def test_get_stats_no_manifest(self, manager):
        """Test getting stats when no manifest exists."""
        stats = manager.get_stats()
        assert "error" in stats

    def test_export_file_list(self, manager, temp_backup_dir):
        """Test exporting file list to text file."""
        # Create files and manifest
        test_file = temp_backup_dir / "test.eml"
        test_file.write_text("Content")
        manager.create_manifest()

        # Export
        output_file = temp_backup_dir / "files.txt"
        count = manager.export_file_list(output_file)
        assert count == 1
        assert output_file.exists()

    def test_find_duplicates(self, manager, temp_backup_dir):
        """Test finding duplicate files by checksum."""
        # Create files with same content
        file1 = temp_backup_dir / "file1.eml"
        file1.write_text("Same content")
        file2 = temp_backup_dir / "file2.eml"
        file2.write_text("Same content")
        manager.create_manifest()

        # Find duplicates
        duplicates = manager.find_duplicates()
        assert len(duplicates) == 1

    def test_find_duplicates_no_duplicates(self, manager, temp_backup_dir):
        """Test finding duplicates when none exist."""
        # Create files with different content
        file1 = temp_backup_dir / "file1.eml"
        file1.write_text("Content 1")
        file2 = temp_backup_dir / "file2.eml"
        file2.write_text("Content 2")
        manager.create_manifest()

        # Find duplicates
        duplicates = manager.find_duplicates()
        assert len(duplicates) == 0


class TestCreateFileEntry:
    """Tests for _create_file_entry method."""

    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_backup_dir):
        """Create ManifestManager instance."""
        return ManifestManager(temp_backup_dir)

    def test_create_entry_eml_file(self, manager, temp_backup_dir):
        """Test creating entry for .eml file."""
        test_file = temp_backup_dir / "test.eml"
        test_file.write_text("Email content")

        entry = manager._create_file_entry(test_file)
        assert entry.content_type == "eml"
        assert entry.path == "test.eml"

    def test_create_entry_md_file(self, manager, temp_backup_dir):
        """Test creating entry for .md file."""
        test_file = temp_backup_dir / "test.md"
        test_file.write_text("Markdown content")

        entry = manager._create_file_entry(test_file)
        assert entry.content_type == "markdown"

    def test_create_entry_txt_file(self, manager, temp_backup_dir):
        """Test creating entry for .txt file."""
        test_file = temp_backup_dir / "test.txt"
        test_file.write_text("Text content")

        entry = manager._create_file_entry(test_file)
        assert entry.content_type == "text"

    def test_create_entry_json_file(self, manager, temp_backup_dir):
        """Test creating entry for .json file."""
        test_file = temp_backup_dir / "test.json"
        test_file.write_text('{"key": "value"}')

        entry = manager._create_file_entry(test_file)
        assert entry.content_type == "json"

    def test_create_entry_unknown_type(self, manager, temp_backup_dir):
        """Test creating entry for unknown file type."""
        test_file = temp_backup_dir / "test.xyz"
        test_file.write_text("Unknown content")

        entry = manager._create_file_entry(test_file)
        assert entry.content_type == "unknown"
