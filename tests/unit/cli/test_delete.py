"""
Comprehensive tests for delete.py command module.
Tests delete_emails and get_email_count functions.
"""

from pathlib import Path
from unittest import mock

import pytest


class TestDeleteEmails:
    """Tests for delete_emails function."""

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_delete_dry_run(self, mock_client_class, tmp_path):
        """Test delete in dry run mode."""
        from gmail_assistant.cli.commands.delete import delete_emails

        # Setup mock service
        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}],
            'resultSizeEstimate': 2
        }
        mock_service.users().messages().get().execute.return_value = {
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'Date', 'value': '2024-01-15'}
                ]
            }
        }

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        result = delete_emails(
            query="from:spam@example.com",
            credentials_path=creds_path,
            dry_run=True
        )

        assert result['found'] == 2
        assert result['deleted'] == 0
        assert result['dry_run'] is True

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_delete_no_emails_found(self, mock_client_class, tmp_path):
        """Test delete when no emails match query."""
        from gmail_assistant.cli.commands.delete import delete_emails

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': []
        }

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        result = delete_emails(
            query="nonexistent",
            credentials_path=creds_path,
            dry_run=True
        )

        assert result['found'] == 0
        assert result['deleted'] == 0

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_delete_trash_mode(self, mock_client_class, tmp_path):
        """Test delete in trash mode."""
        from gmail_assistant.cli.commands.delete import delete_emails

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}]
        }

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client.trash_emails.return_value = {'trashed': 2, 'failed': 0}
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        result = delete_emails(
            query="from:spam@example.com",
            credentials_path=creds_path,
            dry_run=False,
            use_trash=True
        )

        assert result['deleted'] == 2
        mock_client.trash_emails.assert_called_once_with(['msg1', 'msg2'])

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_delete_permanent_mode(self, mock_client_class, tmp_path):
        """Test delete in permanent deletion mode."""
        from gmail_assistant.cli.commands.delete import delete_emails

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}]
        }

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client.delete_emails.return_value = {'deleted': 2, 'failed': 0}
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        result = delete_emails(
            query="from:spam@example.com",
            credentials_path=creds_path,
            dry_run=False,
            use_trash=False
        )

        assert result['deleted'] == 2
        mock_client.delete_emails.assert_called_once_with(['msg1', 'msg2'])

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_delete_respects_max_delete(self, mock_client_class, tmp_path):
        """Test delete respects max_delete limit."""
        from gmail_assistant.cli.commands.delete import delete_emails

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': f'msg{i}'} for i in range(50)]
        }

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client.trash_emails.return_value = {'trashed': 50, 'failed': 0}
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        result = delete_emails(
            query="from:spam@example.com",
            credentials_path=creds_path,
            dry_run=False,
            max_delete=50
        )

        # Verify maxResults was passed correctly
        mock_service.users().messages().list.assert_called_with(
            userId='me',
            q="from:spam@example.com",
            maxResults=50
        )

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_delete_handles_partial_failure(self, mock_client_class, tmp_path):
        """Test delete reports partial failures."""
        from gmail_assistant.cli.commands.delete import delete_emails

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}, {'id': 'msg3'}]
        }

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client.trash_emails.return_value = {'trashed': 2, 'failed': 1}
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        result = delete_emails(
            query="from:spam@example.com",
            credentials_path=creds_path,
            dry_run=False
        )

        assert result['deleted'] == 2
        assert result['failed'] == 1

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_delete_api_error(self, mock_client_class, tmp_path):
        """Test delete raises APIError on failure."""
        from gmail_assistant.cli.commands.delete import delete_emails
        from gmail_assistant.core.exceptions import APIError

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.side_effect = Exception("API Error")

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        with pytest.raises(APIError, match="Delete operation failed"):
            delete_emails(
                query="from:spam@example.com",
                credentials_path=creds_path
            )


class TestGetEmailCount:
    """Tests for get_email_count function."""

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_get_email_count_basic(self, mock_client_class, tmp_path):
        """Test basic email count."""
        from gmail_assistant.cli.commands.delete import get_email_count

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'resultSizeEstimate': 150
        }

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        count = get_email_count("from:test@example.com", creds_path)

        assert count == 150

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_get_email_count_zero(self, mock_client_class, tmp_path):
        """Test count returns zero when no emails."""
        from gmail_assistant.cli.commands.delete import get_email_count

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'resultSizeEstimate': 0
        }

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        count = get_email_count("nonexistent", creds_path)

        assert count == 0

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_get_email_count_error_returns_zero(self, mock_client_class, tmp_path):
        """Test count returns zero on error."""
        from gmail_assistant.cli.commands.delete import get_email_count

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.side_effect = Exception("Error")

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        count = get_email_count("from:test@example.com", creds_path)

        assert count == 0

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_get_email_count_missing_field(self, mock_client_class, tmp_path):
        """Test count returns zero when field missing."""
        from gmail_assistant.cli.commands.delete import get_email_count

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {}

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        count = get_email_count("from:test@example.com", creds_path)

        assert count == 0


class TestDeleteDryRunPreview:
    """Tests for dry run preview functionality."""

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_preview_shows_emails_preview(self, mock_client_class, tmp_path):
        """Test dry run shows email preview."""
        from gmail_assistant.cli.commands.delete import delete_emails

        # Create 15 messages
        messages = [{'id': f'msg{i}'} for i in range(15)]

        # Create a mock for tracking get() calls
        mock_get_result = mock.MagicMock()
        mock_get_result.execute.return_value = {
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'test@example.com'}
                ]
            }
        }

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': messages
        }
        mock_service.users().messages().get.return_value = mock_get_result

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        result = delete_emails(
            query="from:test@example.com",
            credentials_path=creds_path,
            dry_run=True
        )

        # Verify it found emails and is in dry run mode
        assert result['found'] == 15
        assert result['dry_run'] is True
        # Preview should limit to 10 emails
        assert mock_service.users().messages().get.call_count == 10

    @mock.patch('gmail_assistant.cli.commands.delete.GmailAPIClient')
    def test_preview_handles_metadata_error(self, mock_client_class, tmp_path):
        """Test preview handles error getting email metadata."""
        from gmail_assistant.cli.commands.delete import delete_emails

        mock_service = mock.MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}]
        }
        mock_service.users().messages().get().execute.side_effect = Exception("Error")

        mock_client = mock.MagicMock()
        mock_client.service = mock_service
        mock_client_class.return_value = mock_client

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        # Should not raise, just show message ID instead
        result = delete_emails(
            query="from:test@example.com",
            credentials_path=creds_path,
            dry_run=True
        )

        assert result['found'] == 1
        assert result['dry_run'] is True
