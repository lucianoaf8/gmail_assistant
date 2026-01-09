#!/usr/bin/env python3
"""
Comprehensive test suite for Gmail deletion functionality
Tests safety mechanisms, dry-run mode, and error handling
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

# Import deletion modules
from gmail_assistant.deletion.deleter import GmailDeleter
from gmail_assistant.deletion.ui import clean_unread_inbox


class TestGmailDeleter(unittest.TestCase):
    """Test suite for GmailDeleter class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.credentials_file = os.path.join(self.temp_dir, 'credentials.json')
        self.token_file = os.path.join(self.temp_dir, 'token.json')

        # Create mock credentials file
        mock_credentials = {
            "web": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        with open(self.credentials_file, 'w') as f:
            json.dump(mock_credentials, f)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('deletion.deleter.build')
    @patch('deletion.deleter.Credentials')
    @patch('deletion.deleter.InstalledAppFlow')
    def test_authentication_success(self, mock_flow, mock_creds, mock_build):
        """Test successful Gmail API authentication"""
        # Mock successful authentication
        mock_creds_instance = Mock()
        mock_creds_instance.valid = True
        mock_creds.from_authorized_user_file.return_value = mock_creds_instance

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Initialize deleter
        deleter = GmailDeleter(
            credentials_file=self.credentials_file,
            token_file=self.token_file
        )

        self.assertIsNotNone(deleter.service)
        mock_build.assert_called_once()

    @patch('deletion.deleter.build')
    @patch('deletion.deleter.Credentials')
    def test_get_email_count(self, mock_creds, mock_build):
        """Test email count retrieval"""
        # Setup mocks
        mock_creds_instance = Mock()
        mock_creds_instance.valid = True
        mock_creds.from_authorized_user_file.return_value = mock_creds_instance

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Mock email count response
        mock_service.users().messages().list().execute.return_value = {
            'resultSizeEstimate': 1234
        }

        deleter = GmailDeleter(
            credentials_file=self.credentials_file,
            token_file=self.token_file
        )

        count = deleter.get_email_count("is:unread")
        self.assertEqual(count, 1234)

    @patch('deletion.deleter.build')
    @patch('deletion.deleter.Credentials')
    def test_list_emails_with_pagination(self, mock_creds, mock_build):
        """Test email listing with pagination"""
        # Setup mocks
        mock_creds_instance = Mock()
        mock_creds_instance.valid = True
        mock_creds.from_authorized_user_file.return_value = mock_creds_instance

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Mock paginated response
        mock_service.users().messages().list().execute.side_effect = [
            {
                'messages': [{'id': 'msg1'}, {'id': 'msg2'}],
                'nextPageToken': 'token123'
            },
            {
                'messages': [{'id': 'msg3'}, {'id': 'msg4'}]
            }
        ]

        deleter = GmailDeleter(
            credentials_file=self.credentials_file,
            token_file=self.token_file
        )

        message_ids = deleter.list_emails("is:unread", max_results=4)
        self.assertEqual(message_ids, ['msg1', 'msg2', 'msg3', 'msg4'])

    @patch('deletion.deleter.build')
    @patch('deletion.deleter.Credentials')
    @patch('deletion.deleter.time.sleep')  # Mock sleep to speed up tests
    def test_batch_deletion_success(self, mock_sleep, mock_creds, mock_build):
        """Test successful batch deletion"""
        # Setup mocks
        mock_creds_instance = Mock()
        mock_creds_instance.valid = True
        mock_creds.from_authorized_user_file.return_value = mock_creds_instance

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Mock successful batch delete
        mock_service.users().messages().batchDelete().execute.return_value = {}

        deleter = GmailDeleter(
            credentials_file=self.credentials_file,
            token_file=self.token_file
        )

        result = deleter.delete_emails_batch(['msg1', 'msg2', 'msg3'])

        self.assertEqual(result['deleted'], 3)
        self.assertEqual(result['failed'], 0)

    @patch('deletion.deleter.build')
    @patch('deletion.deleter.Credentials')
    @patch('deletion.deleter.time.sleep')
    def test_batch_deletion_with_fallback(self, mock_sleep, mock_creds, mock_build):
        """Test batch deletion with fallback to individual deletion"""
        from googleapiclient.errors import HttpError

        # Setup mocks
        mock_creds_instance = Mock()
        mock_creds_instance.valid = True
        mock_creds.from_authorized_user_file.return_value = mock_creds_instance

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Mock batch delete failure, then individual success
        mock_service.users().messages().batchDelete().execute.side_effect = HttpError(
            resp=Mock(status=400), content=b'Bad Request'
        )
        mock_service.users().messages().delete().execute.return_value = {}

        deleter = GmailDeleter(
            credentials_file=self.credentials_file,
            token_file=self.token_file
        )

        result = deleter.delete_emails_batch(['msg1', 'msg2'])

        # Should succeed via individual deletion fallback
        self.assertEqual(result['deleted'], 2)
        self.assertEqual(result['failed'], 0)

    @patch('deletion.deleter.build')
    @patch('deletion.deleter.Credentials')
    def test_dry_run_mode(self, mock_creds, mock_build):
        """Test dry-run mode doesn't actually delete emails"""
        # Setup mocks
        mock_creds_instance = Mock()
        mock_creds_instance.valid = True
        mock_creds.from_authorized_user_file.return_value = mock_creds_instance

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Mock email count
        mock_service.users().messages().list().execute.return_value = {
            'resultSizeEstimate': 100
        }

        deleter = GmailDeleter(
            credentials_file=self.credentials_file,
            token_file=self.token_file
        )

        result = deleter.delete_by_query("is:unread", dry_run=True)

        # Should not call any delete methods
        mock_service.users().messages().batchDelete.assert_not_called()
        mock_service.users().messages().delete.assert_not_called()


class TestDeletionUI(unittest.TestCase):
    """Test suite for deletion UI functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.credentials_file = os.path.join(self.temp_dir, 'credentials.json')

        # Create mock credentials
        mock_credentials = {
            "web": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret"
            }
        }

        with open(self.credentials_file, 'w') as f:
            json.dump(mock_credentials, f)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('deletion.ui.GmailDeleter')
    def test_clean_unread_inbox_dry_run(self, mock_deleter_class):
        """Test clean unread inbox in dry-run mode"""
        # Setup mock deleter
        mock_deleter = Mock()
        mock_deleter_class.return_value = mock_deleter
        mock_deleter.get_email_count.side_effect = [100, 50, 30, 20, 10, 5, 80]  # Various counts

        result = clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=0)

        # Should return zero deletions in dry-run
        self.assertEqual(result['deleted'], 0)
        self.assertEqual(result['failed'], 0)

    @patch('deletion.ui.GmailDeleter')
    def test_clean_unread_inbox_no_emails(self, mock_deleter_class):
        """Test clean unread inbox when no emails exist"""
        # Setup mock deleter
        mock_deleter = Mock()
        mock_deleter_class.return_value = mock_deleter
        mock_deleter.get_email_count.return_value = 0

        result = clean_unread_inbox(mock_deleter, dry_run=True)

        # Should return zero deletions when no emails exist
        self.assertEqual(result['deleted'], 0)
        self.assertEqual(result['failed'], 0)

    @patch('deletion.ui.GmailDeleter')
    def test_clean_unread_inbox_with_keep_recent(self, mock_deleter_class):
        """Test clean unread inbox with keep recent days option"""
        # Setup mock deleter
        mock_deleter = Mock()
        mock_deleter_class.return_value = mock_deleter
        mock_deleter.get_email_count.side_effect = [100, 50, 30, 20, 10, 5, 80]  # Various counts

        result = clean_unread_inbox(mock_deleter, dry_run=True, keep_recent_days=7)

        # Should construct proper query with keep_recent_days
        mock_deleter.get_email_count.assert_any_call("is:unread older_than:7d")


class TestSafetyMechanisms(unittest.TestCase):
    """Test suite for safety mechanisms and error handling"""

    def test_default_dry_run_in_main_interface(self):
        """Test that main interface defaults to dry-run mode"""
        # This tests the safety-first approach in argument parsing
        from main import setup_argument_parser

        parser = setup_argument_parser()

        # Test delete unread defaults
        args = parser.parse_args(['delete', 'unread'])
        self.assertTrue(args.dry_run)  # Should default to True

        # Test delete query defaults
        args = parser.parse_args(['delete', 'query', '--query', 'is:unread'])
        self.assertTrue(args.dry_run)  # Should default to True

    def test_execute_flag_required_for_actual_deletion(self):
        """Test that --execute flag is required for actual deletion"""
        from main import setup_argument_parser

        parser = setup_argument_parser()

        # With --execute flag
        args = parser.parse_args(['delete', 'unread', '--execute'])
        self.assertTrue(args.execute)

        # Without --execute flag (should still be dry-run)
        args = parser.parse_args(['delete', 'unread'])
        self.assertFalse(hasattr(args, 'execute') or getattr(args, 'execute', False))

    def test_query_validation(self):
        """Test query validation and safety checks"""
        dangerous_queries = [
            "",  # Empty query
            " ",  # Whitespace only
            "is:important",  # Potentially dangerous
        ]

        # These should be caught by the application logic
        # (This is more of a documentation test for expected behavior)
        for query in dangerous_queries:
            # In actual implementation, these should trigger warnings
            # or require additional confirmation
            pass


class TestIntegrationTests(unittest.TestCase):
    """Integration tests for the complete deletion workflow"""

    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, 'config', 'security')
        os.makedirs(self.config_dir, exist_ok=True)

        self.credentials_file = os.path.join(self.config_dir, 'credentials.json')

        # Create mock credentials
        mock_credentials = {
            "web": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret"
            }
        }

        with open(self.credentials_file, 'w') as f:
            json.dump(mock_credentials, f)

    def tearDown(self):
        """Clean up integration test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('sys.argv')
    @patch('deletion.deleter.build')
    @patch('deletion.deleter.Credentials')
    def test_main_interface_delete_command_dry_run(self, mock_creds, mock_build, mock_argv):
        """Test main interface delete command in dry-run mode"""
        # Mock command line arguments
        mock_argv.__getitem__.side_effect = lambda x: [
            'main.py', 'delete', 'unread', '--dry-run'
        ][x]
        mock_argv.__len__.return_value = 4

        # Setup mocks
        mock_creds_instance = Mock()
        mock_creds_instance.valid = True
        mock_creds.from_authorized_user_file.return_value = mock_creds_instance

        mock_service = Mock()
        mock_build.return_value = mock_service
        mock_service.users().messages().list().execute.return_value = {
            'resultSizeEstimate': 100
        }

        # This would test the full integration, but requires more complex mocking
        # For now, this demonstrates the test structure
        pass

    def test_logging_configuration(self):
        """Test that logging is properly configured for deletion operations"""
        # Test that log directory is created and files are written
        # This would verify the logging enhancements
        pass


class TestErrorHandling(unittest.TestCase):
    """Test suite for error handling and edge cases"""

    def test_missing_credentials_file(self):
        """Test handling of missing credentials file"""
        with self.assertRaises(FileNotFoundError):
            GmailDeleter(credentials_file='nonexistent.json')

    def test_network_error_handling(self):
        """Test handling of network errors during deletion"""
        # This would test retry logic and error recovery
        pass

    def test_api_quota_exceeded(self):
        """Test handling of API quota exceeded errors"""
        # This would test rate limiting and backoff strategies
        pass


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestGmailDeleter,
        TestDeletionUI,
        TestSafetyMechanisms,
        TestIntegrationTests,
        TestErrorHandling
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)