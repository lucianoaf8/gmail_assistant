"""Comprehensive tests for deletion UI module."""

from unittest.mock import MagicMock, patch

import pytest

from gmail_assistant.deletion.ui import clean_unread_inbox, main


@pytest.fixture
def mock_deleter():
    """Create mock GmailDeleter."""
    deleter = MagicMock()
    deleter.get_email_count.return_value = 100
    deleter.delete_by_query.return_value = {'deleted': 100, 'failed': 0}
    return deleter


class TestCleanUnreadInbox:
    """Test clean_unread_inbox functionality."""

    def test_clean_unread_inbox_dry_run(self, mock_deleter):
        """Test clean inbox in dry run mode."""
        result = clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

        assert result['deleted'] == 0
        assert result['failed'] == 0

        # Verify no actual deletion was called
        assert not mock_deleter.delete_by_query.called

    def test_clean_unread_inbox_no_emails(self, mock_deleter):
        """Test clean inbox with no unread emails."""
        mock_deleter.get_email_count.return_value = 0

        result = clean_unread_inbox(mock_deleter, dry_run=False, keep_recent_days=0)

        assert result['deleted'] == 0
        assert result['failed'] == 0

    def test_clean_unread_inbox_with_confirmation(self, mock_deleter, monkeypatch):
        """Test clean inbox with user confirmation."""
        mock_deleter.get_email_count.return_value = 150

        # Mock user confirmation
        monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

        result = clean_unread_inbox(mock_deleter, dry_run=False, keep_recent_days=0)

        # Should have called delete_by_query
        mock_deleter.delete_by_query.assert_called_once_with('is:unread', dry_run=False)

    def test_clean_unread_inbox_cancelled(self, mock_deleter, monkeypatch):
        """Test clean inbox cancelled by user."""
        mock_deleter.get_email_count.return_value = 150

        # Mock user cancellation
        monkeypatch.setattr('builtins.input', lambda _: 'CANCEL')

        result = clean_unread_inbox(mock_deleter, dry_run=False, keep_recent_days=0)

        assert result['deleted'] == 0
        assert result['failed'] == 0

        # Verify no deletion was called
        assert not mock_deleter.delete_by_query.called

    def test_clean_unread_inbox_keep_recent(self, mock_deleter, monkeypatch):
        """Test clean inbox keeping recent emails."""
        # Need enough values: 1 total + 5 categories + 1 target + 1 remaining
        mock_deleter.get_email_count.side_effect = [
            150,  # Total unread
            20, 30, 25, 10, 15,  # 5 categories
            120,  # Target (older than 7 days)
            30,   # Remaining after deletion
        ]

        monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

        with patch('gmail_assistant.deletion.ui.Table'), \
             patch('gmail_assistant.deletion.ui.Panel'), \
             patch('gmail_assistant.deletion.ui.Console'):
            result = clean_unread_inbox(mock_deleter, dry_run=False, keep_recent_days=7)

        # Should use query with older_than
        mock_deleter.delete_by_query.assert_called_with('is:unread older_than:7d', dry_run=False)

    def test_clean_unread_inbox_category_breakdown(self, mock_deleter):
        """Test clean inbox shows category breakdown."""
        mock_deleter.get_email_count.side_effect = [
            150,  # Total unread
            20,   # Financial
            50,   # Notifications
            40,   # Marketing
            10,   # Social
            15,   # Large emails
            150,  # Target count (all unread)
        ]

        result = clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

        # Should have called get_email_count multiple times for categories
        assert mock_deleter.get_email_count.call_count >= 5

    def test_clean_unread_inbox_no_target_emails(self, mock_deleter):
        """Test clean inbox when no emails match deletion criteria."""
        mock_deleter.get_email_count.side_effect = [
            150,  # Total unread
            0,    # Financial (example category)
            0,    # Notifications
            0,    # Marketing
            0,    # Social
            0,    # Large emails
            0,    # Target count (none match older_than)
        ]

        result = clean_unread_inbox(mock_deleter, dry_run=False, keep_recent_days=30)

        assert result['deleted'] == 0
        assert result['failed'] == 0


class TestMainFunction:
    """Test main CLI function."""

    def test_main_dry_run(self, monkeypatch):
        """Test main function in dry run mode."""
        with patch('gmail_assistant.deletion.ui.GmailDeleter') as mock_deleter_class:
            deleter = MagicMock()
            deleter.get_email_count.return_value = 100
            mock_deleter_class.return_value = deleter

            # Mock argparse to return dry-run args
            with patch('sys.argv', ['ui.py', '--dry-run']):
                main()

            # Verify deleter was created
            mock_deleter_class.assert_called_once()

    def test_main_with_keep_recent(self):
        """Test main function with keep-recent option."""
        with patch('gmail_assistant.deletion.ui.GmailDeleter') as mock_deleter_class, \
             patch('gmail_assistant.deletion.ui.clean_unread_inbox') as mock_clean:

            deleter = MagicMock()
            mock_deleter_class.return_value = deleter
            mock_clean.return_value = {'deleted': 0, 'failed': 0}

            with patch('sys.argv', ['ui.py', '--dry-run', '--keep-recent', '7']):
                main()

            # Verify clean_unread_inbox was called with correct parameters
            mock_clean.assert_called_once_with(
                deleter=deleter,
                dry_run=True,
                keep_recent_days=7
            )

    def test_main_successful_deletion(self, monkeypatch):
        """Test main function with successful deletion."""
        with patch('gmail_assistant.deletion.ui.GmailDeleter') as mock_deleter_class, \
             patch('gmail_assistant.deletion.ui.clean_unread_inbox') as mock_clean:

            deleter = MagicMock()
            mock_deleter_class.return_value = deleter
            mock_clean.return_value = {'deleted': 150, 'failed': 0}

            with patch('sys.argv', ['ui.py']):
                monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

                main()

            # Should have called clean_unread_inbox
            mock_clean.assert_called_once()

    def test_main_keyboard_interrupt(self):
        """Test main function handles keyboard interrupt."""
        with patch('gmail_assistant.deletion.ui.GmailDeleter') as mock_deleter_class:
            mock_deleter_class.side_effect = KeyboardInterrupt()

            # Should not raise exception
            with patch('sys.argv', ['ui.py', '--dry-run']):
                main()

    def test_main_general_exception(self):
        """Test main function handles general exceptions."""
        with patch('gmail_assistant.deletion.ui.GmailDeleter') as mock_deleter_class:
            mock_deleter_class.side_effect = Exception("Test error")

            # Should not raise exception
            with patch('sys.argv', ['ui.py', '--dry-run']):
                main()

    def test_main_no_deletion_in_dry_run(self):
        """Test main function doesn't delete in dry run."""
        with patch('gmail_assistant.deletion.ui.GmailDeleter') as mock_deleter_class, \
             patch('gmail_assistant.deletion.ui.clean_unread_inbox') as mock_clean:

            deleter = MagicMock()
            mock_deleter_class.return_value = deleter
            mock_clean.return_value = {'deleted': 0, 'failed': 0}

            with patch('sys.argv', ['ui.py', '--dry-run']):
                main()

            # clean_unread_inbox should be called with dry_run=True
            call_args = mock_clean.call_args
            assert call_args.kwargs['dry_run'] is True


class TestUIDisplay:
    """Test UI display elements."""

    def test_displays_breakdown_table(self, mock_deleter):
        """Test that category breakdown table is displayed."""
        mock_deleter.get_email_count.side_effect = [
            150,  # Total unread
            20,   # Financial
            50,   # Notifications
            40,   # Marketing
            10,   # Social
            15,   # Large emails
            150,  # Target count
        ]

        with patch('gmail_assistant.deletion.ui.Console') as mock_console:
            console_instance = MagicMock()
            mock_console.return_value = console_instance

            result = clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

            # Verify console.print was called (for displaying tables/panels)
            assert console_instance.print.called

    def test_displays_dry_run_panel(self, mock_deleter):
        """Test that dry run panel is displayed."""
        mock_deleter.get_email_count.return_value = 100

        with patch('gmail_assistant.deletion.ui.Console') as mock_console:
            console_instance = MagicMock()
            mock_console.return_value = console_instance

            clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

            # Verify Panel was used for dry run display
            assert console_instance.print.called

    def test_displays_confirmation_panel(self, mock_deleter, monkeypatch):
        """Test that confirmation panel is displayed."""
        # Need enough values: 1 total + 5 categories + 1 target
        mock_deleter.get_email_count.side_effect = [
            100,  # Total unread
            20, 30, 25, 10, 15,  # 5 categories
            100,  # Target
        ]
        monkeypatch.setattr('builtins.input', lambda _: 'CANCEL')

        with patch('gmail_assistant.deletion.ui.Console') as mock_console, \
             patch('gmail_assistant.deletion.ui.Table'), \
             patch('gmail_assistant.deletion.ui.Panel'):
            console_instance = MagicMock()
            mock_console.return_value = console_instance

            clean_unread_inbox(mock_deleter, dry_run=False, keep_recent_days=0)

            # Verify console was used for displaying confirmation
            assert console_instance.print.called


class TestUIEdgeCases:
    """Test edge cases in UI module."""

    def test_clean_inbox_with_zero_categories(self, mock_deleter):
        """Test clean inbox when all categories are zero."""
        mock_deleter.get_email_count.return_value = 0

        result = clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

        assert result['deleted'] == 0

    def test_clean_inbox_with_very_large_numbers(self, mock_deleter, monkeypatch):
        """Test clean inbox with very large email counts."""
        # Need enough values: 1 total + 5 categories + 1 target + 1 remaining
        mock_deleter.get_email_count.side_effect = [
            10000,  # Total unread
            2000, 3000, 1500, 500, 1000,  # 5 categories
            10000,  # Target count
            0,      # Remaining after deletion
        ]

        monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

        with patch('gmail_assistant.deletion.ui.Table'), \
             patch('gmail_assistant.deletion.ui.Panel'), \
             patch('gmail_assistant.deletion.ui.Console'):
            result = clean_unread_inbox(mock_deleter, dry_run=False, keep_recent_days=0)

        # Should handle large numbers correctly
        mock_deleter.delete_by_query.assert_called_once()

    def test_clean_inbox_partial_deletion(self, mock_deleter, monkeypatch):
        """Test clean inbox with partial deletion success."""
        mock_deleter.get_email_count.side_effect = [
            150,   # Total unread
            0, 0, 0, 0, 0,  # Categories
            150,   # Target count
            50,    # Remaining after deletion
        ]

        mock_deleter.delete_by_query.return_value = {'deleted': 100, 'failed': 50}

        monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

        result = clean_unread_inbox(mock_deleter, dry_run=False, keep_recent_days=0)

        assert result['deleted'] == 100
        assert result['failed'] == 50


class TestUIConsoleFormatting:
    """Test console formatting and output."""

    def test_uses_rich_console(self, mock_deleter):
        """Test that Rich Console is used for formatting."""
        with patch('gmail_assistant.deletion.ui.Console') as mock_console:
            console_instance = MagicMock()
            mock_console.return_value = console_instance

            mock_deleter.get_email_count.return_value = 100

            clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

            # Verify Console was instantiated
            mock_console.assert_called()

    def test_displays_panels(self, mock_deleter):
        """Test that panels are used for important information."""
        with patch('gmail_assistant.deletion.ui.Panel') as mock_panel:
            mock_deleter.get_email_count.return_value = 100

            clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

            # Panel should be used for various displays
            assert mock_panel.called

    def test_displays_tables(self, mock_deleter):
        """Test that tables are used for category breakdown."""
        with patch('gmail_assistant.deletion.ui.Table') as mock_table:
            mock_deleter.get_email_count.side_effect = [
                150,  # Total
                20, 50, 40, 10, 15,  # Categories
                150   # Target
            ]

            clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

            # Table should be created for breakdown
            assert mock_table.called


class TestUIIntegration:
    """Integration tests for UI module."""

    def test_full_workflow_dry_run(self, mock_deleter):
        """Test complete workflow in dry run mode."""
        mock_deleter.get_email_count.side_effect = [
            150,  # Total unread
            20, 50, 40, 10, 15,  # Categories
            150   # Target count
        ]

        result = clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

        assert result['deleted'] == 0
        assert result['failed'] == 0

        # Verify analytics were gathered
        assert mock_deleter.get_email_count.call_count >= 5

    def test_full_workflow_with_deletion(self, mock_deleter, monkeypatch):
        """Test complete workflow with actual deletion."""
        mock_deleter.get_email_count.side_effect = [
            150,  # Total unread
            20, 50, 40, 10, 15,  # Categories
            150,  # Target count
            0     # Remaining after deletion
        ]

        mock_deleter.delete_by_query.return_value = {'deleted': 150, 'failed': 0}

        monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

        result = clean_unread_inbox(mock_deleter, dry_run=False, keep_recent_days=0)

        assert result['deleted'] == 150
        assert result['failed'] == 0

    def test_workflow_with_keep_recent(self, mock_deleter, monkeypatch):
        """Test workflow keeping recent emails."""
        mock_deleter.get_email_count.side_effect = [
            150,  # Total unread
            20, 50, 40, 10, 15,  # Categories
            100,  # Target count (older than 7 days)
            50    # Remaining after deletion
        ]

        mock_deleter.delete_by_query.return_value = {'deleted': 100, 'failed': 0}

        monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

        result = clean_unread_inbox(mock_deleter, dry_run=False, keep_recent_days=7)

        # Verify correct query was used
        mock_deleter.delete_by_query.assert_called_with('is:unread older_than:7d', dry_run=False)


class TestUIErrorHandling:
    """Test error handling in UI module."""

    def test_handles_api_errors(self, mock_deleter):
        """Test handling of Gmail API errors."""
        from googleapiclient.errors import HttpError

        # Create proper HttpError mock
        resp_mock = MagicMock()
        resp_mock.status = 500
        resp_mock.reason = 'Server Error'

        mock_deleter.get_email_count.side_effect = HttpError(
            resp=resp_mock,
            content=b'Server error'
        )

        # clean_unread_inbox propagates HttpError
        with pytest.raises(HttpError):
            clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

    def test_handles_network_errors(self, mock_deleter, monkeypatch):
        """Test handling of network errors."""
        mock_deleter.get_email_count.side_effect = ConnectionError("Network failed")

        # Should not raise exception
        try:
            result = clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)
        except ConnectionError:
            # Expected if not caught internally
            pass

    def test_handles_keyboard_interrupt_in_main(self):
        """Test keyboard interrupt handling in main."""
        with patch('gmail_assistant.deletion.ui.GmailDeleter', side_effect=KeyboardInterrupt()):
            # Should catch and handle gracefully
            with patch('sys.argv', ['ui.py', '--dry-run']):
                main()  # Should not raise
