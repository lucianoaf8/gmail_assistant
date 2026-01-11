"""
Comprehensive tests for database.py module.
Tests EmailDatabaseImporter class for database operations.
"""

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest import mock

import pytest


class TestEmailDatabaseImporterInit:
    """Tests for EmailDatabaseImporter initialization."""

    def test_init_default_values(self, tmp_path):
        """Test initialization with default values."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        importer = EmailDatabaseImporter()
        assert importer.db_path == Path("emails.db")
        assert importer.json_folder == Path("monthly_email_data")
        assert importer.conn is None

    def test_init_custom_values(self, tmp_path):
        """Test initialization with custom values."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "custom.db"
        json_folder = tmp_path / "custom_json"

        importer = EmailDatabaseImporter(str(db_path), str(json_folder))
        assert importer.db_path == db_path
        assert importer.json_folder == json_folder


class TestConnectDatabase:
    """Tests for connect_database method."""

    def test_connect_creates_connection(self, tmp_path):
        """Test connecting creates database connection."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()

        assert importer.conn is not None
        importer.close_database()

    def test_connect_enables_wal_mode(self, tmp_path):
        """Test connecting enables WAL journal mode."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()

        cursor = importer.conn.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode == "wal"

        importer.close_database()


class TestCloseDatabase:
    """Tests for close_database method."""

    def test_close_database(self, tmp_path):
        """Test closing database connection."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.close_database()

        # Connection should be closed (attempting to use it would raise error)
        # But we just verify the method completes without error

    def test_close_database_when_not_connected(self, tmp_path):
        """Test closing when not connected."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        importer = EmailDatabaseImporter()
        # Should not raise error
        importer.close_database()


class TestCreateDatabaseSchema:
    """Tests for create_database_schema method."""

    def test_creates_emails_table(self, tmp_path):
        """Test schema creates emails table."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        # Verify table exists
        cursor = importer.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='emails'"
        )
        result = cursor.fetchone()
        assert result is not None

        importer.close_database()

    def test_creates_import_batches_table(self, tmp_path):
        """Test schema creates import_batches table."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        cursor = importer.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='import_batches'"
        )
        result = cursor.fetchone()
        assert result is not None

        importer.close_database()

    def test_creates_email_stats_table(self, tmp_path):
        """Test schema creates email_stats table."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        cursor = importer.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='email_stats'"
        )
        result = cursor.fetchone()
        assert result is not None

        importer.close_database()

    def test_creates_indexes(self, tmp_path):
        """Test schema creates indexes."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        cursor = importer.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_emails%'"
        )
        indexes = cursor.fetchall()
        assert len(indexes) > 0

        importer.close_database()


class TestImportMonthlyJson:
    """Tests for import_monthly_json method."""

    def test_import_nonexistent_file(self, tmp_path):
        """Test importing nonexistent file."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        imported, skipped = importer.import_monthly_json(Path("/nonexistent/file.json"))

        assert imported == 0
        assert skipped == 0

        importer.close_database()

    def test_import_empty_json(self, tmp_path):
        """Test importing JSON with no emails."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        json_file = tmp_path / "2024-01_emails.json"
        json_file.write_text(json.dumps({
            "year_month": "2024-01",
            "emails": []
        }))

        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        imported, skipped = importer.import_monthly_json(json_file)

        assert imported == 0
        assert skipped == 0

        importer.close_database()

    def test_import_valid_emails(self, tmp_path):
        """Test importing valid emails."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        json_file = tmp_path / "2024-01_emails.json"

        email_data = {
            "year_month": "2024-01",
            "emails": [
                {
                    "filename": "test.eml",
                    "file_path": "/path/to/test.eml",
                    "gmail_id": "msg123",
                    "thread_id": "thread123",
                    "date_received": "2024-01-15 10:00:00",
                    "parsed_date": "2024-01-15",
                    "year_month": "2024-01",
                    "sender": "test@example.com",
                    "recipient": "me@example.com",
                    "subject": "Test Email",
                    "labels": "INBOX",
                    "message_content": "Test content",
                    "extraction_timestamp": "2024-01-15T12:00:00"
                }
            ],
            "date_range": {
                "first_email": "2024-01-15",
                "last_email": "2024-01-15"
            },
            "extraction_info": {
                "extracted_at": "2024-01-15T12:00:00"
            }
        }
        json_file.write_text(json.dumps(email_data))

        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        imported, skipped = importer.import_monthly_json(json_file)

        assert imported == 1
        assert skipped == 0

        importer.close_database()

    def test_import_skips_duplicate_batch(self, tmp_path):
        """Test importing skips already imported batch."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        json_file = tmp_path / "2024-01_emails.json"

        email_data = {
            "year_month": "2024-01",
            "emails": [
                {
                    "filename": "test.eml",
                    "file_path": "/path/to/test.eml",
                    "gmail_id": "msg123",
                    "year_month": "2024-01",
                    "extraction_timestamp": "2024-01-15T12:00:00"
                }
            ]
        }
        json_file.write_text(json.dumps(email_data))

        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        # First import
        importer.import_monthly_json(json_file)

        # Second import should skip
        imported, skipped = importer.import_monthly_json(json_file)

        assert imported == 0
        assert skipped == 1

        importer.close_database()


class TestImportAllMonthlyFiles:
    """Tests for import_all_monthly_files method."""

    def test_import_all_missing_folder(self, tmp_path):
        """Test import all with missing folder."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        json_folder = tmp_path / "nonexistent"

        importer = EmailDatabaseImporter(str(db_path), str(json_folder))
        importer.connect_database()
        importer.create_database_schema()

        result = importer.import_all_monthly_files()

        assert result == {}

        importer.close_database()

    def test_import_all_empty_folder(self, tmp_path):
        """Test import all with empty folder."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        json_folder = tmp_path / "json_data"
        json_folder.mkdir()

        importer = EmailDatabaseImporter(str(db_path), str(json_folder))
        importer.connect_database()
        importer.create_database_schema()

        result = importer.import_all_monthly_files()

        assert result == {}

        importer.close_database()

    def test_import_all_with_files(self, tmp_path):
        """Test import all with JSON files."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        json_folder = tmp_path / "json_data"
        json_folder.mkdir()

        # Create test JSON file
        json_file = json_folder / "2024-01_emails.json"
        json_file.write_text(json.dumps({
            "year_month": "2024-01",
            "emails": [
                {
                    "filename": "test.eml",
                    "file_path": "/path/test.eml",
                    "year_month": "2024-01",
                    "extraction_timestamp": "2024-01-15"
                }
            ]
        }))

        importer = EmailDatabaseImporter(str(db_path), str(json_folder))
        importer.connect_database()
        importer.create_database_schema()

        result = importer.import_all_monthly_files()

        assert result['total_files'] == 1
        assert result['processed_files'] == 1
        assert result['total_imported'] == 1

        importer.close_database()


class TestUpdateStatistics:
    """Tests for update_statistics method."""

    def test_update_statistics(self, tmp_path):
        """Test updating statistics."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        # Insert test email
        importer.conn.execute("""
            INSERT INTO emails (filename, file_path, gmail_id, year_month,
                               sender, recipient, parsed_date, extraction_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test.eml", "/path/test.eml", "msg123", "2024-01",
              "sender@example.com", "recipient@example.com", "2024-01-15", "2024-01-15"))
        importer.conn.commit()

        importer.update_statistics()

        # Verify stats were inserted
        cursor = importer.conn.execute("SELECT total_emails FROM email_stats")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 1

        importer.close_database()


class TestGetDatabaseInfo:
    """Tests for get_database_info method."""

    def test_get_info_empty_database(self, tmp_path):
        """Test getting info from empty database."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        info = importer.get_database_info()

        assert info['total_emails'] == 0
        assert info['imported_batches'] == 0

        importer.close_database()

    def test_get_info_with_data(self, tmp_path):
        """Test getting info with data."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        # Insert test emails
        for i in range(5):
            importer.conn.execute("""
                INSERT INTO emails (filename, file_path, gmail_id, year_month,
                                   sender, parsed_date, extraction_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (f"test{i}.eml", f"/path/test{i}.eml", f"msg{i}", "2024-01",
                  "sender@example.com", "2024-01-15", "2024-01-15"))
        importer.conn.commit()

        info = importer.get_database_info()

        assert info['total_emails'] == 5
        assert 'date_range' in info
        assert 'top_senders' in info
        assert 'monthly_distribution' in info

        importer.close_database()


class TestSearchEmails:
    """Tests for search_emails method."""

    def test_search_no_results(self, tmp_path):
        """Test search with no results."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        results = importer.search_emails("nonexistent query")

        assert results == []

        importer.close_database()

    def test_search_finds_matching_emails(self, tmp_path):
        """Test search finds matching emails."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        # Insert test email with searchable content
        importer.conn.execute("""
            INSERT INTO emails (filename, file_path, gmail_id, year_month,
                               sender, subject, message_content,
                               parsed_date, extraction_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test.eml", "/path/test.eml", "msg123", "2024-01",
              "sender@example.com", "Test Subject", "Unique search content",
              "2024-01-15", "2024-01-15"))
        importer.conn.commit()

        results = importer.search_emails("Unique search")

        assert len(results) >= 1

        importer.close_database()

    def test_search_respects_limit(self, tmp_path):
        """Test search respects limit parameter."""
        from gmail_assistant.core.processing.database import EmailDatabaseImporter

        db_path = tmp_path / "test.db"
        importer = EmailDatabaseImporter(str(db_path))
        importer.connect_database()
        importer.create_database_schema()

        # Insert multiple test emails
        for i in range(10):
            importer.conn.execute("""
                INSERT INTO emails (filename, file_path, gmail_id, year_month,
                                   sender, subject, message_content,
                                   parsed_date, extraction_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"test{i}.eml", f"/path/test{i}.eml", f"msg{i}", "2024-01",
                  "sender@example.com", "Common Subject", "Common content",
                  "2024-01-15", "2024-01-15"))
        importer.conn.commit()

        results = importer.search_emails("Common", limit=5)

        assert len(results) <= 5

        importer.close_database()
