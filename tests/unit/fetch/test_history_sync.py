"""
Comprehensive tests for history_sync.py module.
Tests HistorySyncClient and SyncStateManager for incremental sync.
"""

import sqlite3
import tempfile
from datetime import datetime
from unittest import mock

import pytest


class TestHistoryEventType:
    """Tests for HistoryEventType enum."""

    def test_event_type_values(self):
        """Test all HistoryEventType values exist."""
        from gmail_assistant.core.fetch.history_sync import HistoryEventType

        assert HistoryEventType.MESSAGE_ADDED.value == "messageAdded"
        assert HistoryEventType.MESSAGE_DELETED.value == "messageDeleted"
        assert HistoryEventType.LABELS_ADDED.value == "labelsAdded"
        assert HistoryEventType.LABELS_REMOVED.value == "labelsRemoved"


class TestHistoryEvent:
    """Tests for HistoryEvent dataclass."""

    def test_history_event_creation(self):
        """Test creating a HistoryEvent."""
        from gmail_assistant.core.fetch.history_sync import HistoryEvent, HistoryEventType

        event = HistoryEvent(
            type=HistoryEventType.MESSAGE_ADDED,
            message_id="msg123",
            labels=["INBOX", "UNREAD"],
            history_id=12345
        )
        assert event.type == HistoryEventType.MESSAGE_ADDED
        assert event.message_id == "msg123"
        assert "INBOX" in event.labels
        assert event.history_id == 12345

    def test_history_event_default_timestamp(self):
        """Test HistoryEvent has default timestamp."""
        from gmail_assistant.core.fetch.history_sync import HistoryEvent, HistoryEventType

        event = HistoryEvent(
            type=HistoryEventType.MESSAGE_ADDED,
            message_id="msg123",
            labels=[],
            history_id=12345
        )
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)


class TestLabelChange:
    """Tests for LabelChange dataclass."""

    def test_label_change_creation(self):
        """Test creating a LabelChange."""
        from gmail_assistant.core.fetch.history_sync import LabelChange

        change = LabelChange(
            message_id="msg123",
            added_labels=["STARRED"],
            removed_labels=["UNREAD"],
            history_id=12345
        )
        assert change.message_id == "msg123"
        assert "STARRED" in change.added_labels
        assert "UNREAD" in change.removed_labels


class TestHistorySyncResult:
    """Tests for HistorySyncResult dataclass."""

    def test_sync_result_creation(self):
        """Test creating a HistorySyncResult."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncResult

        result = HistorySyncResult(
            success=True,
            new_history_id=99999
        )
        assert result.success is True
        assert result.new_history_id == 99999
        assert result.events == []
        assert result.added_message_ids == []
        assert result.deleted_message_ids == []
        assert result.label_changes == []
        assert result.error is None
        assert result.pages_processed == 0

    def test_total_changes_property(self):
        """Test total_changes property calculation."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncResult

        result = HistorySyncResult(
            success=True,
            new_history_id=99999,
            added_message_ids=["msg1", "msg2"],
            deleted_message_ids=["msg3"],
            label_changes=[mock.MagicMock()]
        )
        assert result.total_changes == 4

    def test_to_dict_method(self):
        """Test to_dict serialization method."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncResult

        result = HistorySyncResult(
            success=True,
            new_history_id=99999,
            added_message_ids=["msg1"],
            deleted_message_ids=["msg2"],
            label_changes=[mock.MagicMock()],
            pages_processed=5,
            error=None
        )
        data = result.to_dict()

        assert data['success'] is True
        assert data['new_history_id'] == 99999
        assert data['added_count'] == 1
        assert data['deleted_count'] == 1
        assert data['label_changes_count'] == 1
        assert data['pages_processed'] == 5
        assert data['error'] is None


class TestHistorySyncClientInit:
    """Tests for HistorySyncClient initialization."""

    def test_init_with_service(self):
        """Test initializing with service."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        client = HistorySyncClient(mock_service)
        assert client.service == mock_service
        assert client.batch_client is None

    def test_init_with_batch_client(self):
        """Test initializing with batch client."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        mock_batch = mock.MagicMock()
        client = HistorySyncClient(mock_service, batch_client=mock_batch)
        assert client.batch_client == mock_batch

    def test_history_types_constant(self):
        """Test HISTORY_TYPES constant."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        expected_types = [
            'messageAdded',
            'messageDeleted',
            'labelAdded',
            'labelRemoved'
        ]
        assert HistorySyncClient.HISTORY_TYPES == expected_types


class TestGetBatchClient:
    """Tests for _get_batch_client method."""

    def test_get_batch_client_creates_if_none(self):
        """Test creates batch client if none exists."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        client = HistorySyncClient(mock_service)

        with mock.patch('gmail_assistant.core.fetch.history_sync.GmailBatchClient') as MockBatch:
            mock_batch = mock.MagicMock()
            MockBatch.return_value = mock_batch

            result = client._get_batch_client()

            MockBatch.assert_called_once_with(mock_service)
            assert result == mock_batch

    def test_get_batch_client_returns_existing(self):
        """Test returns existing batch client."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        mock_batch = mock.MagicMock()
        client = HistorySyncClient(mock_service, batch_client=mock_batch)

        result = client._get_batch_client()
        assert result == mock_batch


class TestGetCurrentHistoryId:
    """Tests for get_current_history_id method."""

    def test_get_history_id_success(self):
        """Test getting current history ID."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        mock_service.users().getProfile().execute.return_value = {
            'historyId': '12345'
        }

        client = HistorySyncClient(mock_service)
        result = client.get_current_history_id()

        assert result == 12345


class TestSyncFromHistory:
    """Tests for sync_from_history method."""

    def test_sync_empty_history(self):
        """Test sync with no history records."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        mock_service.users().history().list().execute.return_value = {
            'history': [],
            'historyId': '99999'
        }

        client = HistorySyncClient(mock_service)
        result = client.sync_from_history(12345)

        assert result.success is True
        assert result.added_message_ids == []
        assert result.deleted_message_ids == []

    def test_sync_with_additions(self):
        """Test sync with message additions."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        mock_service.users().history().list().execute.return_value = {
            'history': [{
                'id': '12346',
                'messagesAdded': [{
                    'message': {
                        'id': 'msg123',
                        'labelIds': ['INBOX']
                    }
                }]
            }]
        }

        client = HistorySyncClient(mock_service)
        result = client.sync_from_history(12345)

        assert result.success is True
        assert 'msg123' in result.added_message_ids

    def test_sync_with_deletions(self):
        """Test sync with message deletions."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        mock_service.users().history().list().execute.return_value = {
            'history': [{
                'id': '12346',
                'messagesDeleted': [{
                    'message': {'id': 'msg456'}
                }]
            }]
        }

        client = HistorySyncClient(mock_service)
        result = client.sync_from_history(12345)

        assert result.success is True
        assert 'msg456' in result.deleted_message_ids


class TestFetchAddedMessages:
    """Tests for fetch_added_messages method."""

    def test_fetch_empty_list_returns_empty(self):
        """Test fetching empty list returns empty."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        client = HistorySyncClient(mock_service)

        result = client.fetch_added_messages([])
        assert result == []


class TestCheckSyncRequired:
    """Tests for check_sync_required method."""

    def test_sync_required_when_behind(self):
        """Test sync required when stored ID is behind current."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        mock_service.users().getProfile().execute.return_value = {
            'historyId': '99999'
        }

        client = HistorySyncClient(mock_service)
        required, current_id = client.check_sync_required(12345)

        assert required is True
        assert current_id == 99999

    def test_sync_not_required_when_current(self):
        """Test sync not required when up to date."""
        from gmail_assistant.core.fetch.history_sync import HistorySyncClient

        mock_service = mock.MagicMock()
        mock_service.users().getProfile().execute.return_value = {
            'historyId': '12345'
        }

        client = HistorySyncClient(mock_service)
        required, current_id = client.check_sync_required(12345)

        assert required is False


class TestSyncStateManager:
    """Tests for SyncStateManager class."""

    @pytest.fixture
    def db_connection(self):
        """Create temporary database connection."""
        conn = sqlite3.connect(':memory:')
        yield conn
        conn.close()

    def test_init_creates_table(self, db_connection):
        """Test initialization creates sync_state table."""
        from gmail_assistant.core.fetch.history_sync import SyncStateManager

        manager = SyncStateManager(db_connection)

        # Verify table exists
        cursor = db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sync_state'"
        )
        assert cursor.fetchone() is not None

    def test_get_history_id_none_when_empty(self, db_connection):
        """Test get_history_id returns None when no data."""
        from gmail_assistant.core.fetch.history_sync import SyncStateManager

        manager = SyncStateManager(db_connection)
        result = manager.get_history_id('gmail')
        assert result is None

    def test_update_and_get_history_id(self, db_connection):
        """Test updating and getting history ID."""
        from gmail_assistant.core.fetch.history_sync import SyncStateManager

        manager = SyncStateManager(db_connection)
        manager.update_history_id(12345, synced_count=100)

        result = manager.get_history_id()
        assert result == 12345

    def test_update_increments_total_synced(self, db_connection):
        """Test update increments total synced count."""
        from gmail_assistant.core.fetch.history_sync import SyncStateManager

        manager = SyncStateManager(db_connection)
        manager.update_history_id(12345, synced_count=100)
        manager.update_history_id(12346, synced_count=50)

        stats = manager.get_sync_stats()
        assert stats['total_synced'] == 150

    def test_get_sync_stats_none_when_empty(self, db_connection):
        """Test get_sync_stats returns None when no data."""
        from gmail_assistant.core.fetch.history_sync import SyncStateManager

        manager = SyncStateManager(db_connection)
        result = manager.get_sync_stats()
        assert result is None

    def test_get_sync_stats_returns_dict(self, db_connection):
        """Test get_sync_stats returns expected dict."""
        from gmail_assistant.core.fetch.history_sync import SyncStateManager

        manager = SyncStateManager(db_connection)
        manager.update_history_id(12345, synced_count=100)

        stats = manager.get_sync_stats()
        assert stats['source'] == 'gmail'
        assert stats['last_history_id'] == 12345
        assert stats['total_synced'] == 100
        assert 'last_sync_at' in stats
        assert 'created_at' in stats
        assert 'updated_at' in stats

    def test_different_sources(self, db_connection):
        """Test managing different sync sources."""
        from gmail_assistant.core.fetch.history_sync import SyncStateManager

        manager = SyncStateManager(db_connection)
        manager.update_history_id(12345, source='gmail')
        manager.update_history_id(67890, source='outlook')

        gmail_id = manager.get_history_id('gmail')
        outlook_id = manager.get_history_id('outlook')

        assert gmail_id == 12345
        assert outlook_id == 67890
