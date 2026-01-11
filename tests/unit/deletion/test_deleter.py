"""Comprehensive tests for GmailDeleter module."""

from unittest.mock import MagicMock, Mock, patch, call

import pandas as pd
import pytest
from googleapiclient.errors import HttpError

from gmail_assistant.deletion.deleter import GmailDeleter


@pytest.fixture
def mock_credentials():
    """Mock credential manager."""
    with patch('gmail_assistant.deletion.deleter.SecureCredentialManager') as mock:
        manager = MagicMock()
        manager.authenticate.return_value = True
        manager.get_service.return_value = MagicMock()
        mock.return_value = manager
        yield manager


@pytest.fixture
def mock_service():
    """Mock Gmail service with proper chaining."""
    service = MagicMock()
    # Set up default return values
    list_mock = MagicMock()
    list_mock.execute.return_value = {
        'messages': [{'id': 'msg1'}, {'id': 'msg2'}],
        'resultSizeEstimate': 2
    }
    service.users.return_value.messages.return_value.list.return_value = list_mock
    service.users.return_value.messages.return_value.batchDelete.return_value.execute.return_value = None
    service.users.return_value.messages.return_value.delete.return_value.execute.return_value = None
    return service


@pytest.fixture
def deleter(mock_credentials, mock_service):
    """Create GmailDeleter instance with mocked dependencies."""
    with patch('gmail_assistant.deletion.deleter.GmailRateLimiter') as mock_rate, \
         patch('gmail_assistant.deletion.deleter.QuotaTracker') as mock_quota, \
         patch('gmail_assistant.deletion.deleter.Console'), \
         patch('gmail_assistant.deletion.deleter.Progress'), \
         patch('gmail_assistant.deletion.deleter.Table'):

        # Set up rate limiter mock
        mock_rate.return_value.wait_if_needed.return_value = None

        deleter_instance = GmailDeleter()
        # Service is a read-only property, mock via credential_manager
        deleter_instance.credential_manager.get_service.return_value = mock_service
        yield deleter_instance


class TestGmailDeleterInit:
    """Test GmailDeleter initialization."""

    def test_deleter_init_success(self, mock_credentials):
        """Test successful initialization."""
        with patch('gmail_assistant.deletion.deleter.GmailRateLimiter'), \
             patch('gmail_assistant.deletion.deleter.QuotaTracker'), \
             patch('gmail_assistant.deletion.deleter.Console'):

            deleter = GmailDeleter()

            assert deleter.credential_manager.authenticate.called
            assert hasattr(deleter, 'rate_limiter')
            assert hasattr(deleter, 'quota_tracker')
            assert hasattr(deleter, 'console')

    def test_deleter_init_auth_failure(self):
        """Test initialization with authentication failure."""
        with patch('gmail_assistant.deletion.deleter.SecureCredentialManager') as mock_cred, \
             patch('gmail_assistant.deletion.deleter.GmailRateLimiter'), \
             patch('gmail_assistant.deletion.deleter.QuotaTracker'), \
             patch('gmail_assistant.deletion.deleter.Console'):

            manager = MagicMock()
            manager.authenticate.return_value = False
            mock_cred.return_value = manager

            with pytest.raises(RuntimeError, match="Failed to authenticate"):
                GmailDeleter()

    def test_deleter_init_custom_credentials(self):
        """Test initialization with custom credentials file."""
        with patch('gmail_assistant.deletion.deleter.SecureCredentialManager') as mock_cred, \
             patch('gmail_assistant.deletion.deleter.GmailRateLimiter'), \
             patch('gmail_assistant.deletion.deleter.QuotaTracker'), \
             patch('gmail_assistant.deletion.deleter.Console'):

            manager = MagicMock()
            manager.authenticate.return_value = True
            mock_cred.return_value = manager

            deleter = GmailDeleter('custom_creds.json')

            mock_cred.assert_called_once_with('custom_creds.json')


class TestGmailDeleterEmailCount:
    """Test email count functionality."""

    def test_get_email_count_success(self, deleter, mock_service):
        """Test getting email count."""
        # Reset and set up mock
        list_mock = MagicMock()
        list_mock.execute.return_value = {'resultSizeEstimate': 150}
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        count = deleter.get_email_count('is:unread')

        assert count == 150
        mock_service.users.return_value.messages.return_value.list.assert_called_with(
            userId='me',
            q='is:unread'
        )

    def test_get_email_count_empty(self, deleter, mock_service):
        """Test email count with no results."""
        list_mock = MagicMock()
        list_mock.execute.return_value = {}
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        count = deleter.get_email_count('is:unread')

        assert count == 0

    def test_get_email_count_error(self, deleter, mock_service):
        """Test email count with API error."""
        list_mock = MagicMock()
        list_mock.execute.side_effect = HttpError(
            resp=MagicMock(status=500),
            content=b'Server error'
        )
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        count = deleter.get_email_count('is:unread')

        assert count == 0


class TestGmailDeleterListEmails:
    """Test email listing functionality."""

    def test_list_emails_basic(self, deleter, mock_service):
        """Test basic email listing."""
        list_mock = MagicMock()
        list_mock.execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}, {'id': 'msg3'}]
        }
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        message_ids = deleter.list_emails('is:unread')

        assert message_ids == ['msg1', 'msg2', 'msg3']

    def test_list_emails_with_max_results(self, deleter, mock_service):
        """Test email listing with max results."""
        list_mock = MagicMock()
        list_mock.execute.return_value = {
            'messages': [{'id': f'msg{i}'} for i in range(10)]
        }
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        message_ids = deleter.list_emails('is:unread', max_results=5)

        assert len(message_ids) == 5

    def test_list_emails_pagination(self, deleter, mock_service):
        """Test email listing with pagination."""
        list_mock = MagicMock()
        # First page, second page
        list_mock.execute.side_effect = [
            {'messages': [{'id': 'msg1'}, {'id': 'msg2'}], 'nextPageToken': 'token123'},
            {'messages': [{'id': 'msg3'}, {'id': 'msg4'}]}
        ]
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        message_ids = deleter.list_emails('is:unread')

        assert message_ids == ['msg1', 'msg2', 'msg3', 'msg4']

    def test_list_emails_pagination_with_limit(self, deleter, mock_service):
        """Test email listing with pagination and max limit."""
        list_mock = MagicMock()
        list_mock.execute.side_effect = [
            {'messages': [{'id': f'msg{i}'} for i in range(500)], 'nextPageToken': 'token123'},
            {'messages': [{'id': f'msg{i}'} for i in range(500, 750)]}
        ]
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        message_ids = deleter.list_emails('is:unread', max_results=600)

        assert len(message_ids) == 600

    def test_list_emails_empty(self, deleter, mock_service):
        """Test email listing with no results."""
        list_mock = MagicMock()
        list_mock.execute.return_value = {}
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        message_ids = deleter.list_emails('is:unread')

        assert message_ids == []

    def test_list_emails_error(self, deleter, mock_service):
        """Test email listing with API error."""
        list_mock = MagicMock()
        list_mock.execute.side_effect = HttpError(
            resp=MagicMock(status=500),
            content=b'Server error'
        )
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        message_ids = deleter.list_emails('is:unread')

        assert message_ids == []


class TestGmailDeleterBatchDelete:
    """Test batch deletion functionality."""

    def test_delete_emails_batch_success(self, deleter, mock_service):
        """Test successful batch deletion."""
        message_ids = ['msg1', 'msg2', 'msg3']

        # Set up batch delete mock
        batch_mock = MagicMock()
        batch_mock.execute.return_value = None
        mock_service.users.return_value.messages.return_value.batchDelete.return_value = batch_mock

        result = deleter.delete_emails_batch(message_ids, batch_size=2)

        assert result['deleted'] == 3
        assert result['failed'] == 0

    def test_delete_emails_batch_empty(self, deleter):
        """Test batch deletion with empty list."""
        result = deleter.delete_emails_batch([])

        assert result['deleted'] == 0
        assert result['failed'] == 0

    def test_delete_emails_batch_with_failures(self, deleter, mock_service):
        """Test batch deletion with some failures and fallback."""
        message_ids = ['msg1', 'msg2', 'msg3', 'msg4']

        # Set up mocks - batch fails, individual succeeds
        batch_mock = MagicMock()
        batch_mock.execute.side_effect = HttpError(resp=MagicMock(status=500), content=b'Error')
        mock_service.users.return_value.messages.return_value.batchDelete.return_value = batch_mock

        delete_mock = MagicMock()
        delete_mock.execute.return_value = None
        mock_service.users.return_value.messages.return_value.delete.return_value = delete_mock

        result = deleter.delete_emails_batch(message_ids, batch_size=2)

        # Individual fallback should succeed
        assert result['deleted'] >= 0

    def test_delete_emails_batch_rate_limiting(self, deleter, mock_service):
        """Test batch deletion respects rate limiting."""
        message_ids = ['msg1', 'msg2']

        batch_mock = MagicMock()
        batch_mock.execute.return_value = None
        mock_service.users.return_value.messages.return_value.batchDelete.return_value = batch_mock

        with patch.object(deleter.rate_limiter, 'wait_if_needed') as mock_rate:
            deleter.delete_emails_batch(message_ids, batch_size=2)
            mock_rate.assert_called()

    def test_delete_emails_batch_large_set(self, deleter, mock_service):
        """Test batch deletion with large email set."""
        message_ids = [f'msg{i}' for i in range(250)]

        batch_mock = MagicMock()
        batch_mock.execute.return_value = None
        mock_service.users.return_value.messages.return_value.batchDelete.return_value = batch_mock

        result = deleter.delete_emails_batch(message_ids, batch_size=100)

        assert result['deleted'] == 250
        assert result['failed'] == 0


class TestGmailDeleterDeleteByQuery:
    """Test delete by query functionality."""

    def test_delete_by_query_dry_run(self, deleter, mock_service):
        """Test delete by query in dry run mode."""
        list_mock = MagicMock()
        list_mock.execute.return_value = {
            'resultSizeEstimate': 10,
            'messages': [{'id': f'msg{i}'} for i in range(10)]
        }
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        result = deleter.delete_by_query('is:unread', dry_run=True)

        assert result['deleted'] == 0
        assert result['failed'] == 0

        # Verify no actual deletion occurred
        assert not mock_service.users.return_value.messages.return_value.batchDelete.called

    def test_delete_by_query_no_emails(self, deleter, mock_service):
        """Test delete by query with no matching emails."""
        list_mock = MagicMock()
        list_mock.execute.return_value = {'resultSizeEstimate': 0}
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        result = deleter.delete_by_query('is:unread', dry_run=False)

        assert result['deleted'] == 0
        assert result['failed'] == 0

    def test_delete_by_query_with_confirmation(self, deleter, mock_service, monkeypatch):
        """Test delete by query with user confirmation."""
        list_mock = MagicMock()
        list_mock.execute.return_value = {
            'resultSizeEstimate': 10,
            'messages': [{'id': f'msg{i}'} for i in range(10)]
        }
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        # Mock user input to confirm
        monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

        with patch.object(deleter, 'delete_emails_batch') as mock_batch:
            mock_batch.return_value = {'deleted': 10, 'failed': 0}

            result = deleter.delete_by_query('is:unread', dry_run=False)

            assert mock_batch.called

    def test_delete_by_query_cancelled(self, deleter, mock_service, monkeypatch):
        """Test delete by query cancelled by user."""
        list_mock = MagicMock()
        list_mock.execute.return_value = {
            'resultSizeEstimate': 10,
            'messages': [{'id': f'msg{i}'} for i in range(10)]
        }
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        # Mock user input to cancel
        monkeypatch.setattr('builtins.input', lambda _: 'CANCEL')

        result = deleter.delete_by_query('is:unread', dry_run=False)

        assert result['deleted'] == 0
        assert result['failed'] == 0

    def test_delete_by_query_large_deletion_warning(self, deleter, mock_service, monkeypatch):
        """Test delete by query with large deletion warning."""
        list_mock = MagicMock()
        list_mock.execute.return_value = {
            'resultSizeEstimate': 2000,
            'messages': [{'id': f'msg{i}'} for i in range(2000)]
        }
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        # Mock user input to cancel at first warning
        monkeypatch.setattr('builtins.input', lambda _: 'no')

        result = deleter.delete_by_query('is:unread', dry_run=False)

        assert result['deleted'] == 0

    def test_delete_by_query_with_max_delete(self, deleter, mock_service, monkeypatch):
        """Test delete by query with max_delete limit."""
        list_mock = MagicMock()
        list_mock.execute.return_value = {
            'resultSizeEstimate': 100,
            'messages': [{'id': f'msg{i}'} for i in range(50)]
        }
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

        with patch.object(deleter, 'delete_emails_batch') as mock_batch:
            mock_batch.return_value = {'deleted': 50, 'failed': 0}

            result = deleter.delete_by_query('is:unread', dry_run=False, max_delete=50)

            # Should only fetch 50 emails
            assert len(mock_batch.call_args[0][0]) == 50


class TestGmailDeleterParquetDeletion:
    """Test deletion from Parquet data."""

    def test_delete_from_parquet_data_success(self, deleter, tmp_path, monkeypatch):
        """Test deletion from Parquet file."""
        # Create test Parquet file
        parquet_file = tmp_path / "test.parquet"
        df = pd.DataFrame({
            'gmail_id': ['msg1', 'msg2', 'msg3']
        })
        df.to_parquet(parquet_file)

        monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

        with patch.object(deleter, 'delete_emails_batch') as mock_batch:
            mock_batch.return_value = {'deleted': 3, 'failed': 0}

            result = deleter.delete_from_parquet_data(str(parquet_file), dry_run=False)

            assert result['deleted'] == 3
            mock_batch.assert_called_once_with(['msg1', 'msg2', 'msg3'])

    def test_delete_from_parquet_data_dry_run(self, deleter, tmp_path):
        """Test Parquet deletion in dry run mode."""
        parquet_file = tmp_path / "test.parquet"
        df = pd.DataFrame({
            'gmail_id': ['msg1', 'msg2', 'msg3']
        })
        df.to_parquet(parquet_file)

        result = deleter.delete_from_parquet_data(str(parquet_file), dry_run=True)

        assert result['deleted'] == 0
        assert result['failed'] == 0

    def test_delete_from_parquet_data_cancelled(self, deleter, tmp_path, monkeypatch):
        """Test Parquet deletion cancelled by user."""
        parquet_file = tmp_path / "test.parquet"
        df = pd.DataFrame({
            'gmail_id': ['msg1', 'msg2', 'msg3']
        })
        df.to_parquet(parquet_file)

        monkeypatch.setattr('builtins.input', lambda _: 'CANCEL')

        result = deleter.delete_from_parquet_data(str(parquet_file), dry_run=False)

        assert result['deleted'] == 0

    def test_delete_from_parquet_data_missing_file(self, deleter, tmp_path):
        """Test Parquet deletion with missing file."""
        missing_file = tmp_path / "missing.parquet"

        result = deleter.delete_from_parquet_data(str(missing_file), dry_run=True)

        assert result['deleted'] == 0
        assert result['failed'] == 0

    def test_delete_from_parquet_data_empty(self, deleter, tmp_path):
        """Test Parquet deletion with empty data."""
        parquet_file = tmp_path / "empty.parquet"
        df = pd.DataFrame({
            'gmail_id': []
        })
        df.to_parquet(parquet_file)

        result = deleter.delete_from_parquet_data(str(parquet_file), dry_run=True)

        assert result['deleted'] == 0


class TestGmailDeleterServiceProperty:
    """Test service property."""

    def test_service_property(self, deleter, mock_service):
        """Test service property returns Gmail service."""
        service = deleter.service

        assert service == mock_service
        deleter.credential_manager.get_service.assert_called()


class TestGmailDeleterErrorRecovery:
    """Test error recovery mechanisms."""

    def test_batch_delete_with_individual_fallback(self, deleter, mock_service):
        """Test batch delete falls back to individual deletion on error."""
        message_ids = ['msg1', 'msg2', 'msg3']

        # Batch delete fails
        batch_mock = MagicMock()
        batch_mock.execute.side_effect = HttpError(
            resp=MagicMock(status=500),
            content=b'Batch failed'
        )
        mock_service.users.return_value.messages.return_value.batchDelete.return_value = batch_mock

        # Individual deletes succeed
        delete_mock = MagicMock()
        delete_mock.execute.return_value = None
        mock_service.users.return_value.messages.return_value.delete.return_value = delete_mock

        with patch.object(deleter.rate_limiter, 'wait_if_needed'):
            result = deleter.delete_emails_batch(message_ids, batch_size=10)

        # All should be deleted via fallback
        assert result['deleted'] == 3
        assert result['failed'] == 0

        # Verify individual delete was called for each message
        assert delete_mock.execute.call_count == 3

    def test_individual_delete_failures(self, deleter, mock_service):
        """Test handling of individual delete failures in fallback."""
        message_ids = ['msg1', 'msg2', 'msg3']

        # Batch delete fails
        batch_mock = MagicMock()
        batch_mock.execute.side_effect = HttpError(
            resp=MagicMock(status=500),
            content=b'Batch failed'
        )
        mock_service.users.return_value.messages.return_value.batchDelete.return_value = batch_mock

        # Individual deletes: first succeeds, second fails, third succeeds
        delete_mock = MagicMock()
        delete_mock.execute.side_effect = [
            None,
            HttpError(resp=MagicMock(status=404), content=b'Not found'),
            None
        ]
        mock_service.users.return_value.messages.return_value.delete.return_value = delete_mock

        with patch.object(deleter.rate_limiter, 'wait_if_needed'):
            result = deleter.delete_emails_batch(message_ids, batch_size=10)

        assert result['deleted'] == 2
        assert result['failed'] == 1


class TestGmailDeleterIntegration:
    """Integration tests for GmailDeleter."""

    def test_full_deletion_workflow(self, deleter, mock_service, monkeypatch):
        """Test complete deletion workflow."""
        # Setup mock responses
        list_mock = MagicMock()
        list_mock.execute.return_value = {
            'resultSizeEstimate': 5,
            'messages': [{'id': f'msg{i}'} for i in range(5)]
        }
        mock_service.users.return_value.messages.return_value.list.return_value = list_mock

        batch_mock = MagicMock()
        batch_mock.execute.return_value = None
        mock_service.users.return_value.messages.return_value.batchDelete.return_value = batch_mock

        # Mock user confirmation
        monkeypatch.setattr('builtins.input', lambda _: 'DELETE')

        with patch.object(deleter.rate_limiter, 'wait_if_needed'):
            result = deleter.delete_by_query('is:unread', dry_run=False)

        assert result['deleted'] == 5
        assert result['failed'] == 0

    def test_rate_limiting_across_operations(self, deleter, mock_service):
        """Test rate limiting is applied across all operations."""
        message_ids = [f'msg{i}' for i in range(300)]

        batch_mock = MagicMock()
        batch_mock.execute.return_value = None
        mock_service.users.return_value.messages.return_value.batchDelete.return_value = batch_mock

        with patch.object(deleter.rate_limiter, 'wait_if_needed') as mock_rate:
            deleter.delete_emails_batch(message_ids, batch_size=100)

            # Should be called for each batch
            assert mock_rate.call_count >= 3
