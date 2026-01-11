"""
Dead Letter Queue for handling persistent failures.
Failed operations are stored for later retry or manual inspection.

Usage:
    dlq = DeadLetterQueue()

    # Record failure
    dlq.add_failure("msg123", FailureType.FETCH_ERROR, "Connection timeout")

    # Process retries
    for item in dlq.get_ready_for_retry():
        try:
            process(item.message_id)
            dlq.mark_resolved(item.id)
        except Exception:
            pass  # Will auto-retry with backoff
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FailureType(str, Enum):
    """Types of failures that can be recorded."""
    FETCH_ERROR = "fetch_error"
    PARSE_ERROR = "parse_error"
    SAVE_ERROR = "save_error"
    DELETE_ERROR = "delete_error"
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    NETWORK_ERROR = "network_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    INVALID_DATA = "invalid_data"
    UNKNOWN = "unknown"


@dataclass
class DeadLetterItem:
    """Item in the dead letter queue."""
    id: int
    message_id: str
    failure_type: FailureType
    error_message: str
    error_details: str | None
    attempt_count: int
    first_failure: datetime
    last_failure: datetime
    next_retry: datetime | None
    resolved: bool
    context: dict[str, Any]

    @property
    def is_retriable(self) -> bool:
        """Check if item can be retried."""
        return not self.resolved and self.next_retry is not None

    @property
    def is_exhausted(self) -> bool:
        """Check if retries are exhausted."""
        return not self.resolved and self.next_retry is None


class DeadLetterQueue:
    """
    SQLite-backed dead letter queue for failed operations.

    Features:
    - Automatic retry scheduling with exponential backoff
    - Failure categorization by type
    - Resolution tracking
    - Statistics and reporting
    - Configurable retry limits

    Example:
        >>> dlq = DeadLetterQueue()
        >>> dlq.add_failure("msg123", FailureType.FETCH_ERROR, "Timeout")
        >>> stats = dlq.get_stats()
        >>> print(f"Pending: {stats['total_pending']}")
    """

    DEFAULT_DB = Path("data/databases/dead_letters.db")
    MAX_RETRIES = 5
    BASE_RETRY_DELAY = 300  # 5 minutes

    def __init__(
        self,
        db_path: Path | None = None,
        max_retries: int = 5,
        base_retry_delay: int = 300
    ):
        """
        Initialize dead letter queue.

        Args:
            db_path: Path to SQLite database
            max_retries: Maximum retry attempts
            base_retry_delay: Base delay in seconds (exponential backoff)
        """
        self.db_path = Path(db_path) if db_path else self.DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self.base_retry_delay = base_retry_delay
        self._init_database()

    def _init_database(self) -> None:
        """Initialize DLQ database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS dead_letters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    failure_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    error_details TEXT,
                    attempt_count INTEGER DEFAULT 1,
                    first_failure DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_failure DATETIME DEFAULT CURRENT_TIMESTAMP,
                    next_retry DATETIME,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at DATETIME,
                    context TEXT,

                    UNIQUE(message_id, failure_type)
                );

                CREATE INDEX IF NOT EXISTS idx_dlq_next_retry
                    ON dead_letters(next_retry) WHERE resolved = FALSE;
                CREATE INDEX IF NOT EXISTS idx_dlq_message_id
                    ON dead_letters(message_id);
                CREATE INDEX IF NOT EXISTS idx_dlq_failure_type
                    ON dead_letters(failure_type);
                CREATE INDEX IF NOT EXISTS idx_dlq_resolved
                    ON dead_letters(resolved);
            """)
        logger.debug(f"DLQ database initialized: {self.db_path}")

    def add_failure(
        self,
        message_id: str,
        failure_type: FailureType,
        error_message: str,
        error_details: str | None = None,
        context: dict[str, Any] | None = None
    ) -> int:
        """
        Add or update a failed operation.

        If the same message_id + failure_type exists, it updates the
        attempt count and schedules next retry with exponential backoff.

        Args:
            message_id: Gmail message ID
            failure_type: Category of failure
            error_message: Human-readable error message
            error_details: Additional error details (stack trace, etc.)
            context: Additional context dictionary

        Returns:
            DLQ item ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Check if already exists
            existing = conn.execute(
                "SELECT id, attempt_count FROM dead_letters "
                "WHERE message_id = ? AND failure_type = ? AND resolved = FALSE",
                (message_id, failure_type.value)
            ).fetchone()

            if existing:
                # Update existing entry
                item_id = existing['id']
                new_attempt = existing['attempt_count'] + 1
                next_retry = self._calculate_next_retry(new_attempt)

                conn.execute("""
                    UPDATE dead_letters SET
                        error_message = ?,
                        error_details = ?,
                        attempt_count = ?,
                        last_failure = CURRENT_TIMESTAMP,
                        next_retry = ?,
                        context = ?
                    WHERE id = ?
                """, (
                    error_message,
                    error_details,
                    new_attempt,
                    next_retry.isoformat() if next_retry else None,
                    json.dumps(context) if context else None,
                    item_id
                ))

                if new_attempt >= self.max_retries:
                    logger.warning(
                        f"Message {message_id} exceeded max retries ({self.max_retries})"
                    )

                logger.debug(f"Updated DLQ item {item_id}: attempt {new_attempt}")
                return item_id

            else:
                # Insert new entry
                next_retry = self._calculate_next_retry(1)
                cursor = conn.execute("""
                    INSERT INTO dead_letters
                    (message_id, failure_type, error_message, error_details,
                     next_retry, context)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    message_id,
                    failure_type.value,
                    error_message,
                    error_details,
                    next_retry.isoformat() if next_retry else None,
                    json.dumps(context) if context else None
                ))

                logger.info(
                    f"Added to DLQ: {message_id} ({failure_type.value})"
                )
                return cursor.lastrowid

    def _calculate_next_retry(self, attempt: int) -> datetime | None:
        """
        Calculate next retry time with exponential backoff.

        Backoff: base_delay * 2^(attempt-1)
        - Attempt 1: 5 min
        - Attempt 2: 10 min
        - Attempt 3: 20 min
        - Attempt 4: 40 min
        - Attempt 5: 80 min (then exhausted)
        """
        if attempt >= self.max_retries:
            return None  # No more retries

        delay = self.base_retry_delay * (2 ** (attempt - 1))
        return datetime.now() + timedelta(seconds=delay)

    def get_ready_for_retry(self, limit: int = 100) -> list[DeadLetterItem]:
        """
        Get items ready for retry.

        Args:
            limit: Maximum items to return

        Returns:
            List of DeadLetterItems ready for retry
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM dead_letters
                WHERE resolved = FALSE
                  AND next_retry IS NOT NULL
                  AND next_retry <= datetime('now')
                ORDER BY next_retry ASC
                LIMIT ?
            """, (limit,)).fetchall()

            return [self._row_to_item(row) for row in rows]

    def get_by_message_id(self, message_id: str) -> list[DeadLetterItem]:
        """Get all DLQ items for a message."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM dead_letters WHERE message_id = ?",
                (message_id,)
            ).fetchall()
            return [self._row_to_item(row) for row in rows]

    def get_by_failure_type(
        self,
        failure_type: FailureType,
        resolved: bool = False
    ) -> list[DeadLetterItem]:
        """Get DLQ items by failure type."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM dead_letters WHERE failure_type = ? AND resolved = ?",
                (failure_type.value, resolved)
            ).fetchall()
            return [self._row_to_item(row) for row in rows]

    def mark_resolved(self, item_id: int, reason: str = None) -> None:
        """
        Mark an item as resolved.

        Args:
            item_id: DLQ item ID
            reason: Optional resolution reason
        """
        with sqlite3.connect(self.db_path) as conn:
            context_update = ""
            if reason:
                # Append resolution reason to context
                existing = conn.execute(
                    "SELECT context FROM dead_letters WHERE id = ?",
                    (item_id,)
                ).fetchone()
                if existing:
                    context = json.loads(existing[0] or '{}')
                    context['resolution_reason'] = reason
                    context_update = f", context = '{json.dumps(context)}'"

            conn.execute(f"""
                UPDATE dead_letters SET
                    resolved = TRUE,
                    resolved_at = CURRENT_TIMESTAMP,
                    next_retry = NULL
                    {context_update}
                WHERE id = ?
            """, (item_id,))

        logger.info(f"DLQ item {item_id} resolved")

    def mark_resolved_by_message(self, message_id: str) -> int:
        """
        Mark all failures for a message as resolved.

        Args:
            message_id: Gmail message ID

        Returns:
            Number of items resolved
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE dead_letters SET
                    resolved = TRUE,
                    resolved_at = CURRENT_TIMESTAMP,
                    next_retry = NULL
                WHERE message_id = ? AND resolved = FALSE
            """, (message_id,))
            return cursor.rowcount

    def get_stats(self) -> dict[str, Any]:
        """Get DLQ statistics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            total = conn.execute(
                "SELECT COUNT(*) FROM dead_letters WHERE resolved = FALSE"
            ).fetchone()[0]

            by_type = dict(conn.execute("""
                SELECT failure_type, COUNT(*)
                FROM dead_letters
                WHERE resolved = FALSE
                GROUP BY failure_type
            """).fetchall())

            ready = conn.execute("""
                SELECT COUNT(*) FROM dead_letters
                WHERE resolved = FALSE AND next_retry <= datetime('now')
            """).fetchone()[0]

            exhausted = conn.execute("""
                SELECT COUNT(*) FROM dead_letters
                WHERE resolved = FALSE AND next_retry IS NULL
            """).fetchone()[0]

            resolved_today = conn.execute("""
                SELECT COUNT(*) FROM dead_letters
                WHERE resolved = TRUE AND resolved_at >= date('now')
            """).fetchone()[0]

            avg_attempts = conn.execute("""
                SELECT AVG(attempt_count) FROM dead_letters WHERE resolved = TRUE
            """).fetchone()[0] or 0

            return {
                'total_pending': total,
                'by_failure_type': by_type,
                'ready_for_retry': ready,
                'retries_exhausted': exhausted,
                'resolved_today': resolved_today,
                'avg_attempts_to_resolve': round(avg_attempts, 2)
            }

    def get_exhausted(self, limit: int = 100) -> list[DeadLetterItem]:
        """Get items that have exhausted all retries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM dead_letters
                WHERE resolved = FALSE AND next_retry IS NULL
                ORDER BY last_failure DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [self._row_to_item(row) for row in rows]

    def cleanup_resolved(self, older_than_days: int = 30) -> int:
        """
        Clean up old resolved items.

        Args:
            older_than_days: Remove resolved items older than this

        Returns:
            Number of items removed
        """
        cutoff = datetime.now() - timedelta(days=older_than_days)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM dead_letters
                WHERE resolved = TRUE AND resolved_at < ?
            """, (cutoff.isoformat(),))
            count = cursor.rowcount

        if count:
            logger.info(f"Cleaned up {count} resolved DLQ items")
        return count

    def reset_for_retry(self, item_id: int) -> bool:
        """
        Reset an exhausted item for retry.

        Args:
            item_id: DLQ item ID

        Returns:
            True if reset, False if not found or not exhausted
        """
        with sqlite3.connect(self.db_path) as conn:
            # Only reset if exhausted (no next_retry)
            cursor = conn.execute("""
                UPDATE dead_letters SET
                    attempt_count = 0,
                    next_retry = ?
                WHERE id = ? AND resolved = FALSE AND next_retry IS NULL
            """, (self._calculate_next_retry(1).isoformat(), item_id))

            if cursor.rowcount > 0:
                logger.info(f"Reset DLQ item {item_id} for retry")
                return True
            return False

    def _row_to_item(self, row: sqlite3.Row) -> DeadLetterItem:
        """Convert database row to DeadLetterItem."""
        return DeadLetterItem(
            id=row['id'],
            message_id=row['message_id'],
            failure_type=FailureType(row['failure_type']),
            error_message=row['error_message'],
            error_details=row['error_details'],
            attempt_count=row['attempt_count'],
            first_failure=datetime.fromisoformat(row['first_failure']),
            last_failure=datetime.fromisoformat(row['last_failure']),
            next_retry=datetime.fromisoformat(row['next_retry']) if row['next_retry'] else None,
            resolved=bool(row['resolved']),
            context=json.loads(row['context']) if row['context'] else {}
        )

    def export_to_json(self, output_path: Path, include_resolved: bool = False) -> int:
        """
        Export DLQ to JSON file.

        Args:
            output_path: Output file path
            include_resolved: Include resolved items

        Returns:
            Number of items exported
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM dead_letters"
            if not include_resolved:
                query += " WHERE resolved = FALSE"
            query += " ORDER BY last_failure DESC"

            rows = conn.execute(query).fetchall()
            items = [self._row_to_item(row) for row in rows]

            export_data = {
                'exported_at': datetime.now().isoformat(),
                'total_items': len(items),
                'items': [
                    {
                        'id': item.id,
                        'message_id': item.message_id,
                        'failure_type': item.failure_type.value,
                        'error_message': item.error_message,
                        'attempt_count': item.attempt_count,
                        'first_failure': item.first_failure.isoformat(),
                        'last_failure': item.last_failure.isoformat(),
                        'resolved': item.resolved,
                        'context': item.context
                    }
                    for item in items
                ]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported {len(items)} DLQ items to {output_path}")
            return len(items)
