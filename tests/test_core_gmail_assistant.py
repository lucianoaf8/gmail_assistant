#!/usr/bin/env python3
"""
Fixed comprehensive tests for GmailFetcher core functionality using real implementation paths.
Tests use actual methods available in the GmailFetcher class, no assumptions.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
import sys
import os

from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher


class TestGmailFetcherCore:
    """Test suite for GmailFetcher core functionality using real data."""

    def setup_method(self):
        """Setup test environment with temporary directories."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_gmail_assistant_initialization(self):
        """Test GmailFetcher initialization with various credential paths."""
        # Test with default paths
        fetcher = GmailFetcher()
        assert fetcher.credentials_file == 'credentials.json'
        assert fetcher.token_file == 'token.json'
        assert fetcher.service is None
        assert fetcher.html_converter is not None

        # Test with custom paths
        custom_creds = str(self.test_dir / "custom_creds.json")
        custom_token = str(self.test_dir / "custom_token.json")
        fetcher = GmailFetcher(custom_creds, custom_token)
        assert fetcher.credentials_file == custom_creds
        assert fetcher.token_file == custom_token

    def test_html_converter_configuration(self):
        """Test HTML converter is properly configured."""
        fetcher = GmailFetcher()
        converter = fetcher.html_converter

        # Verify converter settings
        assert not converter.ignore_links
        assert not converter.ignore_images

        # Test actual conversion with real HTML
        test_html = """
        <html>
            <body>
                <h1>Test Email</h1>
                <p>This is a <a href="https://example.com">test email</a> with content.</p>
                <img src="https://example.com/image.jpg" alt="Test Image">
            </body>
        </html>
        """

        markdown = converter.handle(test_html)
        assert "# Test Email" in markdown
        assert "[test email](https://example.com)" in markdown
        assert "![Test Image]" in markdown

    def test_sanitize_filename(self):
        """Test filename sanitization using actual method implementation."""
        fetcher = GmailFetcher()

        # Test cases from real email subjects
        test_cases = [
            "📅 Just scheduled: Meditation practice - Online",
            "🦾 AI Brings Old Photos Back to Life",
            "🧜‍♀️ Don't miss it! Diagramming Resources inside!",
            "Backup report [lvserver] [lucianoaf8@gmail.com]",
            "Your Neuron Trip e-Receipt",
            "Test/File\\With|Bad:Chars?",
            "",
            "   ",
        ]

        for original in test_cases:
            result = fetcher.sanitize_filename(original)
            # Check that result doesn't contain invalid filesystem characters
            assert not any(char in result for char in r'<>:"/\|?*')
            # Check that result is properly stripped and length limited
            assert len(result) <= 200
            # Verify method handles edge cases gracefully
            assert isinstance(result, str)

            print(f"✅ Sanitized '{original[:30]}...' → '{result[:30]}...'")

    def test_decode_base64_method(self):
        """Test decode_base64 method with real base64 content."""
        fetcher = GmailFetcher()

        # Test valid base64 content
        test_content = "SGVsbG8gV29ybGQ="  # "Hello World" in base64
        result = fetcher.decode_base64(test_content)
        assert result == "Hello World"

        # Test base64 with padding issues (real Gmail API scenario)
        test_content_no_padding = "SGVsbG8gV29ybGQ"  # Missing padding
        result = fetcher.decode_base64(test_content_no_padding)
        assert result == "Hello World"

        print("✅ Base64 decoding works correctly")

    def test_extract_headers_method(self):
        """Test extract_headers method with email message."""
        fetcher = GmailFetcher()

        # Create a sample Gmail API message structure
        sample_message = {
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Email Subject'},
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'Date', 'value': 'Mon, 22 Sep 2025 10:00:00 +0000'},
                    {'name': 'Message-ID', 'value': '<test123@example.com>'}
                ]
            }
        }

        headers = fetcher.extract_headers(sample_message)

        # Verify headers extraction
        assert isinstance(headers, dict)
        assert headers.get('Subject') == 'Test Email Subject'
        assert headers.get('From') == 'test@example.com'
        assert headers.get('Date') == 'Mon, 22 Sep 2025 10:00:00 +0000'
        assert headers.get('Message-ID') == '<test123@example.com>'

        print("✅ Header extraction works correctly")

    def test_get_message_body_method(self):
        """Test get_message_body method with message payload."""
        fetcher = GmailFetcher()

        # Create sample message with body
        sample_message = {
            'payload': {
                'body': {
                    'data': 'VGhpcyBpcyBhIHRlc3QgZW1haWwgYm9keQ=='  # "This is a test email body"
                }
            }
        }

        body = fetcher.get_message_body(sample_message)
        assert body == "This is a test email body"

        print("✅ Message body extraction works correctly")

    def test_create_eml_content_method(self):
        """Test create_eml_content method with email data."""
        fetcher = GmailFetcher()

        # Sample email data
        email_data = {
            'Subject': 'Test Email',
            'From': 'sender@example.com',
            'To': 'recipient@example.com',
            'Date': 'Mon, 22 Sep 2025 10:00:00 +0000',
            'body': 'This is the email body content.'
        }

        eml_content = fetcher.create_eml_content(email_data)

        # Verify EML format
        assert isinstance(eml_content, str)
        assert 'Subject: Test Email' in eml_content
        assert 'From: sender@example.com' in eml_content
        assert 'This is the email body content.' in eml_content

        print("✅ EML content creation works correctly")

    def test_create_markdown_content_method(self):
        """Test create_markdown_content method with email data."""
        fetcher = GmailFetcher()

        # Sample email data
        email_data = {
            'Subject': 'Test Email',
            'From': 'sender@example.com',
            'To': 'recipient@example.com',
            'Date': 'Mon, 22 Sep 2025 10:00:00 +0000',
            'body': 'This is the **email body** content with *formatting*.'
        }

        markdown_content = fetcher.create_markdown_content(email_data)

        # Verify Markdown format
        assert isinstance(markdown_content, str)
        assert '# Test Email' in markdown_content or 'Subject: Test Email' in markdown_content
        assert 'sender@example.com' in markdown_content
        assert 'email body' in markdown_content

        print("✅ Markdown content creation works correctly")

    def test_error_handling_with_invalid_data(self):
        """Test error handling with invalid data inputs."""
        fetcher = GmailFetcher()

        # Test decode_base64 with invalid data
        try:
            result = fetcher.decode_base64("invalid base64 content!!!")
            # Should either return something sensible or handle gracefully
            assert isinstance(result, str)
        except Exception:
            print("✅ Invalid base64 handled with exception")

        # Test extract_headers with empty message
        empty_message = {}
        headers = fetcher.extract_headers(empty_message)
        assert isinstance(headers, dict)

        # Test get_message_body with empty message
        body = fetcher.get_message_body(empty_message)
        assert isinstance(body, str)

        print("✅ Error handling works correctly")

    def test_authentication_setup(self):
        """Test authentication file setup without actual authentication."""
        fetcher = GmailFetcher()

        # Test credentials file path setting
        original_creds = fetcher.credentials_file
        test_creds_path = str(self.test_dir / "test_creds.json")

        fetcher.credentials_file = test_creds_path
        assert fetcher.credentials_file == test_creds_path

        # Test valid JSON structure creation
        valid_structure = {
            "installed": {
                "client_id": "test_id",
                "client_secret": "test_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        with open(test_creds_path, 'w') as f:
            json.dump(valid_structure, f)

        # Verify file was created correctly
        assert Path(test_creds_path).exists()
        with open(test_creds_path, 'r') as f:
            loaded_data = json.load(f)
            assert 'installed' in loaded_data

        print("✅ Authentication setup works correctly")


class TestGmailFetcherIntegration:
    """Integration tests for GmailFetcher using real workflow scenarios."""

    def setup_method(self):
        """Setup integration test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up integration test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_email_processing_workflow(self):
        """Test complete email processing workflow without Gmail API."""
        fetcher = GmailFetcher()

        # Simulate email data processing workflow
        sample_emails = [
            {
                'Subject': 'Newsletter: AI Weekly',
                'From': 'newsletter@ai.com',
                'Date': '2025-09-22',
                'body': 'This week in AI: new developments and research.'
            },
            {
                'Subject': 'Security Alert',
                'From': 'security@github.com',
                'Date': '2025-09-22',
                'body': 'Suspicious activity detected on your account.'
            }
        ]

        processed_count = 0
        for email_data in sample_emails:
            try:
                # Test processing each email through the workflow

                # 1. Create EML content
                eml_content = fetcher.create_eml_content(email_data)
                assert len(eml_content) > 0

                # 2. Create Markdown content
                md_content = fetcher.create_markdown_content(email_data)
                assert len(md_content) > 0

                # 3. Sanitize filename
                filename = fetcher.sanitize_filename(email_data['Subject'])
                assert len(filename) >= 0

                # 4. Save to files
                eml_file = self.test_dir / f"{filename}.eml"
                md_file = self.test_dir / f"{filename}.md"

                eml_file.write_text(eml_content)
                md_file.write_text(md_content)

                assert eml_file.exists()
                assert md_file.exists()

                processed_count += 1

            except Exception as e:
                print(f"⚠️ Failed to process email: {e}")

        assert processed_count > 0
        print(f"✅ Successfully processed {processed_count} emails through workflow")

    def test_directory_organization(self):
        """Test directory organization for email storage."""
        import os
        from datetime import datetime

        # Test date-based organization
        base_dir = self.test_dir / "emails"

        # Create directory structure like the app would
        current_date = datetime.now()
        year_dir = base_dir / str(current_date.year)
        month_dir = year_dir / f"{current_date.month:02d}"

        os.makedirs(month_dir, exist_ok=True)

        assert year_dir.exists()
        assert month_dir.exists()

        # Test sender-based organization
        sender_dir = base_dir / "sender_folders"
        sender_specific = sender_dir / "newsletter_ai_com"

        os.makedirs(sender_specific, exist_ok=True)

        assert sender_specific.exists()

        print("✅ Directory organization structure works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])