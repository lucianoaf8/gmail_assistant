"""Comprehensive tests for deletion setup module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gmail_assistant.deletion.setup import (
    check_dependencies,
    check_credentials,
    test_gmail_connection,
    analyze_current_state,
    create_deletion_plan,
    main
)


class TestCheckDependencies:
    """Test dependency checking."""

    def test_check_dependencies_all_installed(self):
        """Test when all dependencies are installed."""
        with patch('builtins.__import__') as mock_import:
            mock_import.return_value = MagicMock()

            result = check_dependencies()

            assert result is True

    def test_check_dependencies_missing(self):
        """Test when dependencies are missing."""
        def import_side_effect(name, *args, **kwargs):
            if 'pandas' in name:
                raise ImportError("pandas not found")
            return MagicMock()

        with patch('builtins.__import__', side_effect=import_side_effect):
            result = check_dependencies()

            assert result is False

    def test_check_dependencies_mixed(self):
        """Test when some dependencies are missing."""
        required_packages = ['google-auth', 'pandas', 'pyarrow']
        missing = ['pyarrow']

        def import_side_effect(name, *args, **kwargs):
            if any(pkg.replace('-', '_') in name for pkg in missing):
                raise ImportError(f"{name} not found")
            return MagicMock()

        with patch('builtins.__import__', side_effect=import_side_effect):
            result = check_dependencies()

            assert result is False


class TestCheckCredentials:
    """Test credential file checking."""

    def test_check_credentials_both_exist(self, tmp_path, monkeypatch):
        """Test when both credentials.json and token.json exist."""
        # Create temporary credential files
        creds_file = tmp_path / "credentials.json"
        token_file = tmp_path / "token.json"
        creds_file.write_text('{"installed":{}}')
        token_file.write_text('{"token":"abc"}')

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        result = check_credentials()

        assert result is True

    def test_check_credentials_only_credentials(self, tmp_path, monkeypatch):
        """Test when only credentials.json exists."""
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"installed":{}}')

        monkeypatch.chdir(tmp_path)

        result = check_credentials()

        assert result is True

    def test_check_credentials_missing(self, tmp_path, monkeypatch):
        """Test when credentials.json is missing."""
        monkeypatch.chdir(tmp_path)

        result = check_credentials()

        assert result is False


class TestGmailConnection:
    """Test Gmail API connection testing."""

    def test_test_gmail_connection_success(self):
        """Test successful Gmail connection."""
        with patch('gmail_assistant.deletion.deleter.GmailDeleter') as mock_deleter:
            deleter_instance = MagicMock()
            deleter_instance.get_email_count.side_effect = [50, 500]  # unread, total
            mock_deleter.return_value = deleter_instance

            success, stats = test_gmail_connection()

            assert success is True
            assert stats['unread'] == 50
            assert stats['total'] == 500

    def test_test_gmail_connection_failure(self):
        """Test Gmail connection failure."""
        with patch('gmail_assistant.deletion.deleter.GmailDeleter') as mock_deleter:
            mock_deleter.side_effect = Exception("Connection failed")

            success, stats = test_gmail_connection()

            assert success is False
            assert stats == {}

    def test_test_gmail_connection_auth_error(self):
        """Test Gmail connection with authentication error."""
        with patch('gmail_assistant.deletion.deleter.GmailDeleter') as mock_deleter:
            deleter_instance = MagicMock()
            deleter_instance.get_email_count.side_effect = RuntimeError("Auth failed")
            mock_deleter.return_value = deleter_instance

            success, stats = test_gmail_connection()

            assert success is False


class TestAnalyzeCurrentState:
    """Test Gmail state analysis."""

    def test_analyze_current_state_success(self):
        """Test successful state analysis."""
        with patch('gmail_assistant.deletion.deleter.GmailDeleter') as mock_deleter:
            deleter_instance = MagicMock()

            # Mock email counts for different categories
            count_map = {
                '': 1000,  # Total
                'is:unread': 150,
                'older_than:1y': 300,
                'larger:10M': 50,
                'payment OR invoice OR bill OR receipt OR bank': 100,
                'notification OR alert OR backup OR report': 200,
                'unsubscribe OR newsletter OR marketing': 250,
                'social OR friend OR follow': 75,
                'has:attachment': 400,
            }

            deleter_instance.get_email_count.side_effect = lambda q: count_map.get(q, 0)
            mock_deleter.return_value = deleter_instance

            results = analyze_current_state()

            assert results['Total emails'] == 1000
            assert results['Unread emails'] == 150
            assert results['Old emails (>1 year)'] == 300
            assert results['Large emails (>10MB)'] == 50

    def test_analyze_current_state_with_opportunities(self):
        """Test state analysis with deletion opportunities."""
        with patch('gmail_assistant.deletion.deleter.GmailDeleter') as mock_deleter:
            deleter_instance = MagicMock()

            count_map = {
                '': 1000,
                'is:unread': 150,
                'is:unread older_than:30d': 80,
                'is:unread larger:1M': 20,
                'is:unread (notification OR alert OR backup)': 50,
            }

            deleter_instance.get_email_count.side_effect = lambda q: count_map.get(q, 0)
            mock_deleter.return_value = deleter_instance

            results = analyze_current_state()

            assert results['Unread emails'] == 150
            # Verify opportunities were identified (printed to console)

    def test_analyze_current_state_no_unread(self):
        """Test state analysis with no unread emails."""
        with patch('gmail_assistant.deletion.deleter.GmailDeleter') as mock_deleter:
            deleter_instance = MagicMock()
            deleter_instance.get_email_count.return_value = 0

            results = analyze_current_state()

            # Should complete without errors
            assert results is not None

    def test_analyze_current_state_error(self):
        """Test state analysis with error."""
        with patch('gmail_assistant.deletion.deleter.GmailDeleter') as mock_deleter:
            mock_deleter.side_effect = Exception("Analysis failed")

            results = analyze_current_state()

            assert results == {}


class TestCreateDeletionPlan:
    """Test deletion plan creation."""

    def test_create_deletion_plan_with_unread(self):
        """Test plan creation with unread emails."""
        email_stats = {
            'Total emails': 1000,
            'Unread emails': 500
        }

        # Should not raise any errors
        create_deletion_plan(email_stats)

    def test_create_deletion_plan_no_unread(self):
        """Test plan creation with no unread emails."""
        email_stats = {
            'Total emails': 1000,
            'Unread emails': 0
        }

        # Should not raise any errors
        create_deletion_plan(email_stats)

    def test_create_deletion_plan_empty_stats(self):
        """Test plan creation with empty stats."""
        email_stats = {}

        # Should handle gracefully
        create_deletion_plan(email_stats)


class TestMainWorkflow:
    """Test main setup workflow."""

    def test_main_success_workflow(self):
        """Test successful main workflow."""
        with patch('gmail_assistant.deletion.setup.check_dependencies', return_value=True), \
             patch('gmail_assistant.deletion.setup.check_credentials', return_value=True), \
             patch('gmail_assistant.deletion.setup.test_gmail_connection', return_value=(True, {'total': 1000, 'unread': 150})), \
             patch('gmail_assistant.deletion.setup.analyze_current_state', return_value={'Total emails': 1000, 'Unread emails': 150}), \
             patch('gmail_assistant.deletion.setup.create_deletion_plan'):

            # Should complete without errors
            main()

    def test_main_missing_dependencies(self):
        """Test main workflow with missing dependencies."""
        with patch('gmail_assistant.deletion.setup.check_dependencies', return_value=False):
            # Should exit early
            main()

    def test_main_missing_credentials(self):
        """Test main workflow with missing credentials."""
        with patch('gmail_assistant.deletion.setup.check_dependencies', return_value=True), \
             patch('gmail_assistant.deletion.setup.check_credentials', return_value=False):

            # Should exit early
            main()

    def test_main_connection_failure(self):
        """Test main workflow with connection failure."""
        with patch('gmail_assistant.deletion.setup.check_dependencies', return_value=True), \
             patch('gmail_assistant.deletion.setup.check_credentials', return_value=True), \
             patch('gmail_assistant.deletion.setup.test_gmail_connection', return_value=(False, {})):

            # Should exit early
            main()

    def test_main_analysis_failure(self):
        """Test main workflow with analysis failure."""
        with patch('gmail_assistant.deletion.setup.check_dependencies', return_value=True), \
             patch('gmail_assistant.deletion.setup.check_credentials', return_value=True), \
             patch('gmail_assistant.deletion.setup.test_gmail_connection', return_value=(True, {'total': 1000, 'unread': 150})), \
             patch('gmail_assistant.deletion.setup.analyze_current_state', return_value={}):

            # Should still complete
            main()


class TestIntegration:
    """Integration tests for setup module."""

    def test_full_setup_validation(self):
        """Test complete setup validation flow."""
        with patch('gmail_assistant.deletion.deleter.GmailDeleter') as mock_deleter, \
             patch('gmail_assistant.deletion.setup.check_dependencies') as mock_check_deps, \
             patch('gmail_assistant.deletion.setup.check_credentials') as mock_check_creds:

            # Mock all checks pass
            mock_check_deps.return_value = True
            mock_check_creds.return_value = True

            # Mock Gmail connection
            deleter_instance = MagicMock()
            deleter_instance.get_email_count.return_value = 100
            mock_deleter.return_value = deleter_instance

            # Run connection check (this is what we're really testing)
            conn_ok, stats = test_gmail_connection()

            assert conn_ok is True
            assert stats.get('total') == 100

    def test_setup_with_real_file_system(self, tmp_path):
        """Test setup with real file system operations."""
        import os

        # Create credentials file
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"installed":{}}')

        # Save current directory
        old_cwd = os.getcwd()

        try:
            # Change to temp directory
            os.chdir(tmp_path)

            result = check_credentials()

            assert result is True

        finally:
            # Restore directory
            os.chdir(old_cwd)


class TestErrorHandling:
    """Test error handling in setup module."""

    def test_import_error_handling(self):
        """Test handling of import errors."""
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            result = check_dependencies()

            assert result is False

    def test_file_not_found_handling(self, tmp_path, monkeypatch):
        """Test handling of missing credential files."""
        monkeypatch.chdir(tmp_path)

        result = check_credentials()

        assert result is False

    def test_api_error_handling(self):
        """Test handling of Gmail API errors."""
        with patch('gmail_assistant.deletion.deleter.GmailDeleter') as mock_deleter:
            from googleapiclient.errors import HttpError

            deleter_instance = MagicMock()
            deleter_instance.get_email_count.side_effect = HttpError(
                resp=MagicMock(status=500),
                content=b'Server error'
            )
            mock_deleter.return_value = deleter_instance

            success, stats = test_gmail_connection()

            assert success is False
            assert stats == {}


class TestDeletionStrategies:
    """Test deletion strategy suggestions."""

    def test_strategy_generation_high_unread(self):
        """Test strategies for high unread count."""
        email_stats = {
            'Total emails': 5000,
            'Unread emails': 3000
        }

        # Should generate strategies without errors
        create_deletion_plan(email_stats)

    def test_strategy_generation_low_unread(self):
        """Test strategies for low unread count."""
        email_stats = {
            'Total emails': 5000,
            'Unread emails': 10
        }

        create_deletion_plan(email_stats)

    def test_strategy_generation_no_emails(self):
        """Test strategies when no emails exist."""
        email_stats = {
            'Total emails': 0,
            'Unread emails': 0
        }

        create_deletion_plan(email_stats)
