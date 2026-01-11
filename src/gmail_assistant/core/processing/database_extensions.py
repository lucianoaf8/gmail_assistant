"""
Database extensions for idempotent operations.

Provides upsert functionality and additional database utilities
to ensure data integrity and prevent duplicates.
"""

import logging
import sqlite3

# Import canonical schema
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class UpsertResult:
    """Result of an upsert operation."""
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            'inserted': self.inserted,
            'updated': self.updated,
            'skipped': self.skipped,
            'failed': self.failed
        }


class EmailDatabaseExtensions:
    """
    Database extensions for idempotent email operations.

    Provides:
    - Upsert (insert or update) by gmail_id
    - Batch upsert with transaction support
    - Deduplication utilities
    - Schema migration helpers
    """

    MIGRATION_SQL = """
    -- Add unique constraint on gmail_id if not exists
    -- Note: SQLite doesn't support ADD CONSTRAINT, so we create an index
    CREATE UNIQUE INDEX IF NOT EXISTS idx_emails_gmail_id_unique
    ON emails(gmail_id) WHERE gmail_id IS NOT NULL AND gmail_id != '';

    -- Add updated_at column if not exists (SQLite workaround)
    -- We'll handle this in Python as SQLite doesn't support ADD COLUMN IF NOT EXISTS
    """

    def __init__(self, db_path: str):
        """
        Initialize database extensions.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        """Connect to database with optimized settings."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent access
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA synchronous = NORMAL")
            self.conn.execute("PRAGMA cache_size = 10000")
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def ensure_schema(self) -> bool:
        """
        Ensure schema supports idempotent operations.

        Returns:
            True if schema is ready
        """
        conn = self.connect()
        try:
            # Check if unique index exists
            index_exists = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name='idx_emails_gmail_id_unique'
            """).fetchone()

            if not index_exists:
                # Create unique index
                conn.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_emails_gmail_id_unique
                    ON emails(gmail_id) WHERE gmail_id IS NOT NULL AND gmail_id != ''
                """)
                logger.info("Created unique index on gmail_id")

            # Check for updated_at column
            columns = conn.execute("PRAGMA table_info(emails)").fetchall()
            column_names = [col['name'] for col in columns]

            if 'updated_at' not in column_names:
                conn.execute("""
                    ALTER TABLE emails ADD COLUMN updated_at TEXT
                """)
                logger.info("Added updated_at column")

            if 'deleted_at' not in column_names:
                conn.execute("""
                    ALTER TABLE emails ADD COLUMN deleted_at TEXT
                """)
                logger.info("Added deleted_at column (soft delete support)")

            conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Error ensuring schema: {e}")
            conn.rollback()
            return False

    def upsert_email(
        self,
        gmail_id: str,
        data: dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Insert or update email by gmail_id (idempotent).

        Args:
            gmail_id: Unique Gmail message ID
            data: Email data dictionary

        Returns:
            Tuple of (was_inserted: bool, action: 'inserted'|'updated'|'skipped')
        """
        conn = self.connect()

        try:
            # Check if exists
            existing = conn.execute(
                "SELECT id, updated_at FROM emails WHERE gmail_id = ?",
                (gmail_id,)
            ).fetchone()

            now = datetime.now().isoformat()

            if existing:
                # Update existing record
                update_fields = []
                update_values = []

                field_mapping = {
                    'subject': 'subject',
                    'sender': 'sender',
                    'recipient': 'recipient',
                    'parsed_date': 'parsed_date',
                    'labels': 'labels',
                    'message_content': 'message_content',
                }

                for data_key, db_key in field_mapping.items():
                    if data_key in data and data[data_key] is not None:
                        update_fields.append(f"{db_key} = ?")
                        update_values.append(data[data_key])

                if update_fields:
                    update_fields.append("updated_at = ?")
                    update_values.append(now)
                    update_values.append(gmail_id)

                    sql = f"UPDATE emails SET {', '.join(update_fields)} WHERE gmail_id = ?"
                    conn.execute(sql, update_values)
                    conn.commit()
                    return (False, 'updated')
                else:
                    return (False, 'skipped')

            else:
                # Insert new record
                # Build insert with available fields
                fields = ['gmail_id', 'import_timestamp', 'updated_at']
                values = [gmail_id, now, now]

                optional_fields = [
                    ('thread_id', 'thread_id'),
                    ('subject', 'subject'),
                    ('sender', 'sender'),
                    ('recipient', 'recipient'),
                    ('date_received', 'date_received'),
                    ('parsed_date', 'parsed_date'),
                    ('year_month', 'year_month'),
                    ('labels', 'labels'),
                    ('message_content', 'message_content'),
                    ('filename', 'filename'),
                    ('file_path', 'file_path'),
                    ('extraction_timestamp', 'extraction_timestamp'),
                ]

                for data_key, db_key in optional_fields:
                    if data_key in data and data[data_key] is not None:
                        fields.append(db_key)
                        values.append(data[data_key])

                placeholders = ', '.join(['?'] * len(values))
                sql = f"INSERT INTO emails ({', '.join(fields)}) VALUES ({placeholders})"

                conn.execute(sql, values)
                conn.commit()
                return (True, 'inserted')

        except sqlite3.IntegrityError as e:
            # Handle race condition with concurrent inserts
            logger.warning(f"Concurrent insert detected for {gmail_id}: {e}")
            conn.rollback()
            return (False, 'skipped')
        except sqlite3.Error as e:
            logger.error(f"Database error upserting {gmail_id}: {e}")
            conn.rollback()
            raise

    def upsert_emails_batch(
        self,
        emails: list[dict[str, Any]],
        gmail_id_key: str = 'gmail_id'
    ) -> UpsertResult:
        """
        Batch upsert emails with transaction.

        Args:
            emails: List of email dictionaries
            gmail_id_key: Key name for gmail_id in dictionaries

        Returns:
            UpsertResult with counts
        """
        result = UpsertResult()
        conn = self.connect()

        try:
            # Start transaction
            conn.execute("BEGIN TRANSACTION")

            for email in emails:
                gmail_id = email.get(gmail_id_key) or email.get('id')
                if not gmail_id:
                    result.skipped += 1
                    continue

                try:
                    was_inserted, action = self.upsert_email(gmail_id, email)
                    if action == 'inserted':
                        result.inserted += 1
                    elif action == 'updated':
                        result.updated += 1
                    else:
                        result.skipped += 1
                except Exception as e:
                    logger.error(f"Failed to upsert email {gmail_id}: {e}")
                    result.failed += 1

            conn.commit()

        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            conn.rollback()
            raise

        logger.info(
            f"Batch upsert complete: {result.inserted} inserted, "
            f"{result.updated} updated, {result.skipped} skipped, "
            f"{result.failed} failed"
        )
        return result

    def check_exists(self, gmail_id: str) -> bool:
        """Check if email exists by gmail_id."""
        conn = self.connect()
        result = conn.execute(
            "SELECT 1 FROM emails WHERE gmail_id = ?",
            (gmail_id,)
        ).fetchone()
        return result is not None

    def check_exists_batch(self, gmail_ids: list[str]) -> dict[str, bool]:
        """
        Check existence of multiple gmail_ids.

        Args:
            gmail_ids: List of gmail IDs to check

        Returns:
            Dictionary mapping gmail_id to exists boolean
        """
        conn = self.connect()
        results = {}

        # Process in chunks for large lists
        chunk_size = 500
        for i in range(0, len(gmail_ids), chunk_size):
            chunk = gmail_ids[i:i + chunk_size]
            placeholders = ', '.join(['?'] * len(chunk))
            query = f"SELECT gmail_id FROM emails WHERE gmail_id IN ({placeholders})"
            existing = conn.execute(query, chunk).fetchall()
            existing_ids = {row['gmail_id'] for row in existing}

            for gid in chunk:
                results[gid] = gid in existing_ids

        return results

    def soft_delete(self, gmail_id: str) -> bool:
        """
        Soft delete email by setting deleted_at timestamp.

        Args:
            gmail_id: Email to soft delete

        Returns:
            True if deleted, False if not found
        """
        conn = self.connect()
        now = datetime.now().isoformat()

        result = conn.execute(
            "UPDATE emails SET deleted_at = ?, updated_at = ? WHERE gmail_id = ? AND deleted_at IS NULL",
            (now, now, gmail_id)
        )
        conn.commit()

        return result.rowcount > 0

    def restore(self, gmail_id: str) -> bool:
        """
        Restore soft-deleted email.

        Args:
            gmail_id: Email to restore

        Returns:
            True if restored, False if not found or not deleted
        """
        conn = self.connect()
        now = datetime.now().isoformat()

        result = conn.execute(
            "UPDATE emails SET deleted_at = NULL, updated_at = ? WHERE gmail_id = ? AND deleted_at IS NOT NULL",
            (now, gmail_id)
        )
        conn.commit()

        return result.rowcount > 0

    def find_duplicates(self) -> list[dict[str, Any]]:
        """
        Find duplicate emails by gmail_id.

        Returns:
            List of duplicate groups with counts
        """
        conn = self.connect()
        duplicates = conn.execute("""
            SELECT gmail_id, COUNT(*) as count, GROUP_CONCAT(id) as ids
            FROM emails
            WHERE gmail_id IS NOT NULL AND gmail_id != ''
            GROUP BY gmail_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """).fetchall()

        return [dict(row) for row in duplicates]

    def deduplicate(self, keep: str = 'first') -> int:
        """
        Remove duplicate emails, keeping specified record.

        Args:
            keep: 'first' (oldest id) or 'last' (newest id)

        Returns:
            Number of duplicates removed
        """
        conn = self.connect()
        duplicates = self.find_duplicates()

        removed = 0
        for dup in duplicates:
            ids = [int(id_str) for id_str in dup['ids'].split(',')]
            ids.sort()

            if keep == 'first':
                ids_to_remove = ids[1:]  # Keep first (smallest id)
            else:
                ids_to_remove = ids[:-1]  # Keep last (largest id)

            for id_to_remove in ids_to_remove:
                conn.execute("DELETE FROM emails WHERE id = ?", (id_to_remove,))
                removed += 1

        conn.commit()
        logger.info(f"Deduplicated {removed} records from {len(duplicates)} duplicate groups")
        return removed

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        conn = self.connect()

        stats = {}

        # Total counts
        stats['total_emails'] = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
        stats['unique_gmail_ids'] = conn.execute(
            "SELECT COUNT(DISTINCT gmail_id) FROM emails WHERE gmail_id IS NOT NULL"
        ).fetchone()[0]

        # Soft deleted count
        stats['soft_deleted'] = conn.execute(
            "SELECT COUNT(*) FROM emails WHERE deleted_at IS NOT NULL"
        ).fetchone()[0]

        # Duplicate count
        duplicates = self.find_duplicates()
        stats['duplicate_groups'] = len(duplicates)
        stats['total_duplicates'] = sum(d['count'] - 1 for d in duplicates)

        # Date range
        date_range = conn.execute("""
            SELECT MIN(parsed_date) as earliest, MAX(parsed_date) as latest
            FROM emails WHERE parsed_date IS NOT NULL AND deleted_at IS NULL
        """).fetchone()
        stats['date_range'] = {
            'earliest': date_range['earliest'],
            'latest': date_range['latest']
        }

        return stats
