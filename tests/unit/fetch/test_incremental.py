"""
Comprehensive tests for incremental.py module.
Tests IncrementalGmailFetcher class for incremental operations.
"""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

from gmail_assistant.utils.input_validator import ValidationError


class TestIncrementalGmailFetcherInit:
    """Tests for IncrementalGmailFetcher initialization."""

    def test_init_default_db_path(self):
        """Test initialization with default database path."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher

        fetcher = IncrementalGmailFetcher()
        assert fetcher.db_path == Path("data/databases/emails_final.db")

    def test_init_custom_db_path(self):
        """Test initialization with custom database path."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher

        fetcher = IncrementalGmailFetcher("custom/path.db")
        assert fetcher.db_path == Path("custom/path.db")

    def test_init_creates_checkpoint_manager(self):
        """Test initialization creates checkpoint manager."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher

        fetcher = IncrementalGmailFetcher()
        assert fetcher.checkpoint_manager is not None
        assert fetcher.current_checkpoint is None


class TestGetLatestEmailDate:
    """Tests for get_latest_email_date method."""

    def test_get_latest_date_db_not_found(self):
        """Test returns None when database not found."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher

        fetcher = IncrementalGmailFetcher("/nonexistent/path.db")
        result = fetcher.get_latest_email_date()
        assert result is None

    def test_get_latest_date_with_valid_db(self):
        """Test returns date when database has emails."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create test database with email
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE emails (
                    id INTEGER PRIMARY KEY,
                    parsed_date TEXT
                )
            """)
            conn.execute(
                "INSERT INTO emails (parsed_date) VALUES (?)",
                ("2024-03-15T10:30:00Z",)
            )
            conn.commit()
            conn.close()

            fetcher = IncrementalGmailFetcher(str(db_path))
            result = fetcher.get_latest_email_date()

            assert result == "2024/03/15"

    def test_get_latest_date_empty_db(self):
        """Test returns None when database is empty."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create empty database
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE emails (
                    id INTEGER PRIMARY KEY,
                    parsed_date TEXT
                )
            """)
            conn.commit()
            conn.close()

            fetcher = IncrementalGmailFetcher(str(db_path))
            result = fetcher.get_latest_email_date()

            assert result is None


class TestValidateSubprocessPath:
    """Tests for _validate_subprocess_path method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher
        return IncrementalGmailFetcher()

    def test_validate_path_traversal_rejected(self, fetcher):
        """Test path traversal patterns are rejected."""
        with pytest.raises(ValidationError, match="Path traversal detected"):
            fetcher._validate_subprocess_path("../../../etc/passwd")

    def test_validate_dangerous_chars_rejected(self, fetcher):
        """Test dangerous characters are rejected."""
        dangerous_paths = [
            "path|command",
            "path&command",
            "path;command",
            "path$var",
            "path`command`",
            "path>file",
            "path<file"
        ]
        for path in dangerous_paths:
            with pytest.raises(ValidationError, match="dangerous characters"):
                fetcher._validate_subprocess_path(path)

    def test_validate_safe_path_accepted(self, fetcher):
        """Test safe paths are accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a path under current working directory
            test_path = Path.cwd() / "test_dir"
            test_path.mkdir(exist_ok=True)
            try:
                result = fetcher._validate_subprocess_path(str(test_path))
                assert result == test_path.resolve()
            finally:
                test_path.rmdir()


class TestSafeSubprocessRun:
    """Tests for _safe_subprocess_run method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher
        return IncrementalGmailFetcher()

    def test_safe_subprocess_shell_false(self, fetcher):
        """Test subprocess runs with shell=False."""
        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)

            fetcher._safe_subprocess_run(['echo', 'test'])

            # Verify shell=False was passed
            call_kwargs = mock_run.call_args.kwargs
            assert call_kwargs['shell'] is False

    def test_safe_subprocess_default_timeout(self, fetcher):
        """Test subprocess has default timeout."""
        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)

            fetcher._safe_subprocess_run(['echo', 'test'])

            call_kwargs = mock_run.call_args.kwargs
            assert call_kwargs['timeout'] == 300

    def test_safe_subprocess_custom_timeout(self, fetcher):
        """Test subprocess accepts custom timeout."""
        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)

            fetcher._safe_subprocess_run(['echo', 'test'], timeout=60)

            call_kwargs = mock_run.call_args.kwargs
            assert call_kwargs['timeout'] == 60


class TestFetchIncrementalEmails:
    """Tests for fetch_incremental_emails method."""

    def test_fetch_no_latest_date_fails(self):
        """Test fetch fails when no latest date available."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher

        fetcher = IncrementalGmailFetcher("/nonexistent/path.db")
        success, path = fetcher.fetch_incremental_emails()

        assert success is False
        assert path == ""


class TestConvertEmlToMarkdown:
    """Tests for convert_eml_to_markdown method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher
        return IncrementalGmailFetcher()

    def test_convert_invalid_path_fails(self, fetcher):
        """Test conversion fails with invalid path."""
        result = fetcher.convert_eml_to_markdown("../../../invalid")
        assert result is False

    def test_convert_dangerous_path_fails(self, fetcher):
        """Test conversion fails with dangerous path."""
        result = fetcher.convert_eml_to_markdown("path|command")
        assert result is False


class TestRunIncrementalFetch:
    """Tests for run_incremental_fetch method."""

    def test_run_fetch_fails_without_latest_date(self):
        """Test run fails when no latest date available."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher

        fetcher = IncrementalGmailFetcher("/nonexistent/path.db")
        result = fetcher.run_incremental_fetch()

        assert result is False


class TestAliasBackwardCompatibility:
    """Tests for backward compatibility alias."""

    def test_incremental_fetcher_alias_exists(self):
        """Test IncrementalFetcher alias exists."""
        from gmail_assistant.core.fetch.incremental import (
            IncrementalFetcher,
            IncrementalGmailFetcher,
        )

        assert IncrementalFetcher is IncrementalGmailFetcher


class TestCheckpointIntegration:
    """Tests for checkpoint integration."""

    def test_fetcher_has_checkpoint_manager(self):
        """Test fetcher creates checkpoint manager."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher

        fetcher = IncrementalGmailFetcher()
        assert hasattr(fetcher, 'checkpoint_manager')
        assert fetcher.checkpoint_manager is not None

    def test_fetcher_checkpoint_initially_none(self):
        """Test current checkpoint is initially None."""
        from gmail_assistant.core.fetch.incremental import IncrementalGmailFetcher

        fetcher = IncrementalGmailFetcher()
        assert fetcher.current_checkpoint is None
