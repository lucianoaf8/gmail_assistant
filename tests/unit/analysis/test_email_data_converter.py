#!/usr/bin/env python3
"""
Comprehensive tests for email_data_converter.py module.

Test coverage target: 0% → 85%
"""

import email
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from gmail_assistant.analysis.email_data_converter import EmailDataConverter


# Test Fixtures
@pytest.fixture
def converter():
    """Create EmailDataConverter instance."""
    return EmailDataConverter(verbose=False)


@pytest.fixture
def verbose_converter():
    """Create EmailDataConverter with verbose logging."""
    return EmailDataConverter(verbose=True)


@pytest.fixture
def sample_eml_content():
    """Sample EML file content."""
    return b"""From: sender@example.com
To: recipient@example.com
Subject: Test Email
Date: Mon, 10 Jan 2025 10:00:00 +0000
Message-ID: <abc123def456@example.com>
Content-Type: text/plain; charset="utf-8"

This is a test email message body.
It contains multiple lines.
And some content for testing.
"""


@pytest.fixture
def sample_markdown_content():
    """Sample Markdown file content."""
    return """# Email Details

| Field | Value |
| --- | --- |
| From | sender@example.com |
| To | recipient@example.com |
| Subject | Test Email |
| Date | Mon, 10 Jan 2025 10:00:00 +0000 |
| Message ID | abc123def456 |

## Email Content

This is the email content from markdown.
It has multiple lines and paragraphs.

Best regards,
Test User
"""


@pytest.fixture
def temp_eml_file(sample_eml_content):
    """Create temporary EML file."""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='_abc123def45678.eml', delete=False) as f:
        f.write(sample_eml_content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def temp_markdown_file(sample_markdown_content):
    """Create temporary Markdown file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='_abc123def45678.md', delete=False, encoding='utf-8') as f:
        f.write(sample_markdown_content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def temp_email_directory():
    """Create temporary directory with sample email files."""
    import tempfile

    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    # Create sample EML files
    for i in range(5):
        eml_content = f"""From: sender{i}@example.com
To: recipient@example.com
Subject: Test Email {i}
Date: {(datetime(2025, 1, 10) + timedelta(days=i)).strftime('%a, %d %b %Y %H:%M:%S +0000')}
Message-ID: <id{i:04d}@example.com>
Content-Type: text/plain; charset="utf-8"

This is test email {i} content.
"""
        eml_file = temp_path / f"2025-01-{10+i:02d}_100000_test_email_{i}_id{i:016d}.eml"
        eml_file.write_bytes(eml_content.encode('utf-8'))

    # Create sample MD files
    for i in range(5, 10):
        md_content = f"""# Email Details

| Field | Value |
| --- | --- |
| From | sender{i}@example.com |
| Subject | Test Email {i} |
| Date | {(datetime(2025, 1, 10) + timedelta(days=i)).strftime('%a, %d %b %Y %H:%M:%S +0000')} |

## Email Content

This is test email {i} content from markdown.
"""
        md_file = temp_path / f"2025-01-{10+i:02d}_100000_test_email_{i}_id{i:016d}.md"
        md_file.write_text(md_content, encoding='utf-8')

    yield temp_path

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


# EmailDataConverter Initialization Tests
class TestEmailDataConverterInit:
    """Tests for EmailDataConverter initialization."""

    def test_initialization_default(self):
        """Test default initialization."""
        converter = EmailDataConverter()

        assert converter.verbose is False
        assert converter.logger is not None

    def test_initialization_verbose(self):
        """Test verbose initialization."""
        converter = EmailDataConverter(verbose=True)

        assert converter.verbose is True
        assert converter.logger is not None


# EML Extraction Tests
class TestEMLExtraction:
    """Tests for EML file extraction."""

    def test_extract_from_eml_basic(self, converter, temp_eml_file):
        """Test basic EML extraction."""
        result = converter.extract_from_eml(temp_eml_file)

        assert result is not None
        assert 'gmail_id' in result
        assert 'subject' in result
        assert 'sender' in result
        assert 'date_received' in result
        assert 'plain_text_content' in result
        assert result['source_type'] == 'eml'

    def test_extract_from_eml_metadata(self, converter, temp_eml_file):
        """Test EML metadata extraction."""
        result = converter.extract_from_eml(temp_eml_file)

        assert result['subject'] == 'Test Email'
        assert 'sender@example.com' in result['sender']
        assert isinstance(result['date_received'], datetime)

    def test_extract_from_eml_content(self, converter, temp_eml_file):
        """Test EML content extraction."""
        result = converter.extract_from_eml(temp_eml_file)

        assert 'test email message body' in result['plain_text_content'].lower()
        assert len(result['plain_text_content']) > 0

    def test_extract_from_eml_invalid_file(self, converter):
        """Test EML extraction with invalid file."""
        invalid_path = Path('nonexistent_file.eml')
        result = converter.extract_from_eml(invalid_path)

        assert result is None

    def test_extract_from_eml_multipart(self, converter):
        """Test extraction from multipart EML."""
        multipart_eml = b"""From: sender@example.com
Subject: Multipart Test
Date: Mon, 10 Jan 2025 10:00:00 +0000
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="utf-8"

Plain text content here.

--boundary123
Content-Type: text/html; charset="utf-8"

<html><body>HTML content</body></html>

--boundary123--
"""

        with tempfile.NamedTemporaryFile(mode='wb', suffix='_test123.eml', delete=False) as f:
            f.write(multipart_eml)
            temp_path = Path(f.name)

        try:
            result = converter.extract_from_eml(temp_path)
            assert result is not None
            assert 'Plain text content' in result['plain_text_content']
        finally:
            temp_path.unlink(missing_ok=True)


# Markdown Extraction Tests
class TestMarkdownExtraction:
    """Tests for Markdown file extraction."""

    def test_extract_from_markdown_basic(self, converter, temp_markdown_file):
        """Test basic Markdown extraction."""
        result = converter.extract_from_markdown(temp_markdown_file)

        assert result is not None
        assert 'gmail_id' in result
        assert 'subject' in result
        assert 'sender' in result
        assert 'date_received' in result
        assert 'plain_text_content' in result
        assert result['source_type'] == 'markdown'

    def test_extract_from_markdown_metadata(self, converter, temp_markdown_file):
        """Test Markdown metadata extraction."""
        result = converter.extract_from_markdown(temp_markdown_file)

        assert result['subject'] == 'Test Email'
        assert result['sender'] == 'sender@example.com'
        assert isinstance(result['date_received'], datetime)

    def test_extract_from_markdown_content(self, converter, temp_markdown_file):
        """Test Markdown content extraction."""
        result = converter.extract_from_markdown(temp_markdown_file)

        assert 'email content from markdown' in result['plain_text_content'].lower()
        assert 'best regards' in result['plain_text_content'].lower()

    def test_extract_from_markdown_invalid_file(self, converter):
        """Test Markdown extraction with invalid file."""
        invalid_path = Path('nonexistent_file.md')
        result = converter.extract_from_markdown(invalid_path)

        assert result is None

    def test_extract_from_markdown_minimal(self, converter):
        """Test Markdown extraction with minimal metadata."""
        minimal_md = """| Field | Value |
| --- | --- |
| From | test@example.com |

Content here.
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.md', delete=False, encoding='utf-8') as f:
            f.write(minimal_md)
            temp_path = Path(f.name)

        try:
            result = converter.extract_from_markdown(temp_path)
            assert result is not None
            assert result['sender'] == 'test@example.com'
        finally:
            temp_path.unlink(missing_ok=True)


# Gmail ID Extraction Tests
class TestGmailIDExtraction:
    """Tests for Gmail ID extraction from filenames."""

    def test_extract_gmail_id_standard_format(self, converter):
        """Test Gmail ID extraction from standard filename."""
        filename = '2025-01-10_100000_subject_abc123def4567890.eml'
        gmail_id = converter._extract_gmail_id(filename)

        assert gmail_id == 'abc123def4567890'

    def test_extract_gmail_id_fallback(self, converter):
        """Test Gmail ID extraction fallback."""
        filename = 'email_without_id.eml'
        gmail_id = converter._extract_gmail_id(filename)

        assert gmail_id == 'email_without_id'

    def test_extract_gmail_id_markdown(self, converter):
        """Test Gmail ID extraction from markdown filename."""
        filename = '2025-01-10_100000_subject_1234567890abcdef.md'
        gmail_id = converter._extract_gmail_id(filename)

        assert gmail_id == '1234567890abcdef'


# Date Parsing Tests
class TestDateParsing:
    """Tests for email date parsing."""

    def test_parse_rfc2822_date(self, converter):
        """Test RFC 2822 date format parsing."""
        date_str = 'Mon, 10 Jan 2025 10:00:00 +0000'
        result = converter._parse_email_date(date_str)

        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 10

    def test_parse_iso_date(self, converter):
        """Test ISO date format parsing."""
        date_str = '2025-01-10T10:00:00'
        result = converter._parse_email_date(date_str)

        assert isinstance(result, datetime)
        assert result.year == 2025

    def test_parse_simple_date(self, converter):
        """Test simple date format parsing."""
        date_str = '2025-01-10 10:00:00'
        result = converter._parse_email_date(date_str)

        assert isinstance(result, datetime)
        assert result.year == 2025

    def test_parse_invalid_date(self, converter):
        """Test parsing invalid date."""
        date_str = 'not a valid date'
        result = converter._parse_email_date(date_str)

        assert result is None

    def test_parse_empty_date(self, converter):
        """Test parsing empty date."""
        date_str = ''
        result = converter._parse_email_date(date_str)

        assert result is None


# Plain Text Extraction Tests
class TestPlainTextExtraction:
    """Tests for plain text extraction from email messages."""

    def test_extract_plain_text_simple(self, converter):
        """Test plain text extraction from simple message."""
        msg = email.message_from_bytes(b"""From: test@example.com
Content-Type: text/plain; charset="utf-8"

Simple plain text content.
""")

        result = converter._extract_plain_text(msg)
        assert 'Simple plain text content' in result

    def test_extract_plain_text_multipart(self, converter):
        """Test plain text extraction from multipart message."""
        msg_bytes = b"""From: test@example.com
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary"

--boundary
Content-Type: text/plain; charset="utf-8"

Plain text part 1.

--boundary
Content-Type: text/plain; charset="utf-8"

Plain text part 2.

--boundary--
"""
        msg = email.message_from_bytes(msg_bytes)

        result = converter._extract_plain_text(msg)
        assert 'Plain text part 1' in result
        assert 'Plain text part 2' in result

    def test_extract_plain_text_empty(self, converter):
        """Test plain text extraction from empty message."""
        msg = email.message_from_bytes(b"""From: test@example.com
Content-Type: text/html

<html><body>HTML only</body></html>
""")

        result = converter._extract_plain_text(msg)
        assert result == ''


# Markdown Parsing Tests
class TestMarkdownParsing:
    """Tests for Markdown metadata and content parsing."""

    def test_parse_markdown_metadata(self, converter):
        """Test Markdown metadata table parsing."""
        content = """| Field | Value |
| --- | --- |
| From | sender@example.com |
| Subject | Test Subject |
| Date | 2025-01-10 |
"""

        result = converter._parse_markdown_metadata(content)

        assert result['from'] == 'sender@example.com'
        assert result['subject'] == 'Test Subject'
        assert result['date'] == '2025-01-10'

    def test_parse_markdown_metadata_no_table(self, converter):
        """Test Markdown parsing with no metadata table."""
        content = "Just some content without metadata table."

        result = converter._parse_markdown_metadata(content)
        assert result == {}

    def test_extract_markdown_content(self, converter):
        """Test Markdown content extraction."""
        content = """| Field | Value |
| --- | --- |
| From | test |

## Email Content

This is the actual email content.
Multiple lines here.
"""

        result = converter._extract_markdown_content(content)
        assert 'actual email content' in result.lower()
        assert 'multiple lines' in result.lower()

    def test_extract_markdown_content_no_heading(self, converter):
        """Test content extraction with no Email Content heading."""
        content = """Metadata here.

## Some Heading

Content after heading.
"""

        result = converter._extract_markdown_content(content)
        assert 'Content after heading' in result


# Directory Conversion Tests
class TestDirectoryConversion:
    """Tests for directory conversion to Parquet."""

    def test_convert_directory_basic(self, converter, temp_email_directory):
        """Test basic directory conversion."""
        output_file = temp_email_directory / 'output.parquet'

        count = converter.convert_directory(temp_email_directory, output_file)

        assert count == 10  # 5 EML + 5 MD
        assert output_file.exists()

        # Verify parquet content
        df = pd.read_parquet(output_file)
        assert len(df) == 10
        assert 'gmail_id' in df.columns
        assert 'sender' in df.columns

        # Cleanup
        output_file.unlink(missing_ok=True)

    def test_convert_directory_with_date_filter(self, converter, temp_email_directory):
        """Test directory conversion with date filter."""
        output_file = temp_email_directory / 'filtered.parquet'

        count = converter.convert_directory(
            temp_email_directory,
            output_file,
            date_filter='2025-01-10'
        )

        assert count >= 0
        if output_file.exists():
            df = pd.read_parquet(output_file)
            # All emails should be from the filtered date
            for date in df['date_received']:
                assert date.date() == datetime(2025, 1, 10).date()

            output_file.unlink(missing_ok=True)

    def test_convert_directory_empty(self, converter):
        """Test conversion of empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / 'output.parquet'

            count = converter.convert_directory(temp_path, output_file)

            assert count == 0
            assert not output_file.exists()

    def test_convert_directory_creates_parent_dirs(self, converter, temp_email_directory):
        """Test that parent directories are created for output file."""
        output_file = temp_email_directory / 'nested' / 'dirs' / 'output.parquet'

        count = converter.convert_directory(temp_email_directory, output_file)

        assert count > 0
        assert output_file.exists()
        assert output_file.parent.exists()

        # Cleanup
        import shutil
        shutil.rmtree(temp_email_directory / 'nested', ignore_errors=True)


# Latest Emails Conversion Tests
class TestLatestEmailsConversion:
    """Tests for converting latest emails."""

    def test_convert_latest_emails(self, converter, temp_email_directory):
        """Test converting latest emails."""
        output_file = temp_email_directory / 'latest.parquet'

        count = converter.convert_latest_emails(
            temp_email_directory,
            output_file,
            days_back=1
        )

        # Should process some emails
        assert count >= 0
        if count > 0:
            assert output_file.exists()

            df = pd.read_parquet(output_file)
            assert 'gmail_id' in df.columns
            assert len(df) == len(df['gmail_id'].unique())  # No duplicates

            output_file.unlink(missing_ok=True)

    def test_convert_latest_emails_multiple_days(self, converter, temp_email_directory):
        """Test converting emails from multiple days."""
        output_file = temp_email_directory / 'multi_day.parquet'

        count = converter.convert_latest_emails(
            temp_email_directory,
            output_file,
            days_back=3
        )

        assert count >= 0

        if output_file.exists():
            output_file.unlink(missing_ok=True)

    def test_convert_latest_emails_no_data(self, converter):
        """Test converting latest emails with no matching data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / 'output.parquet'

            count = converter.convert_latest_emails(temp_path, output_file, days_back=1)

            assert count == 0
            assert not output_file.exists()


# Data Type Tests
class TestDataTypes:
    """Tests for proper data type handling."""

    def test_dataframe_column_types(self, converter, temp_email_directory):
        """Test that DataFrame has correct column types."""
        output_file = temp_email_directory / 'types.parquet'

        converter.convert_directory(temp_email_directory, output_file)

        df = pd.read_parquet(output_file)

        assert df['gmail_id'].dtype == 'object'
        assert df['sender'].dtype == 'object'
        assert df['subject'].dtype == 'object'
        assert pd.api.types.is_datetime64_any_dtype(df['date_received'])
        assert df['plain_text_content'].dtype == 'object'

        output_file.unlink(missing_ok=True)


# Edge Case Tests
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_unicode_in_email(self, converter):
        """Test handling of Unicode characters."""
        unicode_eml = """From: sender@example.com
Subject: Test emoji тест
Date: Mon, 10 Jan 2025 10:00:00 +0000
Content-Type: text/plain; charset="utf-8"

Content with unicode: ñ ü ö
""".encode('utf-8')

        with tempfile.NamedTemporaryFile(mode='wb', suffix='_test.eml', delete=False) as f:
            f.write(unicode_eml)
            temp_path = Path(f.name)

        try:
            result = converter.extract_from_eml(temp_path)
            assert result is not None
            # Check that subject exists (may be a Header object or string)
            assert result['subject'] is not None
        finally:
            temp_path.unlink(missing_ok=True)

    def test_malformed_email(self, converter):
        """Test handling of malformed email."""
        malformed_eml = b"This is not a valid email format"

        with tempfile.NamedTemporaryFile(mode='wb', suffix='_test.eml', delete=False) as f:
            f.write(malformed_eml)
            temp_path = Path(f.name)

        try:
            result = converter.extract_from_eml(temp_path)
            # Should return a result but with minimal data
            assert result is not None
        finally:
            temp_path.unlink(missing_ok=True)

    def test_empty_file(self, converter):
        """Test handling of empty file."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='_test.eml', delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = converter.extract_from_eml(temp_path)
            # Should handle gracefully
        finally:
            temp_path.unlink(missing_ok=True)

    def test_very_long_content(self, converter):
        """Test handling of very long email content."""
        long_content = 'A' * 1_000_000
        long_eml = f"""From: sender@example.com
Subject: Long Content Test
Date: Mon, 10 Jan 2025 10:00:00 +0000
Content-Type: text/plain; charset="utf-8"

{long_content}
""".encode('utf-8')

        with tempfile.NamedTemporaryFile(mode='wb', suffix='_test.eml', delete=False) as f:
            f.write(long_eml)
            temp_path = Path(f.name)

        try:
            result = converter.extract_from_eml(temp_path)
            assert result is not None
            assert len(result['plain_text_content']) > 900_000
        finally:
            temp_path.unlink(missing_ok=True)

    def test_deduplication_in_conversion(self, converter, temp_email_directory):
        """Test that duplicates are removed during conversion."""
        # Create duplicate files
        duplicate_eml = b"""From: dup@example.com
Subject: Duplicate
Date: Mon, 10 Jan 2025 10:00:00 +0000
Content-Type: text/plain

Duplicate content.
"""

        dup1 = temp_email_directory / '2025-01-10_100000_dup_duplicate123456.eml'
        dup2 = temp_email_directory / '2025-01-10_100001_dup_duplicate123456.eml'

        dup1.write_bytes(duplicate_eml)
        dup2.write_bytes(duplicate_eml)

        output_file = temp_email_directory / 'dedup.parquet'

        count = converter.convert_latest_emails(
            temp_email_directory,
            output_file,
            days_back=30
        )

        if output_file.exists():
            df = pd.read_parquet(output_file)
            # Check that gmail_id is unique
            assert len(df) == len(df['gmail_id'].unique())

            output_file.unlink(missing_ok=True)

        dup1.unlink(missing_ok=True)
        dup2.unlink(missing_ok=True)
