"""
Comprehensive tests for extractor.py module.
Tests EmailDataExtractor class for email data extraction operations.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest


class TestEmailDataExtractorInit:
    """Tests for EmailDataExtractor initialization."""

    def test_init_default_output(self, tmp_path):
        """Test initialization with default output folder."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor

        extractor = EmailDataExtractor(str(tmp_path / "input"))
        assert extractor.output_folder == Path("monthly_email_data")

    def test_init_custom_output(self, tmp_path):
        """Test initialization with custom output folder."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor

        input_folder = tmp_path / "input"
        output_folder = tmp_path / "output"

        extractor = EmailDataExtractor(str(input_folder), str(output_folder))
        assert extractor.output_folder == output_folder

    def test_init_creates_output_folder(self, tmp_path):
        """Test initialization creates output folder."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor

        input_folder = tmp_path / "input"
        output_folder = tmp_path / "output"

        assert not output_folder.exists()
        extractor = EmailDataExtractor(str(input_folder), str(output_folder))
        assert output_folder.exists()


class TestParseDate:
    """Tests for parse_date method."""

    @pytest.fixture
    def extractor(self, tmp_path):
        """Create extractor instance."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor
        return EmailDataExtractor(str(tmp_path / "input"), str(tmp_path / "output"))

    def test_parse_rfc_2822_format(self, extractor):
        """Test parsing RFC 2822 date format."""
        date_str = "Mon, 15 Jan 2024 10:30:00 +0000"
        result = extractor.parse_date(date_str)

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_iso_format(self, extractor):
        """Test parsing ISO date format."""
        date_str = "2024-01-15 10:30:00"
        result = extractor.parse_date(date_str)

        assert result is not None
        assert result.year == 2024
        assert result.month == 1

    def test_parse_date_only(self, extractor):
        """Test parsing date only format."""
        date_str = "2024-01-15"
        result = extractor.parse_date(date_str)

        assert result is not None
        assert result.year == 2024

    def test_parse_empty_string(self, extractor):
        """Test parsing empty string returns None."""
        result = extractor.parse_date("")
        assert result is None

    def test_parse_none(self, extractor):
        """Test parsing None returns None."""
        result = extractor.parse_date(None)
        assert result is None

    def test_parse_with_timezone_annotation(self, extractor):
        """Test parsing date with timezone annotation."""
        date_str = "Mon, 15 Jan 2024 10:30:00 +0000 (UTC)"
        result = extractor.parse_date(date_str)

        assert result is not None
        assert result.year == 2024

    def test_parse_day_month_year_format(self, extractor):
        """Test parsing DD Mon YYYY format."""
        date_str = "15 Jan 2024"
        result = extractor.parse_date(date_str)

        assert result is not None
        assert result.year == 2024
        assert result.month == 1


class TestExtractEmailMetadata:
    """Tests for extract_email_metadata method."""

    @pytest.fixture
    def extractor(self, tmp_path):
        """Create extractor instance."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor
        return EmailDataExtractor(str(tmp_path / "input"), str(tmp_path / "output"))

    def test_extract_from_markdown_file(self, extractor, tmp_path):
        """Test extracting metadata from markdown file."""
        md_file = tmp_path / "2024-01-15_100000_test_abc123.md"
        md_content = """# Email

| Field | Value |
| --- | --- |
| Date | Mon, 15 Jan 2024 10:00:00 +0000 |
| From | sender@example.com |
| To | recipient@example.com |
| Subject | Test Subject |
| Gmail ID | msg123 |
| Thread ID | thread123 |
| Labels | INBOX,UNREAD |

## Message Content

This is the email body content.
"""
        md_file.write_text(md_content)

        result = extractor.extract_email_metadata(md_file)

        assert result is not None
        assert result['sender'] == 'sender@example.com'
        assert result['subject'] == 'Test Subject'
        assert result['gmail_id'] == 'msg123'
        assert 'message_content' in result

    def test_extract_with_missing_fields(self, extractor, tmp_path):
        """Test extracting with missing fields."""
        md_file = tmp_path / "2024-01-15_100000_test_abc123.md"
        md_content = """# Email

| Field | Value |
| --- | --- |
| Subject | Only Subject |

## Message Content

Content here.
"""
        md_file.write_text(md_content)

        result = extractor.extract_email_metadata(md_file)

        assert result is not None
        assert result['subject'] == 'Only Subject'
        assert result['sender'] == ''

    def test_extract_handles_error(self, extractor, tmp_path):
        """Test extracting handles errors gracefully."""
        nonexistent_file = tmp_path / "nonexistent.md"

        result = extractor.extract_email_metadata(nonexistent_file)

        assert result is None


class TestFindMdFilesManually:
    """Tests for find_md_files_manually method."""

    @pytest.fixture
    def extractor(self, tmp_path):
        """Create extractor instance."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor
        input_folder = tmp_path / "input"
        input_folder.mkdir()
        return EmailDataExtractor(str(input_folder), str(tmp_path / "output"))

    def test_find_md_files_fallback(self, extractor, tmp_path):
        """Test finding markdown files with fallback."""
        # Create input folder and files
        input_folder = tmp_path / "input"
        input_folder.mkdir(exist_ok=True)

        md_file = input_folder / "test.md"
        md_file.write_text("# Test")

        # Test the Python fallback method directly
        result = extractor.find_md_files_python_fallback()

        assert len(result) >= 1


class TestFindMdFilesPythonFallback:
    """Tests for find_md_files_python_fallback method."""

    def test_finds_md_files(self, tmp_path):
        """Test finding markdown files."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor

        input_folder = tmp_path / "input"
        input_folder.mkdir()
        (input_folder / "test1.md").write_text("# Test 1")
        (input_folder / "test2.md").write_text("# Test 2")
        (input_folder / "test.txt").write_text("Not markdown")

        extractor = EmailDataExtractor(str(input_folder), str(tmp_path / "output"))
        result = extractor.find_md_files_python_fallback()

        md_files = [f for f in result if f.suffix == '.md']
        assert len(md_files) == 2

    def test_finds_nested_md_files(self, tmp_path):
        """Test finding nested markdown files."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor

        input_folder = tmp_path / "input"
        input_folder.mkdir()
        nested_folder = input_folder / "nested"
        nested_folder.mkdir()
        (nested_folder / "nested.md").write_text("# Nested")

        extractor = EmailDataExtractor(str(input_folder), str(tmp_path / "output"))
        result = extractor.find_md_files_python_fallback()

        assert len(result) >= 1


class TestProcessAllEmails:
    """Tests for process_all_emails method."""

    def test_process_empty_folder(self, tmp_path):
        """Test processing empty folder."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor

        input_folder = tmp_path / "input"
        input_folder.mkdir()

        extractor = EmailDataExtractor(str(input_folder), str(tmp_path / "output"))
        stats = extractor.process_all_emails()

        assert stats['total_processed'] == 0
        assert stats['successful_extractions'] == 0

    def test_process_valid_files(self, tmp_path):
        """Test processing valid markdown files."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor

        input_folder = tmp_path / "input"
        input_folder.mkdir()

        # Create valid markdown file
        md_file = input_folder / "2024-01-15_100000_test_abc123.md"
        md_content = """# Email

| Field | Value |
| --- | --- |
| Date | Mon, 15 Jan 2024 10:00:00 +0000 |
| From | sender@example.com |
| Subject | Test |

## Message Content

Content.
"""
        md_file.write_text(md_content)

        extractor = EmailDataExtractor(str(input_folder), str(tmp_path / "output"))
        stats = extractor.process_all_emails()

        assert stats['total_processed'] == 1
        assert stats['successful_extractions'] == 1

    def test_process_creates_monthly_json(self, tmp_path):
        """Test processing creates monthly JSON files."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor

        input_folder = tmp_path / "input"
        input_folder.mkdir()
        output_folder = tmp_path / "output"

        # Create valid markdown file
        md_file = input_folder / "2024-01-15_100000_test_abc123.md"
        md_content = """# Email

| Field | Value |
| --- | --- |
| Date | Mon, 15 Jan 2024 10:00:00 +0000 |
| From | sender@example.com |
| Subject | Test |

## Message Content

Content.
"""
        md_file.write_text(md_content)

        extractor = EmailDataExtractor(str(input_folder), str(output_folder))
        stats = extractor.process_all_emails()

        # Check for monthly JSON file
        json_files = list(output_folder.glob("*_emails.json"))
        assert stats['months_created'] == len(json_files)


class TestGenerateSummaryReport:
    """Tests for generate_summary_report method."""

    def test_generate_summary_report(self, tmp_path):
        """Test generating summary report."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor

        output_folder = tmp_path / "output"
        output_folder.mkdir()

        extractor = EmailDataExtractor(str(tmp_path / "input"), str(output_folder))

        stats = {
            'total_processed': 100,
            'successful_extractions': 95,
            'failed_extractions': 5,
            'months_created': 3
        }

        extractor.generate_summary_report(stats)

        # Verify summary file was created
        summary_file = output_folder / "extraction_summary.json"
        assert summary_file.exists()

        # Verify content
        with open(summary_file) as f:
            summary = json.load(f)

        assert summary['extraction_summary']['total_files_processed'] == 100
        assert summary['extraction_summary']['successful_extractions'] == 95
        assert summary['extraction_summary']['success_rate'] == "95.0%"

    def test_generate_summary_report_zero_processed(self, tmp_path):
        """Test generating summary report with zero processed raises ZeroDivisionError.

        Note: The current implementation doesn't handle the zero-division case.
        This test documents the current behavior.
        """
        from gmail_assistant.core.processing.extractor import EmailDataExtractor

        output_folder = tmp_path / "output"
        output_folder.mkdir()

        extractor = EmailDataExtractor(str(tmp_path / "input"), str(output_folder))

        stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'months_created': 0
        }

        # Current implementation raises ZeroDivisionError when total_processed is 0
        with pytest.raises(ZeroDivisionError):
            extractor.generate_summary_report(stats)


class TestExtractorDateFormats:
    """Additional tests for date format handling."""

    @pytest.fixture
    def extractor(self, tmp_path):
        """Create extractor instance."""
        from gmail_assistant.core.processing.extractor import EmailDataExtractor
        return EmailDataExtractor(str(tmp_path / "input"), str(tmp_path / "output"))

    def test_parse_date_without_day_name(self, extractor):
        """Test parsing date without day name."""
        date_str = "15 Jan 2024 10:30:00 +0000"
        result = extractor.parse_date(date_str)

        assert result is not None
        assert result.year == 2024

    def test_parse_date_iso_with_timezone(self, extractor):
        """Test parsing ISO date with timezone."""
        date_str = "2024-01-15 10:30:00 +0000"
        result = extractor.parse_date(date_str)

        assert result is not None
        assert result.year == 2024

    def test_parse_date_extracts_embedded_date(self, extractor):
        """Test parsing extracts embedded date pattern."""
        date_str = "Some text 2024-01-15 more text"
        result = extractor.parse_date(date_str)

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
