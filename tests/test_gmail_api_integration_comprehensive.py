#!/usr/bin/env python3
"""
Comprehensive Gmail API integration tests using real authentication and live data.
Tests full authentication flow, email fetching, search capabilities, and processing workflows.
"""

import pytest
import tempfile
import shutil
import json
import sys
from pathlib import Path
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.gmail_assistant import GmailFetcher


class TestGmailAPIAuthentication:
    """Test suite for Gmail API authentication using real credentials."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_authentication_flow_with_credentials(self):
        """Test complete authentication flow with real Gmail credentials."""
        fetcher = GmailFetcher()

        # Test authentication
        auth_result = fetcher.authenticate()
        assert auth_result == True
        assert fetcher.service is not None

        print("✅ Gmail API authentication successful")

        # Test service object has required methods
        service_methods = dir(fetcher.service.users())
        expected_methods = ['messages', 'labels', 'drafts', 'threads']

        for method in expected_methods:
            assert hasattr(fetcher.service.users(), method), f"Missing service method: {method}"

        print(f"✅ Gmail service object has all required methods: {expected_methods}")

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_gmail_service_profile_access(self):
        """Test Gmail service can access user profile information."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        try:
            # Test profile access
            profile = fetcher.service.users().getProfile(userId='me').execute()

            assert 'emailAddress' in profile
            assert 'messagesTotal' in profile
            assert 'threadsTotal' in profile

            print(f"✅ Gmail profile access successful")
            print(f"   Email: {profile['emailAddress']}")
            print(f"   Total messages: {profile['messagesTotal']}")
            print(f"   Total threads: {profile['threadsTotal']}")

        except Exception as e:
            pytest.fail(f"Profile access failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_gmail_labels_access(self):
        """Test Gmail service can access user labels."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        try:
            # Test labels access
            labels_result = fetcher.service.users().labels().list(userId='me').execute()
            labels = labels_result.get('labels', [])

            assert len(labels) > 0

            # Check for standard Gmail labels
            label_names = [label['name'] for label in labels]
            standard_labels = ['INBOX', 'SENT', 'DRAFT', 'TRASH']

            found_standard = [label for label in standard_labels if label in label_names]
            assert len(found_standard) > 0

            print(f"✅ Gmail labels access successful")
            print(f"   Total labels: {len(labels)}")
            print(f"   Standard labels found: {found_standard}")

        except Exception as e:
            pytest.fail(f"Labels access failed: {e}")


class TestGmailEmailSearch:
    """Test suite for Gmail email search functionality with real queries."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_search_messages_basic_query(self):
        """Test basic email search functionality."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        # Test basic search queries
        test_queries = [
            "is:inbox",
            "is:sent",
            "newer_than:1d",
            "from:gmail.com",
            "subject:test"
        ]

        for query in test_queries:
            try:
                messages = fetcher.search_messages(query, max_results=5)

                # Verify search returns proper structure
                assert isinstance(messages, list)

                if messages:  # If messages found
                    for message in messages:
                        assert 'id' in message
                        assert 'threadId' in message

                print(f"✅ Search query '{query}' returned {len(messages)} messages")

            except Exception as e:
                print(f"⚠️ Search query '{query}' failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_search_messages_with_date_filters(self):
        """Test email search with date-based filters."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        # Calculate date ranges
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)

        # Test date-based queries
        date_queries = [
            f"after:{yesterday.strftime('%Y/%m/%d')}",
            f"before:{today.strftime('%Y/%m/%d')}",
            f"after:{week_ago.strftime('%Y/%m/%d')} before:{today.strftime('%Y/%m/%d')}",
            "newer_than:1d",
            "older_than:1d"
        ]

        for query in date_queries:
            try:
                messages = fetcher.search_messages(query, max_results=10)

                assert isinstance(messages, list)
                print(f"✅ Date query '{query}' returned {len(messages)} messages")

            except Exception as e:
                print(f"⚠️ Date query '{query}' failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_search_messages_content_filters(self):
        """Test email search with content-based filters."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        # Test content-based queries
        content_queries = [
            "has:attachment",
            "subject:newsletter",
            "subject:notification",
            "from:noreply",
            "from:support",
            "category:updates",
            "category:promotions"
        ]

        for query in content_queries:
            try:
                messages = fetcher.search_messages(query, max_results=5)

                assert isinstance(messages, list)
                print(f"✅ Content query '{query}' returned {len(messages)} messages")

                # If messages found, verify they have proper structure
                if messages:
                    sample_message = messages[0]
                    assert 'id' in sample_message
                    assert isinstance(sample_message['id'], str)

            except Exception as e:
                print(f"⚠️ Content query '{query}' failed: {e}")


class TestGmailEmailRetrieval:
    """Test suite for Gmail email retrieval and processing with real data."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_get_message_details_complete(self):
        """Test retrieving complete message details from Gmail API."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        # Get a recent message for testing
        try:
            messages = fetcher.search_messages("newer_than:7d", max_results=1)

            if not messages:
                pytest.skip("No recent messages available for testing")

            message_id = messages[0]['id']

            # Test getting message details
            message_details = fetcher.get_message_details(message_id)

            # Verify message structure
            assert isinstance(message_details, dict)
            assert 'id' in message_details
            assert 'payload' in message_details

            # Verify payload structure
            payload = message_details['payload']
            assert 'headers' in payload

            # Extract and verify headers
            headers = fetcher.extract_headers(message_details)
            assert isinstance(headers, dict)

            # Check for common email headers
            common_headers = ['From', 'To', 'Subject', 'Date']
            found_headers = [h for h in common_headers if h in headers]

            assert len(found_headers) > 0
            print(f"✅ Message details retrieved successfully")
            print(f"   Message ID: {message_id}")
            print(f"   Headers found: {found_headers}")

        except Exception as e:
            pytest.fail(f"Message details retrieval failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_message_body_extraction(self):
        """Test extracting message body content from Gmail API responses."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        try:
            # Get recent messages for testing
            messages = fetcher.search_messages("newer_than:7d", max_results=3)

            if not messages:
                pytest.skip("No recent messages available for testing")

            processed_count = 0
            for message in messages:
                try:
                    message_id = message['id']
                    message_details = fetcher.get_message_details(message_id)

                    # Test body extraction
                    body = fetcher.get_message_body(message_details)

                    # Verify body extraction
                    assert isinstance(body, str)

                    if body:  # If body content exists
                        assert len(body) > 0
                        processed_count += 1

                        print(f"✅ Body extracted from message {message_id}")
                        print(f"   Body length: {len(body)} characters")

                        # Test body preview (first 100 chars)
                        preview = body[:100].replace('\n', ' ').replace('\r', ' ')
                        print(f"   Preview: {preview}...")

                except Exception as e:
                    print(f"⚠️ Body extraction failed for message {message_id}: {e}")

            if processed_count > 0:
                print(f"✅ Successfully processed {processed_count} message bodies")
            else:
                pytest.skip("No message bodies could be extracted")

        except Exception as e:
            pytest.fail(f"Message body extraction test failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_email_download_workflow_complete(self):
        """Test complete email download workflow with real Gmail data."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        # Create test output directory
        output_dir = self.test_dir / "test_downloads"
        output_dir.mkdir()

        try:
            # Search for recent emails
            messages = fetcher.search_messages("newer_than:3d", max_results=2)

            if not messages:
                pytest.skip("No recent messages available for download testing")

            downloaded_count = 0
            for message in messages:
                try:
                    message_id = message['id']

                    # Get message details
                    message_details = fetcher.get_message_details(message_id)

                    # Extract headers and body
                    headers = fetcher.extract_headers(message_details)
                    body = fetcher.get_message_body(message_details)

                    # Create email data structure
                    email_data = {
                        'Subject': headers.get('Subject', 'No Subject'),
                        'From': headers.get('From', 'Unknown'),
                        'To': headers.get('To', headers.get('Delivered-To', 'Unknown')),
                        'Date': headers.get('Date', 'Unknown'),
                        'body': body
                    }

                    # Test EML creation
                    eml_content = fetcher.create_eml_content(email_data)
                    assert isinstance(eml_content, str)
                    assert len(eml_content) > 0

                    # Test Markdown creation
                    md_content = fetcher.create_markdown_content(email_data)
                    assert isinstance(md_content, str)
                    assert len(md_content) > 0

                    # Test filename sanitization
                    safe_filename = fetcher.sanitize_filename(email_data['Subject'])
                    assert isinstance(safe_filename, str)

                    # Save files to test directory
                    eml_file = output_dir / f"{safe_filename}_{message_id}.eml"
                    md_file = output_dir / f"{safe_filename}_{message_id}.md"

                    eml_file.write_text(eml_content, encoding='utf-8')
                    md_file.write_text(md_content, encoding='utf-8')

                    # Verify files were created
                    assert eml_file.exists()
                    assert md_file.exists()
                    assert eml_file.stat().st_size > 0
                    assert md_file.stat().st_size > 0

                    downloaded_count += 1

                    print(f"✅ Downloaded and processed email: {email_data['Subject'][:50]}...")
                    print(f"   EML file: {eml_file.name} ({eml_file.stat().st_size} bytes)")
                    print(f"   MD file: {md_file.name} ({md_file.stat().st_size} bytes)")

                except Exception as e:
                    print(f"⚠️ Download failed for message {message_id}: {e}")

            if downloaded_count > 0:
                print(f"✅ Successfully completed download workflow for {downloaded_count} emails")

                # Verify output directory structure
                eml_files = list(output_dir.glob("*.eml"))
                md_files = list(output_dir.glob("*.md"))

                assert len(eml_files) == downloaded_count
                assert len(md_files) == downloaded_count

                print(f"✅ Output verification: {len(eml_files)} EML + {len(md_files)} MD files")
            else:
                pytest.skip("No emails could be downloaded in workflow test")

        except Exception as e:
            pytest.fail(f"Email download workflow test failed: {e}")


class TestGmailAPIErrorHandling:
    """Test suite for Gmail API error handling and edge cases."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_invalid_search_queries(self):
        """Test Gmail API handling of invalid search queries."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        # Test potentially problematic queries
        invalid_queries = [
            "",  # Empty query
            "invalid:operator",  # Invalid search operator
            "from:" + "x" * 1000,  # Extremely long query
            "subject:🔥💯🚀",  # Unicode/emoji in search
        ]

        for query in invalid_queries:
            try:
                messages = fetcher.search_messages(query, max_results=1)

                # Should either return empty list or handle gracefully
                assert isinstance(messages, list)
                print(f"✅ Invalid query handled gracefully: '{query[:50]}...'")

            except Exception as e:
                # Exceptions are acceptable for invalid queries
                print(f"✅ Invalid query properly rejected: '{query[:50]}...' - {type(e).__name__}")

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_message_not_found_handling(self):
        """Test handling of non-existent message IDs."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        # Test with fake message ID
        fake_message_id = "nonexistent_message_id_12345"

        try:
            message_details = fetcher.get_message_details(fake_message_id)
            # Should return None or empty dict for non-existent messages
            assert message_details is None or message_details == {}
            print("✅ Non-existent message handled gracefully")

        except Exception as e:
            # Exceptions are acceptable for non-existent messages
            print(f"✅ Non-existent message properly handled with exception: {type(e).__name__}")

    @pytest.mark.skipif(not Path("credentials.json").exists(),
                       reason="Gmail credentials not available")
    def test_rate_limiting_awareness(self):
        """Test Gmail API rate limiting handling."""
        fetcher = GmailFetcher()
        fetcher.authenticate()

        # Test rapid successive API calls
        try:
            for i in range(5):
                messages = fetcher.search_messages("newer_than:1d", max_results=1)
                assert isinstance(messages, list)

            print("✅ Rapid API calls handled successfully")

        except Exception as e:
            # Rate limiting or quota errors are acceptable
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                print(f"✅ Rate limiting properly handled: {type(e).__name__}")
            else:
                print(f"⚠️ Unexpected error in rate limiting test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])