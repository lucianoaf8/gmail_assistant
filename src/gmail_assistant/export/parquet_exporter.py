"""
Parquet export for email data analytics.
Optimized for analytical queries and data science workflows.

Features:
- Columnar storage for efficient queries
- Compression for storage efficiency
- Partitioning by date for time-based analysis
- Schema evolution support

Usage:
    exporter = ParquetExporter(db_path)
    stats = exporter.export_emails(output_dir, partition_by='year_month')
    print(f"Exported {stats['total_rows']} rows")
"""

import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Check for PyArrow availability
try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False
    pa = None
    pq = None
    logger.info("PyArrow not installed - Parquet export unavailable. "
                "Install with: pip install pyarrow")


class ParquetExportError(Exception):
    """Error during Parquet export."""
    pass


class ParquetExporter:
    """
    Export email data to Parquet format for analytics.

    Features:
    - Columnar storage for efficient analytical queries
    - Compression (snappy, gzip, zstd) for storage efficiency
    - Partitioning by date, sender domain, or labels
    - Schema evolution support for future fields
    - Summary statistics export

    Example:
        >>> exporter = ParquetExporter(Path("data/emails.db"))
        >>> stats = exporter.export_emails(Path("exports/parquet"))
        >>> print(f"Exported: {stats['total_rows']} emails in {stats['files_created']} files")
    """

    # Schema definition for email data
    EMAIL_SCHEMA = [
        ('gmail_id', 'string'),
        ('thread_id', 'string'),
        ('subject', 'string'),
        ('sender', 'string'),
        ('sender_domain', 'string'),
        ('recipient', 'string'),
        ('parsed_date', 'timestamp[us]'),
        ('year_month', 'string'),
        ('labels', 'list<string>'),
        ('message_length', 'int32'),
        ('has_attachments', 'bool'),
        ('is_read', 'bool'),
    ]

    def __init__(self, db_path: Path):
        """
        Initialize Parquet exporter.

        Args:
            db_path: Path to SQLite database

        Raises:
            ImportError: If PyArrow is not available
        """
        if not PYARROW_AVAILABLE:
            raise ImportError(
                "PyArrow required for Parquet export. "
                "Install with: pip install pyarrow"
            )

        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

    def _get_arrow_schema(self) -> 'pa.Schema':
        """Build PyArrow schema."""
        type_mapping = {
            'string': pa.string(),
            'int32': pa.int32(),
            'int64': pa.int64(),
            'float64': pa.float64(),
            'bool': pa.bool_(),
            'timestamp[us]': pa.timestamp('us'),
            'list<string>': pa.list_(pa.string()),
        }

        fields = []
        for name, type_str in self.EMAIL_SCHEMA:
            pa_type = type_mapping.get(type_str, pa.string())
            fields.append(pa.field(name, pa_type))

        return pa.schema(fields)

    def export_emails(
        self,
        output_dir: Path,
        partition_by: str = 'year_month',
        compression: str = 'snappy',
        batch_size: int = 10000,
        include_deleted: bool = False
    ) -> Dict[str, Any]:
        """
        Export emails to Parquet files.

        Args:
            output_dir: Output directory for Parquet files
            partition_by: Partition column (year_month, sender_domain)
            compression: Compression codec (snappy, gzip, zstd, none)
            batch_size: Rows per batch for memory efficiency
            include_deleted: Include soft-deleted emails

        Returns:
            Export statistics dictionary
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        stats = {
            'total_rows': 0,
            'files_created': 0,
            'total_size_bytes': 0,
            'partitions': [],
            'compression': compression,
            'started_at': datetime.now().isoformat(),
        }

        schema = self._get_arrow_schema()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Build delete filter
            delete_filter = "" if include_deleted else "WHERE deleted_at IS NULL"

            # Get partition values
            partition_query = f"""
                SELECT DISTINCT {partition_by}
                FROM emails
                {delete_filter}
                AND {partition_by} IS NOT NULL
                ORDER BY {partition_by}
            """
            partitions = conn.execute(partition_query).fetchall()

            logger.info(f"Exporting {len(partitions)} partitions")

            for partition_row in partitions:
                partition_value = partition_row[0]
                if not partition_value:
                    continue

                # Export partition
                partition_stats = self._export_partition(
                    conn=conn,
                    output_dir=output_dir,
                    partition_by=partition_by,
                    partition_value=partition_value,
                    schema=schema,
                    compression=compression,
                    include_deleted=include_deleted
                )

                stats['total_rows'] += partition_stats['rows']
                stats['files_created'] += 1
                stats['total_size_bytes'] += partition_stats['size_bytes']
                stats['partitions'].append(partition_value)

            stats['completed_at'] = datetime.now().isoformat()
            stats['success'] = True

            logger.info(
                f"Export complete: {stats['total_rows']} rows in "
                f"{stats['files_created']} files "
                f"({stats['total_size_bytes'] / 1024 / 1024:.1f} MB)"
            )

            # Save export metadata
            self._save_export_metadata(output_dir, stats)

            return stats

        except Exception as e:
            logger.error(f"Export failed: {e}")
            stats['success'] = False
            stats['error'] = str(e)
            raise ParquetExportError(str(e)) from e
        finally:
            conn.close()

    def _export_partition(
        self,
        conn: sqlite3.Connection,
        output_dir: Path,
        partition_by: str,
        partition_value: str,
        schema: 'pa.Schema',
        compression: str,
        include_deleted: bool
    ) -> Dict[str, int]:
        """Export a single partition."""
        delete_filter = "" if include_deleted else "AND deleted_at IS NULL"

        query = f"""
            SELECT
                gmail_id, thread_id, subject, sender, recipient,
                parsed_date, year_month, labels, message_content
            FROM emails
            WHERE {partition_by} = ?
            {delete_filter}
        """

        rows = conn.execute(query, (partition_value,)).fetchall()

        if not rows:
            return {'rows': 0, 'size_bytes': 0}

        # Build data arrays
        data = self._build_data_arrays(rows)

        # Create Arrow table
        table = pa.table(data, schema=schema)

        # Write Parquet file
        partition_dir = output_dir / f"{partition_by}={partition_value}"
        partition_dir.mkdir(parents=True, exist_ok=True)
        output_file = partition_dir / "data.parquet"

        pq.write_table(
            table,
            output_file,
            compression=compression if compression != 'none' else None
        )

        logger.debug(f"Exported partition {partition_value}: {len(rows)} rows")

        return {
            'rows': len(rows),
            'size_bytes': output_file.stat().st_size
        }

    def _build_data_arrays(self, rows: List) -> Dict[str, List]:
        """Build data arrays from database rows."""
        data = {
            'gmail_id': [],
            'thread_id': [],
            'subject': [],
            'sender': [],
            'sender_domain': [],
            'recipient': [],
            'parsed_date': [],
            'year_month': [],
            'labels': [],
            'message_length': [],
            'has_attachments': [],
            'is_read': [],
        }

        for row in rows:
            data['gmail_id'].append(row['gmail_id'])
            data['thread_id'].append(row['thread_id'])
            data['subject'].append(row['subject'] or '')
            data['sender'].append(row['sender'] or '')
            data['sender_domain'].append(
                self._extract_domain(row['sender'])
            )
            data['recipient'].append(row['recipient'] or '')
            data['parsed_date'].append(
                self._parse_datetime(row['parsed_date'])
            )
            data['year_month'].append(row['year_month'] or '')
            data['labels'].append(
                self._parse_labels(row['labels'])
            )
            data['message_length'].append(
                len(row['message_content']) if row['message_content'] else 0
            )
            data['has_attachments'].append(
                self._check_attachments(row['labels'])
            )
            data['is_read'].append(
                not self._check_unread(row['labels'])
            )

        return data

    def _extract_domain(self, sender: str) -> str:
        """Extract domain from sender email."""
        if not sender or '@' not in sender:
            return ''
        try:
            # Handle "Name <email@domain.com>" format
            if '<' in sender:
                email = sender.split('<')[1].split('>')[0]
            else:
                email = sender
            return email.split('@')[1].lower()
        except (IndexError, AttributeError):
            return ''

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None

    def _parse_labels(self, labels_str: str) -> List[str]:
        """Parse comma-separated labels."""
        if not labels_str:
            return []
        return [l.strip() for l in labels_str.split(',') if l.strip()]

    def _check_attachments(self, labels_str: str) -> bool:
        """Check if email has attachments based on labels."""
        if not labels_str:
            return False
        labels = labels_str.upper()
        return 'ATTACHMENT' in labels or 'HAS_ATTACHMENT' in labels

    def _check_unread(self, labels_str: str) -> bool:
        """Check if email is unread based on labels."""
        if not labels_str:
            return False
        return 'UNREAD' in labels_str.upper()

    def _save_export_metadata(self, output_dir: Path, stats: Dict) -> None:
        """Save export metadata file."""
        import json
        metadata_path = output_dir / '_export_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(stats, f, indent=2, default=str)

    def export_summary_stats(
        self,
        output_file: Path,
        compression: str = 'snappy'
    ) -> Dict[str, Any]:
        """
        Export summary statistics as Parquet.

        Args:
            output_file: Output Parquet file path
            compression: Compression codec

        Returns:
            Export statistics
        """
        conn = sqlite3.connect(self.db_path)

        try:
            # Monthly statistics
            monthly_query = """
                SELECT
                    year_month,
                    COUNT(*) as email_count,
                    COUNT(DISTINCT sender) as unique_senders,
                    COUNT(DISTINCT recipient) as unique_recipients,
                    MIN(parsed_date) as first_email,
                    MAX(parsed_date) as last_email,
                    SUM(CASE WHEN labels LIKE '%UNREAD%' THEN 1 ELSE 0 END) as unread_count
                FROM emails
                WHERE deleted_at IS NULL
                GROUP BY year_month
                ORDER BY year_month
            """

            rows = conn.execute(monthly_query).fetchall()

            data = {
                'year_month': [r[0] for r in rows],
                'email_count': [r[1] for r in rows],
                'unique_senders': [r[2] for r in rows],
                'unique_recipients': [r[3] for r in rows],
                'first_email': [r[4] for r in rows],
                'last_email': [r[5] for r in rows],
                'unread_count': [r[6] for r in rows],
            }

            table = pa.table(data)
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            pq.write_table(
                table,
                output_file,
                compression=compression if compression != 'none' else None
            )

            logger.info(f"Exported summary stats to {output_file}")

            return {
                'rows': len(rows),
                'output_file': str(output_file),
                'size_bytes': output_file.stat().st_size
            }

        finally:
            conn.close()

    def export_sender_stats(
        self,
        output_file: Path,
        min_emails: int = 5,
        compression: str = 'snappy'
    ) -> Dict[str, Any]:
        """
        Export sender statistics as Parquet.

        Args:
            output_file: Output Parquet file path
            min_emails: Minimum emails to include sender
            compression: Compression codec

        Returns:
            Export statistics
        """
        conn = sqlite3.connect(self.db_path)

        try:
            query = """
                SELECT
                    sender,
                    COUNT(*) as email_count,
                    MIN(parsed_date) as first_email,
                    MAX(parsed_date) as last_email
                FROM emails
                WHERE deleted_at IS NULL AND sender IS NOT NULL
                GROUP BY sender
                HAVING COUNT(*) >= ?
                ORDER BY email_count DESC
            """

            rows = conn.execute(query, (min_emails,)).fetchall()

            data = {
                'sender': [r[0] for r in rows],
                'sender_domain': [self._extract_domain(r[0]) for r in rows],
                'email_count': [r[1] for r in rows],
                'first_email': [r[2] for r in rows],
                'last_email': [r[3] for r in rows],
            }

            table = pa.table(data)
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            pq.write_table(
                table,
                output_file,
                compression=compression if compression != 'none' else None
            )

            logger.info(f"Exported sender stats to {output_file}")

            return {
                'rows': len(rows),
                'output_file': str(output_file),
                'size_bytes': output_file.stat().st_size
            }

        finally:
            conn.close()
