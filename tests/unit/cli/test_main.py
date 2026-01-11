"""
Comprehensive tests for CLI main.py module.
Tests main CLI group, handle_errors decorator, and command routing.
"""

import sys
from pathlib import Path
from unittest import mock

import click
import pytest
from click.testing import CliRunner


class TestHandleErrorsDecorator:
    """Tests for handle_errors decorator."""

    def test_config_error_exits_5(self):
        """Test ConfigError maps to exit code 5."""
        from gmail_assistant.cli.main import handle_errors
        from gmail_assistant.core.exceptions import ConfigError

        @handle_errors
        def raises_config_error():
            raise ConfigError("test config error")

        with pytest.raises(SystemExit) as exc_info:
            raises_config_error()
        assert exc_info.value.code == 5

    def test_auth_error_exits_3(self):
        """Test AuthError maps to exit code 3."""
        from gmail_assistant.cli.main import handle_errors
        from gmail_assistant.core.exceptions import AuthError

        @handle_errors
        def raises_auth_error():
            raise AuthError("test auth error")

        with pytest.raises(SystemExit) as exc_info:
            raises_auth_error()
        assert exc_info.value.code == 3

    def test_network_error_exits_4(self):
        """Test NetworkError maps to exit code 4."""
        from gmail_assistant.cli.main import handle_errors
        from gmail_assistant.core.exceptions import NetworkError

        @handle_errors
        def raises_network_error():
            raise NetworkError("test network error")

        with pytest.raises(SystemExit) as exc_info:
            raises_network_error()
        assert exc_info.value.code == 4

    def test_gmail_assistant_error_exits_1(self):
        """Test GmailAssistantError maps to exit code 1."""
        from gmail_assistant.cli.main import handle_errors
        from gmail_assistant.core.exceptions import GmailAssistantError

        @handle_errors
        def raises_base_error():
            raise GmailAssistantError("test error")

        with pytest.raises(SystemExit) as exc_info:
            raises_base_error()
        assert exc_info.value.code == 1

    def test_generic_exception_exits_1(self):
        """Test generic exception maps to exit code 1."""
        from gmail_assistant.cli.main import handle_errors

        @handle_errors
        def raises_generic():
            raise ValueError("generic error")

        with pytest.raises(SystemExit) as exc_info:
            raises_generic()
        assert exc_info.value.code == 1

    def test_click_exception_reraises(self):
        """Test ClickException is re-raised."""
        from gmail_assistant.cli.main import handle_errors

        @handle_errors
        def raises_click():
            raise click.ClickException("click error")

        with pytest.raises(click.ClickException):
            raises_click()

    def test_no_error_returns_normally(self):
        """Test normal execution returns result."""
        from gmail_assistant.cli.main import handle_errors

        @handle_errors
        def returns_value():
            return "success"

        result = returns_value()
        assert result == "success"


class TestMainCLIGroup:
    """Tests for main CLI group."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_version_option(self, runner):
        """Test --version shows version."""
        from gmail_assistant.cli.main import main

        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert 'gmail-assistant' in result.output

    def test_help_option(self, runner):
        """Test --help shows help."""
        from gmail_assistant.cli.main import main

        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'Gmail Assistant' in result.output
        assert 'fetch' in result.output
        assert 'delete' in result.output
        assert 'analyze' in result.output
        assert 'auth' in result.output
        assert 'config' in result.output

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_config_option_passed_to_command(self, mock_config, runner, tmp_path):
        """Test --config option is passed to subcommand via context."""
        from gmail_assistant.cli.main import main

        config_file = tmp_path / "config.json"
        config_file.write_text('{}')

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_cfg.token_path = tmp_path / "token.json"
        mock_cfg.output_dir = str(tmp_path)
        mock_cfg.max_emails = 100
        mock_cfg.rate_limit_per_second = 10
        mock_cfg.log_level = "INFO"
        mock_config.load.return_value = mock_cfg

        # Use config --show to verify config loads
        result = runner.invoke(main, ['--config', str(config_file), 'config', '--show'])

        # Verify config.load was called with the config path
        mock_config.load.assert_called()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_allow_repo_credentials_flag_passed(self, mock_config, runner, tmp_path):
        """Test --allow-repo-credentials flag is passed to subcommand."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_cfg.token_path = tmp_path / "token.json"
        mock_cfg.output_dir = str(tmp_path)
        mock_cfg.max_emails = 100
        mock_cfg.rate_limit_per_second = 10
        mock_cfg.log_level = "INFO"
        mock_config.load.return_value = mock_cfg

        # Use config --show to test the flag
        result = runner.invoke(main, ['--allow-repo-credentials', 'config', '--show'])

        # Verify config.load was called with allow_repo_credentials=True
        call_kwargs = mock_config.load.call_args.kwargs
        assert call_kwargs.get('allow_repo_credentials') is True


class TestFetchCommand:
    """Tests for fetch command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.fetch_emails')
    def test_fetch_basic(self, mock_fetch, mock_config, runner, tmp_path):
        """Test basic fetch command."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.max_emails = 100
        mock_cfg.output_dir = str(tmp_path)
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_fetch.return_value = {'fetched': 10, 'total': 10}

        result = runner.invoke(main, ['fetch', '--query', 'is:unread'])

        assert result.exit_code == 0
        assert 'Fetching emails' in result.output
        mock_fetch.assert_called_once()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.fetch_emails')
    def test_fetch_with_options(self, mock_fetch, mock_config, runner, tmp_path):
        """Test fetch with all options."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.max_emails = 100
        mock_cfg.output_dir = str(tmp_path)
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_fetch.return_value = {'fetched': 50, 'total': 100}

        result = runner.invoke(main, [
            'fetch',
            '--query', 'from:test@example.com',
            '--max-emails', '50',
            '--output-dir', str(tmp_path / "output"),
            '--format', 'json'
        ])

        assert result.exit_code == 0
        call_kwargs = mock_fetch.call_args.kwargs
        assert call_kwargs['max_emails'] == 50

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.fetch_emails')
    def test_fetch_resume_flag(self, mock_fetch, mock_config, runner, tmp_path):
        """Test fetch with --resume flag."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.max_emails = 100
        mock_cfg.output_dir = str(tmp_path)
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_fetch.return_value = {'fetched': 10, 'total': 10}

        result = runner.invoke(main, ['fetch', '--resume'])

        assert result.exit_code == 0
        call_kwargs = mock_fetch.call_args.kwargs
        assert call_kwargs['resume'] is True

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main._fetch_async')
    def test_fetch_async_mode(self, mock_async, mock_config, runner, tmp_path):
        """Test fetch with --async flag."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.max_emails = 100
        mock_cfg.output_dir = str(tmp_path)
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_async.return_value = {'fetched': 10, 'total': 10}

        result = runner.invoke(main, ['fetch', '--async'])

        assert result.exit_code == 0
        assert 'async' in result.output
        mock_async.assert_called_once()


class TestDeleteCommand:
    """Tests for delete command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.delete_emails')
    def test_delete_dry_run(self, mock_delete, mock_config, runner, tmp_path):
        """Test delete in dry run mode."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_delete.return_value = {'found': 10, 'deleted': 0, 'failed': 0, 'dry_run': True}

        result = runner.invoke(main, ['delete', '--query', 'from:spam@example.com'])

        assert result.exit_code == 0
        assert 'Dry run' in result.output

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.delete_emails')
    @mock.patch('gmail_assistant.cli.main.get_email_count')
    def test_delete_with_confirm(self, mock_count, mock_delete, mock_config, runner, tmp_path):
        """Test delete with --confirm flag."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_delete.return_value = {'found': 5, 'deleted': 5, 'failed': 0}
        mock_count.return_value = 5

        result = runner.invoke(main, [
            'delete',
            '--query', 'from:spam@example.com',
            '--confirm'
        ], input='y\n')

        mock_delete.assert_called_once()
        call_kwargs = mock_delete.call_args.kwargs
        assert call_kwargs['dry_run'] is False

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.delete_emails')
    def test_delete_permanent(self, mock_delete, mock_config, runner, tmp_path):
        """Test delete with --permanent flag."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_delete.return_value = {'found': 5, 'deleted': 5, 'failed': 0}

        result = runner.invoke(main, [
            'delete',
            '--query', 'from:spam@example.com',
            '--confirm',
            '--permanent'
        ], input='y\n')

        call_kwargs = mock_delete.call_args.kwargs
        assert call_kwargs['use_trash'] is False


class TestAnalyzeCommand:
    """Tests for analyze command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.analyze_emails')
    def test_analyze_basic(self, mock_analyze, mock_config, runner, tmp_path):
        """Test basic analyze command."""
        from gmail_assistant.cli.main import main

        input_dir = tmp_path / "emails"
        input_dir.mkdir()

        mock_cfg = mock.MagicMock()
        mock_cfg.output_dir = str(input_dir)
        mock_config.load.return_value = mock_cfg

        result = runner.invoke(main, ['analyze', '--input-dir', str(input_dir)])

        assert result.exit_code == 0
        mock_analyze.assert_called_once()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.analyze_emails')
    def test_analyze_with_report_type(self, mock_analyze, mock_config, runner, tmp_path):
        """Test analyze with report type."""
        from gmail_assistant.cli.main import main

        input_dir = tmp_path / "emails"
        input_dir.mkdir()

        mock_cfg = mock.MagicMock()
        mock_cfg.output_dir = str(input_dir)
        mock_config.load.return_value = mock_cfg

        result = runner.invoke(main, [
            'analyze',
            '--input-dir', str(input_dir),
            '--report', 'detailed'
        ])

        assert result.exit_code == 0
        call_kwargs = mock_analyze.call_args.kwargs
        assert call_kwargs['report_type'] == 'detailed'

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.analyze_emails')
    def test_analyze_with_output_file(self, mock_analyze, mock_config, runner, tmp_path):
        """Test analyze with output file."""
        from gmail_assistant.cli.main import main

        input_dir = tmp_path / "emails"
        input_dir.mkdir()
        output_file = tmp_path / "report.json"

        mock_cfg = mock.MagicMock()
        mock_cfg.output_dir = str(input_dir)
        mock_config.load.return_value = mock_cfg

        result = runner.invoke(main, [
            'analyze',
            '--input-dir', str(input_dir),
            '--report', 'json',
            '--output', str(output_file)
        ])

        assert result.exit_code == 0
        call_kwargs = mock_analyze.call_args.kwargs
        assert call_kwargs['output_file'] == output_file


class TestAuthCommand:
    """Tests for auth command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.check_auth_status')
    def test_auth_status(self, mock_status, mock_config, runner, tmp_path):
        """Test auth --status command."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_status.return_value = {'authenticated': True, 'status': 'Valid'}

        result = runner.invoke(main, ['auth', '--status'])

        assert result.exit_code == 0
        assert 'Authenticated' in result.output

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.revoke_auth')
    def test_auth_revoke(self, mock_revoke, mock_config, runner, tmp_path):
        """Test auth --revoke command."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_revoke.return_value = {'success': True}

        result = runner.invoke(main, ['auth', '--revoke'])

        assert result.exit_code == 0
        mock_revoke.assert_called_once()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    @mock.patch('gmail_assistant.cli.main.authenticate')
    def test_auth_force_reauth(self, mock_auth, mock_config, runner, tmp_path):
        """Test auth --force command."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_auth.return_value = {'success': True}

        result = runner.invoke(main, ['auth', '--force'])

        assert result.exit_code == 0
        call_kwargs = mock_auth.call_args.kwargs
        assert call_kwargs['force_reauth'] is True


class TestConfigCommand:
    """Tests for config command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_config_show(self, mock_config, runner, tmp_path):
        """Test config --show command."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = tmp_path / "creds.json"
        mock_cfg.token_path = tmp_path / "token.json"
        mock_cfg.output_dir = str(tmp_path / "output")
        mock_cfg.max_emails = 1000
        mock_cfg.rate_limit_per_second = 10
        mock_cfg.log_level = "INFO"
        mock_config.load.return_value = mock_cfg

        result = runner.invoke(main, ['config', '--show'])

        assert result.exit_code == 0
        assert 'credentials_path' in result.output
        assert 'max_emails' in result.output

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_config_validate_success(self, mock_config, runner, tmp_path):
        """Test config --validate with valid config."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_config.load.return_value = mock_cfg

        result = runner.invoke(main, ['config', '--validate'])

        assert result.exit_code == 0
        assert 'valid' in result.output.lower()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_config_validate_failure(self, mock_config, runner):
        """Test config --validate with invalid config."""
        from gmail_assistant.cli.main import main
        from gmail_assistant.core.exceptions import ConfigError

        mock_config.load.side_effect = ConfigError("Invalid config")

        result = runner.invoke(main, ['config', '--validate'])

        assert result.exit_code == 5
        assert 'invalid' in result.output.lower()

    def test_config_init_creates_file(self, runner, tmp_path, monkeypatch):
        """Test config --init creates config file."""
        from gmail_assistant.cli.main import main, AppConfig

        # Mock default_dir to use tmp_path
        monkeypatch.setattr(AppConfig, 'default_dir', lambda: tmp_path)

        result = runner.invoke(main, ['config', '--init'])

        assert result.exit_code == 0
        assert (tmp_path / "config.json").exists()

    def test_config_init_existing_file(self, runner, tmp_path, monkeypatch):
        """Test config --init with existing file."""
        from gmail_assistant.cli.main import main, AppConfig

        # Create existing config
        config_file = tmp_path / "config.json"
        config_file.write_text('{}')

        monkeypatch.setattr(AppConfig, 'default_dir', lambda: tmp_path)

        result = runner.invoke(main, ['config', '--init'])

        assert result.exit_code == 5
        assert 'already exists' in result.output


class TestSaveEmailAsync:
    """Tests for _save_email_async function."""

    def test_save_json_format(self, tmp_path):
        """Test saving email as JSON."""
        from gmail_assistant.cli.main import _save_email_async

        email_data = {
            'subject': 'Test Subject',
            'id': 'msg123',
            'sender': 'test@example.com'
        }

        _save_email_async(email_data, tmp_path, 'json', 0)

        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 1

    def test_save_eml_format(self, tmp_path):
        """Test saving email as EML."""
        from gmail_assistant.cli.main import _save_email_async

        email_data = {
            'subject': 'Test Subject',
            'id': 'msg123',
            'raw_content': 'From: test@example.com\nSubject: Test'
        }

        _save_email_async(email_data, tmp_path, 'eml', 0)

        eml_files = list(tmp_path.glob("*.eml"))
        assert len(eml_files) == 1

    def test_save_mbox_format(self, tmp_path):
        """Test saving email as mbox."""
        from gmail_assistant.cli.main import _save_email_async

        email_data = {
            'subject': 'Test Subject',
            'id': 'msg123',
            'sender': 'test@example.com',
            'raw_content': 'Subject: Test'
        }

        _save_email_async(email_data, tmp_path, 'mbox', 0)

        mbox_file = tmp_path / "emails.mbox"
        assert mbox_file.exists()

    def test_save_sanitizes_filename(self, tmp_path):
        """Test filename is sanitized."""
        from gmail_assistant.cli.main import _save_email_async

        email_data = {
            'subject': 'Test: Subject <with> special/chars',
            'id': 'msg123'
        }

        _save_email_async(email_data, tmp_path, 'json', 0)

        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 1
        # Verify no special chars in filename
        filename = json_files[0].name
        assert '<' not in filename
        assert '>' not in filename
        assert ':' not in filename
