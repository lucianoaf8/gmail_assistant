"""
Comprehensive tests for analyze.py command module.
Tests analyze_emails function and analysis helpers.
"""

import json
from pathlib import Path
from unittest import mock

import pytest


class TestAnalyzeEmails:
    """Tests for analyze_emails function."""

    def test_analyze_nonexistent_directory(self, tmp_path):
        """Test analyze raises error for nonexistent directory."""
        from gmail_assistant.cli.commands.analyze import analyze_emails
        from gmail_assistant.core.exceptions import ConfigError

        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(ConfigError, match="not found"):
            analyze_emails(nonexistent)

    def test_analyze_empty_directory(self, tmp_path):
        """Test analyze with empty directory."""
        from gmail_assistant.cli.commands.analyze import analyze_emails

        result = analyze_emails(tmp_path)

        assert result['total'] == 0
        assert result['analyzed'] == 0

    def test_analyze_json_files(self, tmp_path):
        """Test analyze with JSON email files."""
        from gmail_assistant.cli.commands.analyze import analyze_emails

        # Create test JSON files
        for i in range(3):
            email_data = {
                'id': f'msg{i}',
                'subject': f'Test Subject {i}',
                'sender': f'test{i}@example.com'
            }
            (tmp_path / f"email_{i}.json").write_text(json.dumps(email_data))

        result = analyze_emails(tmp_path)

        assert result['metadata']['total_files'] == 3
        assert result['file_statistics']['by_extension']['.json'] == 3

    def test_analyze_eml_files(self, tmp_path):
        """Test analyze counts EML files."""
        from gmail_assistant.cli.commands.analyze import analyze_emails

        # Create test EML files
        for i in range(2):
            (tmp_path / f"email_{i}.eml").write_text(f"From: test{i}@example.com\nSubject: Test")

        result = analyze_emails(tmp_path)

        assert result['metadata']['total_files'] == 2
        assert result['file_statistics']['by_extension']['.eml'] == 2

    def test_analyze_mixed_files(self, tmp_path):
        """Test analyze with mixed file types."""
        from gmail_assistant.cli.commands.analyze import analyze_emails

        # Create mixed files
        (tmp_path / "email1.json").write_text('{"sender": "test@example.com"}')
        (tmp_path / "email2.eml").write_text("From: test@example.com")

        result = analyze_emails(tmp_path)

        assert result['metadata']['total_files'] == 2
        assert result['file_statistics']['by_extension']['.json'] == 1
        assert result['file_statistics']['by_extension']['.eml'] == 1

    def test_analyze_nested_directories(self, tmp_path):
        """Test analyze finds files in nested directories."""
        from gmail_assistant.cli.commands.analyze import analyze_emails

        # Create nested structure
        (tmp_path / "2024" / "01").mkdir(parents=True)
        (tmp_path / "2024" / "01" / "email.json").write_text('{"sender": "test@example.com"}')

        result = analyze_emails(tmp_path)

        assert result['metadata']['total_files'] == 1

    def test_analyze_report_summary(self, tmp_path, capsys):
        """Test analyze with summary report type."""
        from gmail_assistant.cli.commands.analyze import analyze_emails

        (tmp_path / "email.json").write_text('{"sender": "test@example.com"}')

        result = analyze_emails(tmp_path, report_type="summary")

        captured = capsys.readouterr()
        assert 'SUMMARY' in captured.out
        assert 'Analyzed:' in captured.out

    def test_analyze_report_detailed(self, tmp_path, capsys):
        """Test analyze with detailed report type."""
        from gmail_assistant.cli.commands.analyze import analyze_emails

        (tmp_path / "email.json").write_text('{"sender": "test@example.com"}')

        result = analyze_emails(tmp_path, report_type="detailed")

        captured = capsys.readouterr()
        assert 'DETAILED' in captured.out

    def test_analyze_report_json(self, tmp_path):
        """Test analyze with JSON report output to file."""
        from gmail_assistant.cli.commands.analyze import analyze_emails

        (tmp_path / "email.json").write_text('{"sender": "test@example.com"}')
        output_file = tmp_path / "output.json"

        result = analyze_emails(tmp_path, report_type="json", output_file=output_file)

        # Verify JSON was written to file
        assert output_file.exists()
        with open(output_file) as f:
            output_json = json.load(f)
        assert 'metadata' in output_json

    def test_analyze_output_to_file(self, tmp_path):
        """Test analyze saves report to file."""
        from gmail_assistant.cli.commands.analyze import analyze_emails

        (tmp_path / "email.json").write_text('{"sender": "test@example.com"}')
        output_file = tmp_path / "report.json"

        analyze_emails(tmp_path, report_type="json", output_file=output_file)

        assert output_file.exists()
        with open(output_file) as f:
            report = json.load(f)
        assert 'metadata' in report


class TestFileStatistics:
    """Tests for _analyze_file_statistics helper."""

    def test_file_statistics_counts_extensions(self, tmp_path):
        """Test file statistics counts by extension."""
        from gmail_assistant.cli.commands.analyze import _analyze_file_statistics

        files = [
            tmp_path / "test1.json",
            tmp_path / "test2.json",
            tmp_path / "test3.eml"
        ]
        for f in files:
            f.write_text("test")

        result = _analyze_file_statistics(files)

        assert result['by_extension']['.json'] == 2
        assert result['by_extension']['.eml'] == 1

    def test_file_statistics_calculates_size(self, tmp_path):
        """Test file statistics calculates total size."""
        from gmail_assistant.cli.commands.analyze import _analyze_file_statistics

        # Create files with known sizes
        file1 = tmp_path / "test1.json"
        file1.write_text("x" * 1000)  # 1000 bytes

        file2 = tmp_path / "test2.json"
        file2.write_text("y" * 500)  # 500 bytes

        result = _analyze_file_statistics([file1, file2])

        assert result['total_size_bytes'] == 1500
        assert result['total_size_mb'] == round(1500 / (1024 * 1024), 2)

    def test_file_statistics_handles_missing_file(self, tmp_path):
        """Test file statistics handles missing files gracefully."""
        from gmail_assistant.cli.commands.analyze import _analyze_file_statistics

        existing = tmp_path / "exists.json"
        existing.write_text("test")
        missing = tmp_path / "missing.json"

        result = _analyze_file_statistics([existing, missing])

        assert result['by_extension']['.json'] == 2  # Counted
        # Size should only include existing file


class TestTemporalDistribution:
    """Tests for _analyze_temporal_distribution helper."""

    def test_temporal_extracts_years(self, tmp_path):
        """Test temporal analysis extracts years from paths."""
        from gmail_assistant.cli.commands.analyze import _analyze_temporal_distribution

        (tmp_path / "2024").mkdir()
        (tmp_path / "2023").mkdir()
        files = [
            tmp_path / "2024" / "email1.json",
            tmp_path / "2024" / "email2.json",
            tmp_path / "2023" / "email3.json"
        ]
        for f in files:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("{}")

        result = _analyze_temporal_distribution(files)

        assert result['by_year']['2024'] == 2
        assert result['by_year']['2023'] == 1

    def test_temporal_extracts_months(self, tmp_path):
        """Test temporal analysis extracts months from paths."""
        from gmail_assistant.cli.commands.analyze import _analyze_temporal_distribution

        (tmp_path / "2024" / "01").mkdir(parents=True)
        (tmp_path / "2024" / "02").mkdir(parents=True)
        files = [
            tmp_path / "2024" / "01" / "email1.json",
            tmp_path / "2024" / "02" / "email2.json"
        ]
        for f in files:
            f.write_text("{}")

        result = _analyze_temporal_distribution(files)

        assert result['by_month']['01'] == 1
        assert result['by_month']['02'] == 1


class TestSenderAnalysis:
    """Tests for _analyze_senders helper."""

    def test_sender_analysis_counts_senders(self):
        """Test sender analysis counts unique senders."""
        from gmail_assistant.cli.commands.analyze import _analyze_senders

        emails = [
            {'sender': 'user1@example.com'},
            {'sender': 'user1@example.com'},
            {'sender': 'user2@example.com'}
        ]

        result = _analyze_senders(emails)

        assert result['unique_senders'] == 2
        assert result['top_senders']['user1@example.com'] == 2
        assert result['top_senders']['user2@example.com'] == 1

    def test_sender_analysis_uses_from_field(self):
        """Test sender analysis falls back to 'from' field."""
        from gmail_assistant.cli.commands.analyze import _analyze_senders

        emails = [
            {'from': 'user@example.com'}
        ]

        result = _analyze_senders(emails)

        assert result['unique_senders'] == 1
        assert 'user@example.com' in result['top_senders']

    def test_sender_analysis_limits_top_senders(self):
        """Test sender analysis limits to top 20."""
        from gmail_assistant.cli.commands.analyze import _analyze_senders

        emails = [{'sender': f'user{i}@example.com'} for i in range(30)]

        result = _analyze_senders(emails)

        assert len(result['top_senders']) <= 20

    def test_sender_analysis_sorts_by_count(self):
        """Test top senders are sorted by count."""
        from gmail_assistant.cli.commands.analyze import _analyze_senders

        emails = [
            {'sender': 'rare@example.com'},
            {'sender': 'common@example.com'},
            {'sender': 'common@example.com'},
            {'sender': 'common@example.com'}
        ]

        result = _analyze_senders(emails)

        top_senders = list(result['top_senders'].keys())
        assert top_senders[0] == 'common@example.com'


class TestEmailClassification:
    """Tests for _classify_emails helper."""

    def test_classify_financial_emails(self):
        """Test classification of financial emails."""
        from gmail_assistant.cli.commands.analyze import _classify_emails

        emails = [
            {'subject': 'Your payment receipt', 'sender': 'bank@example.com'},
            {'subject': 'Invoice #12345', 'sender': 'billing@example.com'}
        ]

        result = _classify_emails(emails)

        assert result['counts']['Financial'] == 2

    def test_classify_notification_emails(self):
        """Test classification of notification emails."""
        from gmail_assistant.cli.commands.analyze import _classify_emails

        emails = [
            {'subject': 'Notification: Update available', 'sender': 'service@example.com'},
            {'subject': 'Alert: New login', 'sender': 'security@example.com'}
        ]

        result = _classify_emails(emails)

        assert result['counts']['Notifications'] == 2

    def test_classify_marketing_emails(self):
        """Test classification of marketing emails."""
        from gmail_assistant.cli.commands.analyze import _classify_emails

        emails = [
            {'subject': 'Weekly Newsletter', 'sender': 'news@example.com'},
            {'subject': 'Special Offer!', 'sender': 'deals@example.com'}
        ]

        result = _classify_emails(emails)

        assert result['counts']['Marketing'] == 2

    def test_classify_social_emails(self):
        """Test classification of social emails."""
        from gmail_assistant.cli.commands.analyze import _classify_emails

        emails = [
            {'subject': 'John sent you a friend request', 'sender': 'social@example.com'},
            {'subject': 'Someone liked your post', 'sender': 'network@example.com'}
        ]

        result = _classify_emails(emails)

        assert result['counts']['Social'] == 2

    def test_classify_other_emails(self):
        """Test classification of uncategorized emails."""
        from gmail_assistant.cli.commands.analyze import _classify_emails

        emails = [
            {'subject': 'Hello there', 'sender': 'person@example.com'},
            {'subject': 'Meeting tomorrow', 'sender': 'colleague@example.com'}
        ]

        result = _classify_emails(emails)

        assert result['counts']['Other'] == 2

    def test_classify_calculates_percentages(self):
        """Test classification calculates percentages."""
        from gmail_assistant.cli.commands.analyze import _classify_emails

        # Use clear, unambiguous emails for each category
        emails = [
            {'subject': 'Your payment invoice', 'sender': 'bank@example.com'},  # Financial
            {'subject': 'Random email 1', 'sender': 'random1@example.com'},  # Other
            {'subject': 'Random email 2', 'sender': 'random2@example.com'},  # Other
            {'subject': 'Random email 3', 'sender': 'random3@example.com'}   # Other
        ]

        result = _classify_emails(emails)

        # Verify percentages add up to 100%
        total_pct = sum(result['percentages'].values())
        assert total_pct == 100.0
        # Verify Financial got 25% (1 out of 4)
        assert result['percentages']['Financial'] == 25.0

    def test_classify_handles_none_values(self):
        """Test classification handles None values."""
        from gmail_assistant.cli.commands.analyze import _classify_emails

        emails = [
            {'subject': None, 'sender': None},
            {'subject': 'Test', 'sender': 'test@example.com'}
        ]

        result = _classify_emails(emails)

        total = sum(result['counts'].values())
        assert total == 2

    def test_classify_empty_list(self):
        """Test classification handles empty list."""
        from gmail_assistant.cli.commands.analyze import _classify_emails

        result = _classify_emails([])

        # Should not raise, percentages should be 0
        assert result['percentages']['Financial'] == 0


class TestReportOutput:
    """Tests for report output functions."""

    def test_summary_report_output(self, tmp_path, capsys):
        """Test summary report outputs to console."""
        from gmail_assistant.cli.commands.analyze import _output_summary_report

        analysis = {
            'metadata': {
                'total_files': 10,
                'analysis_timestamp': '2024-01-15T10:00:00'
            },
            'file_statistics': {
                'total_size_mb': 1.5,
                'by_extension': {'.json': 10}
            },
            'category_summary': {
                'percentages': {'Financial': 50.0, 'Other': 50.0}
            },
            'sender_summary': {
                'unique_senders': 5,
                'top_senders': {'test@example.com': 3}
            }
        }

        _output_summary_report(analysis)

        captured = capsys.readouterr()
        assert 'EMAIL ANALYSIS SUMMARY' in captured.out
        assert '10 files' in captured.out

    def test_json_report_to_file(self, tmp_path):
        """Test JSON report saves to file."""
        from gmail_assistant.cli.commands.analyze import _output_json_report

        analysis = {'metadata': {'test': True}}
        output_file = tmp_path / "report.json"

        _output_json_report(analysis, output_file)

        assert output_file.exists()
        with open(output_file) as f:
            saved = json.load(f)
        assert saved['metadata']['test'] is True

    def test_json_report_to_console(self, capsys):
        """Test JSON report outputs to console when no file specified."""
        from gmail_assistant.cli.commands.analyze import _output_json_report

        analysis = {'metadata': {'test': True}}

        _output_json_report(analysis, None)

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output['metadata']['test'] is True

    def test_detailed_report_saves_file(self, tmp_path, capsys):
        """Test detailed report saves to file when specified."""
        from gmail_assistant.cli.commands.analyze import _output_detailed_report

        analysis = {
            'metadata': {
                'total_files': 10,
                'analysis_timestamp': '2024-01-15T10:00:00'
            },
            'file_statistics': {
                'total_size_mb': 1.5,
                'by_extension': {'.json': 10}
            },
            'temporal_distribution': {
                'by_year': {'2024': 10},
                'by_month': {}
            },
            'category_summary': {},
            'sender_summary': {
                'unique_senders': 5,
                'top_senders': {}
            }
        }

        output_file = tmp_path / "detailed.json"
        _output_detailed_report(analysis, output_file)

        assert output_file.exists()
        captured = capsys.readouterr()
        assert 'saved to' in captured.out
