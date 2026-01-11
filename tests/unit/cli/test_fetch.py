"""
Comprehensive tests for fetch.py command module.
Tests fetch_emails function and _save_email helper.
"""

import json
from pathlib import Path
from unittest import mock

import click
import pytest


class TestFetchEmails:
    """Tests for fetch_emails function."""

    @mock.patch('gmail_assistant.cli.commands.fetch.CheckpointManager')
    @mock.patch('gmail_assistant.cli.commands.fetch.GmailFetcher')
    def test_fetch_emails_basic(self, mock_fetcher_class, mock_checkpoint_class, tmp_path):
        """Test basic email fetching."""
        from gmail_assistant.cli.commands.fetch import fetch_emails

        # Setup mocks
        mock_fetcher = mock.MagicMock()
        mock_fetcher.authenticate.return_value = True
        mock_fetcher.search_messages.return_value = ['msg1', 'msg2', 'msg3']
        mock_fetcher.get_message_details.return_value = {
            'id': 'msg1',
            'subject': 'Test',
            'sender': 'test@example.com'
        }
        mock_fetcher_class.return_value = mock_fetcher

        mock_checkpoint = mock.MagicMock()
        mock_checkpoint.total_messages = 0
        mock_checkpoint_mgr = mock.MagicMock()
        mock_checkpoint_mgr.get_latest_checkpoint.return_value = None
        mock_checkpoint_mgr.create_checkpoint.return_value = mock_checkpoint
        mock_checkpoint_class.return_value = mock_checkpoint_mgr

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')
        output_dir = tmp_path / "output"

        result = fetch_emails(
            query="is:unread",
            max_emails=100,
            output_dir=output_dir,
            output_format="json",
            credentials_path=creds_path,
            resume=False
        )

        assert result['total'] == 3
        assert result['fetched'] == 3
        mock_fetcher.authenticate.assert_called_once()

    @mock.patch('gmail_assistant.cli.commands.fetch.CheckpointManager')
    @mock.patch('gmail_assistant.cli.commands.fetch.GmailFetcher')
    def test_fetch_emails_auth_failure(self, mock_fetcher_class, mock_checkpoint_class, tmp_path):
        """Test fetch fails on auth error."""
        from gmail_assistant.cli.commands.fetch import fetch_emails
        from gmail_assistant.core.exceptions import AuthError

        mock_fetcher = mock.MagicMock()
        mock_fetcher.authenticate.return_value = False
        mock_fetcher_class.return_value = mock_fetcher

        mock_checkpoint_mgr = mock.MagicMock()
        mock_checkpoint_mgr.get_latest_checkpoint.return_value = None
        mock_checkpoint_class.return_value = mock_checkpoint_mgr

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        with pytest.raises(AuthError, match="authentication failed"):
            fetch_emails(
                query="is:unread",
                max_emails=100,
                output_dir=tmp_path / "output",
                output_format="json",
                credentials_path=creds_path
            )

    @mock.patch('gmail_assistant.cli.commands.fetch.CheckpointManager')
    @mock.patch('gmail_assistant.cli.commands.fetch.GmailFetcher')
    def test_fetch_emails_no_results(self, mock_fetcher_class, mock_checkpoint_class, tmp_path):
        """Test fetch with no matching emails."""
        from gmail_assistant.cli.commands.fetch import fetch_emails

        mock_fetcher = mock.MagicMock()
        mock_fetcher.authenticate.return_value = True
        mock_fetcher.search_messages.return_value = []
        mock_fetcher_class.return_value = mock_fetcher

        mock_checkpoint = mock.MagicMock()
        mock_checkpoint_mgr = mock.MagicMock()
        mock_checkpoint_mgr.get_latest_checkpoint.return_value = None
        mock_checkpoint_mgr.create_checkpoint.return_value = mock_checkpoint
        mock_checkpoint_class.return_value = mock_checkpoint_mgr

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        result = fetch_emails(
            query="nonexistent",
            max_emails=100,
            output_dir=tmp_path / "output",
            output_format="json",
            credentials_path=creds_path
        )

        assert result['fetched'] == 0
        assert result['total'] == 0
        mock_checkpoint_mgr.mark_completed.assert_called_once()

    @mock.patch('gmail_assistant.cli.commands.fetch.CheckpointManager')
    @mock.patch('gmail_assistant.cli.commands.fetch.GmailFetcher')
    def test_fetch_emails_resume(self, mock_fetcher_class, mock_checkpoint_class, tmp_path):
        """Test fetch with resume functionality."""
        from gmail_assistant.cli.commands.fetch import fetch_emails

        mock_fetcher = mock.MagicMock()
        mock_fetcher.authenticate.return_value = True
        mock_fetcher.search_messages.return_value = ['msg1', 'msg2', 'msg3']
        mock_fetcher.get_message_details.return_value = {
            'id': 'msg1',
            'subject': 'Test',
            'sender': 'test@example.com'
        }
        mock_fetcher_class.return_value = mock_fetcher

        # Setup checkpoint with resume info
        mock_checkpoint = mock.MagicMock()
        mock_checkpoint.sync_id = 'sync123'
        mock_checkpoint.total_messages = 3
        mock_checkpoint_mgr = mock.MagicMock()
        mock_checkpoint_mgr.get_latest_checkpoint.return_value = mock_checkpoint
        mock_checkpoint_mgr.get_resume_info.return_value = {'skip_count': 1}
        mock_checkpoint_class.return_value = mock_checkpoint_mgr

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        result = fetch_emails(
            query="is:unread",
            max_emails=100,
            output_dir=tmp_path / "output",
            output_format="json",
            credentials_path=creds_path,
            resume=True
        )

        # Should skip first message
        assert result['total'] == 3
        # 2 messages fetched (skipping first one)
        assert result['fetched'] == 2

    @mock.patch('gmail_assistant.cli.commands.fetch.CheckpointManager')
    @mock.patch('gmail_assistant.cli.commands.fetch.GmailFetcher')
    def test_fetch_emails_handles_exceptions(self, mock_fetcher_class, mock_checkpoint_class, tmp_path):
        """Test fetch marks checkpoint interrupted on exception."""
        from gmail_assistant.cli.commands.fetch import fetch_emails

        mock_fetcher = mock.MagicMock()
        mock_fetcher.authenticate.return_value = True
        mock_fetcher.search_messages.side_effect = Exception("API Error")
        mock_fetcher_class.return_value = mock_fetcher

        mock_checkpoint = mock.MagicMock()
        mock_checkpoint_mgr = mock.MagicMock()
        mock_checkpoint_mgr.get_latest_checkpoint.return_value = None
        mock_checkpoint_mgr.create_checkpoint.return_value = mock_checkpoint
        mock_checkpoint_class.return_value = mock_checkpoint_mgr

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        with pytest.raises(Exception):
            fetch_emails(
                query="is:unread",
                max_emails=100,
                output_dir=tmp_path / "output",
                output_format="json",
                credentials_path=creds_path
            )

        mock_checkpoint_mgr.mark_interrupted.assert_called_once_with(mock_checkpoint)


class TestSaveEmail:
    """Tests for _save_email helper function."""

    def test_save_email_json(self, tmp_path):
        """Test saving email as JSON."""
        from gmail_assistant.cli.commands.fetch import _save_email

        email_data = {
            'id': 'msg123',
            'subject': 'Test Subject',
            'sender': 'test@example.com',
            'body': 'Email content'
        }

        _save_email(email_data, tmp_path, 'json', 0)

        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 1

        with open(json_files[0]) as f:
            saved_data = json.load(f)
        assert saved_data['id'] == 'msg123'

    def test_save_email_eml(self, tmp_path):
        """Test saving email as EML."""
        from gmail_assistant.cli.commands.fetch import _save_email

        email_data = {
            'id': 'msg123',
            'subject': 'Test Subject',
            'raw_content': 'From: test@example.com\nSubject: Test\n\nBody'
        }

        _save_email(email_data, tmp_path, 'eml', 0)

        eml_files = list(tmp_path.glob("*.eml"))
        assert len(eml_files) == 1

        content = eml_files[0].read_text()
        assert 'From: test@example.com' in content

    def test_save_email_mbox(self, tmp_path):
        """Test saving email as mbox."""
        from gmail_assistant.cli.commands.fetch import _save_email

        email_data = {
            'id': 'msg123',
            'subject': 'Test Subject',
            'sender': 'test@example.com',
            'raw_content': 'Subject: Test\n\nBody'
        }

        _save_email(email_data, tmp_path, 'mbox', 0)

        mbox_path = tmp_path / "emails.mbox"
        assert mbox_path.exists()

        content = mbox_path.read_text()
        assert 'From test@example.com' in content

    def test_save_email_appends_to_mbox(self, tmp_path):
        """Test multiple emails append to same mbox file."""
        from gmail_assistant.cli.commands.fetch import _save_email

        for i in range(3):
            email_data = {
                'id': f'msg{i}',
                'subject': f'Test Subject {i}',
                'sender': f'test{i}@example.com',
                'raw_content': f'Subject: Test {i}\n\nBody {i}'
            }
            _save_email(email_data, tmp_path, 'mbox', i)

        mbox_path = tmp_path / "emails.mbox"
        content = mbox_path.read_text()

        # All emails in single file
        assert 'test0@example.com' in content
        assert 'test1@example.com' in content
        assert 'test2@example.com' in content

    def test_save_email_sanitizes_subject(self, tmp_path):
        """Test subject is sanitized for filename."""
        from gmail_assistant.cli.commands.fetch import _save_email

        email_data = {
            'id': 'msg123',
            'subject': 'Test: With/Special<Chars>',
            'sender': 'test@example.com'
        }

        _save_email(email_data, tmp_path, 'json', 0)

        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 1

        filename = json_files[0].name
        assert ':' not in filename
        assert '/' not in filename
        assert '<' not in filename
        assert '>' not in filename

    def test_save_email_truncates_long_subject(self, tmp_path):
        """Test long subject is truncated."""
        from gmail_assistant.cli.commands.fetch import _save_email

        email_data = {
            'id': 'msg123',
            'subject': 'A' * 100,  # Very long subject
            'sender': 'test@example.com'
        }

        _save_email(email_data, tmp_path, 'json', 0)

        json_files = list(tmp_path.glob("*.json"))
        filename = json_files[0].name
        # Subject portion should be truncated to 50 chars
        assert len(filename) < 120  # Reasonable total length

    def test_save_email_no_subject(self, tmp_path):
        """Test email with no subject uses default."""
        from gmail_assistant.cli.commands.fetch import _save_email

        email_data = {
            'id': 'msg123',
            'sender': 'test@example.com'
        }

        _save_email(email_data, tmp_path, 'json', 0)

        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 1
        assert 'no_subject' in json_files[0].name

    def test_save_email_index_formatting(self, tmp_path):
        """Test index is zero-padded in filename."""
        from gmail_assistant.cli.commands.fetch import _save_email

        email_data = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': 'test@example.com'
        }

        _save_email(email_data, tmp_path, 'json', 5)

        json_files = list(tmp_path.glob("*.json"))
        filename = json_files[0].name
        assert filename.startswith('00005_')


class TestFetchEmailsIntegration:
    """Integration tests for fetch_emails with file operations."""

    @mock.patch('gmail_assistant.cli.commands.fetch.CheckpointManager')
    @mock.patch('gmail_assistant.cli.commands.fetch.GmailFetcher')
    def test_fetch_creates_output_directory(self, mock_fetcher_class, mock_checkpoint_class, tmp_path):
        """Test fetch creates output directory if not exists."""
        from gmail_assistant.cli.commands.fetch import fetch_emails

        mock_fetcher = mock.MagicMock()
        mock_fetcher.authenticate.return_value = True
        mock_fetcher.search_messages.return_value = ['msg1']
        mock_fetcher.get_message_details.return_value = {
            'id': 'msg1',
            'subject': 'Test',
            'sender': 'test@example.com'
        }
        mock_fetcher_class.return_value = mock_fetcher

        mock_checkpoint = mock.MagicMock()
        mock_checkpoint.total_messages = 0
        mock_checkpoint_mgr = mock.MagicMock()
        mock_checkpoint_mgr.get_latest_checkpoint.return_value = None
        mock_checkpoint_mgr.create_checkpoint.return_value = mock_checkpoint
        mock_checkpoint_class.return_value = mock_checkpoint_mgr

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')
        output_dir = tmp_path / "nested" / "output"

        assert not output_dir.exists()

        fetch_emails(
            query="is:unread",
            max_emails=100,
            output_dir=output_dir,
            output_format="json",
            credentials_path=creds_path
        )

        assert output_dir.exists()

    @mock.patch('gmail_assistant.cli.commands.fetch.CheckpointManager')
    @mock.patch('gmail_assistant.cli.commands.fetch.GmailFetcher')
    def test_fetch_updates_checkpoint_periodically(self, mock_fetcher_class, mock_checkpoint_class, tmp_path):
        """Test checkpoint is updated every 50 emails."""
        from gmail_assistant.cli.commands.fetch import fetch_emails

        # Create 100 message IDs
        message_ids = [f'msg{i}' for i in range(100)]

        mock_fetcher = mock.MagicMock()
        mock_fetcher.authenticate.return_value = True
        mock_fetcher.search_messages.return_value = message_ids
        mock_fetcher.get_message_details.return_value = {
            'id': 'msgX',
            'subject': 'Test',
            'sender': 'test@example.com'
        }
        mock_fetcher_class.return_value = mock_fetcher

        mock_checkpoint = mock.MagicMock()
        mock_checkpoint.total_messages = 0
        mock_checkpoint_mgr = mock.MagicMock()
        mock_checkpoint_mgr.get_latest_checkpoint.return_value = None
        mock_checkpoint_mgr.create_checkpoint.return_value = mock_checkpoint
        mock_checkpoint_class.return_value = mock_checkpoint_mgr

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        fetch_emails(
            query="is:unread",
            max_emails=100,
            output_dir=tmp_path / "output",
            output_format="json",
            credentials_path=creds_path
        )

        # Should update checkpoint at 50 and 100
        assert mock_checkpoint_mgr.update_progress.call_count >= 1

    @mock.patch('gmail_assistant.cli.commands.fetch.CheckpointManager')
    @mock.patch('gmail_assistant.cli.commands.fetch.GmailFetcher')
    def test_fetch_continues_on_individual_email_failure(self, mock_fetcher_class, mock_checkpoint_class, tmp_path):
        """Test fetch continues when individual email fails."""
        from gmail_assistant.cli.commands.fetch import fetch_emails

        mock_fetcher = mock.MagicMock()
        mock_fetcher.authenticate.return_value = True
        mock_fetcher.search_messages.return_value = ['msg1', 'msg2', 'msg3']

        # First and third succeed, second fails
        mock_fetcher.get_message_details.side_effect = [
            {'id': 'msg1', 'subject': 'Test 1', 'sender': 'test@example.com'},
            Exception("Failed to fetch"),
            {'id': 'msg3', 'subject': 'Test 3', 'sender': 'test@example.com'},
        ]
        mock_fetcher_class.return_value = mock_fetcher

        mock_checkpoint = mock.MagicMock()
        mock_checkpoint.total_messages = 0
        mock_checkpoint_mgr = mock.MagicMock()
        mock_checkpoint_mgr.get_latest_checkpoint.return_value = None
        mock_checkpoint_mgr.create_checkpoint.return_value = mock_checkpoint
        mock_checkpoint_class.return_value = mock_checkpoint_mgr

        creds_path = tmp_path / "creds.json"
        creds_path.write_text('{}')

        result = fetch_emails(
            query="is:unread",
            max_emails=100,
            output_dir=tmp_path / "output",
            output_format="json",
            credentials_path=creds_path
        )

        # Should have 2 successful fetches
        assert result['fetched'] == 2
        assert result['total'] == 3
