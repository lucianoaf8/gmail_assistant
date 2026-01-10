"""
True incremental sync using Gmail History API.
Only fetches changes since last sync, not all matching messages.

The History API returns only changes since a given historyId, making it
far more efficient than re-scanning all messages for each sync.

Usage:
    client = HistorySyncClient(service)

    # Initial sync - get starting history ID
    history_id = client.get_current_history_id()

    # Later - sync only changes
    result = client.sync_from_history(history_id)
    for msg_id in result.added_message_ids:
        # Process new message
        pass
"""

import logging
from typing import List, Dict, Optional, Tuple, Callable, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

try:
    from googleapiclient.errors import HttpError
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False
    HttpError = Exception

from ..schemas import Email
from .batch_api import GmailBatchClient

logger = logging.getLogger(__name__)


class HistoryEventType(str, Enum):
    """Types of history events from Gmail API."""
    MESSAGE_ADDED = "messageAdded"
    MESSAGE_DELETED = "messageDeleted"
    LABELS_ADDED = "labelsAdded"
    LABELS_REMOVED = "labelsRemoved"


@dataclass
class HistoryEvent:
    """Single history event from Gmail API."""
    type: HistoryEventType
    message_id: str
    labels: List[str]
    history_id: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LabelChange:
    """Represents a label change on a message."""
    message_id: str
    added_labels: List[str]
    removed_labels: List[str]
    history_id: int


@dataclass
class HistorySyncResult:
    """Result of history sync operation."""
    success: bool
    new_history_id: int
    events: List[HistoryEvent] = field(default_factory=list)
    added_message_ids: List[str] = field(default_factory=list)
    deleted_message_ids: List[str] = field(default_factory=list)
    label_changes: List[LabelChange] = field(default_factory=list)
    error: Optional[str] = None
    pages_processed: int = 0

    @property
    def total_changes(self) -> int:
        """Total number of changes in this sync."""
        return (
            len(self.added_message_ids) +
            len(self.deleted_message_ids) +
            len(self.label_changes)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'success': self.success,
            'new_history_id': self.new_history_id,
            'added_count': len(self.added_message_ids),
            'deleted_count': len(self.deleted_message_ids),
            'label_changes_count': len(self.label_changes),
            'total_events': len(self.events),
            'pages_processed': self.pages_processed,
            'error': self.error
        }


class HistorySyncClient:
    """
    Gmail History API client for efficient incremental sync.

    The History API returns only changes since a given historyId,
    making it far more efficient than re-scanning all messages.

    Workflow:
    1. Initial full sync - store final historyId
    2. Subsequent syncs - use history.list() from last historyId
    3. Process only changed messages

    Example:
        >>> client = HistorySyncClient(gmail_service)
        >>> # Get initial history ID
        >>> initial_id = client.get_current_history_id()
        >>> # ... time passes, emails arrive ...
        >>> result = client.sync_from_history(initial_id)
        >>> print(f"New messages: {len(result.added_message_ids)}")
    """

    HISTORY_TYPES = [
        'messageAdded',
        'messageDeleted',
        'labelAdded',
        'labelRemoved'
    ]

    def __init__(
        self,
        service,
        batch_client: Optional[GmailBatchClient] = None
    ):
        """
        Initialize history sync client.

        Args:
            service: Authenticated Gmail API service
            batch_client: Optional batch client for fetching messages
        """
        if not GMAIL_API_AVAILABLE:
            raise ImportError(
                "google-api-python-client required. "
                "Install with: pip install google-api-python-client"
            )

        self.service = service
        self.batch_client = batch_client

    def _get_batch_client(self) -> GmailBatchClient:
        """Get or create batch client."""
        if not self.batch_client:
            self.batch_client = GmailBatchClient(self.service)
        return self.batch_client

    def get_current_history_id(self) -> int:
        """
        Get current history ID from Gmail profile.

        Returns:
            Current history ID

        Raises:
            HttpError: If API call fails
        """
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            history_id = int(profile.get('historyId', 0))
            logger.debug(f"Current history ID: {history_id}")
            return history_id
        except HttpError as e:
            logger.error(f"Failed to get history ID: {e}")
            raise

    def sync_from_history(
        self,
        start_history_id: int,
        label_filter: Optional[str] = None,
        max_pages: int = 100
    ) -> HistorySyncResult:
        """
        Sync changes from a given history ID.

        Args:
            start_history_id: History ID to start from
            label_filter: Optional label to filter by (e.g., 'INBOX')
            max_pages: Maximum pages to process (safety limit)

        Returns:
            HistorySyncResult with all changes
        """
        events = []
        added_ids = set()
        deleted_ids = set()
        label_changes = []

        page_token = None
        latest_history_id = start_history_id
        pages_processed = 0

        try:
            while pages_processed < max_pages:
                # Build request
                request_params = {
                    'userId': 'me',
                    'startHistoryId': start_history_id,
                    'historyTypes': self.HISTORY_TYPES
                }

                if label_filter:
                    request_params['labelId'] = label_filter
                if page_token:
                    request_params['pageToken'] = page_token

                # Execute request
                response = self.service.users().history().list(
                    **request_params
                ).execute()

                pages_processed += 1

                # Process history records
                for record in response.get('history', []):
                    record_id = int(record.get('id', 0))
                    latest_history_id = max(latest_history_id, record_id)

                    # Process message additions
                    for msg in record.get('messagesAdded', []):
                        msg_id = msg['message']['id']
                        labels = msg['message'].get('labelIds', [])
                        added_ids.add(msg_id)
                        events.append(HistoryEvent(
                            type=HistoryEventType.MESSAGE_ADDED,
                            message_id=msg_id,
                            labels=labels,
                            history_id=record_id
                        ))

                    # Process message deletions
                    for msg in record.get('messagesDeleted', []):
                        msg_id = msg['message']['id']
                        deleted_ids.add(msg_id)
                        events.append(HistoryEvent(
                            type=HistoryEventType.MESSAGE_DELETED,
                            message_id=msg_id,
                            labels=[],
                            history_id=record_id
                        ))

                    # Process label additions
                    for change in record.get('labelsAdded', []):
                        msg_id = change['message']['id']
                        labels = change.get('labelIds', [])
                        label_changes.append(LabelChange(
                            message_id=msg_id,
                            added_labels=labels,
                            removed_labels=[],
                            history_id=record_id
                        ))
                        events.append(HistoryEvent(
                            type=HistoryEventType.LABELS_ADDED,
                            message_id=msg_id,
                            labels=labels,
                            history_id=record_id
                        ))

                    # Process label removals
                    for change in record.get('labelsRemoved', []):
                        msg_id = change['message']['id']
                        labels = change.get('labelIds', [])
                        label_changes.append(LabelChange(
                            message_id=msg_id,
                            added_labels=[],
                            removed_labels=labels,
                            history_id=record_id
                        ))
                        events.append(HistoryEvent(
                            type=HistoryEventType.LABELS_REMOVED,
                            message_id=msg_id,
                            labels=labels,
                            history_id=record_id
                        ))

                # Check for more pages
                page_token = response.get('nextPageToken')
                if not page_token:
                    break

            # Calculate net changes (added that weren't deleted)
            net_added = list(added_ids - deleted_ids)
            net_deleted = list(deleted_ids)

            logger.info(
                f"History sync complete: {len(net_added)} added, "
                f"{len(net_deleted)} deleted, {len(label_changes)} label changes"
            )

            return HistorySyncResult(
                success=True,
                new_history_id=latest_history_id,
                events=events,
                added_message_ids=net_added,
                deleted_message_ids=net_deleted,
                label_changes=label_changes,
                pages_processed=pages_processed
            )

        except HttpError as e:
            if e.resp.status == 404:
                # History ID expired - need full sync
                logger.warning(
                    f"History ID {start_history_id} expired, full sync required"
                )
                return HistorySyncResult(
                    success=False,
                    new_history_id=0,
                    error="HISTORY_EXPIRED"
                )
            logger.error(f"History sync failed: {e}")
            return HistorySyncResult(
                success=False,
                new_history_id=start_history_id,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error during history sync: {e}")
            return HistorySyncResult(
                success=False,
                new_history_id=start_history_id,
                error=str(e)
            )

    def fetch_added_messages(
        self,
        message_ids: List[str],
        format: str = 'full'
    ) -> List[Email]:
        """
        Fetch full message details for added messages.

        Args:
            message_ids: List of message IDs to fetch
            format: Message format ('full', 'metadata', 'minimal')

        Returns:
            List of Email objects
        """
        if not message_ids:
            return []

        client = self._get_batch_client()
        return client.batch_get_messages(message_ids, format=format)

    def perform_incremental_sync(
        self,
        last_history_id: int,
        on_messages_added: Optional[Callable[[List[Email]], None]] = None,
        on_messages_deleted: Optional[Callable[[List[str]], None]] = None,
        on_labels_changed: Optional[Callable[[List[LabelChange]], None]] = None,
        fetch_full_messages: bool = True
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Perform complete incremental sync with callbacks.

        Args:
            last_history_id: Last synced history ID
            on_messages_added: Callback for new messages
            on_messages_deleted: Callback for deleted message IDs
            on_labels_changed: Callback for label changes
            fetch_full_messages: Whether to fetch full message details

        Returns:
            Tuple of (new_history_id, stats_dict)

        Raises:
            ValueError: If history ID expired
            RuntimeError: If sync fails
        """
        stats = {
            'added': 0,
            'deleted': 0,
            'label_changes': 0,
            'pages_processed': 0
        }

        # Sync history
        result = self.sync_from_history(last_history_id)

        if not result.success:
            if result.error == "HISTORY_EXPIRED":
                raise ValueError(
                    f"History ID {last_history_id} expired - full sync required"
                )
            raise RuntimeError(f"History sync failed: {result.error}")

        stats['pages_processed'] = result.pages_processed

        # Process additions
        if result.added_message_ids:
            if fetch_full_messages and on_messages_added:
                messages = self.fetch_added_messages(result.added_message_ids)
                stats['added'] = len(messages)
                on_messages_added(messages)
            else:
                stats['added'] = len(result.added_message_ids)
                if on_messages_added:
                    # Pass IDs if no fetch requested
                    on_messages_added(result.added_message_ids)

        # Process deletions
        if result.deleted_message_ids:
            stats['deleted'] = len(result.deleted_message_ids)
            if on_messages_deleted:
                on_messages_deleted(result.deleted_message_ids)

        # Process label changes
        if result.label_changes:
            stats['label_changes'] = len(result.label_changes)
            if on_labels_changed:
                on_labels_changed(result.label_changes)

        return result.new_history_id, stats

    def check_sync_required(
        self,
        stored_history_id: int
    ) -> Tuple[bool, int]:
        """
        Check if sync is required by comparing history IDs.

        Args:
            stored_history_id: Last stored history ID

        Returns:
            Tuple of (sync_required, current_history_id)
        """
        current_id = self.get_current_history_id()
        sync_required = current_id > stored_history_id
        return (sync_required, current_id)


class SyncStateManager:
    """
    Manages sync state persistence in database.

    Stores history IDs and sync metadata for resumable operations.
    """

    def __init__(self, db_connection):
        """
        Initialize sync state manager.

        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Ensure sync_state table exists."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL UNIQUE,
                last_history_id INTEGER,
                last_sync_at DATETIME,
                total_synced INTEGER DEFAULT 0,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def get_history_id(self, source: str = 'gmail') -> Optional[int]:
        """
        Get last synced history ID for a source.

        Args:
            source: Sync source identifier

        Returns:
            History ID or None if never synced
        """
        result = self.conn.execute(
            "SELECT last_history_id FROM sync_state WHERE source = ?",
            (source,)
        ).fetchone()
        return result[0] if result else None

    def update_history_id(
        self,
        history_id: int,
        synced_count: int = 0,
        source: str = 'gmail'
    ) -> None:
        """
        Update sync state with new history ID.

        Args:
            history_id: New history ID
            synced_count: Number of messages synced
            source: Sync source identifier
        """
        now = datetime.now().isoformat()

        self.conn.execute("""
            INSERT INTO sync_state (source, last_history_id, last_sync_at, total_synced, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(source) DO UPDATE SET
                last_history_id = excluded.last_history_id,
                last_sync_at = excluded.last_sync_at,
                total_synced = total_synced + excluded.total_synced,
                updated_at = excluded.updated_at
        """, (source, history_id, now, synced_count, now))
        self.conn.commit()

    def get_sync_stats(self, source: str = 'gmail') -> Optional[Dict[str, Any]]:
        """
        Get sync statistics for a source.

        Args:
            source: Sync source identifier

        Returns:
            Dictionary with sync stats or None
        """
        result = self.conn.execute(
            "SELECT * FROM sync_state WHERE source = ?",
            (source,)
        ).fetchone()

        if not result:
            return None

        return {
            'source': result[1],
            'last_history_id': result[2],
            'last_sync_at': result[3],
            'total_synced': result[4],
            'created_at': result[6],
            'updated_at': result[7]
        }
