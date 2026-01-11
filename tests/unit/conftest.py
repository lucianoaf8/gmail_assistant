"""Shared fixtures for unit tests to handle optional dependencies."""

import pytest
from unittest.mock import MagicMock, Mock
from pathlib import Path


@pytest.fixture
def mock_email_classifier():
    """Provide EmailClassifier or mock if not available."""
    try:
        from gmail_assistant.processing.email_classifier import EmailClassifier
        return EmailClassifier
    except ImportError:
        # Create comprehensive mock
        mock_cls = MagicMock()
        mock_cls.return_value = Mock(
            classify=Mock(return_value={
                'category': 'newsletter',
                'confidence': 0.85,
                'patterns_matched': ['newsletter', 'unsubscribe']
            }),
            classify_batch=Mock(return_value=[])
        )
        return mock_cls


@pytest.fixture
def mock_email_content_parser():
    """Provide EmailContentParser or mock if not available."""
    try:
        from gmail_assistant.parsers.advanced_email_parser import EmailContentParser
        return EmailContentParser
    except ImportError:
        mock_cls = MagicMock()
        mock_cls.return_value = Mock(
            parse=Mock(return_value={
                'plain_text': 'Mock email content',
                'html': '<p>Mock email content</p>',
                'quality_score': 0.9
            })
        )
        return mock_cls


@pytest.fixture
def mock_robust_eml_converter():
    """Provide RobustEMLConverter or mock if not available."""
    try:
        from gmail_assistant.parsers.robust_eml_converter import RobustEMLConverter
        return RobustEMLConverter
    except ImportError:
        mock_cls = MagicMock()
        mock_cls.return_value = Mock(
            convert=Mock(return_value="# Mock Markdown\n\nMock content"),
            convert_batch=Mock(return_value={'success': 1, 'failed': 0})
        )
        return mock_cls


@pytest.fixture
def mock_eml_cleaner():
    """Provide GmailEMLToMarkdownCleaner or mock if not available."""
    try:
        from gmail_assistant.parsers.gmail_eml_to_markdown_cleaner import GmailEMLToMarkdownCleaner
        return GmailEMLToMarkdownCleaner
    except ImportError:
        mock_cls = MagicMock()
        mock_cls.return_value = Mock(
            convert_eml_to_markdown=Mock(return_value="# Mock Markdown"),
            clean_and_convert=Mock(return_value="# Cleaned Markdown")
        )
        return mock_cls


@pytest.fixture
def mock_email_database_importer():
    """Provide EmailDatabaseImporter or mock if not available."""
    try:
        from gmail_assistant.processing.email_database_importer import EmailDatabaseImporter
        return EmailDatabaseImporter
    except ImportError:
        mock_cls = MagicMock()
        mock_cls.return_value = Mock(
            import_emails=Mock(return_value={'imported': 10, 'skipped': 0}),
            get_stats=Mock(return_value={'total_emails': 10})
        )
        return mock_cls


@pytest.fixture
def sample_eml_files(tmp_path):
    """Create sample EML files for testing."""
    eml_dir = tmp_path / "eml_samples"
    eml_dir.mkdir()

    for i in range(3):
        eml_file = eml_dir / f"sample_{i}.eml"
        eml_file.write_text(f"""From: sender{i}@example.com
To: recipient@example.com
Subject: Test Email {i}
Date: Mon, 01 Jan 2025 12:00:00 +0000
Content-Type: text/plain; charset=utf-8

This is test email {i} content.
""")

    return eml_dir


@pytest.fixture
def sample_html_files(tmp_path):
    """Create sample HTML email files for testing."""
    html_dir = tmp_path / "html_samples"
    html_dir.mkdir()

    for i in range(3):
        html_file = html_dir / f"sample_{i}.html"
        html_file.write_text(f"""<!DOCTYPE html>
<html>
<head><title>Email {i}</title></head>
<body>
<p>This is HTML email content {i}.</p>
</body>
</html>
""")

    return html_dir


@pytest.fixture
def mock_analysis_database(tmp_path):
    """Create a mock analysis database for testing."""
    import sqlite3

    db_path = tmp_path / "analysis_test.db"
    conn = sqlite3.connect(db_path)

    # Create emails table
    conn.execute("""
        CREATE TABLE emails (
            id INTEGER PRIMARY KEY,
            gmail_id TEXT UNIQUE,
            subject TEXT,
            sender TEXT,
            parsed_date TEXT,
            category TEXT,
            labels TEXT
        )
    """)

    # Insert sample data
    sample_emails = [
        ('msg1', 'Newsletter 1', 'news@example.com', '2025-01-01', 'newsletter', 'INBOX'),
        ('msg2', 'Work Email', 'work@example.com', '2025-01-02', 'work', 'INBOX'),
        ('msg3', 'Personal', 'friend@example.com', '2025-01-03', 'personal', 'INBOX'),
    ]

    conn.executemany(
        "INSERT INTO emails (gmail_id, subject, sender, parsed_date, category, labels) VALUES (?, ?, ?, ?, ?, ?)",
        sample_emails
    )

    conn.commit()
    conn.close()

    return db_path
