"""
Checkpoint persistence for incremental sync operations.
Enables resume capability after interruptions.

Usage:
    manager = CheckpointManager()
    checkpoint = manager.create_checkpoint(query="after:2024/01/01")

    # During sync
    manager.update_progress(checkpoint, processed=50, last_message_id="abc123")

    # On interruption
    manager.mark_interrupted(checkpoint)

    # On resume
    existing = manager.get_latest_checkpoint()
    if existing:
        resume_info = manager.get_resume_info(existing)
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SyncState(str, Enum):
    """Sync operation states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass
class SyncCheckpoint:
    """
    Checkpoint data for sync operations.

    Persists:
    - Current sync progress
    - Last successful message ID
    - Gmail history ID for incremental sync
    - Retry information for failed items
    """
    sync_id: str
    state: SyncState
    started_at: datetime
    updated_at: datetime

    # Progress tracking
    total_messages: int = 0
    processed_messages: int = 0
    failed_messages: int = 0

    # Resume information
    last_message_id: str | None = None
    last_page_token: str | None = None
    history_id: int | None = None

    # Query context
    query: str = ""
    output_directory: str = ""

    # Failed items for retry
    failed_ids: list[str] = field(default_factory=list)

    # Metadata
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.total_messages == 0:
            return 0.0
        return (self.processed_messages / self.total_messages) * 100

    @property
    def is_resumable(self) -> bool:
        """Check if checkpoint can be resumed."""
        return self.state in (SyncState.IN_PROGRESS, SyncState.INTERRUPTED)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['state'] = self.state.value
        data['started_at'] = self.started_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'SyncCheckpoint':
        """Create from dictionary."""
        data = data.copy()
        data['state'] = SyncState(data['state'])
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class CheckpointManager:
    """
    Manages sync checkpoints for failure recovery.

    Features:
    - Atomic writes (write to temp, then rename)
    - Automatic cleanup of old checkpoints
    - Multiple concurrent syncs support
    - Query-based checkpoint lookup
    """

    DEFAULT_DIR = Path("data/checkpoints")
    MAX_CHECKPOINTS = 10  # Keep last N checkpoints per type

    def __init__(self, checkpoint_dir: Path | None = None):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint files (default: data/checkpoints)
        """
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else self.DEFAULT_DIR
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Checkpoint directory: {self.checkpoint_dir}")

    def create_checkpoint(
        self,
        query: str,
        output_directory: str,
        total_messages: int = 0,
        metadata: dict[str, Any] | None = None
    ) -> SyncCheckpoint:
        """
        Create new sync checkpoint.

        Args:
            query: Gmail search query
            output_directory: Output directory for emails
            total_messages: Expected total messages (0 if unknown)
            metadata: Additional metadata to store

        Returns:
            New SyncCheckpoint instance
        """
        now = datetime.now()
        sync_id = f"sync_{now.strftime('%Y%m%d_%H%M%S')}_{abs(hash(query)) % 10000:04d}"

        checkpoint = SyncCheckpoint(
            sync_id=sync_id,
            state=SyncState.PENDING,
            started_at=now,
            updated_at=now,
            query=query,
            output_directory=output_directory,
            total_messages=total_messages,
            metadata=metadata or {}
        )

        self.save_checkpoint(checkpoint)
        logger.info(f"Created checkpoint: {sync_id}")
        return checkpoint

    def save_checkpoint(self, checkpoint: SyncCheckpoint) -> None:
        """
        Save checkpoint atomically.

        Uses temp file + rename pattern to prevent corruption.
        """
        checkpoint.updated_at = datetime.now()
        filepath = self.checkpoint_dir / f"{checkpoint.sync_id}.json"
        temp_filepath = filepath.with_suffix('.tmp')

        try:
            # Write to temp file first
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(checkpoint.to_dict(), f, indent=2)

            # Atomic rename (on POSIX systems)
            temp_filepath.replace(filepath)
            logger.debug(f"Saved checkpoint: {checkpoint.sync_id}")

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            if temp_filepath.exists():
                temp_filepath.unlink()
            raise

    def load_checkpoint(self, sync_id: str) -> SyncCheckpoint | None:
        """
        Load checkpoint by ID.

        Args:
            sync_id: Checkpoint identifier

        Returns:
            SyncCheckpoint or None if not found
        """
        filepath = self.checkpoint_dir / f"{sync_id}.json"

        if not filepath.exists():
            return None

        try:
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)
            return SyncCheckpoint.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load checkpoint {sync_id}: {e}")
            return None

    def get_latest_checkpoint(
        self,
        query: str | None = None,
        resumable_only: bool = True
    ) -> SyncCheckpoint | None:
        """
        Get most recent checkpoint.

        Args:
            query: Filter by query string (optional)
            resumable_only: Only return resumable checkpoints

        Returns:
            Most recent matching checkpoint or None
        """
        checkpoints = self.list_checkpoints()

        # Filter by query if specified
        if query:
            checkpoints = [c for c in checkpoints if c.query == query]

        # Filter for resumable states
        if resumable_only:
            checkpoints = [c for c in checkpoints if c.is_resumable]

        if not checkpoints:
            return None

        return max(checkpoints, key=lambda c: c.updated_at)

    def list_checkpoints(
        self,
        state: SyncState | None = None
    ) -> list[SyncCheckpoint]:
        """
        List all checkpoints.

        Args:
            state: Filter by state (optional)

        Returns:
            List of checkpoints sorted by updated_at descending
        """
        checkpoints = []

        for filepath in self.checkpoint_dir.glob("sync_*.json"):
            checkpoint = self.load_checkpoint(filepath.stem)
            if checkpoint:
                if state is None or checkpoint.state == state:
                    checkpoints.append(checkpoint)

        return sorted(checkpoints, key=lambda c: c.updated_at, reverse=True)

    def update_progress(
        self,
        checkpoint: SyncCheckpoint,
        processed: int,
        last_message_id: str | None = None,
        last_page_token: str | None = None,
        failed_ids: list[str] | None = None
    ) -> None:
        """
        Update checkpoint progress.

        Args:
            checkpoint: Checkpoint to update
            processed: Number of messages processed
            last_message_id: Last successfully processed message ID
            last_page_token: Last page token for pagination
            failed_ids: List of failed message IDs
        """
        checkpoint.processed_messages = processed
        checkpoint.state = SyncState.IN_PROGRESS

        if last_message_id:
            checkpoint.last_message_id = last_message_id
        if last_page_token:
            checkpoint.last_page_token = last_page_token
        if failed_ids:
            checkpoint.failed_ids.extend(failed_ids)
            checkpoint.failed_messages = len(checkpoint.failed_ids)

        self.save_checkpoint(checkpoint)

    def mark_completed(
        self,
        checkpoint: SyncCheckpoint,
        history_id: int | None = None
    ) -> None:
        """
        Mark sync as completed.

        Args:
            checkpoint: Checkpoint to mark complete
            history_id: Gmail history ID for future incremental syncs
        """
        checkpoint.state = SyncState.COMPLETED
        if history_id:
            checkpoint.history_id = history_id
        self.save_checkpoint(checkpoint)
        logger.info(f"Sync completed: {checkpoint.sync_id}")

    def mark_failed(
        self,
        checkpoint: SyncCheckpoint,
        error: str,
        failed_ids: list[str] | None = None
    ) -> None:
        """
        Mark sync as failed.

        Args:
            checkpoint: Checkpoint to mark failed
            error: Error message
            failed_ids: List of failed message IDs
        """
        checkpoint.state = SyncState.FAILED
        checkpoint.error_message = error
        if failed_ids:
            checkpoint.failed_ids.extend(failed_ids)
            checkpoint.failed_messages = len(checkpoint.failed_ids)
        self.save_checkpoint(checkpoint)
        logger.error(f"Sync failed: {checkpoint.sync_id} - {error}")

    def mark_interrupted(self, checkpoint: SyncCheckpoint) -> None:
        """
        Mark sync as interrupted (for graceful shutdown).

        Args:
            checkpoint: Checkpoint to mark interrupted
        """
        checkpoint.state = SyncState.INTERRUPTED
        self.save_checkpoint(checkpoint)
        logger.warning(f"Sync interrupted: {checkpoint.sync_id}")

    def get_resume_info(self, checkpoint: SyncCheckpoint) -> dict[str, Any]:
        """
        Get information needed to resume a sync.

        Args:
            checkpoint: Checkpoint to resume from

        Returns:
            Dictionary with resume parameters
        """
        return {
            'sync_id': checkpoint.sync_id,
            'query': checkpoint.query,
            'output_directory': checkpoint.output_directory,
            'skip_count': checkpoint.processed_messages,
            'last_message_id': checkpoint.last_message_id,
            'last_page_token': checkpoint.last_page_token,
            'failed_ids': checkpoint.failed_ids.copy(),
            'history_id': checkpoint.history_id,
            'metadata': checkpoint.metadata.copy()
        }

    def cleanup_old_checkpoints(self, keep_completed: int = 5, keep_failed: int = 3) -> int:
        """
        Remove old checkpoints beyond retention limits.

        Args:
            keep_completed: Number of completed checkpoints to keep
            keep_failed: Number of failed checkpoints to keep

        Returns:
            Number of checkpoints removed
        """
        checkpoints = self.list_checkpoints()

        # Group by state
        completed = [c for c in checkpoints if c.state == SyncState.COMPLETED]
        failed = [c for c in checkpoints if c.state == SyncState.FAILED]

        removed = 0

        # Remove old completed checkpoints
        for checkpoint in completed[keep_completed:]:
            self.delete_checkpoint(checkpoint.sync_id)
            removed += 1

        # Remove old failed checkpoints
        for checkpoint in failed[keep_failed:]:
            self.delete_checkpoint(checkpoint.sync_id)
            removed += 1

        if removed:
            logger.info(f"Cleaned up {removed} old checkpoints")

        return removed

    def delete_checkpoint(self, sync_id: str) -> bool:
        """
        Delete a checkpoint file.

        Args:
            sync_id: Checkpoint to delete

        Returns:
            True if deleted, False if not found
        """
        filepath = self.checkpoint_dir / f"{sync_id}.json"
        if filepath.exists():
            filepath.unlink()
            logger.debug(f"Deleted checkpoint: {sync_id}")
            return True
        return False

    def get_stats(self) -> dict[str, Any]:
        """Get checkpoint statistics."""
        checkpoints = self.list_checkpoints()

        by_state = {}
        for checkpoint in checkpoints:
            state = checkpoint.state.value
            by_state[state] = by_state.get(state, 0) + 1

        return {
            'total': len(checkpoints),
            'by_state': by_state,
            'resumable': sum(1 for c in checkpoints if c.is_resumable),
            'directory': str(self.checkpoint_dir)
        }
