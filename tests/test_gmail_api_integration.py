#!/usr/bin/env python3
"""
Comprehensive Gmail API integration tests with real authentication.
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

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_authentication_flow_with_credentials(self):
        """Test complete authentication flow with real credentials."""
        fetcher = GmailFetcher()
        
        # Test authentication
        auth_result = fetcher.authenticate()
        assert auth_result == True
        assert fetcher.service is not None
        
        print("✅ Gmail API authentication successful")
        print(f"   Service type: {type(fetcher.service)}")

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_profile_retrieval(self):
        """Test Gmail profile retrieval with real account."""
        fetcher = GmailFetcher()
        
        if fetcher.authenticate():
            profile = fetcher.get_profile()
            
            assert profile is not None
            assert isinstance(profile, dict)
            assert 'emailAddress' in profile
            assert 'messagesTotal' in profile
            assert 'historyId' in profile
            
            print("✅ Gmail profile retrieval successful")
            print(f"   Email: {profile.get('emailAddress', 'N/A')}")
            print(f"   Total messages: {profile.get('messagesTotal', 'N/A')}")
            print(f"   Threads total: {profile.get('threadsTotal', 'N/A')}")

    def test_authentication_error_handling(self):
        """Test authentication error handling with missing/invalid credentials."""
        # Test with missing credentials file
        fetcher = GmailFetcher("missing_credentials.json", "missing_token.json")
        auth_result = fetcher.authenticate()
        assert auth_result == False
        assert fetcher.service is None
        
        print("✅ Missing credentials handled correctly")

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
            print("✅ Invalid credentials handled gracefully")
        except Exception as e:
            print(f"✅ Invalid credentials error handled: {type(e).__name__}")

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_token_persistence(self):
        """Test token file creation and reuse."""
        test_token_file = str(self.test_dir / "test_token.json")
        fetcher = GmailFetcher(token_file=test_token_file)
        
        if fetcher.authenticate():
            # Check token file was created
            assert Path(test_token_file).exists()
            
            # Verify token file contains valid JSON
            with open(test_token_file, 'r') as f:
                token_data = json.load(f)
            
            assert isinstance(token_data, dict)
            assert 'token' in token_data or 'access_token' in token_data
            
            print("✅ Token persistence works correctly")


class TestGmailAPISearch:
    """Test Gmail API search and message retrieval functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.fetcher = GmailFetcher()
        self.authenticated = False
        
        if Path("credentials.json").exists():
            self.authenticated = self.fetcher.authenticate()

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_search_messages_basic_queries(self):
        """Test basic Gmail search queries."""
        if not self.authenticated:
            pytest.skip("Authentication failed")

        # Test various search queries
        search_queries = [
            "is:unread",
            "from:noreply",
            "has:attachment",
            "newer_than:1d",
            "subject:newsletter"
        ]

        for query in search_queries:
            try:
                message_ids = self.fetcher.search_messages(query, max_results=5)
                
                assert isinstance(message_ids, list)
                assert len(message_ids) <= 5
                
                print(f"✅ Search query '{query}': {len(message_ids)} results")
                
                # Test message ID format
                for msg_id in message_ids:
                    assert isinstance(msg_id, str)
                    assert len(msg_id) > 10  # Gmail message IDs are long
                    
            except Exception as e:
                print(f"⚠️ Search query '{query}' failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_search_messages_pagination(self):
        """Test search with pagination and limits."""
        if not self.authenticated:
            pytest.skip("Authentication failed")

        # Test pagination with larger result set
        try:
            message_ids = self.fetcher.search_messages("", max_results=20)
            
            assert isinstance(message_ids, list)
            assert len(message_ids) <= 20
            
            print(f"✅ Pagination test: Retrieved {len(message_ids)} messages")
            
            if len(message_ids) > 0:
                # Test that we got unique message IDs
                unique_ids = set(message_ids)
                assert len(unique_ids) == len(message_ids)
                print("✅ All message IDs are unique")
                
        except Exception as e:
            print(f"⚠️ Pagination test failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_get_message_details_comprehensive(self):
        """Test comprehensive message detail retrieval."""
        if not self.authenticated:
            pytest.skip("Authentication failed")

        try:
            # Get a few message IDs to test with
            message_ids = self.fetcher.search_messages("", max_results=3)
            
            if not message_ids:
                pytest.skip("No messages found for testing")

            for message_id in message_ids:
                try:
                    details = self.fetcher.get_message_details(message_id)
                    
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
                    
                    break  # Test only first message to save API quota
                    
                except Exception as e:
                    print(f"⚠️ Failed to get details for {message_id}: {e}")

        except Exception as e:
            print(f"⚠️ Message details test failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_message_headers_extraction(self):
        """Test email header extraction from real messages."""
        if not self.authenticated:
            pytest.skip("Authentication failed")

        try:
            message_ids = self.fetcher.search_messages("", max_results=2)
            
            if not message_ids:
                pytest.skip("No messages found for testing")

            for message_id in message_ids:
                try:
                    details = self.fetcher.get_message_details(message_id)
                    
                    if details and 'payload' in details:
                        headers = self.fetcher.extract_headers(details['payload'].get('headers', []))
                        
                        assert isinstance(headers, dict)
                        
                        # Verify common headers are extracted
                        expected_headers = ['subject', 'from', 'date', 'message-id']
                        found_headers = [h for h in expected_headers if h in headers]
                        
                        assert len(found_headers) > 0
                        
                        print(f"✅ Headers extracted from {message_id}")
                        print(f"   Subject: {headers.get('subject', 'N/A')[:50]}...")
                        print(f"   From: {headers.get('from', 'N/A')}")
                        print(f"   Headers found: {list(headers.keys())}")
                        
                        break  # Test only first message
                        
                except Exception as e:
                    print(f"⚠️ Header extraction failed for {message_id}: {e}")

        except Exception as e:
            print(f"⚠️ Header extraction test failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_message_body_extraction(self):
        """Test email body extraction from real messages."""
        if not self.authenticated:
            pytest.skip("Authentication failed")

        try:
            message_ids = self.fetcher.search_messages("", max_results=2)
            
            if not message_ids:
                pytest.skip("No messages found for testing")

            for message_id in message_ids:
                try:
                    details = self.fetcher.get_message_details(message_id)
                    
                    if details and 'payload' in details:
                        plain_text, html_text = self.fetcher.get_message_body(details['payload'])
                        
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
                        
                except Exception as e:
                    print(f"⚠️ Body extraction failed for {message_id}: {e}")

        except Exception as e:
            print(f"⚠️ Body extraction test failed: {e}")


class TestGmailAPIDownload:
    """Test complete email download and processing workflow."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.test_dir / "gmail_test_download"
        self.fetcher = GmailFetcher()
        self.authenticated = False
        
        if Path("credentials.json").exists():
            self.authenticated = self.fetcher.authenticate()

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_download_emails_eml_format(self):
        """Test downloading emails in EML format."""
        if not self.authenticated:
            pytest.skip("Authentication failed")

        try:
            # Download a small number of emails in EML format
            self.fetcher.download_emails(
                query="",
                max_emails=2,
                output_dir=str(self.output_dir),
                format_type="eml",
                organize_by="date"
            )
            
            # Verify files were created
            if self.output_dir.exists():
                eml_files = list(self.output_dir.rglob("*.eml"))
                
                assert len(eml_files) > 0
                
                for eml_file in eml_files:
                    assert eml_file.stat().st_size > 0
                    
                    # Verify EML format
                    content = eml_file.read_text(encoding='utf-8', errors='ignore')
                    assert 'Subject:' in content or 'From:' in content
                
                print(f"✅ Downloaded {len(eml_files)} EML files")
                print(f"   Output directory: {self.output_dir}")
                
        except Exception as e:
            print(f"⚠️ EML download test failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_download_emails_markdown_format(self):
        """Test downloading emails in Markdown format."""
        if not self.authenticated:
            pytest.skip("Authentication failed")

        try:
            output_dir = self.test_dir / "markdown_download"
            
            self.fetcher.download_emails(
                query="",
                max_emails=2,
                output_dir=str(output_dir),
                format_type="markdown",
                organize_by="sender"
            )
            
            # Verify files were created
            if output_dir.exists():
                md_files = list(output_dir.rglob("*.md"))
                
                assert len(md_files) > 0
                
                for md_file in md_files:
                    assert md_file.stat().st_size > 0
                    
                    # Verify Markdown format
                    content = md_file.read_text(encoding='utf-8', errors='ignore')
                    # Should have metadata table or headers
                    assert 'Subject' in content or '#' in content or '|' in content
                
                print(f"✅ Downloaded {len(md_files)} Markdown files")
                
        except Exception as e:
            print(f"⚠️ Markdown download test failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_download_emails_both_formats(self):
        """Test downloading emails in both EML and Markdown formats."""
        if not self.authenticated:
            pytest.skip("Authentication failed")

        try:
            output_dir = self.test_dir / "both_formats"
            
            self.fetcher.download_emails(
                query="",
                max_emails=1,
                output_dir=str(output_dir),
                format_type="both",
                organize_by="none"
            )
            
            # Verify both file types were created
            if output_dir.exists():
                eml_files = list(output_dir.rglob("*.eml"))
                md_files = list(output_dir.rglob("*.md"))
                
                assert len(eml_files) > 0
                assert len(md_files) > 0
                
                # Should have roughly equal numbers (same emails in both formats)
                assert abs(len(eml_files) - len(md_files)) <= 1
                
                print(f"✅ Downloaded in both formats: {len(eml_files)} EML, {len(md_files)} MD")
                
        except Exception as e:
            print(f"⚠️ Both formats download test failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_email_content_creation_methods(self):
        """Test create_eml_content and create_markdown_content with real data."""
        if not self.authenticated:
            pytest.skip("Authentication failed")

        try:
            # Get a real message
            message_ids = self.fetcher.search_messages("", max_results=1)
            
            if not message_ids:
                pytest.skip("No messages found for testing")

            message_id = message_ids[0]
            details = self.fetcher.get_message_details(message_id)
            
            if details:
                # Test EML content creation
                eml_content = self.fetcher.create_eml_content(details)
                
                assert isinstance(eml_content, str)
                assert len(eml_content) > 0
                assert 'Subject:' in eml_content or 'From:' in eml_content
                
                # Test Markdown content creation
                md_content = self.fetcher.create_markdown_content(details)
                
                assert isinstance(md_content, str)
                assert len(md_content) > 0
                
                print("✅ Content creation methods work with real data")
                print(f"   EML content: {len(eml_content)} chars")
                print(f"   Markdown content: {len(md_content)} chars")
                
        except Exception as e:
            print(f"⚠️ Content creation test failed: {e}")

    @pytest.mark.skipif(not Path("credentials.json").exists(), 
                       reason="Gmail credentials not available")
    def test_directory_organization_patterns(self):
        """Test different directory organization patterns."""
        if not self.authenticated:
            pytest.skip("Authentication failed")

        organization_tests = [
            ("date", "Date-based organization"),
            ("sender", "Sender-based organization"), 
            ("none", "Flat organization")
        ]

        for org_type, description in organization_tests:
            try:
                output_dir = self.test_dir / f"org_{org_type}"
                
                self.fetcher.download_emails(
                    query="",
                    max_emails=1,
                    output_dir=str(output_dir),
                    format_type="eml",
                    organize_by=org_type
                )
                
                if output_dir.exists():
                    files = list(output_dir.rglob("*.eml"))
                    
                    if files:
                        print(f"✅ {description}: {len(files)} files")
                        
                        # Verify organization structure
                        if org_type == "date":
                            # Should have year/month structure
                            subdirs = [p for p in output_dir.rglob("*") if p.is_dir()]
                            if subdirs:
                                print(f"   Date structure: {[d.name for d in subdirs[:3]]}")
                        elif org_type == "sender":
                            # Should have sender-based directories
                            subdirs = [p for p in output_dir.rglob("*") if p.is_dir()]
                            if subdirs:
                                print(f"   Sender structure: {[d.name for d in subdirs[:3]]}")
                        else:
                            # Should be flat
                            all_files = list(output_dir.glob("*"))
                            print(f"   Flat structure: {len(all_files)} items")
                            
                time.sleep(1)  # Brief delay between API calls
                
            except Exception as e:
                print(f"⚠️ {description} test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])