"""
Tests for the Gmail Fetcher CLI module.

Tests argument parsing and command handling.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

# Add src to path for direct import
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli.main import create_parser, main
from src.cli import fetch, delete, analyze, config, auth


class TestArgumentParser:
    """Tests for CLI argument parsing."""

    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "gmail-fetcher"

    def test_parse_global_options(self):
        """Test parsing global options."""
        parser = create_parser()

        args = parser.parse_args(['--verbose', '--credentials', 'custom.json', 'fetch', '--query', 'test'])

        assert args.verbose is True
        assert args.credentials == 'custom.json'

    def test_parse_version(self):
        """Test version flag."""
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--version'])

        assert exc_info.value.code == 0


class TestFetchCommand:
    """Tests for fetch command."""

    def test_fetch_parser_setup(self):
        """Test fetch parser configuration."""
        parser = create_parser()

        args = parser.parse_args([
            'fetch',
            '--query', 'is:unread',
            '--max', '500',
            '--output', 'my_backup',
            '--format', 'markdown',
            '--organize', 'sender'
        ])

        assert args.command == 'fetch'
        assert args.query == 'is:unread'
        assert args.max == 500
        assert args.output == 'my_backup'
        assert args.format == 'markdown'
        assert args.organize == 'sender'

    def test_fetch_requires_query(self):
        """Test that fetch requires --query argument."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(['fetch'])

    def test_fetch_default_values(self):
        """Test fetch command default values."""
        parser = create_parser()

        args = parser.parse_args(['fetch', '--query', 'test'])

        assert args.max == 1000
        assert args.output == 'gmail_backup'
        assert args.format == 'both'
        assert args.organize == 'date'

    def test_fetch_auth_only_flag(self):
        """Test fetch --auth-only flag."""
        parser = create_parser()

        args = parser.parse_args(['fetch', '--query', 'test', '--auth-only'])

        assert args.auth_only is True


class TestDeleteCommand:
    """Tests for delete command."""

    def test_delete_unread_parser(self):
        """Test delete unread subcommand."""
        parser = create_parser()

        args = parser.parse_args(['delete', 'unread', '--execute', '--keep-recent', '7'])

        assert args.command == 'delete'
        assert args.delete_action == 'unread'
        assert args.execute is True
        assert args.keep_recent == 7

    def test_delete_query_parser(self):
        """Test delete query subcommand."""
        parser = create_parser()

        args = parser.parse_args([
            'delete', 'query',
            '--query', 'older_than:1y',
            '--max-delete', '100'
        ])

        assert args.delete_action == 'query'
        assert args.query == 'older_than:1y'
        assert args.max_delete == 100

    def test_delete_preset_parser(self):
        """Test delete preset subcommand."""
        parser = create_parser()

        args = parser.parse_args(['delete', 'preset', 'old'])

        assert args.delete_action == 'preset'
        assert args.preset_name == 'old'

    def test_delete_preset_choices(self):
        """Test delete preset valid choices."""
        parser = create_parser()

        # Valid presets
        for preset in ['old', 'large', 'newsletters', 'notifications']:
            args = parser.parse_args(['delete', 'preset', preset])
            assert args.preset_name == preset

        # Invalid preset
        with pytest.raises(SystemExit):
            parser.parse_args(['delete', 'preset', 'invalid'])


class TestAnalyzeCommand:
    """Tests for analyze command."""

    def test_analyze_parser(self):
        """Test analyze parser configuration."""
        parser = create_parser()

        args = parser.parse_args([
            'analyze',
            '--input', '/path/to/backup',
            '--output', 'results.json',
            '--days', '7'
        ])

        assert args.command == 'analyze'
        assert args.input == '/path/to/backup'
        assert args.output == 'results.json'
        assert args.days == 7

    def test_analyze_yesterday_flag(self):
        """Test analyze --yesterday flag."""
        parser = create_parser()

        args = parser.parse_args(['analyze', '--yesterday'])

        assert args.yesterday is True

    def test_analyze_default_values(self):
        """Test analyze command defaults."""
        parser = create_parser()

        args = parser.parse_args(['analyze'])

        assert args.input == 'gmail_backup'
        assert args.output == 'analysis_results.json'
        assert args.days == 1


class TestConfigCommand:
    """Tests for config command."""

    def test_config_show_parser(self):
        """Test config show subcommand."""
        parser = create_parser()

        args = parser.parse_args(['config', 'show', '--format', 'json'])

        assert args.command == 'config'
        assert args.config_action == 'show'
        assert args.format == 'json'

    def test_config_setup_parser(self):
        """Test config setup subcommand."""
        parser = create_parser()

        args = parser.parse_args(['config', 'setup', '--force'])

        assert args.config_action == 'setup'
        assert args.force is True

    def test_config_validate_parser(self):
        """Test config validate subcommand."""
        parser = create_parser()

        args = parser.parse_args(['config', 'validate'])

        assert args.config_action == 'validate'


class TestAuthCommand:
    """Tests for auth command."""

    def test_auth_test_parser(self):
        """Test auth test subcommand."""
        parser = create_parser()

        args = parser.parse_args(['auth', 'test'])

        assert args.command == 'auth'
        assert args.auth_action == 'test'

    def test_auth_refresh_parser(self):
        """Test auth refresh subcommand."""
        parser = create_parser()

        args = parser.parse_args(['auth', 'refresh'])

        assert args.auth_action == 'refresh'

    def test_auth_reset_parser(self):
        """Test auth reset subcommand."""
        parser = create_parser()

        args = parser.parse_args(['auth', 'reset', '--force'])

        assert args.auth_action == 'reset'
        assert args.force is True

    def test_auth_status_parser(self):
        """Test auth status subcommand."""
        parser = create_parser()

        args = parser.parse_args(['auth', 'status'])

        assert args.auth_action == 'status'


class TestMainFunction:
    """Tests for main CLI function."""

    def test_main_no_args_returns_error(self):
        """Test main with no args shows help and returns 1."""
        result = main([])
        assert result == 1

    @patch('src.cli.fetch.handle')
    def test_main_routes_to_fetch(self, mock_handle):
        """Test main routes to fetch handler."""
        mock_handle.return_value = 0

        result = main(['fetch', '--query', 'test'])

        mock_handle.assert_called_once()
        assert result == 0

    @patch('src.cli.config.handle')
    def test_main_routes_to_config(self, mock_handle):
        """Test main routes to config handler."""
        mock_handle.return_value = 0

        result = main(['config', 'show'])

        mock_handle.assert_called_once()
        assert result == 0

    def test_main_handles_keyboard_interrupt(self):
        """Test main handles KeyboardInterrupt gracefully."""
        with patch('src.cli.fetch.handle', side_effect=KeyboardInterrupt):
            result = main(['fetch', '--query', 'test'])
            assert result == 130

    def test_main_handles_exceptions(self):
        """Test main handles exceptions and returns error code."""
        with patch('src.cli.fetch.handle', side_effect=Exception("Test error")):
            result = main(['fetch', '--query', 'test'])
            assert result == 1


class TestPresetQueries:
    """Tests for delete preset queries."""

    def test_preset_queries_defined(self):
        """Test all preset queries are defined."""
        from src.cli.delete import PRESET_QUERIES

        assert 'old' in PRESET_QUERIES
        assert 'large' in PRESET_QUERIES
        assert 'newsletters' in PRESET_QUERIES
        assert 'notifications' in PRESET_QUERIES

    def test_preset_queries_are_valid(self):
        """Test preset queries are valid Gmail queries."""
        from src.cli.delete import PRESET_QUERIES

        for name, query in PRESET_QUERIES.items():
            assert isinstance(query, str)
            assert len(query) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
