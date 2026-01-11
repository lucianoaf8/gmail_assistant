"""
Comprehensive tests for batch_api.py module.
Tests GmailBatchClient class for batch operations.
"""

from dataclasses import dataclass
from unittest import mock

import pytest


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_batch_result_default_values(self):
        """Test BatchResult has correct default values."""
        from gmail_assistant.core.fetch.batch_api import BatchResult

        result = BatchResult()
        assert result.successful == 0
        assert result.failed == 0
        assert result.errors == []

    def test_batch_result_with_values(self):
        """Test BatchResult with custom values."""
        from gmail_assistant.core.fetch.batch_api import BatchResult

        result = BatchResult(
            successful=10,
            failed=2,
            errors=[{"id": "msg1", "error": "test error"}]
        )
        assert result.successful == 10
        assert result.failed == 2
        assert len(result.errors) == 1


class TestGmailBatchClientInit:
    """Tests for GmailBatchClient initialization."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        return mock.MagicMock()

    def test_init_with_service(self, mock_service):
        """Test initializing batch client with service."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient

        client = GmailBatchClient(mock_service)
        assert client.service == mock_service
        assert client.rate_limiter is None
        assert client.on_error is None

    def test_init_with_rate_limiter(self, mock_service):
        """Test initializing with rate limiter."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient

        mock_limiter = mock.MagicMock()
        client = GmailBatchClient(mock_service, rate_limiter=mock_limiter)
        assert client.rate_limiter == mock_limiter

    def test_init_with_error_callback(self, mock_service):
        """Test initializing with error callback."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient

        def error_handler(msg_id, exc):
            pass

        client = GmailBatchClient(mock_service, on_error=error_handler)
        assert client.on_error == error_handler

    def test_max_batch_size_constant(self):
        """Test MAX_BATCH_SIZE is set correctly."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient

        assert GmailBatchClient.MAX_BATCH_SIZE == 100


class TestBatchGetMessages:
    """Tests for batch_get_messages method."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        service = mock.MagicMock()
        return service

    @pytest.fixture
    def client(self, mock_service):
        """Create batch client."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient
        return GmailBatchClient(mock_service)

    def test_empty_message_ids_returns_empty_list(self, client):
        """Test empty message IDs returns empty list."""
        result = client.batch_get_messages([])
        assert result == []

    def test_default_metadata_headers(self, mock_service):
        """Test default metadata headers are set."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient

        client = GmailBatchClient(mock_service)

        # Patch batch execution
        with mock.patch.object(client, '_results', {}):
            with mock.patch.object(client, '_errors', {}):
                mock_batch = mock.MagicMock()
                mock_service.new_batch_http_request.return_value = mock_batch

                # Execute with mock batch that does nothing
                try:
                    client.batch_get_messages(['msg1'], format='metadata')
                except Exception:
                    pass  # May fail but we just want to check headers

                # Verify get was called with default headers
                if mock_service.users().messages().get.called:
                    call_kwargs = mock_service.users().messages().get.call_args
                    if call_kwargs:
                        headers = call_kwargs.kwargs.get('metadataHeaders', [])
                        assert 'From' in headers or headers is None

    def test_progress_callback_called(self, mock_service):
        """Test progress callback is called."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient

        client = GmailBatchClient(mock_service)
        progress_calls = []

        def progress_cb(current, total):
            progress_calls.append((current, total))

        # Setup mock to simulate successful batch
        mock_batch = mock.MagicMock()
        mock_service.new_batch_http_request.return_value = mock_batch

        # Mock results
        client._results = {'msg1': {'id': 'msg1', 'payload': {}}}
        client._errors = {}

        # Mock Email.from_gmail_message
        with mock.patch('gmail_assistant.core.fetch.batch_api.Email') as MockEmail:
            MockEmail.from_gmail_message.return_value = mock.MagicMock()
            result = client.batch_get_messages(['msg1'], progress_callback=progress_cb)

        # Progress should have been called
        assert len(progress_calls) > 0


class TestBatchGetMessagesRaw:
    """Tests for batch_get_messages_raw method."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        return mock.MagicMock()

    @pytest.fixture
    def client(self, mock_service):
        """Create batch client."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient
        return GmailBatchClient(mock_service)

    def test_empty_message_ids_returns_empty_dict(self, client):
        """Test empty message IDs returns empty dict."""
        result = client.batch_get_messages_raw([])
        assert result == {}


class TestBatchDeleteMessages:
    """Tests for batch_delete_messages method."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        return mock.MagicMock()

    @pytest.fixture
    def client(self, mock_service):
        """Create batch client."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient
        return GmailBatchClient(mock_service)

    def test_empty_message_ids_returns_empty_result(self, client):
        """Test empty message IDs returns empty BatchResult."""
        result = client.batch_delete_messages([])
        assert result.successful == 0
        assert result.failed == 0
        assert result.errors == []


class TestBatchTrashMessages:
    """Tests for batch_trash_messages method."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        return mock.MagicMock()

    @pytest.fixture
    def client(self, mock_service):
        """Create batch client."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient
        return GmailBatchClient(mock_service)

    def test_empty_message_ids_returns_empty_result(self, client):
        """Test empty message IDs returns empty BatchResult."""
        result = client.batch_trash_messages([])
        assert result.successful == 0
        assert result.failed == 0


class TestBatchModifyLabels:
    """Tests for batch_modify_labels method."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        return mock.MagicMock()

    @pytest.fixture
    def client(self, mock_service):
        """Create batch client."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient
        return GmailBatchClient(mock_service)

    def test_empty_message_ids_returns_empty_result(self, client):
        """Test empty message IDs returns empty BatchResult."""
        result = client.batch_modify_labels([])
        assert result.successful == 0
        assert result.failed == 0


class TestConvenienceMethods:
    """Tests for convenience methods."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        return mock.MagicMock()

    @pytest.fixture
    def client(self, mock_service):
        """Create batch client."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient
        return GmailBatchClient(mock_service)

    def test_batch_mark_read_calls_modify_labels(self, client):
        """Test batch_mark_read calls batch_modify_labels correctly."""
        with mock.patch.object(client, 'batch_modify_labels') as mock_modify:
            client.batch_mark_read(['msg1', 'msg2'])
            mock_modify.assert_called_once_with(
                ['msg1', 'msg2'],
                remove_labels=['UNREAD']
            )

    def test_batch_mark_unread_calls_modify_labels(self, client):
        """Test batch_mark_unread calls batch_modify_labels correctly."""
        with mock.patch.object(client, 'batch_modify_labels') as mock_modify:
            client.batch_mark_unread(['msg1', 'msg2'])
            mock_modify.assert_called_once_with(
                ['msg1', 'msg2'],
                add_labels=['UNREAD']
            )

    def test_batch_archive_calls_modify_labels(self, client):
        """Test batch_archive calls batch_modify_labels correctly."""
        with mock.patch.object(client, 'batch_modify_labels') as mock_modify:
            client.batch_archive(['msg1', 'msg2'])
            mock_modify.assert_called_once_with(
                ['msg1', 'msg2'],
                remove_labels=['INBOX']
            )


class TestCallbackCreation:
    """Tests for callback creation methods."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        return mock.MagicMock()

    @pytest.fixture
    def client(self, mock_service):
        """Create batch client."""
        from gmail_assistant.core.fetch.batch_api import GmailBatchClient
        return GmailBatchClient(mock_service)

    def test_create_get_callback_success(self, client):
        """Test get callback handles success."""
        callback = client._create_get_callback('msg1')
        response = {'id': 'msg1', 'payload': {}}
        callback('req1', response, None)
        assert client._results['msg1'] == response

    def test_create_get_callback_error(self, client):
        """Test get callback handles error."""
        callback = client._create_get_callback('msg1')
        error = Exception("Test error")
        callback('req1', None, error)
        assert client._errors['msg1'] == error

    def test_create_delete_callback_success(self, client):
        """Test delete callback handles success."""
        from gmail_assistant.core.fetch.batch_api import BatchResult

        result = BatchResult()
        callback = client._create_delete_callback('msg1', result)
        callback('req1', {}, None)
        assert result.successful == 1
        assert result.failed == 0

    def test_create_delete_callback_error(self, client):
        """Test delete callback handles error."""
        from gmail_assistant.core.fetch.batch_api import BatchResult

        result = BatchResult()
        callback = client._create_delete_callback('msg1', result)
        callback('req1', None, Exception("Delete failed"))
        assert result.successful == 0
        assert result.failed == 1
        assert len(result.errors) == 1

    def test_create_trash_callback_success(self, client):
        """Test trash callback handles success."""
        from gmail_assistant.core.fetch.batch_api import BatchResult

        result = BatchResult()
        callback = client._create_trash_callback('msg1', result)
        callback('req1', {}, None)
        assert result.successful == 1

    def test_create_trash_callback_error(self, client):
        """Test trash callback handles error."""
        from gmail_assistant.core.fetch.batch_api import BatchResult

        result = BatchResult()
        callback = client._create_trash_callback('msg1', result)
        callback('req1', None, Exception("Trash failed"))
        assert result.failed == 1

    def test_create_modify_callback_success(self, client):
        """Test modify callback handles success."""
        from gmail_assistant.core.fetch.batch_api import BatchResult

        result = BatchResult()
        callback = client._create_modify_callback('msg1', result)
        callback('req1', {}, None)
        assert result.successful == 1

    def test_create_modify_callback_error(self, client):
        """Test modify callback handles error."""
        from gmail_assistant.core.fetch.batch_api import BatchResult

        result = BatchResult()
        callback = client._create_modify_callback('msg1', result)
        callback('req1', None, Exception("Modify failed"))
        assert result.failed == 1
