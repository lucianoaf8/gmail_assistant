"""
Integration tests for CLI workflows.
Tests end-to-end CLI command execution with mocked Gmail API.
"""

import json
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner


class TestCLIFetchWorkflow:
    """Integration tests for fetch workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.commands.fetch.GmailFetcher')
    @mock.patch('gmail_assistant.cli.commands.fetch.CheckpointManager')
    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_fetch_workflow_end_to_end(
        self, mock_config, mock_checkpoint_class, mock_fetcher_class, runner, integration_temp_dir
    ):
        """Test complete fetch workflow from CLI to file creation."""
        from gmail_assistant.cli.main import main

        # Setup config mock
        mock_cfg = mock.MagicMock()
        mock_cfg.max_emails = 100
        mock_cfg.output_dir = str(integration_temp_dir / "output")
        mock_cfg.credentials_path = integration_temp_dir / "creds.json"
        mock_config.load.return_value = mock_cfg

        # Setup fetcher mock
        mock_fetcher = mock.MagicMock()
        mock_fetcher.authenticate.return_value = True
        mock_fetcher.search_messages.return_value = ['msg1', 'msg2', 'msg3']
        mock_fetcher.get_message_details.return_value = {
            'id': 'msg1',
            'subject': 'Test Subject',
            'sender': 'test@example.com',
            'body': 'Test body'
        }
        mock_fetcher_class.return_value = mock_fetcher

        # Setup checkpoint mock
        mock_checkpoint = mock.MagicMock()
        mock_checkpoint.total_messages = 0
        mock_checkpoint_mgr = mock.MagicMock()
        mock_checkpoint_mgr.get_latest_checkpoint.return_value = None
        mock_checkpoint_mgr.create_checkpoint.return_value = mock_checkpoint
        mock_checkpoint_class.return_value = mock_checkpoint_mgr

        # Run fetch command
        result = runner.invoke(main, [
            'fetch',
            '--query', 'is:unread',
            '--max-emails', '10',
            '--format', 'json'
        ])

        assert result.exit_code == 0
        assert 'Fetching emails' in result.output
        assert 'Fetched' in result.output
        mock_fetcher.authenticate.assert_called_once()

    @mock.patch('gmail_assistant.cli.commands.fetch.GmailFetcher')
    @mock.patch('gmail_assistant.cli.commands.fetch.CheckpointManager')
    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_fetch_creates_files(
        self, mock_config, mock_checkpoint_class, mock_fetcher_class, runner, integration_temp_dir
    ):
        """Test fetch actually creates email files."""
        from gmail_assistant.cli.main import main

        output_dir = integration_temp_dir / "emails"

        mock_cfg = mock.MagicMock()
        mock_cfg.max_emails = 100
        mock_cfg.output_dir = str(output_dir)
        mock_cfg.credentials_path = integration_temp_dir / "creds.json"
        mock_config.load.return_value = mock_cfg

        mock_fetcher = mock.MagicMock()
        mock_fetcher.authenticate.return_value = True
        mock_fetcher.search_messages.return_value = ['msg1', 'msg2']
        mock_fetcher.get_message_details.side_effect = [
            {'id': 'msg1', 'subject': 'Email 1', 'sender': 'a@test.com'},
            {'id': 'msg2', 'subject': 'Email 2', 'sender': 'b@test.com'}
        ]
        mock_fetcher_class.return_value = mock_fetcher

        mock_checkpoint = mock.MagicMock()
        mock_checkpoint.total_messages = 0
        mock_checkpoint_mgr = mock.MagicMock()
        mock_checkpoint_mgr.get_latest_checkpoint.return_value = None
        mock_checkpoint_mgr.create_checkpoint.return_value = mock_checkpoint
        mock_checkpoint_class.return_value = mock_checkpoint_mgr

        result = runner.invoke(main, [
            'fetch',
            '--query', 'test',
            '--output-dir', str(output_dir)
        ])

        assert result.exit_code == 0
        assert output_dir.exists()
        # Files should be created
        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) == 2


class TestCLIAnalyzeWorkflow:
    """Integration tests for analyze workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_analyze_workflow_with_sample_files(
        self, mock_config, runner, sample_email_files
    ):
        """Test complete analyze workflow with sample files."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.output_dir = str(sample_email_files)
        mock_config.load.return_value = mock_cfg

        result = runner.invoke(main, [
            'analyze',
            '--input-dir', str(sample_email_files),
            '--report', 'summary'
        ])

        assert result.exit_code == 0
        assert 'SUMMARY' in result.output
        assert 'files' in result.output.lower()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_analyze_json_output(
        self, mock_config, runner, sample_email_files, integration_temp_dir
    ):
        """Test analyze with JSON output file."""
        from gmail_assistant.cli.main import main

        output_file = integration_temp_dir / "report.json"

        mock_cfg = mock.MagicMock()
        mock_cfg.output_dir = str(sample_email_files)
        mock_config.load.return_value = mock_cfg

        result = runner.invoke(main, [
            'analyze',
            '--input-dir', str(sample_email_files),
            '--report', 'json',
            '--output', str(output_file)
        ])

        assert result.exit_code == 0
        assert output_file.exists()

        with open(output_file) as f:
            report = json.load(f)

        assert 'metadata' in report
        assert 'file_statistics' in report

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_analyze_sender_analysis(
        self, mock_config, runner, sample_email_files
    ):
        """Test analyze extracts sender information."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.output_dir = str(sample_email_files)
        mock_config.load.return_value = mock_cfg

        result = runner.invoke(main, [
            'analyze',
            '--input-dir', str(sample_email_files),
            '--report', 'detailed'
        ])

        assert result.exit_code == 0
        assert 'sender' in result.output.lower()


class TestCLIDeleteWorkflow:
    """Integration tests for delete workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_delete_dry_run_workflow(
        self, mock_config, mock_client_class, runner, integration_temp_dir
    ):
        """Test delete dry run shows preview."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = integration_temp_dir / "creds.json"
        mock_config.load.return_value = mock_cfg

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}]
        }
        mock_service.users().messages().get().execute.return_value = {
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Spam Email'},
                    {'name': 'From', 'value': 'spam@example.com'}
                ]
            }
        }

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client_class.return_value = mock_client

        result = runner.invoke(main, [
            'delete',
            '--query', 'from:spam@example.com',
            '--dry-run'
        ])

        assert result.exit_code == 0
        assert 'dry run' in result.output.lower() or 'would be' in result.output.lower()

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    @mock.patch('gmail_assistant.cli.main.get_email_count')
    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_delete_confirm_workflow(
        self, mock_config, mock_count, mock_client_class, runner, integration_temp_dir
    ):
        """Test delete with confirmation."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = integration_temp_dir / "creds.json"
        mock_config.load.return_value = mock_cfg
        mock_count.return_value = 5

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}]
        }

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client.trash_emails.return_value = {'trashed': 2, 'failed': 0}
        mock_client_class.return_value = mock_client

        result = runner.invoke(main, [
            'delete',
            '--query', 'from:spam@example.com',
            '--confirm'
        ], input='y\n')

        # Should execute deletion
        mock_client.trash_emails.assert_called_once()


class TestCLIAuthWorkflow:
    """Integration tests for auth workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_auth_status_check(
        self, mock_config, mock_manager_class, runner, integration_temp_dir
    ):
        """Test auth status check workflow."""
        from gmail_assistant.cli.main import main

        creds_path = integration_temp_dir / "credentials.json"
        creds_path.write_text('{}')

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = creds_path
        mock_config.load.return_value = mock_cfg

        mock_creds = mock.MagicMock()
        mock_creds.valid = True
        mock_manager = mock.MagicMock()
        mock_manager._load_credentials_securely.return_value = mock_creds
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(main, ['auth', '--status'])

        assert result.exit_code == 0
        assert 'Authenticated' in result.output or 'Status' in result.output

    @mock.patch('gmail_assistant.cli.commands.auth.SecureCredentialManager')
    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_auth_revoke_workflow(
        self, mock_config, mock_manager_class, runner, integration_temp_dir
    ):
        """Test auth revoke workflow."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = integration_temp_dir / "creds.json"
        mock_config.load.return_value = mock_cfg

        mock_manager = mock.MagicMock()
        mock_manager.reset_credentials.return_value = True
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(main, ['auth', '--revoke'])

        assert result.exit_code == 0
        assert 'revoked' in result.output.lower()
        mock_manager.reset_credentials.assert_called_once()


class TestCLIConfigWorkflow:
    """Integration tests for config workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_config_show_workflow(
        self, mock_config, runner, integration_temp_dir
    ):
        """Test config show workflow."""
        from gmail_assistant.cli.main import main

        mock_cfg = mock.MagicMock()
        mock_cfg.credentials_path = integration_temp_dir / "creds.json"
        mock_cfg.token_path = integration_temp_dir / "token.json"
        mock_cfg.output_dir = str(integration_temp_dir / "output")
        mock_cfg.max_emails = 1000
        mock_cfg.rate_limit_per_second = 10
        mock_cfg.log_level = "INFO"
        mock_config.load.return_value = mock_cfg

        result = runner.invoke(main, ['config', '--show'])

        assert result.exit_code == 0
        assert 'credentials_path' in result.output
        assert 'max_emails' in result.output

    def test_config_init_workflow(self, runner, integration_temp_dir, monkeypatch):
        """Test config init creates default config."""
        from gmail_assistant.cli.main import main, AppConfig

        monkeypatch.setattr(AppConfig, 'default_dir', lambda: integration_temp_dir)

        result = runner.invoke(main, ['config', '--init'])

        assert result.exit_code == 0
        config_file = integration_temp_dir / "config.json"
        assert config_file.exists()

        with open(config_file) as f:
            config = json.load(f)

        assert 'credentials_path' in config
        assert 'max_emails' in config


class TestCLIErrorHandling:
    """Integration tests for CLI error handling."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_network_error_handling(self, mock_config, runner, integration_temp_dir):
        """Test CLI handles network errors gracefully."""
        from gmail_assistant.cli.main import main
        from gmail_assistant.core.exceptions import NetworkError

        mock_config.load.side_effect = NetworkError("Connection refused")

        result = runner.invoke(main, ['fetch', '--query', 'test'])

        assert result.exit_code == 4  # Network error code
        assert 'Network error' in result.output or 'error' in result.output.lower()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_auth_error_handling(self, mock_config, runner, integration_temp_dir):
        """Test CLI handles auth errors gracefully."""
        from gmail_assistant.cli.main import main
        from gmail_assistant.core.exceptions import AuthError

        mock_config.load.side_effect = AuthError("Invalid credentials")

        result = runner.invoke(main, ['fetch', '--query', 'test'])

        assert result.exit_code == 3  # Auth error code
        assert 'Authentication error' in result.output or 'error' in result.output.lower()

    @mock.patch('gmail_assistant.cli.main.AppConfig')
    def test_config_error_handling(self, mock_config, runner):
        """Test CLI handles config errors gracefully."""
        from gmail_assistant.cli.main import main
        from gmail_assistant.core.exceptions import ConfigError

        mock_config.load.side_effect = ConfigError("Invalid configuration")

        result = runner.invoke(main, ['config', '--validate'])

        assert result.exit_code == 5  # Config error code
