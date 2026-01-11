"""
Comprehensive tests for dead_letter_queue.py module.
Tests DeadLetterQueue for failure tracking and retry management.
"""

import json
from datetime import datetime, timedelta

import pytest

from gmail_assistant.core.fetch.dead_letter_queue import (
    DeadLetterQueue,
    DeadLetterItem,
    FailureType,
)


class TestFailureType:
    """Tests for FailureType enum."""

    def test_failure_type_values(self):
        """Test all FailureType enum values exist."""
        assert FailureType.FETCH_ERROR.value == "fetch_error"
        assert FailureType.PARSE_ERROR.value == "parse_error"
        assert FailureType.SAVE_ERROR.value == "save_error"
        assert FailureType.DELETE_ERROR.value == "delete_error"
        assert FailureType.RATE_LIMIT.value == "rate_limit"
        assert FailureType.AUTH_ERROR.value == "auth_error"
        assert FailureType.NETWORK_ERROR.value == "network_error"
        assert FailureType.QUOTA_EXCEEDED.value == "quota_exceeded"
        assert FailureType.INVALID_DATA.value == "invalid_data"
        assert FailureType.UNKNOWN.value == "unknown"

    def test_failure_type_is_string_enum(self):
        """Test FailureType is a string enum."""
        for ft in FailureType:
            assert isinstance(ft.value, str)


class TestDeadLetterItem:
    """Tests for DeadLetterItem dataclass."""

    @pytest.fixture
    def sample_item(self):
        """Create a sample DeadLetterItem."""
        return DeadLetterItem(
            id=1,
            message_id="msg123",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Connection timeout",
            error_details="Stack trace here",
            attempt_count=2,
            first_failure=datetime(2024, 1, 1, 12, 0, 0),
            last_failure=datetime(2024, 1, 1, 12, 30, 0),
            next_retry=datetime(2024, 1, 1, 13, 0, 0),
            resolved=False,
            context={"source": "api"}
        )

    def test_item_creation(self, sample_item):
        """Test creating a DeadLetterItem."""
        assert sample_item.id == 1
        assert sample_item.message_id == "msg123"
        assert sample_item.failure_type == FailureType.FETCH_ERROR
        assert sample_item.attempt_count == 2
        assert sample_item.resolved is False

    def test_is_retriable(self, sample_item):
        """Test is_retriable property when retriable."""
        assert sample_item.is_retriable is True

    def test_is_retriable_resolved(self):
        """Test is_retriable is False when resolved."""
        item = DeadLetterItem(
            id=1,
            message_id="msg123",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Error",
            error_details=None,
            attempt_count=1,
            first_failure=datetime.now(),
            last_failure=datetime.now(),
            next_retry=datetime.now() + timedelta(hours=1),
            resolved=True,
            context={}
        )
        assert item.is_retriable is False

    def test_is_retriable_no_next_retry(self):
        """Test is_retriable is False when no next_retry."""
        item = DeadLetterItem(
            id=1,
            message_id="msg123",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Error",
            error_details=None,
            attempt_count=5,
            first_failure=datetime.now(),
            last_failure=datetime.now(),
            next_retry=None,  # Exhausted
            resolved=False,
            context={}
        )
        assert item.is_retriable is False

    def test_is_exhausted(self):
        """Test is_exhausted property."""
        item = DeadLetterItem(
            id=1,
            message_id="msg123",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Error",
            error_details=None,
            attempt_count=5,
            first_failure=datetime.now(),
            last_failure=datetime.now(),
            next_retry=None,
            resolved=False,
            context={}
        )
        assert item.is_exhausted is True


class TestDeadLetterQueue:
    """Tests for DeadLetterQueue class."""

    def test_dlq_init(self, tmp_path):
        """Test DeadLetterQueue initialization."""
        db_path = tmp_path / "test.db"
        dlq = DeadLetterQueue(db_path=db_path)
        assert db_path.exists()

    def test_dlq_default_params(self, tmp_path):
        """Test DLQ default parameters."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        assert dlq.max_retries == 5
        assert dlq.base_retry_delay == 300


class TestAddFailure:
    """Tests for add_failure method."""

    def test_add_failure_basic(self, tmp_path):
        """Test adding a basic failure."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        item_id = dlq.add_failure(
            message_id="msg123",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Connection timeout"
        )
        assert item_id is not None
        assert item_id > 0

    def test_add_failure_with_details(self, tmp_path):
        """Test adding failure with error details."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        item_id = dlq.add_failure(
            message_id="msg456",
            failure_type=FailureType.PARSE_ERROR,
            error_message="Invalid JSON",
            error_details="Stack trace: ..."
        )
        assert item_id is not None

    def test_add_failure_with_context(self, tmp_path):
        """Test adding failure with context."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        context = {"source": "batch_api", "batch_id": 42}
        item_id = dlq.add_failure(
            message_id="msg789",
            failure_type=FailureType.NETWORK_ERROR,
            error_message="DNS lookup failed",
            context=context
        )
        assert item_id is not None

    def test_add_failure_increments_attempts(self, tmp_path):
        """Test adding same failure increments attempt count."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        dlq.add_failure(
            message_id="msg_retry",
            failure_type=FailureType.FETCH_ERROR,
            error_message="First attempt"
        )

        dlq.add_failure(
            message_id="msg_retry",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Second attempt"
        )

        items = dlq.get_by_message_id("msg_retry")
        assert len(items) == 1
        assert items[0].attempt_count == 2

    def test_add_failure_different_types(self, tmp_path):
        """Test same message with different failure types creates separate entries."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        dlq.add_failure(
            message_id="msg_multi",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Fetch failed"
        )

        dlq.add_failure(
            message_id="msg_multi",
            failure_type=FailureType.PARSE_ERROR,
            error_message="Parse failed"
        )

        items = dlq.get_by_message_id("msg_multi")
        assert len(items) == 2


class TestRetryCalculation:
    """Tests for retry time calculation."""

    def test_calculate_next_retry_first_attempt(self, tmp_path):
        """Test first attempt retry delay."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(
            db_path=db_path,
            max_retries=5,
            base_retry_delay=300  # 5 minutes
        )
        next_retry = dlq._calculate_next_retry(1)
        expected = datetime.now() + timedelta(seconds=300)  # 5 min
        assert abs((next_retry - expected).total_seconds()) < 2

    def test_calculate_next_retry_exponential(self, tmp_path):
        """Test exponential backoff calculation."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(
            db_path=db_path,
            max_retries=5,
            base_retry_delay=300  # 5 minutes
        )
        # Attempt 2: 10 min (300 * 2)
        retry_2 = dlq._calculate_next_retry(2)
        expected_2 = datetime.now() + timedelta(seconds=600)
        assert abs((retry_2 - expected_2).total_seconds()) < 2

        # Attempt 3: 20 min (300 * 4)
        retry_3 = dlq._calculate_next_retry(3)
        expected_3 = datetime.now() + timedelta(seconds=1200)
        assert abs((retry_3 - expected_3).total_seconds()) < 2

    def test_calculate_next_retry_max_exhausted(self, tmp_path):
        """Test retry returns None when max retries exceeded."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(
            db_path=db_path,
            max_retries=5,
            base_retry_delay=300  # 5 minutes
        )
        next_retry = dlq._calculate_next_retry(5)  # At max
        assert next_retry is None


class TestGetReadyForRetry:
    """Tests for get_ready_for_retry method."""

    def test_get_ready_for_retry_empty(self, tmp_path):
        """Test get_ready_for_retry with no items."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(
            db_path=db_path,
            base_retry_delay=1  # 1 second for fast tests
        )
        items = dlq.get_ready_for_retry()
        assert items == []

    def test_get_ready_for_retry_not_ready(self, tmp_path):
        """Test get_ready_for_retry when items not yet ready."""
        db_path = tmp_path / "test_dlq.db"
        # Use long delay so items aren't ready
        dlq = DeadLetterQueue(
            db_path=db_path,
            base_retry_delay=3600  # 1 hour
        )
        dlq.add_failure(
            message_id="msg_future",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Error"
        )

        items = dlq.get_ready_for_retry()
        assert len(items) == 0


class TestMarkResolved:
    """Tests for mark_resolved methods."""

    def test_mark_resolved(self, tmp_path):
        """Test marking item as resolved."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        item_id = dlq.add_failure(
            message_id="msg_resolve",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Error"
        )

        dlq.mark_resolved(item_id)

        items = dlq.get_by_message_id("msg_resolve")
        assert len(items) == 1
        assert items[0].resolved is True

    def test_mark_resolved_with_reason(self, tmp_path):
        """Test marking resolved with reason."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        item_id = dlq.add_failure(
            message_id="msg_reason",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Error"
        )

        dlq.mark_resolved(item_id, reason="Manually fixed")

        items = dlq.get_by_message_id("msg_reason")
        assert items[0].resolved is True

    def test_mark_resolved_by_message(self, tmp_path):
        """Test marking all failures for message as resolved."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        dlq.add_failure(
            message_id="msg_multi_resolve",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Fetch error"
        )
        dlq.add_failure(
            message_id="msg_multi_resolve",
            failure_type=FailureType.PARSE_ERROR,
            error_message="Parse error"
        )

        count = dlq.mark_resolved_by_message("msg_multi_resolve")
        assert count == 2


class TestGetByFilters:
    """Tests for getting items by various filters."""

    def test_get_by_message_id(self, tmp_path):
        """Test getting items by message ID."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        dlq.add_failure(
            message_id="specific_msg",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Error"
        )

        items = dlq.get_by_message_id("specific_msg")
        assert len(items) == 1
        assert items[0].message_id == "specific_msg"

    def test_get_by_message_id_not_found(self, tmp_path):
        """Test getting by nonexistent message ID returns empty list."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        items = dlq.get_by_message_id("nonexistent")
        assert items == []

    def test_get_by_failure_type(self, tmp_path):
        """Test getting items by failure type."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        dlq.add_failure(
            message_id="msg1",
            failure_type=FailureType.RATE_LIMIT,
            error_message="Rate limit"
        )
        dlq.add_failure(
            message_id="msg2",
            failure_type=FailureType.RATE_LIMIT,
            error_message="Rate limit"
        )
        dlq.add_failure(
            message_id="msg3",
            failure_type=FailureType.AUTH_ERROR,
            error_message="Auth error"
        )

        items = dlq.get_by_failure_type(FailureType.RATE_LIMIT)
        assert len(items) == 2


class TestGetStats:
    """Tests for get_stats method."""

    def test_get_stats_empty(self, tmp_path):
        """Test getting stats with empty DLQ."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        stats = dlq.get_stats()
        assert stats["total_pending"] == 0
        assert stats["ready_for_retry"] == 0
        assert stats["retries_exhausted"] == 0

    def test_get_stats(self, tmp_path):
        """Test getting DLQ statistics."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        dlq.add_failure(
            message_id="msg1",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Error 1"
        )
        dlq.add_failure(
            message_id="msg2",
            failure_type=FailureType.PARSE_ERROR,
            error_message="Error 2"
        )

        stats = dlq.get_stats()
        assert stats["total_pending"] == 2
        assert "fetch_error" in stats["by_failure_type"]
        assert "parse_error" in stats["by_failure_type"]


class TestGetExhausted:
    """Tests for get_exhausted method."""

    def test_get_exhausted_empty(self, tmp_path):
        """Test get_exhausted with no exhausted items."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(
            db_path=db_path,
            max_retries=2,
            base_retry_delay=1
        )
        items = dlq.get_exhausted()
        assert items == []

    def test_get_exhausted(self, tmp_path):
        """Test getting exhausted items after max retries."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(
            db_path=db_path,
            max_retries=2,
            base_retry_delay=1
        )
        # Add failure 3 times to exhaust retries (max_retries=2)
        for i in range(3):
            dlq.add_failure(
                message_id="msg_exhaust",
                failure_type=FailureType.FETCH_ERROR,
                error_message=f"Attempt {i+1}"
            )

        items = dlq.get_exhausted()
        assert len(items) == 1
        assert items[0].message_id == "msg_exhaust"


class TestCleanupResolved:
    """Tests for cleanup_resolved method."""

    def test_cleanup_resolved(self, tmp_path):
        """Test cleaning up resolved items."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        item_id = dlq.add_failure(
            message_id="msg_cleanup",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Error"
        )
        dlq.mark_resolved(item_id)

        # Cleanup with 0 days (remove all)
        count = dlq.cleanup_resolved(older_than_days=0)
        assert count >= 1


class TestResetForRetry:
    """Tests for reset_for_retry method."""

    def test_reset_for_retry(self, tmp_path):
        """Test resetting exhausted item for retry."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(
            db_path=db_path,
            max_retries=2,
            base_retry_delay=1
        )
        # Exhaust retries
        for i in range(3):
            dlq.add_failure(
                message_id="msg_reset",
                failure_type=FailureType.FETCH_ERROR,
                error_message=f"Attempt {i+1}"
            )

        exhausted = dlq.get_exhausted()
        assert len(exhausted) == 1

        result = dlq.reset_for_retry(exhausted[0].id)
        assert result is True

        # Should no longer be exhausted
        new_exhausted = dlq.get_exhausted()
        assert len(new_exhausted) == 0

    def test_reset_for_retry_nonexistent(self, tmp_path):
        """Test reset on nonexistent item returns False."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(
            db_path=db_path,
            max_retries=2,
            base_retry_delay=1
        )
        result = dlq.reset_for_retry(9999)
        assert result is False


class TestExportToJson:
    """Tests for export_to_json method."""

    def test_export_to_json(self, tmp_path):
        """Test exporting DLQ to JSON file."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        dlq.add_failure(
            message_id="msg_export",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Export test"
        )

        output_file = tmp_path / "export.json"
        count = dlq.export_to_json(output_file)

        assert count == 1
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)
        assert data["total_items"] == 1
        assert len(data["items"]) == 1

    def test_export_to_json_include_resolved(self, tmp_path):
        """Test exporting including resolved items."""
        db_path = tmp_path / "test_dlq.db"
        dlq = DeadLetterQueue(db_path=db_path)
        item_id = dlq.add_failure(
            message_id="msg_resolved",
            failure_type=FailureType.FETCH_ERROR,
            error_message="Resolved export test"
        )
        dlq.mark_resolved(item_id)

        output_file = tmp_path / "export_all.json"
        count = dlq.export_to_json(output_file, include_resolved=True)

        assert count == 1
