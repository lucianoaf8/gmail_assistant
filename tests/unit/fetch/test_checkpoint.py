"""
Comprehensive tests for checkpoint.py module.
Tests CheckpointManager for sync operation persistence.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from gmail_assistant.core.fetch.checkpoint import (
    CheckpointManager,
    SyncCheckpoint,
    SyncState,
)


class TestSyncState:
    """Tests for SyncState enum."""

    def test_sync_state_values(self):
        """Test all SyncState enum values exist."""
        assert SyncState.PENDING.value == "pending"
        assert SyncState.IN_PROGRESS.value == "in_progress"
        assert SyncState.COMPLETED.value == "completed"
        assert SyncState.FAILED.value == "failed"
        assert SyncState.INTERRUPTED.value == "interrupted"

    def test_sync_state_is_string_enum(self):
        """Test SyncState values are strings."""
        for state in SyncState:
            assert isinstance(state.value, str)


class TestSyncCheckpoint:
    """Tests for SyncCheckpoint dataclass."""

    @pytest.fixture
    def sample_checkpoint(self):
        """Create a sample checkpoint."""
        return SyncCheckpoint(
            sync_id="sync_20240101_120000_1234",
            state=SyncState.IN_PROGRESS,
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 30, 0),
            total_messages=100,
            processed_messages=50,
            query="is:unread",
            output_directory="/backup"
        )

    def test_checkpoint_creation(self, sample_checkpoint):
        """Test creating a SyncCheckpoint."""
        assert sample_checkpoint.sync_id == "sync_20240101_120000_1234"
        assert sample_checkpoint.state == SyncState.IN_PROGRESS
        assert sample_checkpoint.total_messages == 100
        assert sample_checkpoint.processed_messages == 50

    def test_progress_percent_calculation(self, sample_checkpoint):
        """Test progress percentage calculation."""
        assert sample_checkpoint.progress_percent == 50.0

    def test_progress_percent_zero_total(self):
        """Test progress percentage with zero total messages."""
        checkpoint = SyncCheckpoint(
            sync_id="test",
            state=SyncState.PENDING,
            started_at=datetime.now(),
            updated_at=datetime.now(),
            total_messages=0
        )
        assert checkpoint.progress_percent == 0.0

    def test_is_resumable_in_progress(self):
        """Test is_resumable for in_progress state."""
        checkpoint = SyncCheckpoint(
            sync_id="test",
            state=SyncState.IN_PROGRESS,
            started_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert checkpoint.is_resumable is True

    def test_is_resumable_interrupted(self):
        """Test is_resumable for interrupted state."""
        checkpoint = SyncCheckpoint(
            sync_id="test",
            state=SyncState.INTERRUPTED,
            started_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert checkpoint.is_resumable is True

    def test_is_resumable_completed(self):
        """Test is_resumable for completed state."""
        checkpoint = SyncCheckpoint(
            sync_id="test",
            state=SyncState.COMPLETED,
            started_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert checkpoint.is_resumable is False

    def test_is_resumable_failed(self):
        """Test is_resumable for failed state."""
        checkpoint = SyncCheckpoint(
            sync_id="test",
            state=SyncState.FAILED,
            started_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert checkpoint.is_resumable is False

    def test_to_dict(self, sample_checkpoint):
        """Test checkpoint to_dict serialization."""
        data = sample_checkpoint.to_dict()
        assert data["sync_id"] == "sync_20240101_120000_1234"
        assert data["state"] == "in_progress"
        assert data["total_messages"] == 100
        assert "started_at" in data
        assert "updated_at" in data

    def test_from_dict(self):
        """Test checkpoint from_dict deserialization."""
        data = {
            "sync_id": "test_sync",
            "state": "pending",
            "started_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:30:00",
            "total_messages": 50,
            "processed_messages": 10,
            "failed_messages": 0,
            "last_message_id": None,
            "last_page_token": None,
            "history_id": None,
            "query": "is:unread",
            "output_directory": "/backup",
            "failed_ids": [],
            "error_message": None,
            "metadata": {}
        }
        checkpoint = SyncCheckpoint.from_dict(data)
        assert checkpoint.sync_id == "test_sync"
        assert checkpoint.state == SyncState.PENDING
        assert checkpoint.total_messages == 50


class TestCheckpointManager:
    """Tests for CheckpointManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create CheckpointManager instance."""
        return CheckpointManager(temp_dir)

    def test_manager_init(self, temp_dir):
        """Test CheckpointManager initialization."""
        manager = CheckpointManager(temp_dir)
        assert manager.checkpoint_dir == temp_dir
        assert temp_dir.exists()

    def test_manager_default_dir(self):
        """Test CheckpointManager default directory."""
        manager = CheckpointManager()
        assert manager.checkpoint_dir == Path("data/checkpoints")

    def test_create_checkpoint(self, manager):
        """Test creating a new checkpoint."""
        checkpoint = manager.create_checkpoint(
            query="is:unread",
            output_directory="/backup",
            total_messages=100
        )
        assert checkpoint.sync_id.startswith("sync_")
        assert checkpoint.state == SyncState.PENDING
        assert checkpoint.query == "is:unread"

    def test_create_checkpoint_with_metadata(self, manager):
        """Test creating checkpoint with metadata."""
        metadata = {"source": "api", "version": "1.0"}
        checkpoint = manager.create_checkpoint(
            query="is:unread",
            output_directory="/backup",
            metadata=metadata
        )
        assert checkpoint.metadata == metadata

    def test_save_and_load_checkpoint(self, manager):
        """Test saving and loading checkpoint."""
        checkpoint = manager.create_checkpoint(
            query="test",
            output_directory="/test"
        )

        loaded = manager.load_checkpoint(checkpoint.sync_id)
        assert loaded is not None
        assert loaded.sync_id == checkpoint.sync_id
        assert loaded.query == "test"

    def test_load_nonexistent_checkpoint(self, manager):
        """Test loading nonexistent checkpoint returns None."""
        result = manager.load_checkpoint("nonexistent_sync")
        assert result is None


class TestCheckpointProgress:
    """Tests for checkpoint progress updates."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create CheckpointManager instance."""
        return CheckpointManager(temp_dir)

    def test_update_progress(self, manager):
        """Test updating checkpoint progress."""
        checkpoint = manager.create_checkpoint(
            query="test",
            output_directory="/test",
            total_messages=100
        )

        manager.update_progress(checkpoint, processed=50, last_message_id="msg123")

        # Reload and verify
        loaded = manager.load_checkpoint(checkpoint.sync_id)
        assert loaded.processed_messages == 50
        assert loaded.last_message_id == "msg123"
        assert loaded.state == SyncState.IN_PROGRESS

    def test_update_progress_with_page_token(self, manager):
        """Test updating progress with page token."""
        checkpoint = manager.create_checkpoint(
            query="test",
            output_directory="/test"
        )

        manager.update_progress(
            checkpoint,
            processed=25,
            last_page_token="token123"
        )

        loaded = manager.load_checkpoint(checkpoint.sync_id)
        assert loaded.last_page_token == "token123"

    def test_update_progress_with_failed_ids(self, manager):
        """Test updating progress with failed message IDs."""
        checkpoint = manager.create_checkpoint(
            query="test",
            output_directory="/test"
        )

        manager.update_progress(
            checkpoint,
            processed=10,
            failed_ids=["fail1", "fail2"]
        )

        loaded = manager.load_checkpoint(checkpoint.sync_id)
        assert "fail1" in loaded.failed_ids
        assert "fail2" in loaded.failed_ids
        assert loaded.failed_messages == 2


class TestCheckpointCompletion:
    """Tests for checkpoint completion states."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create CheckpointManager instance."""
        return CheckpointManager(temp_dir)

    def test_mark_completed(self, manager):
        """Test marking checkpoint as completed."""
        checkpoint = manager.create_checkpoint(
            query="test",
            output_directory="/test"
        )

        manager.mark_completed(checkpoint, history_id=12345)

        loaded = manager.load_checkpoint(checkpoint.sync_id)
        assert loaded.state == SyncState.COMPLETED
        assert loaded.history_id == 12345

    def test_mark_failed(self, manager):
        """Test marking checkpoint as failed."""
        checkpoint = manager.create_checkpoint(
            query="test",
            output_directory="/test"
        )

        manager.mark_failed(checkpoint, error="Test error")

        loaded = manager.load_checkpoint(checkpoint.sync_id)
        assert loaded.state == SyncState.FAILED
        assert loaded.error_message == "Test error"

    def test_mark_interrupted(self, manager):
        """Test marking checkpoint as interrupted."""
        checkpoint = manager.create_checkpoint(
            query="test",
            output_directory="/test"
        )

        manager.mark_interrupted(checkpoint)

        loaded = manager.load_checkpoint(checkpoint.sync_id)
        assert loaded.state == SyncState.INTERRUPTED


class TestCheckpointListing:
    """Tests for listing and querying checkpoints."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create CheckpointManager instance."""
        return CheckpointManager(temp_dir)

    def test_list_checkpoints_empty(self, manager):
        """Test listing checkpoints when none exist."""
        result = manager.list_checkpoints()
        assert result == []

    def test_list_checkpoints(self, manager):
        """Test listing all checkpoints."""
        manager.create_checkpoint(query="test1", output_directory="/test1")
        manager.create_checkpoint(query="test2", output_directory="/test2")

        result = manager.list_checkpoints()
        assert len(result) == 2

    def test_list_checkpoints_by_state(self, manager):
        """Test listing checkpoints filtered by state."""
        cp1 = manager.create_checkpoint(query="test1", output_directory="/test1")
        cp2 = manager.create_checkpoint(query="test2", output_directory="/test2")

        manager.mark_completed(cp1)

        result = manager.list_checkpoints(state=SyncState.COMPLETED)
        assert len(result) == 1
        assert result[0].state == SyncState.COMPLETED

    def test_get_latest_checkpoint(self, manager):
        """Test getting most recent checkpoint."""
        manager.create_checkpoint(query="old", output_directory="/old")
        import time
        time.sleep(0.01)
        manager.create_checkpoint(query="new", output_directory="/new")

        # All are PENDING, so not resumable by default
        result = manager.get_latest_checkpoint(resumable_only=False)
        assert result is not None
        assert result.query == "new"

    def test_get_latest_checkpoint_resumable_only(self, manager):
        """Test getting latest resumable checkpoint."""
        cp1 = manager.create_checkpoint(query="test1", output_directory="/test1")
        manager.update_progress(cp1, processed=10)  # This sets it to IN_PROGRESS

        result = manager.get_latest_checkpoint(resumable_only=True)
        assert result is not None
        assert result.state == SyncState.IN_PROGRESS

    def test_get_latest_checkpoint_by_query(self, manager):
        """Test getting latest checkpoint filtered by query."""
        manager.create_checkpoint(query="query_a", output_directory="/a")
        manager.create_checkpoint(query="query_b", output_directory="/b")

        result = manager.get_latest_checkpoint(
            query="query_a",
            resumable_only=False
        )
        assert result is not None
        assert result.query == "query_a"


class TestCheckpointResumeInfo:
    """Tests for checkpoint resume information."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create CheckpointManager instance."""
        return CheckpointManager(temp_dir)

    def test_get_resume_info(self, manager):
        """Test getting resume information."""
        checkpoint = manager.create_checkpoint(
            query="is:unread",
            output_directory="/backup"
        )
        manager.update_progress(
            checkpoint,
            processed=50,
            last_message_id="msg123",
            last_page_token="token456"
        )

        info = manager.get_resume_info(checkpoint)

        assert info["sync_id"] == checkpoint.sync_id
        assert info["query"] == "is:unread"
        assert info["skip_count"] == 50
        assert info["last_message_id"] == "msg123"
        assert info["last_page_token"] == "token456"


class TestCheckpointCleanup:
    """Tests for checkpoint cleanup functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create CheckpointManager instance."""
        return CheckpointManager(temp_dir)

    def test_delete_checkpoint(self, manager):
        """Test deleting a checkpoint."""
        checkpoint = manager.create_checkpoint(
            query="test",
            output_directory="/test"
        )

        result = manager.delete_checkpoint(checkpoint.sync_id)
        assert result is True

        # Verify deleted
        loaded = manager.load_checkpoint(checkpoint.sync_id)
        assert loaded is None

    def test_delete_nonexistent_checkpoint(self, manager):
        """Test deleting nonexistent checkpoint returns False."""
        result = manager.delete_checkpoint("nonexistent")
        assert result is False

    def test_cleanup_old_checkpoints(self, manager):
        """Test cleaning up old checkpoints."""
        # Create completed checkpoints
        for i in range(8):
            cp = manager.create_checkpoint(
                query=f"test{i}",
                output_directory=f"/test{i}"
            )
            manager.mark_completed(cp)

        # Cleanup keeping only 5
        removed = manager.cleanup_old_checkpoints(keep_completed=5)
        assert removed == 3

        remaining = manager.list_checkpoints(state=SyncState.COMPLETED)
        assert len(remaining) == 5


class TestCheckpointStats:
    """Tests for checkpoint statistics."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create CheckpointManager instance."""
        return CheckpointManager(temp_dir)

    def test_get_stats_empty(self, manager):
        """Test getting stats with no checkpoints."""
        stats = manager.get_stats()
        assert stats["total"] == 0
        assert stats["resumable"] == 0

    def test_get_stats(self, manager):
        """Test getting checkpoint statistics."""
        cp1 = manager.create_checkpoint(query="test1", output_directory="/test1")
        cp2 = manager.create_checkpoint(query="test2", output_directory="/test2")

        manager.mark_completed(cp1)
        manager.update_progress(cp2, processed=10)

        stats = manager.get_stats()
        assert stats["total"] == 2
        assert stats["resumable"] == 1
        assert "completed" in stats["by_state"]
        assert "in_progress" in stats["by_state"]
