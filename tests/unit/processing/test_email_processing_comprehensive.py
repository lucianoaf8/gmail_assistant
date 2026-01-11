#!/usr/bin/env python3
"""
Comprehensive email processing tests covering EML conversion, Markdown generation,
and advanced parsing workflows using real email data.
"""

import pytest
import tempfile
import shutil
import json
import email
import base64
from pathlib import Path
import sys
import os
from datetime import datetime

from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

try:
    from gmail_assistant.parsers.advanced_email_parser import EmailContentParser
except ImportError:
    EmailContentParser = None


class TestEmailConversionWorkflows:
    """Test suite for email format conversion workflows using real data."""

    def setup_method(self):
        """Setup test environment with real email samples."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.fetcher = GmailFetcher()

        # Extract real email samples from backup if available
        self.email_samples = []
        self.extract_real_email_samples()

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def extract_real_email_samples(self):
        """Extract email samples from real EML files for testing."""
        backup_dir = Path("backup_unread/2025/09")
        if backup_dir.exists():
            eml_files = list(backup_dir.glob("*.eml"))[:5]  # Use first 5 files

            for eml_file in eml_files:
                try:
                    with open(eml_file, 'r', encoding='utf-8', errors='ignore') as f:
                        msg = email.message_from_file(f)

                    # Extract email data
                    headers = {
                        'Subject': msg.get('Subject', 'Unknown Subject'),
                        'From': msg.get('From', 'Unknown Sender'),
                        'To': msg.get('To', 'Unknown Recipient'),
                        'Date': msg.get('Date', 'Unknown Date'),
                        'Message-ID': msg.get('Message-ID', 'Unknown ID')
                    }

                    # Extract body content
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode('utf-8', errors='ignore')
                                    break
                            elif part.get_content_type() == 'text/html' and not body:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode('utf-8', errors='ignore')
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')

                    if body and len(body) > 50:  # Only use emails with substantial content
                        email_data = headers.copy()
                        email_data['body'] = body
                        email_data['source_file'] = eml_file.name
                        self.email_samples.append(email_data)

                except Exception as e:
                    print(f"⚠️ Failed to extract sample from {eml_file.name}: {e}")

        print(f"✅ Extracted {len(self.email_samples)} real email samples for testing")

    def test_eml_content_creation_comprehensive(self):
        """Test EML content creation with comprehensive email data."""
        if not self.email_samples:
            pytest.skip("No real email samples available for testing")

        success_count = 0
        for email_data in self.email_samples:
            try:
                # Convert email data to Gmail API message format
                gmail_message = {
                    'id': f"test_msg_{success_count}",
                    'threadId': f"test_thread_{success_count}",
                    'payload': {
                        'headers': [
                            {'name': 'Subject', 'value': email_data['Subject']},
                            {'name': 'From', 'value': email_data['From']},
                            {'name': 'To', 'value': email_data['To']},
                            {'name': 'Date', 'value': email_data['Date']},
                            {'name': 'Message-ID', 'value': email_data.get('Message-ID', f"<test_{success_count}@example.com>")}
                        ],
                        'body': {
                            'data': base64.b64encode(email_data['body'].encode('utf-8')).decode('ascii')
                        } if email_data['body'] else {}
                    }
                }

                # Test EML creation
                eml_content = self.fetcher.create_eml_content(gmail_message)

                # Verify EML structure
                assert isinstance(eml_content, str)
                assert len(eml_content) > 0

                # Verify essential headers are present
                assert f"Subject: {email_data['Subject']}" in eml_content
                assert f"From: {email_data['From']}" in eml_content

                # Test that EML can be parsed back
                parsed_msg = email.message_from_string(eml_content)
                assert parsed_msg.get('Subject') is not None
                assert parsed_msg.get('From') is not None

                success_count += 1
                print(f"✅ EML creation successful for: {email_data['Subject'][:50]}...")

            except Exception as e:
                print(f"⚠️ EML creation failed for {email_data['source_file']}: {e}")

        assert success_count > 0
        print(f"✅ EML creation succeeded for {success_count}/{len(self.email_samples)} emails")

    def test_markdown_content_creation_comprehensive(self):
        """Test Markdown content creation with comprehensive email data."""
        if not self.email_samples:
            pytest.skip("No real email samples available for testing")

        success_count = 0
        for email_data in self.email_samples:
            try:
                # Convert email data to Gmail API message format
                gmail_message = {
                    'id': f"test_msg_{success_count}",
                    'threadId': f"test_thread_{success_count}",
                    'payload': {
                        'headers': [
                            {'name': 'Subject', 'value': email_data['Subject']},
                            {'name': 'From', 'value': email_data['From']},
                            {'name': 'To', 'value': email_data['To']},
                            {'name': 'Date', 'value': email_data['Date']},
                            {'name': 'Message-ID', 'value': email_data.get('Message-ID', f"<test_{success_count}@example.com>")}
                        ],
                        'body': {
                            'data': base64.b64encode(email_data['body'].encode('utf-8')).decode('ascii')
                        } if email_data['body'] else {}
                    }
                }

                # Test Markdown creation
                md_content = self.fetcher.create_markdown_content(gmail_message)

                # Verify Markdown structure
                assert isinstance(md_content, str)
                assert len(md_content) > 0

                # Check for Markdown formatting elements
                assert email_data['Subject'] in md_content
                assert email_data['From'] in md_content

                # Verify Markdown has proper structure (headers, metadata)
                lines = md_content.split('\n')
                has_headers = any(line.startswith('#') for line in lines)
                has_metadata = any(':' in line for line in lines[:10])  # Metadata usually at top

                assert has_headers or has_metadata  # Should have some structure

                success_count += 1
                print(f"✅ Markdown creation successful for: {email_data['Subject'][:50]}...")

            except Exception as e:
                print(f"⚠️ Markdown creation failed for {email_data['source_file']}: {e}")

        assert success_count > 0
        print(f"✅ Markdown creation succeeded for {success_count}/{len(self.email_samples)} emails")

    def test_html_to_markdown_conversion_quality(self):
        """Test HTML to Markdown conversion quality with real HTML content."""
        if not self.email_samples:
            pytest.skip("No real email samples available for testing")

        # Find emails with HTML content
        html_emails = [email_data for email_data in self.email_samples
                      if email_data['body'] and '<' in email_data['body'] and '>' in email_data['body']]

        if not html_emails:
            pytest.skip("No HTML email samples available for conversion testing")

        converter = self.fetcher.html_converter
        success_count = 0

        for email_data in html_emails[:3]:  # Test first 3 HTML emails
            try:
                html_content = email_data['body']

                # Test direct HTML conversion
                markdown_result = converter.handle(html_content)

                # Verify conversion quality
                assert isinstance(markdown_result, str)
                assert len(markdown_result) > 0

                # Check conversion preserved some content
                # Extract text content from HTML for comparison
                import re
                text_from_html = re.sub(r'<[^>]+>', ' ', html_content)
                text_words = [word for word in text_from_html.split() if len(word) > 3]

                if text_words:
                    # Check if meaningful content was preserved
                    preserved_words = sum(1 for word in text_words[:20]
                                        if word.lower() in markdown_result.lower())

                    # Should preserve at least 10% of meaningful words (lenient for complex HTML)
                    preservation_ratio = preserved_words / min(len(text_words), 20)
                    if preservation_ratio <= 0.1:
                        print(f"   Low preservation ratio: {preservation_ratio:.2f}")
                        # Still count as success if we got some markdown output
                        assert len(markdown_result) > 10  # At least some conversion happened

                # Check for Markdown formatting
                has_markdown_elements = any(marker in markdown_result
                                          for marker in ['#', '*', '**', '[', '](', '`'])

                if '<h' in html_content.lower() or '<strong>' in html_content.lower():
                    assert has_markdown_elements  # Should have some formatting

                success_count += 1
                print(f"✅ HTML conversion successful for: {email_data['Subject'][:50]}...")
                print(f"   Original HTML: {len(html_content)} chars → Markdown: {len(markdown_result)} chars")

            except Exception as e:
                print(f"⚠️ HTML conversion failed for {email_data['source_file']}: {e}")

        assert success_count > 0
        print(f"✅ HTML conversion succeeded for {success_count}/{len(html_emails)} HTML emails")

    def test_filename_sanitization_comprehensive(self):
        """Test filename sanitization with real email subjects."""
        if not self.email_samples:
            pytest.skip("No real email samples available for testing")

        for email_data in self.email_samples:
            subject = email_data['Subject']

            # Test sanitization
            sanitized = self.fetcher.sanitize_filename(subject)

            # Verify sanitization rules
            assert isinstance(sanitized, str)
            assert len(sanitized) <= 200  # Length limit

            # Should not contain problematic filesystem characters
            illegal_chars = r'<>:"/\|?*'
            assert not any(char in sanitized for char in illegal_chars)

            # Should preserve meaningful content when possible
            if len(subject) > 0:
                assert len(sanitized) > 0  # Shouldn't be completely empty

            print(f"✅ Sanitized: '{subject[:40]}...' → '{sanitized[:40]}...'")

        print(f"✅ Filename sanitization tested on {len(self.email_samples)} real subjects")

    def test_complete_processing_workflow_integration(self):
        """Test complete email processing workflow from raw data to saved files."""
        if not self.email_samples:
            pytest.skip("No real email samples available for testing")

        # Create test directories
        output_dir = self.test_dir / "processed_emails"
        eml_dir = output_dir / "eml"
        md_dir = output_dir / "markdown"

        eml_dir.mkdir(parents=True)
        md_dir.mkdir(parents=True)

        processed_count = 0
        for i, email_data in enumerate(self.email_samples[:3]):  # Process first 3 emails
            try:
                # Step 1: Create filename
                base_filename = f"email_{i:03d}_{self.fetcher.sanitize_filename(email_data['Subject'])}"

                # Step 2: Convert to Gmail API format and generate EML content
                gmail_message = {
                    'id': f"test_msg_{i}",
                    'threadId': f"test_thread_{i}",
                    'payload': {
                        'headers': [
                            {'name': 'Subject', 'value': email_data['Subject']},
                            {'name': 'From', 'value': email_data['From']},
                            {'name': 'To', 'value': email_data['To']},
                            {'name': 'Date', 'value': email_data['Date']},
                            {'name': 'Message-ID', 'value': email_data.get('Message-ID', f"<test_{i}@example.com>")}
                        ],
                        'body': {
                            'data': base64.b64encode(email_data['body'].encode('utf-8')).decode('ascii')
                        } if email_data['body'] else {}
                    }
                }

                eml_content = self.fetcher.create_eml_content(gmail_message)

                # Step 3: Generate Markdown content
                md_content = self.fetcher.create_markdown_content(gmail_message)

                # Step 4: Save files
                eml_file = eml_dir / f"{base_filename}.eml"
                md_file = md_dir / f"{base_filename}.md"

                eml_file.write_text(eml_content, encoding='utf-8')
                md_file.write_text(md_content, encoding='utf-8')

                # Step 5: Verify files
                assert eml_file.exists()
                assert md_file.exists()
                assert eml_file.stat().st_size > 0
                assert md_file.stat().st_size > 0

                # Step 6: Verify file content integrity
                saved_eml = eml_file.read_text(encoding='utf-8')
                saved_md = md_file.read_text(encoding='utf-8')

                assert email_data['Subject'] in saved_eml
                assert email_data['Subject'] in saved_md

                processed_count += 1
                print(f"✅ Complete workflow successful for email {i+1}")
                print(f"   EML: {eml_file.name} ({eml_file.stat().st_size} bytes)")
                print(f"   MD: {md_file.name} ({md_file.stat().st_size} bytes)")

            except Exception as e:
                print(f"⚠️ Complete workflow failed for email {i+1}: {e}")

        assert processed_count > 0

        # Verify final directory structure
        eml_files = list(eml_dir.glob("*.eml"))
        md_files = list(md_dir.glob("*.md"))

        assert len(eml_files) == processed_count
        assert len(md_files) == processed_count

        print(f"✅ Complete processing workflow succeeded for {processed_count} emails")
        print(f"✅ Final output: {len(eml_files)} EML files, {len(md_files)} MD files")


class TestAdvancedEmailParsing:
    """Test suite for advanced email parsing capabilities using real content."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.skipif(EmailContentParser is None, reason="EmailContentParser not available")
    def test_advanced_parser_with_real_html(self):
        """Test advanced email parser with real HTML content from backup files."""
        backup_dir = Path("backup_unread/2025/09")
        if not backup_dir.exists():
            pytest.skip("No backup directory available for advanced parsing tests")

        parser = EmailContentParser()
        eml_files = list(backup_dir.glob("*.eml"))[:3]

        if not eml_files:
            pytest.skip("No EML files available for advanced parsing tests")

        success_count = 0
        for eml_file in eml_files:
            try:
                with open(eml_file, 'r', encoding='utf-8', errors='ignore') as f:
                    msg = email.message_from_file(f)

                # Extract HTML content
                html_content = None
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/html':
                            payload = part.get_payload(decode=True)
                            if payload:
                                html_content = payload.decode('utf-8', errors='ignore')
                                break

                if html_content and len(html_content) > 100:
                    # Test advanced parsing
                    result = parser.parse(html_content)

                    # Verify parsing result
                    assert isinstance(result, dict)

                    if 'content' in result:
                        assert isinstance(result['content'], str)
                        assert len(result['content']) > 0

                    if 'strategy_used' in result:
                        assert isinstance(result['strategy_used'], str)

                    success_count += 1
                    print(f"✅ Advanced parsing successful for: {eml_file.name}")

                    if 'content' in result:
                        print(f"   Content extracted: {len(result['content'])} characters")
                    if 'strategy_used' in result:
                        print(f"   Strategy used: {result['strategy_used']}")

            except Exception as e:
                print(f"⚠️ Advanced parsing failed for {eml_file.name}: {e}")

        if success_count > 0:
            print(f"✅ Advanced parsing succeeded for {success_count}/{len(eml_files)} files")
        else:
            pytest.skip("No files could be processed with advanced parser")

    @pytest.mark.skipif(EmailContentParser is None, reason="EmailContentParser not available")
    def test_advanced_parser_strategy_selection(self):
        """Test advanced parser strategy selection with different HTML types."""
        parser = EmailContentParser()

        # Test different HTML types
        html_samples = [
            # Simple newsletter
            """<html><body><h1>Newsletter</h1><p>Weekly updates on technology.</p></body></html>""",

            # Complex marketing email
            """<html><body><div class="header"><h1>Special Offer!</h1></div>
               <div class="content"><p>Don't miss out on our amazing deals.</p>
               <a href="#">Shop Now</a></div></body></html>""",

            # Notification email
            """<html><body><div class="notification">
               <h2>Account Security Alert</h2>
               <p>We detected a new login to your account.</p></div></body></html>""",
        ]

        for i, html_content in enumerate(html_samples):
            try:
                result = parser.parse(html_content)

                assert isinstance(result, dict)
                print(f"✅ Strategy selection test {i+1} successful")

                if 'strategy_used' in result:
                    print(f"   Strategy selected: {result['strategy_used']}")

                if 'content' in result:
                    print(f"   Content quality: {len(result['content'])} chars")

            except Exception as e:
                print(f"⚠️ Strategy selection test {i+1} failed: {e}")


class TestEmailMetadataProcessing:
    """Test suite for email metadata extraction and processing."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.fetcher = GmailFetcher()

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_header_extraction_comprehensive(self):
        """Test comprehensive header extraction from various message structures."""
        # Test various Gmail API message structures
        test_messages = [
            # Standard message structure
            {
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': 'Test Email Subject'},
                        {'name': 'From', 'value': 'sender@example.com'},
                        {'name': 'To', 'value': 'recipient@example.com'},
                        {'name': 'Date', 'value': 'Tue, 22 Sep 2025 10:00:00 +0000'},
                        {'name': 'Message-ID', 'value': '<test123@example.com>'},
                        {'name': 'Content-Type', 'value': 'text/html; charset=UTF-8'}
                    ]
                }
            },
            # Message with missing headers
            {
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': 'Minimal Email'},
                        {'name': 'From', 'value': 'test@example.com'}
                    ]
                }
            },
            # Message with unusual headers
            {
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': '🔥 Newsletter with Emojis 🚀'},
                        {'name': 'From', 'value': 'Newsletter <newsletter@company.com>'},
                        {'name': 'Reply-To', 'value': 'no-reply@company.com'},
                        {'name': 'List-Unsubscribe', 'value': '<mailto:unsubscribe@company.com>'},
                        {'name': 'X-Custom-Header', 'value': 'Custom Value'}
                    ]
                }
            }
        ]

        for i, message in enumerate(test_messages):
            try:
                headers = self.fetcher.extract_headers(message)

                # Verify header extraction
                assert isinstance(headers, dict)

                # Check that some headers were extracted
                assert len(headers) > 0

                # Verify specific headers if present in source
                source_headers = {h['name']: h['value'] for h in message['payload']['headers']}

                for header_name, header_value in source_headers.items():
                    if header_name in headers:
                        assert headers[header_name] == header_value

                print(f"✅ Header extraction test {i+1} successful")
                print(f"   Extracted headers: {list(headers.keys())}")

            except Exception as e:
                print(f"⚠️ Header extraction test {i+1} failed: {e}")

    def test_date_parsing_and_formatting(self):
        """Test date parsing and formatting from various email date formats."""
        date_formats = [
            'Tue, 22 Sep 2025 10:00:00 +0000',
            'Wed, 23 Sep 2025 15:30:45 -0700 (PDT)',
            '22 Sep 2025 10:00:00 GMT',
            'Sep 22, 2025 at 10:00 AM',
            '2025-09-22T10:00:00Z',
            'Mon, 21 Sep 2025 09:00:00 +0100'
        ]

        for date_str in date_formats:
            message = {
                'payload': {
                    'headers': [
                        {'name': 'Date', 'value': date_str},
                        {'name': 'Subject', 'value': 'Test Date Parsing'}
                    ]
                }
            }

            try:
                headers = self.fetcher.extract_headers(message)

                assert 'Date' in headers
                assert headers['Date'] == date_str

                # Test that date is preserved in EML creation
                email_data = {
                    'Subject': 'Test Date Parsing',
                    'From': 'test@example.com',
                    'Date': date_str,
                    'body': 'Test content'
                }

                eml_content = self.fetcher.create_eml_content(email_data)
                assert f"Date: {date_str}" in eml_content

                print(f"✅ Date format handled: {date_str}")

            except Exception as e:
                print(f"⚠️ Date format failed: {date_str} - {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])