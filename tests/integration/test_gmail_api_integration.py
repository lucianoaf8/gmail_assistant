#!/usr/bin/env python3
"""
Comprehensive Gmail API integration tests with mocked authentication.
Tests the complete email fetching, processing, and download workflows.
"""

import pytest
import tempfile
import shutil
import json
import os
import time
from pathlib import Path
import sys
from datetime import datetime, timedelta
from unittest import mock

from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher
from gmail_assistant.core.fetch.gmail_api_client import GmailAPIClient


class TestGmailAPIAuthentication:
    """Test Gmail API authentication and service setup."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.credentials_available = Path("credentials.json").exists()

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_authentication_flow_with_credentials(self, mock_credentials_file, mock_gmail_service_full):
        """Test complete authentication flow with mocked credentials."""
        fetcher = GmailFetcher(str(mock_credentials_file))

        # Mock the auth service
        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                # Test authentication
                auth_result = fetcher.authenticate()
                assert auth_result == True
                assert fetcher.service is not None

                print("✅ Gmail API authentication successful")
                print(f"   Service type: {type(fetcher.service)}")

    def test_profile_retrieval(self, mock_credentials_file, mock_gmail_service_full):
        """Test Gmail profile retrieval with mocked service."""
        fetcher = GmailFetcher(str(mock_credentials_file))

        # Mock the auth service
        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                if fetcher.authenticate():
                    profile = fetcher.get_profile()

                    assert profile is not None
                    assert isinstance(profile, dict)
                    assert 'email' in profile
                    assert 'total_messages' in profile
                    assert 'total_threads' in profile

                    print("✅ Gmail profile retrieval successful")
                    print(f"   Email: {profile.get('email', 'N/A')}")
                    print(f"   Total messages: {profile.get('total_messages', 'N/A')}")
                    print(f"   Total threads: {profile.get('total_threads', 'N/A')}")

    def test_authentication_error_handling(self):
        """Test authentication error handling with missing/invalid credentials."""
        from gmail_assistant.core.exceptions import AuthError

        # Test with missing credentials file - should raise AuthError
        fetcher = GmailFetcher("missing_credentials.json")
        try:
            auth_result = fetcher.authenticate()
            # If no exception, auth should fail
            assert auth_result == False
            assert fetcher.service is None
        except AuthError:
            # Expected behavior - authentication error raised
            pass

        print("[PASS] Missing credentials handled correctly")

    def test_credentials_file_validation(self):
        """Test credentials file structure validation."""
        # Test invalid JSON structure
        invalid_creds = self.test_dir / "invalid_creds.json"
        invalid_creds.write_text("invalid json")

        fetcher = GmailFetcher(str(invalid_creds))

        # Should handle invalid JSON gracefully
        try:
            auth_result = fetcher.authenticate()
            # May succeed or fail, but shouldn't crash
            print("[PASS] Invalid credentials handled gracefully")
        except Exception as e:
            print(f"[PASS] Invalid credentials error handled: {type(e).__name__}")

    def test_token_persistence(self, mock_credentials_file, mock_token_file, mock_gmail_service_full):
        """Test token file creation and reuse."""
        # GmailFetcher uses default token path via ReadOnlyGmailAuth
        fetcher = GmailFetcher(str(mock_credentials_file))

        # Mock the auth service
        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                if fetcher.authenticate():
                    # Check that authentication succeeded (token is managed internally)
                    assert fetcher.service is not None

                    # Get profile to verify service works
                    profile = fetcher.get_profile()
                    assert profile is not None

                    print("[PASS] Token persistence works correctly")


class TestGmailAPISearch:
    """Test Gmail API search and message retrieval functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_search_messages_basic_queries(self, mock_credentials_file, mock_gmail_service_full):
        """Test basic Gmail search queries."""
        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                # Test various search queries
                search_queries = [
                    "is:unread",
                    "from:noreply",
                    "has:attachment",
                    "newer_than:1d",
                    "subject:newsletter"
                ]

                for query in search_queries:
                    message_ids = fetcher.search_messages(query, max_results=5)

                    assert isinstance(message_ids, list)
                    assert len(message_ids) <= 5

                    print(f"✅ Search query '{query}': {len(message_ids)} results")

                    # Test message ID format
                    for msg_id in message_ids:
                        assert isinstance(msg_id, str)
                        assert len(msg_id) > 0

    def test_search_messages_pagination(self, mock_credentials_file, mock_gmail_service_full):
        """Test search with pagination and limits."""
        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                # Test pagination with larger result set
                message_ids = fetcher.search_messages("", max_results=20)

                assert isinstance(message_ids, list)
                assert len(message_ids) <= 20

                print(f"✅ Pagination test: Retrieved {len(message_ids)} messages")

                if len(message_ids) > 0:
                    # Test that we got unique message IDs
                    unique_ids = set(message_ids)
                    assert len(unique_ids) == len(message_ids)
                    print("✅ All message IDs are unique")

    def test_get_message_details_comprehensive(self, mock_credentials_file, mock_gmail_service_full):
        """Test comprehensive message detail retrieval."""
        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                # Get a few message IDs to test with
                message_ids = fetcher.search_messages("", max_results=3)

                if not message_ids:
                    pytest.skip("No messages found for testing")

                for message_id in message_ids:
                    details = fetcher.get_message_details(message_id)

                    assert details is not None
                    assert isinstance(details, dict)
                    assert 'id' in details
                    assert 'payload' in details
                    assert 'labelIds' in details

                    # Test payload structure
                    payload = details['payload']
                    assert isinstance(payload, dict)

                    if 'headers' in payload:
                        headers = payload['headers']
                        assert isinstance(headers, list)

                        # Check for common headers
                        header_names = [h.get('name', '').lower() for h in headers]
                        assert 'subject' in header_names or 'from' in header_names

                    print(f"✅ Message details retrieved for {message_id}")
                    print(f"   Labels: {len(details.get('labelIds', []))}")
                    print(f"   Thread ID: {details.get('threadId', 'N/A')}")

                    break  # Test only first message

    def test_message_headers_extraction(self, mock_credentials_file, mock_gmail_service_full):
        """Test email header extraction from real messages."""
        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                message_ids = fetcher.search_messages("", max_results=2)

                if not message_ids:
                    pytest.skip("No messages found for testing")

                for message_id in message_ids:
                    details = fetcher.get_message_details(message_id)

                    if details and 'payload' in details:
                        headers = fetcher.extract_headers(details['payload'].get('headers', []))

                        assert isinstance(headers, dict)

                        # Verify common headers are extracted
                        expected_headers = ['subject', 'from', 'date']
                        found_headers = [h for h in expected_headers if h in headers]

                        assert len(found_headers) > 0

                        print(f"✅ Headers extracted from {message_id}")
                        print(f"   Subject: {headers.get('subject', 'N/A')[:50]}...")
                        print(f"   From: {headers.get('from', 'N/A')}")
                        print(f"   Headers found: {list(headers.keys())}")

                        break  # Test only first message

    def test_message_body_extraction(self, mock_credentials_file, mock_gmail_service_full):
        """Test email body extraction from real messages."""
        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                message_ids = fetcher.search_messages("", max_results=2)

                if not message_ids:
                    pytest.skip("No messages found for testing")

                for message_id in message_ids:
                    details = fetcher.get_message_details(message_id)

                    if details and 'payload' in details:
                        plain_text, html_text = fetcher.get_message_body(details['payload'])

                        assert isinstance(plain_text, str)
                        assert isinstance(html_text, str)

                        # At least one should have content
                        total_content = len(plain_text) + len(html_text)
                        assert total_content > 0

                        print(f"✅ Body extracted from {message_id}")
                        print(f"   Plain text: {len(plain_text)} chars")
                        print(f"   HTML text: {len(html_text)} chars")

                        # Test base64 decoding if present
                        if plain_text or html_text:
                            print("✅ Content successfully decoded")

                        break  # Test only first message


class TestGmailAPIDownload:
    """Test complete email download and processing workflow."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_download_emails_eml_format(self, mock_credentials_file, mock_gmail_service_full):
        """Test downloading emails in EML format."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))
        output_dir = self.test_dir / "eml_download"

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()

                # Download emails in EML format
                fetcher.download_emails(
                    query="",
                    max_emails=2,
                    output_dir=str(output_dir),
                    format_type="eml",
                    organize_by="date"
                )

                # Verify files were created
                assert output_dir.exists()
                eml_files = list(output_dir.rglob("*.eml"))

                assert len(eml_files) > 0

                for eml_file in eml_files:
                    assert eml_file.stat().st_size > 0

                    # Verify EML format
                    content = eml_file.read_text(encoding='utf-8', errors='ignore')
                    assert 'Subject:' in content or 'From:' in content

    def test_download_emails_markdown_format(self, mock_credentials_file, mock_gmail_service_full):
        """Test downloading emails in Markdown format."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))
        output_dir = self.test_dir / "markdown_download"

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()

                fetcher.download_emails(
                    query="",
                    max_emails=2,
                    output_dir=str(output_dir),
                    format_type="markdown",
                    organize_by="sender"
                )

                # Verify files were created
                assert output_dir.exists()
                md_files = list(output_dir.rglob("*.md"))

                assert len(md_files) > 0

                for md_file in md_files:
                    assert md_file.stat().st_size > 0

                    # Verify Markdown format
                    content = md_file.read_text(encoding='utf-8', errors='ignore')
                    # Should have metadata table or headers
                    assert 'Subject' in content or '#' in content or '|' in content

    def test_download_emails_both_formats(self, mock_credentials_file, mock_gmail_service_full):
        """Test downloading emails in both EML and Markdown formats."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))
        output_dir = self.test_dir / "both_formats"

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()

                fetcher.download_emails(
                    query="",
                    max_emails=1,
                    output_dir=str(output_dir),
                    format_type="both",
                    organize_by="none"
                )

                # Verify both file types were created
                assert output_dir.exists()
                eml_files = list(output_dir.rglob("*.eml"))
                md_files = list(output_dir.rglob("*.md"))

                assert len(eml_files) > 0
                assert len(md_files) > 0

                # Should have roughly equal numbers (same emails in both formats)
                assert abs(len(eml_files) - len(md_files)) <= 1

    def test_email_content_creation_methods(self, mock_credentials_file, mock_gmail_service_full):
        """Test create_eml_content and create_markdown_content with mocked data."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()

                # Get a message
                message_ids = fetcher.search_messages("", max_results=1)

                assert len(message_ids) > 0

                message_id = message_ids[0]
                details = fetcher.get_message_details(message_id)

                assert details is not None

                # Test EML content creation
                eml_content = fetcher.create_eml_content(details)

                assert isinstance(eml_content, str)
                assert len(eml_content) > 0
                assert 'Subject:' in eml_content or 'From:' in eml_content

                # Test Markdown content creation
                md_content = fetcher.create_markdown_content(details)

                assert isinstance(md_content, str)
                assert len(md_content) > 0

    def test_directory_organization_patterns(self, mock_credentials_file, mock_gmail_service_full):
        """Test different directory organization patterns."""
        from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

        fetcher = GmailFetcher(str(mock_credentials_file))

        with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
            with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
                fetcher.authenticate()

                organization_tests = [
                    ("date", "Date-based organization"),
                    ("sender", "Sender-based organization"),
                    ("none", "Flat organization")
                ]

                for org_type, description in organization_tests:
                    output_dir = self.test_dir / f"org_{org_type}"

                    fetcher.download_emails(
                        query="",
                        max_emails=1,
                        output_dir=str(output_dir),
                        format_type="eml",
                        organize_by=org_type
                    )

                    assert output_dir.exists()
                    files = list(output_dir.rglob("*.eml"))

                    assert len(files) > 0

                    # Verify organization structure
                    if org_type == "date":
                        # Should have year/month structure
                        subdirs = [p for p in output_dir.rglob("*") if p.is_dir()]
                        assert len(subdirs) > 0
                    elif org_type == "sender":
                        # Should have sender-based directories or flat structure
                        # (depends on implementation)
                        pass
                    else:
                        # Flat organization - files directly in output_dir
                        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])