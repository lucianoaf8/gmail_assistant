"""Unit tests for gmail_assistant.cli.main using Click's testing utilities."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from gmail_assistant.cli.main import main
from gmail_assistant import __version__


@pytest.fixture
def runner():
    """Create a Click CLI runner."""
    return CliRunner()


class TestCLIVersion:
    """Test --version option."""

    def test_version_flag(self, runner: CliRunner):
        """--version should output version string."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output
        assert "gmail-assistant" in result.output


class TestCLIHelp:
    """Test --help option."""

    def test_main_help(self, runner: CliRunner):
        """--help should show available commands."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "fetch" in result.output
        assert "delete" in result.output
        assert "analyze" in result.output
        assert "auth" in result.output
        assert "config" in result.output

    def test_main_help_shows_options(self, runner: CliRunner):
        """--help should show global options."""
        result = runner.invoke(main, ["--help"])
        assert "--config" in result.output
        assert "--allow-repo-credentials" in result.output


class TestFetchCommand:
    """Test fetch subcommand."""

    def test_fetch_help(self, runner: CliRunner):
        """fetch --help should show options."""
        result = runner.invoke(main, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "--query" in result.output
        assert "--max-emails" in result.output
        assert "--output-dir" in result.output
        assert "--format" in result.output

    def test_fetch_runs(self, runner: CliRunner):
        """fetch should run without errors."""
        result = runner.invoke(main, ["fetch"])
        assert result.exit_code == 0
        assert "Fetching emails" in result.output

    def test_fetch_with_query(self, runner: CliRunner):
        """fetch --query should accept query string."""
        result = runner.invoke(main, ["fetch", "--query", "is:unread"])
        assert result.exit_code == 0
        assert "is:unread" in result.output

    def test_fetch_with_format(self, runner: CliRunner):
        """fetch --format should accept format option."""
        result = runner.invoke(main, ["fetch", "--format", "mbox"])
        assert result.exit_code == 0
        assert "mbox" in result.output


class TestDeleteCommand:
    """Test delete subcommand."""

    def test_delete_help(self, runner: CliRunner):
        """delete --help should show options."""
        result = runner.invoke(main, ["delete", "--help"])
        assert result.exit_code == 0
        assert "--query" in result.output
        assert "--dry-run" in result.output
        assert "--confirm" in result.output

    def test_delete_requires_query(self, runner: CliRunner):
        """delete should require --query option."""
        result = runner.invoke(main, ["delete"])
        assert result.exit_code == 2  # Click usage error
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_delete_with_query(self, runner: CliRunner):
        """delete --query should run."""
        result = runner.invoke(main, ["delete", "--query", "from:test@example.com"])
        assert result.exit_code == 0
        assert "from:test@example.com" in result.output

    def test_delete_dry_run(self, runner: CliRunner):
        """delete --dry-run should indicate dry run."""
        result = runner.invoke(main, ["delete", "--query", "test", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run: True" in result.output


class TestAnalyzeCommand:
    """Test analyze subcommand."""

    def test_analyze_help(self, runner: CliRunner):
        """analyze --help should show options."""
        result = runner.invoke(main, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "--input-dir" in result.output
        assert "--report" in result.output

    def test_analyze_runs(self, runner: CliRunner):
        """analyze should run without errors."""
        result = runner.invoke(main, ["analyze"])
        assert result.exit_code == 0
        assert "Analyzing emails" in result.output

    def test_analyze_with_report_type(self, runner: CliRunner):
        """analyze --report should accept report type."""
        result = runner.invoke(main, ["analyze", "--report", "json"])
        assert result.exit_code == 0
        assert "json" in result.output


class TestAuthCommand:
    """Test auth subcommand."""

    def test_auth_help(self, runner: CliRunner):
        """auth --help should show help."""
        result = runner.invoke(main, ["auth", "--help"])
        assert result.exit_code == 0

    def test_auth_runs(self, runner: CliRunner):
        """auth should run without errors."""
        result = runner.invoke(main, ["auth"])
        assert result.exit_code == 0
        assert "OAuth flow" in result.output


class TestConfigCommand:
    """Test config subcommand."""

    def test_config_help(self, runner: CliRunner):
        """config --help should show options."""
        result = runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0
        assert "--show" in result.output
        assert "--validate" in result.output
        assert "--init" in result.output

    def test_config_show(self, runner: CliRunner):
        """config --show should display configuration."""
        result = runner.invoke(main, ["config", "--show"])
        assert result.exit_code == 0
        assert "credentials_path" in result.output
        assert "token_path" in result.output
        assert "output_dir" in result.output

    def test_config_validate(self, runner: CliRunner):
        """config --validate should validate configuration."""
        result = runner.invoke(main, ["config", "--validate"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_config_init_creates_file(self, runner: CliRunner, temp_dir: Path):
        """config --init should create config file."""
        with runner.isolated_filesystem(temp_dir=str(temp_dir)):
            # Mock default_dir to use temp directory
            from unittest import mock
            from gmail_assistant.core.config import AppConfig

            config_dir = Path(temp_dir) / ".gmail-assistant"
            with mock.patch.object(AppConfig, "default_dir", return_value=config_dir):
                result = runner.invoke(main, ["config", "--init"])
                assert result.exit_code == 0
                assert "Created" in result.output
                assert (config_dir / "config.json").exists()


class TestGlobalOptions:
    """Test global CLI options."""

    def test_config_option(self, runner: CliRunner, config_file: Path):
        """--config should accept path."""
        result = runner.invoke(main, ["--config", str(config_file), "config", "--show"])
        assert result.exit_code == 0

    def test_allow_repo_credentials(self, runner: CliRunner):
        """--allow-repo-credentials flag should be accepted."""
        result = runner.invoke(main, ["--allow-repo-credentials", "config", "--show"])
        assert result.exit_code == 0
