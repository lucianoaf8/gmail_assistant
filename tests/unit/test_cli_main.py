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


class TestHandleErrorsDecorator:
    """Test error handling decorator for CLI commands."""

    def test_config_error_exit_code(self, runner: CliRunner, temp_dir: Path):
        """ConfigError should result in exit code 5."""
        from unittest import mock
        from gmail_assistant.core.exceptions import ConfigError

        with mock.patch(
            'gmail_assistant.core.config.AppConfig.load',
            side_effect=ConfigError("Invalid configuration")
        ):
            result = runner.invoke(main, ["fetch"])
            assert result.exit_code == 5
            assert "Configuration error" in result.output

    def test_auth_error_exit_code(self, runner: CliRunner):
        """AuthError should result in exit code 3."""
        from unittest import mock
        from gmail_assistant.core.exceptions import AuthError

        with mock.patch(
            'gmail_assistant.core.config.AppConfig.load',
            side_effect=AuthError("Authentication failed")
        ):
            result = runner.invoke(main, ["fetch"])
            assert result.exit_code == 3
            assert "Authentication error" in result.output

    def test_network_error_exit_code(self, runner: CliRunner):
        """NetworkError should result in exit code 4."""
        from unittest import mock
        from gmail_assistant.core.exceptions import NetworkError

        with mock.patch(
            'gmail_assistant.core.config.AppConfig.load',
            side_effect=NetworkError("Network unavailable")
        ):
            result = runner.invoke(main, ["fetch"])
            assert result.exit_code == 4
            assert "Network error" in result.output

    def test_gmail_assistant_error_exit_code(self, runner: CliRunner):
        """GmailAssistantError should result in exit code 1."""
        from unittest import mock
        from gmail_assistant.core.exceptions import GmailAssistantError

        with mock.patch(
            'gmail_assistant.core.config.AppConfig.load',
            side_effect=GmailAssistantError("General error")
        ):
            result = runner.invoke(main, ["fetch"])
            assert result.exit_code == 1
            assert "Error" in result.output

    def test_unexpected_error_exit_code(self, runner: CliRunner):
        """Unexpected exceptions should result in exit code 1."""
        from unittest import mock

        with mock.patch(
            'gmail_assistant.core.config.AppConfig.load',
            side_effect=RuntimeError("Unexpected error")
        ):
            result = runner.invoke(main, ["fetch"])
            assert result.exit_code == 1
            assert "Unexpected error" in result.output

    def test_click_exception_reraise(self, runner: CliRunner):
        """Click exceptions should be re-raised, not caught."""
        # Click handles its own exceptions like missing required options
        result = runner.invoke(main, ["delete"])  # --query is required
        assert result.exit_code == 2  # Click usage error


class TestConfigCommandEdgeCases:
    """Test config command edge cases."""

    def test_config_init_already_exists(self, runner: CliRunner, temp_dir: Path):
        """config --init should fail if config already exists."""
        from unittest import mock
        from gmail_assistant.core.config import AppConfig

        config_dir = temp_dir / ".gmail-assistant"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        config_file.write_text('{"test": "config"}')

        with mock.patch.object(AppConfig, "default_dir", return_value=config_dir):
            result = runner.invoke(main, ["config", "--init"])
            assert result.exit_code == 5
            assert "already exists" in result.output

    def test_config_validate_invalid_config(self, runner: CliRunner, temp_dir: Path):
        """config --validate should detect invalid config."""
        from unittest import mock
        from gmail_assistant.core.exceptions import ConfigError

        with mock.patch(
            'gmail_assistant.core.config.AppConfig.load',
            side_effect=ConfigError("Invalid JSON")
        ):
            result = runner.invoke(main, ["config", "--validate"])
            assert result.exit_code == 5
            assert "invalid" in result.output.lower()

    def test_config_default_shows_help(self, runner: CliRunner):
        """config without flags should show help."""
        result = runner.invoke(main, ["config"])
        assert result.exit_code == 0
        # Should show help text with available options
        assert "--show" in result.output or "help" in result.output.lower() or "Usage" in result.output


class TestDeleteCommandEdgeCases:
    """Test delete command edge cases."""

    def test_delete_with_confirm_flag(self, runner: CliRunner):
        """delete --confirm should skip prompt."""
        result = runner.invoke(
            main, ["delete", "--query", "test@example.com", "--confirm"]
        )
        assert result.exit_code == 0

    def test_delete_with_all_options(self, runner: CliRunner):
        """delete with all options should work."""
        result = runner.invoke(
            main, [
                "delete",
                "--query", "is:unread",
                "--dry-run",
                "--confirm"
            ]
        )
        assert result.exit_code == 0
        assert "Dry run: True" in result.output


class TestAnalyzeCommandEdgeCases:
    """Test analyze command edge cases."""

    def test_analyze_with_input_dir(self, runner: CliRunner, temp_dir: Path):
        """analyze --input-dir should accept directory path."""
        # Create the input directory
        input_dir = temp_dir / "emails"
        input_dir.mkdir()

        result = runner.invoke(main, ["analyze", "--input-dir", str(input_dir)])
        assert result.exit_code == 0
        assert str(input_dir) in result.output

    def test_analyze_detailed_report(self, runner: CliRunner):
        """analyze --report detailed should work."""
        result = runner.invoke(main, ["analyze", "--report", "detailed"])
        assert result.exit_code == 0
        assert "detailed" in result.output


class TestFetchCommandEdgeCases:
    """Test fetch command edge cases."""

    def test_fetch_with_max_emails(self, runner: CliRunner):
        """fetch --max-emails should accept integer."""
        result = runner.invoke(main, ["fetch", "--max-emails", "500"])
        assert result.exit_code == 0
        assert "500" in result.output

    def test_fetch_with_output_dir(self, runner: CliRunner, temp_dir: Path):
        """fetch --output-dir should accept path."""
        output_dir = temp_dir / "backups"
        result = runner.invoke(main, ["fetch", "--output-dir", str(output_dir)])
        assert result.exit_code == 0
        assert str(output_dir) in result.output

    def test_fetch_with_eml_format(self, runner: CliRunner):
        """fetch --format eml should work."""
        result = runner.invoke(main, ["fetch", "--format", "eml"])
        assert result.exit_code == 0
        assert "eml" in result.output

    def test_fetch_with_all_options(self, runner: CliRunner, temp_dir: Path):
        """fetch with all options should work."""
        output_dir = temp_dir / "output"
        result = runner.invoke(
            main, [
                "fetch",
                "--query", "is:starred",
                "--max-emails", "100",
                "--output-dir", str(output_dir),
                "--format", "json"
            ]
        )
        assert result.exit_code == 0
        assert "is:starred" in result.output


class TestMainEntryPoint:
    """Test main entry point behavior."""

    def test_main_with_no_args(self, runner: CliRunner):
        """main with no args should show help or usage."""
        result = runner.invoke(main, [])
        # Either shows help (exit 0) or usage error
        assert result.exit_code in (0, 2)

    def test_main_with_unknown_command(self, runner: CliRunner):
        """main with unknown command should error."""
        result = runner.invoke(main, ["unknown_command"])
        assert result.exit_code == 2  # Click usage error

    def test_main_with_invalid_option(self, runner: CliRunner):
        """main with invalid option should error."""
        result = runner.invoke(main, ["--invalid-option"])
        assert result.exit_code == 2  # Click usage error
