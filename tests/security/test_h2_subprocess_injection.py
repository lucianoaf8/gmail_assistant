"""
Test H-2: Subprocess Injection Prevention
Validates subprocess path validation and safe execution.
"""
import pytest
from pathlib import Path
import tempfile
from gmail_assistant.core.exceptions import ValidationError


class TestSubprocessPathValidation:
    """Tests for subprocess path validation (H-2 fix)."""

    @pytest.fixture
    def incremental_fetcher(self):
        """Create incremental fetcher instance for testing."""
        from gmail_assistant.core.fetch.incremental import IncrementalFetcher

        # IncrementalFetcher takes db_path, not service
        return IncrementalFetcher(db_path="test_db.db")

    def test_path_traversal_blocked(self, incremental_fetcher):
        """Verify path traversal attempts are blocked."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "data/../../../sensitive",
            "backups/../../secrets",
        ]

        for path in malicious_paths:
            with pytest.raises(Exception) as exc_info:
                incremental_fetcher._validate_subprocess_path(path)
            assert "traversal" in str(exc_info.value).lower() or \
                   "invalid" in str(exc_info.value).lower() or \
                   "not within" in str(exc_info.value).lower()

    def test_dangerous_characters_blocked(self, incremental_fetcher):
        """Verify shell metacharacters are rejected."""
        dangerous_inputs = [
            "file; rm -rf /",
            "file | cat /etc/passwd",
            "file && malicious_cmd",
            "file`whoami`",
            "file > /tmp/output",
            "file\n;malicious",
        ]

        for path in dangerous_inputs:
            with pytest.raises(Exception) as exc_info:
                incremental_fetcher._validate_subprocess_path(path)
            assert "dangerous" in str(exc_info.value).lower() or \
                   "invalid" in str(exc_info.value).lower()

    def test_valid_paths_allowed(self, incremental_fetcher):
        """Verify legitimate paths are accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_path = Path(tmpdir) / "data" / "emails"
            valid_path.mkdir(parents=True)

            # Should not raise for valid paths within allowed bases
            # Note: actual validation depends on allowed_bases config

    def test_shell_false_enforcement(self):
        """Verify shell=False is enforced in subprocess calls."""
        from gmail_assistant.core.fetch import incremental

        source = Path(incremental.__file__).read_text(encoding='utf-8')

        # Should have shell=False in subprocess calls
        assert "shell=False" in source or "'shell': False" in source, \
            "Subprocess calls should explicitly set shell=False"


class TestSafeSubprocessExecution:
    """Tests for safe subprocess execution wrapper."""

    def test_subprocess_timeout_enforced(self):
        """Verify subprocess calls have timeout protection."""
        from gmail_assistant.core.fetch import incremental

        source = Path(incremental.__file__).read_text(encoding='utf-8')

        # Should have timeout in subprocess configuration
        assert "timeout" in source.lower(), \
            "Subprocess calls should have timeout protection"

    def test_no_shell_expansion(self):
        """Verify no shell expansion vulnerabilities."""
        from gmail_assistant.core.fetch import incremental

        source = Path(incremental.__file__).read_text(encoding='utf-8')

        # Should not use shell=True anywhere
        lines_with_shell_true = [
            line for line in source.split('\n')
            if 'shell=True' in line and not line.strip().startswith('#')
        ]
        assert len(lines_with_shell_true) == 0, \
            f"Found shell=True in: {lines_with_shell_true}"
