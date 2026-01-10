"""
Database migration: Normalize schema for labels and participants.

Migration 002: Creates normalized tables for email_participants and email_labels,
migrates existing data, and adds sync_state table for history tracking.

Usage:
    # Dry run (preview changes)
    python scripts/migration/002_normalize_schema.py --db data/databases/emails.db

    # Execute migration
    python scripts/migration/002_normalize_schema.py --db data/databases/emails.db --execute

    # Rollback (if needed)
    python scripts/migration/002_normalize_schema.py --db data/databases/emails.db --rollback
"""

import sqlite3
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of migration operation."""
    success: bool
    labels_migrated: int = 0
    participants_migrated: int = 0
    tables_created: int = 0
    error: Optional[str] = None


# Schema definitions
MIGRATION_SQL = """
-- Email participants table (normalized from sender/recipient)
CREATE TABLE IF NOT EXISTS email_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK(type IN ('from', 'to', 'cc', 'bcc')),
    address TEXT NOT NULL,
    display_name TEXT,
    domain TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(email_id, type, address)
);

CREATE INDEX IF NOT EXISTS idx_participants_email_id ON email_participants(email_id);
CREATE INDEX IF NOT EXISTS idx_participants_address ON email_participants(address);
CREATE INDEX IF NOT EXISTS idx_participants_domain ON email_participants(domain);
CREATE INDEX IF NOT EXISTS idx_participants_type ON email_participants(type);

-- Email labels table (normalized from comma-separated labels)
CREATE TABLE IF NOT EXISTS email_labels (
    email_id INTEGER NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (email_id, label)
);

CREATE INDEX IF NOT EXISTS idx_labels_label ON email_labels(label);

-- Sync state for Gmail history API tracking
CREATE TABLE IF NOT EXISTS sync_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL UNIQUE,
    last_history_id INTEGER,
    last_sync_at DATETIME,
    total_synced INTEGER DEFAULT 0,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    description TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT
);
"""

ROLLBACK_SQL = """
DROP TABLE IF EXISTS email_participants;
DROP TABLE IF EXISTS email_labels;
DROP TABLE IF EXISTS sync_state;
DELETE FROM schema_migrations WHERE version = '002';
"""


def migrate(db_path: Path, dry_run: bool = True) -> MigrationResult:
    """
    Execute schema normalization migration.

    Changes:
    1. Create email_participants table
    2. Create email_labels table
    3. Create sync_state table
    4. Migrate existing comma-separated data to normalized tables

    Args:
        db_path: Path to SQLite database
        dry_run: If True, preview changes without applying

    Returns:
        MigrationResult with operation counts
    """
    result = MigrationResult(success=False)

    if not db_path.exists():
        result.error = f"Database not found: {db_path}"
        logger.error(result.error)
        return result

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Check if already migrated
        if _is_already_migrated(conn):
            logger.info("Migration 002 already applied, skipping")
            result.success = True
            return result

        if dry_run:
            logger.info("=" * 60)
            logger.info("DRY RUN - No changes will be made")
            logger.info("=" * 60)

        # Create new tables
        logger.info("Creating normalized tables...")
        if not dry_run:
            conn.executescript(MIGRATION_SQL)
            result.tables_created = 3
        else:
            logger.info("Would create: email_participants, email_labels, sync_state")
            result.tables_created = 3

        # Migrate labels
        logger.info("Migrating labels...")
        result.labels_migrated = _migrate_labels(conn, dry_run)

        # Migrate participants
        logger.info("Migrating participants...")
        result.participants_migrated = _migrate_participants(conn, dry_run)

        # Record migration
        if not dry_run:
            conn.execute(
                "INSERT INTO schema_migrations (version, description, checksum) VALUES (?, ?, ?)",
                ('002', 'Normalize labels and participants', _calculate_checksum())
            )
            conn.commit()
            logger.info("Migration 002 recorded in schema_migrations")

        result.success = True
        logger.info("=" * 60)
        logger.info(f"Migration {'preview' if dry_run else 'complete'}:")
        logger.info(f"  Tables created: {result.tables_created}")
        logger.info(f"  Labels migrated: {result.labels_migrated}")
        logger.info(f"  Participants migrated: {result.participants_migrated}")
        logger.info("=" * 60)

    except Exception as e:
        result.error = str(e)
        logger.error(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

    return result


def rollback(db_path: Path, force: bool = False) -> bool:
    """
    Rollback migration 002.

    Args:
        db_path: Path to database
        force: Skip confirmation prompt

    Returns:
        True if rollback successful
    """
    if not force:
        confirm = input("This will DELETE normalized tables. Continue? [y/N]: ")
        if confirm.lower() != 'y':
            logger.info("Rollback cancelled")
            return False

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(ROLLBACK_SQL)
        conn.commit()
        logger.info("Rollback complete - normalized tables removed")
        return True
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def _is_already_migrated(conn: sqlite3.Connection) -> bool:
    """Check if migration 002 was already applied."""
    try:
        result = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE version = '002'"
        ).fetchone()
        return result is not None
    except sqlite3.OperationalError:
        # schema_migrations table doesn't exist yet
        return False


def _calculate_checksum() -> str:
    """Calculate checksum of migration SQL for verification."""
    import hashlib
    return hashlib.md5(MIGRATION_SQL.encode()).hexdigest()


def _migrate_labels(conn: sqlite3.Connection, dry_run: bool) -> int:
    """
    Migrate comma-separated labels to normalized email_labels table.

    Args:
        conn: Database connection
        dry_run: Preview only if True

    Returns:
        Number of label entries migrated
    """
    cursor = conn.execute("""
        SELECT id, labels FROM emails
        WHERE labels IS NOT NULL AND labels != ''
    """)

    count = 0
    batch = []
    batch_size = 1000

    for row in cursor:
        email_id = row['id']
        labels_str = row['labels']

        # Parse comma-separated labels
        labels = [l.strip() for l in labels_str.split(',') if l.strip()]

        for label in labels:
            if dry_run:
                count += 1
            else:
                batch.append((email_id, label))
                count += 1

                if len(batch) >= batch_size:
                    _insert_labels_batch(conn, batch)
                    batch = []

    # Insert remaining batch
    if batch and not dry_run:
        _insert_labels_batch(conn, batch)

    logger.info(f"{'Would migrate' if dry_run else 'Migrated'} {count} label entries")
    return count


def _insert_labels_batch(conn: sqlite3.Connection, batch: list) -> None:
    """Insert batch of labels."""
    conn.executemany(
        "INSERT OR IGNORE INTO email_labels (email_id, label) VALUES (?, ?)",
        batch
    )


def _migrate_participants(conn: sqlite3.Connection, dry_run: bool) -> int:
    """
    Migrate sender/recipient columns to normalized email_participants table.

    Args:
        conn: Database connection
        dry_run: Preview only if True

    Returns:
        Number of participant entries migrated
    """
    cursor = conn.execute("""
        SELECT id, sender, recipient FROM emails
        WHERE sender IS NOT NULL OR recipient IS NOT NULL
    """)

    count = 0
    batch = []
    batch_size = 1000

    for row in cursor:
        email_id = row['id']

        # Migrate sender as 'from' type
        if row['sender']:
            address, display_name = _parse_email_address(row['sender'])
            domain = _extract_domain(address)

            if dry_run:
                count += 1
            else:
                batch.append((email_id, 'from', address, display_name, domain))
                count += 1

        # Migrate recipients as 'to' type
        if row['recipient']:
            # Recipients may be comma-separated
            recipients = _split_addresses(row['recipient'])

            for recipient in recipients:
                address, display_name = _parse_email_address(recipient)
                domain = _extract_domain(address)

                if dry_run:
                    count += 1
                else:
                    batch.append((email_id, 'to', address, display_name, domain))
                    count += 1

        if len(batch) >= batch_size and not dry_run:
            _insert_participants_batch(conn, batch)
            batch = []

    # Insert remaining batch
    if batch and not dry_run:
        _insert_participants_batch(conn, batch)

    logger.info(f"{'Would migrate' if dry_run else 'Migrated'} {count} participant entries")
    return count


def _insert_participants_batch(conn: sqlite3.Connection, batch: list) -> None:
    """Insert batch of participants."""
    conn.executemany("""
        INSERT OR IGNORE INTO email_participants
        (email_id, type, address, display_name, domain)
        VALUES (?, ?, ?, ?, ?)
    """, batch)


def _parse_email_address(header_value: str) -> Tuple[str, str]:
    """
    Parse email address from header value.

    Examples:
        "John Doe <john@example.com>" -> ("john@example.com", "John Doe")
        "john@example.com" -> ("john@example.com", "")
        '"John Doe" <john@example.com>' -> ("john@example.com", "John Doe")

    Args:
        header_value: Email header value

    Returns:
        Tuple of (address, display_name)
    """
    header_value = header_value.strip()

    # Pattern: "Display Name" <email@domain.com> or Display Name <email@domain.com>
    match = re.match(r'^"?([^"<]+)"?\s*<([^>]+)>$', header_value)
    if match:
        display_name = match.group(1).strip()
        address = match.group(2).strip().lower()
        return (address, display_name)

    # Pattern: <email@domain.com>
    match = re.match(r'^<([^>]+)>$', header_value)
    if match:
        return (match.group(1).strip().lower(), '')

    # Plain email address
    return (header_value.lower(), '')


def _extract_domain(address: str) -> str:
    """Extract domain from email address."""
    if '@' in address:
        return address.split('@')[1]
    return ''


def _split_addresses(addresses_str: str) -> list:
    """
    Split comma-separated email addresses, respecting quoted strings.

    Args:
        addresses_str: Comma-separated email addresses

    Returns:
        List of individual address strings
    """
    # Simple split for most cases
    # TODO: Handle quoted commas in display names if needed
    addresses = []
    for addr in addresses_str.split(','):
        addr = addr.strip()
        if addr:
            addresses.append(addr)
    return addresses


def get_migration_status(db_path: Path) -> dict:
    """
    Get current migration status for database.

    Returns:
        Dictionary with migration status info
    """
    if not db_path.exists():
        return {'exists': False, 'error': 'Database not found'}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    status = {
        'exists': True,
        'migrations': [],
        'tables': []
    }

    try:
        # Get applied migrations
        try:
            migrations = conn.execute(
                "SELECT version, description, applied_at FROM schema_migrations ORDER BY version"
            ).fetchall()
            status['migrations'] = [dict(m) for m in migrations]
        except sqlite3.OperationalError:
            status['migrations'] = []

        # Check for normalized tables
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('email_participants', 'email_labels', 'sync_state')"
        ).fetchall()
        status['tables'] = [t['name'] for t in tables]

        # Count records in normalized tables
        for table in status['tables']:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            status[f'{table}_count'] = count

    except Exception as e:
        status['error'] = str(e)
    finally:
        conn.close()

    return status


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="Database schema normalization migration (002)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview migration (dry run)
  python 002_normalize_schema.py --db data/databases/emails.db

  # Execute migration
  python 002_normalize_schema.py --db data/databases/emails.db --execute

  # Check migration status
  python 002_normalize_schema.py --db data/databases/emails.db --status

  # Rollback migration
  python 002_normalize_schema.py --db data/databases/emails.db --rollback
        """
    )

    parser.add_argument(
        "--db",
        required=True,
        help="Path to SQLite database"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute migration (default is dry run)"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show migration status"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts"
    )

    args = parser.parse_args()
    db_path = Path(args.db)

    if args.status:
        status = get_migration_status(db_path)
        print("\nMigration Status:")
        print("-" * 40)
        for key, value in status.items():
            print(f"  {key}: {value}")

    elif args.rollback:
        rollback(db_path, force=args.force)

    else:
        result = migrate(db_path, dry_run=not args.execute)
        if not result.success:
            exit(1)
