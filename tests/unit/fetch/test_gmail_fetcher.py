"""
Comprehensive tests for gmail_assistant.py module.
Tests GmailFetcher class for email downloading and processing.
"""

import base64
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher


class TestGmailFetcherInit:
    """Tests for GmailFetcher initialization."""

    def test_fetcher_init_default_credentials(self):
        """Test GmailFetcher initializes with default credentials path."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            fetcher = GmailFetcher()
            assert fetcher.auth is not None

    def test_fetcher_init_custom_credentials(self):
        """Test GmailFetcher with custom credentials path."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            fetcher = GmailFetcher('custom_creds.json')
            assert fetcher.auth is not None

    def test_fetcher_has_memory_tracker(self):
        """Test GmailFetcher has memory tracker."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            fetcher = GmailFetcher()
            assert fetcher.memory_tracker is not None

    def test_fetcher_has_html_converter(self):
        """Test GmailFetcher has HTML converter."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            fetcher = GmailFetcher()
            assert fetcher.html_converter is not None


class TestAuthentication:
    """Tests for authentication."""

    @pytest.fixture
    def mock_auth(self):
        """Create mock auth."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth') as mock_cls:
            mock_instance = mock.Mock()
            mock_cls.return_value = mock_instance
            yield mock_instance

    def test_authenticate_success(self, mock_auth):
        """Test successful authentication."""
        mock_auth.authenticate.return_value = True

        fetcher = GmailFetcher()
        result = fetcher.authenticate()

        assert result is True
        mock_auth.authenticate.assert_called_once()

    def test_authenticate_failure(self, mock_auth):
        """Test failed authentication."""
        mock_auth.authenticate.return_value = False

        fetcher = GmailFetcher()
        result = fetcher.authenticate()

        assert result is False


class TestGetProfile:
    """Tests for get_profile method."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        service = mock.Mock()
        profile_response = {
            "emailAddress": "test@gmail.com",
            "messagesTotal": 10000,
            "threadsTotal": 5000
        }
        service.users().getProfile().execute.return_value = profile_response
        return service

    @pytest.fixture
    def fetcher_with_service(self, mock_service):
        """Create fetcher with mocked service."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth') as mock_cls:
            mock_auth = mock.Mock()
            mock_auth.service = mock_service
            mock_cls.return_value = mock_auth
            fetcher = GmailFetcher()
            return fetcher

    def test_get_profile_success(self, fetcher_with_service, mock_service):
        """Test getting profile successfully."""
        profile = fetcher_with_service.get_profile()

        assert profile is not None
        assert profile['email'] == 'test@gmail.com'
        assert profile['total_messages'] == 10000
        assert profile['total_threads'] == 5000

    def test_get_profile_error(self, fetcher_with_service, mock_service):
        """Test get_profile handles errors."""
        from googleapiclient.errors import HttpError
        mock_resp = mock.Mock()
        mock_resp.status = 500
        mock_service.users().getProfile().execute.side_effect = HttpError(mock_resp, b"Error")

        profile = fetcher_with_service.get_profile()
        assert profile is None


class TestSearchMessages:
    """Tests for search_messages method."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        service = mock.Mock()
        return service

    @pytest.fixture
    def fetcher_with_service(self, mock_service):
        """Create fetcher with mocked service."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth') as mock_cls:
            mock_auth = mock.Mock()
            mock_auth.service = mock_service
            mock_cls.return_value = mock_auth
            fetcher = GmailFetcher()
            return fetcher

    def test_search_messages_basic(self, fetcher_with_service, mock_service):
        """Test searching messages with basic query."""
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1"}, {"id": "msg2"}],
            "resultSizeEstimate": 2
        }

        result = fetcher_with_service.search_messages("is:unread", max_results=10)

        assert result == ["msg1", "msg2"]

    def test_search_messages_empty(self, fetcher_with_service, mock_service):
        """Test searching with no results."""
        mock_service.users().messages().list().execute.return_value = {
            "messages": []
        }

        result = fetcher_with_service.search_messages("nonexistent")
        assert result == []

    def test_search_messages_pagination(self, fetcher_with_service, mock_service):
        """Test searching with pagination."""
        # First page
        mock_service.users().messages().list().execute.side_effect = [
            {
                "messages": [{"id": "msg1"}, {"id": "msg2"}],
                "nextPageToken": "token123"
            },
            {
                "messages": [{"id": "msg3"}]
            }
        ]

        result = fetcher_with_service.search_messages("is:unread", max_results=10)

        assert len(result) == 3
        assert "msg1" in result
        assert "msg3" in result

    def test_search_messages_error(self, fetcher_with_service, mock_service):
        """Test search handles errors."""
        from googleapiclient.errors import HttpError
        mock_resp = mock.Mock()
        mock_resp.status = 500
        mock_service.users().messages().list().execute.side_effect = HttpError(mock_resp, b"Error")

        result = fetcher_with_service.search_messages("query")
        assert result == []


class TestDecodeBase64:
    """Tests for decode_base64 method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            return GmailFetcher()

    def test_decode_base64_standard(self, fetcher):
        """Test decoding standard base64."""
        encoded = base64.b64encode(b"Hello World").decode('ascii')
        result = fetcher.decode_base64(encoded)
        assert result == "Hello World"

    def test_decode_base64_url_safe(self, fetcher):
        """Test decoding URL-safe base64."""
        # URL-safe encoding uses - and _ instead of + and /
        text = "Test with special chars: +/"
        encoded = base64.urlsafe_b64encode(text.encode()).decode('ascii')
        result = fetcher.decode_base64(encoded)
        assert result == text

    def test_decode_base64_with_padding(self, fetcher):
        """Test decoding base64 with missing padding."""
        # Base64 without padding
        encoded = base64.b64encode(b"Test").decode('ascii').rstrip('=')
        result = fetcher.decode_base64(encoded)
        assert result == "Test"

    def test_decode_base64_invalid(self, fetcher):
        """Test decoding invalid base64 returns empty string."""
        result = fetcher.decode_base64("not valid base64!!!")
        assert result == ""


class TestExtractHeaders:
    """Tests for extract_headers method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            return GmailFetcher()

    def test_extract_headers_basic(self, fetcher):
        """Test extracting headers from list."""
        headers = [
            {"name": "From", "value": "sender@example.com"},
            {"name": "To", "value": "recipient@example.com"},
            {"name": "Subject", "value": "Test Subject"}
        ]

        result = fetcher.extract_headers(headers)

        assert result["from"] == "sender@example.com"
        assert result["to"] == "recipient@example.com"
        assert result["subject"] == "Test Subject"

    def test_extract_headers_lowercase(self, fetcher):
        """Test headers are stored lowercase."""
        headers = [
            {"name": "Message-ID", "value": "<123@example.com>"}
        ]

        result = fetcher.extract_headers(headers)
        assert "message-id" in result

    def test_extract_headers_empty(self, fetcher):
        """Test extracting from empty headers."""
        result = fetcher.extract_headers([])
        assert result == {}


class TestSanitizeFilename:
    """Tests for sanitize_filename method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            return GmailFetcher()

    def test_sanitize_basic(self, fetcher):
        """Test basic filename sanitization."""
        result = fetcher.sanitize_filename("normal_filename")
        assert result == "normal_filename"

    def test_sanitize_special_chars(self, fetcher):
        """Test sanitizing special characters."""
        result = fetcher.sanitize_filename('file<>:"/\\|?*name')
        assert "<" not in result
        assert ">" not in result
        assert "/" not in result
        assert "\\" not in result

    def test_sanitize_control_chars(self, fetcher):
        """Test removing control characters."""
        result = fetcher.sanitize_filename("file\x00name\x1f")
        assert "\x00" not in result
        assert "\x1f" not in result

    def test_sanitize_length_limit(self, fetcher):
        """Test filename length is limited."""
        long_name = "a" * 300
        result = fetcher.sanitize_filename(long_name)
        assert len(result) <= 200

    def test_sanitize_strips_whitespace(self, fetcher):
        """Test filename is stripped of whitespace."""
        result = fetcher.sanitize_filename("  filename  ")
        assert result == "filename"


class TestValidateApiResponse:
    """Tests for _validate_api_response method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            return GmailFetcher()

    def test_validate_response_success(self, fetcher):
        """Test validating valid response."""
        response = {"id": "123", "threadId": "456"}
        result = fetcher._validate_api_response(response, ["id", "threadId"])
        assert result == response

    def test_validate_response_none(self, fetcher):
        """Test validating None response raises."""
        with pytest.raises(ValueError, match="null response"):
            fetcher._validate_api_response(None, ["id"])

    def test_validate_response_not_dict(self, fetcher):
        """Test validating non-dict response raises."""
        with pytest.raises(ValueError, match="non-dict"):
            fetcher._validate_api_response("string", ["id"])

    def test_validate_response_missing_fields(self, fetcher):
        """Test validating response with missing fields raises."""
        response = {"id": "123"}
        with pytest.raises(ValueError, match="missing required fields"):
            fetcher._validate_api_response(response, ["id", "missing"])


class TestGetMessageBody:
    """Tests for get_message_body method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            return GmailFetcher()

    def test_get_body_plain_text(self, fetcher):
        """Test extracting plain text body."""
        payload = {
            "mimeType": "text/plain",
            "body": {"data": base64.urlsafe_b64encode(b"Plain text content").decode()}
        }

        plain, html = fetcher.get_message_body(payload)
        assert "Plain text content" in plain
        assert html == ""

    def test_get_body_html(self, fetcher):
        """Test extracting HTML body."""
        payload = {
            "mimeType": "text/html",
            "body": {"data": base64.urlsafe_b64encode(b"<html>HTML content</html>").decode()}
        }

        plain, html = fetcher.get_message_body(payload)
        assert plain == ""
        assert "<html>" in html

    def test_get_body_multipart(self, fetcher):
        """Test extracting from multipart message."""
        payload = {
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": base64.urlsafe_b64encode(b"Plain part").decode()}
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": base64.urlsafe_b64encode(b"<html>HTML part</html>").decode()}
                }
            ]
        }

        plain, html = fetcher.get_message_body(payload)
        assert "Plain part" in plain
        assert "HTML part" in html


class TestAtomicWrite:
    """Tests for atomic_write method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            return GmailFetcher()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_atomic_write_creates_file(self, fetcher, temp_dir):
        """Test atomic write creates file."""
        path = temp_dir / "test.txt"
        fetcher.atomic_write(path, "Test content")

        assert path.exists()
        assert path.read_text() == "Test content"

    def test_atomic_write_creates_dirs(self, fetcher, temp_dir):
        """Test atomic write creates parent directories."""
        path = temp_dir / "sub" / "dir" / "test.txt"
        fetcher.atomic_write(path, "Content")

        assert path.exists()

    def test_atomic_write_overwrites(self, fetcher, temp_dir):
        """Test atomic write overwrites existing file."""
        path = temp_dir / "test.txt"
        path.write_text("Original")

        fetcher.atomic_write(path, "Updated")

        assert path.read_text() == "Updated"


class TestCreateEmlContent:
    """Tests for create_eml_content method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            return GmailFetcher()

    def test_create_eml_basic(self, fetcher):
        """Test creating basic EML content."""
        message_data = {
            "id": "msg123",
            "threadId": "thread456",
            "labelIds": ["INBOX"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test Subject"}
                ],
                "mimeType": "text/plain",
                "body": {"data": base64.urlsafe_b64encode(b"Body content").decode()}
            }
        }

        eml = fetcher.create_eml_content(message_data)

        assert "From: sender@example.com" in eml
        assert "Subject: Test Subject" in eml
        assert "X-Gmail-Message-ID: msg123" in eml
        assert "Body content" in eml

    def test_create_eml_multipart(self, fetcher):
        """Test creating EML with multipart content."""
        message_data = {
            "id": "msg123",
            "threadId": "thread456",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"}
                ],
                "mimeType": "multipart/alternative",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": base64.urlsafe_b64encode(b"Plain").decode()}
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": base64.urlsafe_b64encode(b"<html>HTML</html>").decode()}
                    }
                ]
            }
        }

        eml = fetcher.create_eml_content(message_data)

        assert "multipart/alternative" in eml
        assert "Plain" in eml
        assert "HTML" in eml


class TestCreateMarkdownContent:
    """Tests for create_markdown_content method."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth'):
            return GmailFetcher()

    def test_create_markdown_basic(self, fetcher):
        """Test creating basic markdown content."""
        message_data = {
            "id": "msg123",
            "threadId": "thread456",
            "labelIds": ["INBOX"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"}
                ],
                "mimeType": "text/plain",
                "body": {"data": base64.urlsafe_b64encode(b"Email body").decode()}
            }
        }

        md = fetcher.create_markdown_content(message_data)

        assert "# Email Details" in md
        assert "| From | sender@example.com |" in md
        assert "| Subject | Test Subject |" in md
        assert "Email body" in md

    def test_create_markdown_no_body(self, fetcher):
        """Test creating markdown with no body content."""
        message_data = {
            "id": "msg123",
            "threadId": "thread456",
            "payload": {
                "headers": [],
                "body": {}
            }
        }

        md = fetcher.create_markdown_content(message_data)

        assert "No readable content found" in md


class TestDownloadEmails:
    """Tests for download_emails method."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Gmail service."""
        service = mock.Mock()
        return service

    @pytest.fixture
    def fetcher_with_service(self, mock_service):
        """Create fetcher with mocked service."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth') as mock_cls:
            mock_auth = mock.Mock()
            mock_auth.service = mock_service
            mock_cls.return_value = mock_auth
            fetcher = GmailFetcher()
            return fetcher

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_download_not_authenticated(self, mock_service, temp_dir):
        """Test download fails when not authenticated."""
        with mock.patch('gmail_assistant.core.fetch.gmail_assistant.ReadOnlyGmailAuth') as mock_cls:
            mock_auth = mock.Mock()
            mock_auth.service = None  # Not authenticated
            mock_cls.return_value = mock_auth

            fetcher = GmailFetcher()
            # Should log error and return early
            fetcher.download_emails(output_dir=str(temp_dir))

    def test_download_no_messages(self, fetcher_with_service, mock_service, temp_dir):
        """Test download with no messages found."""
        mock_service.users().messages().list().execute.return_value = {"messages": []}

        fetcher_with_service.download_emails(
            query="nonexistent",
            output_dir=str(temp_dir)
        )

        # Should complete without error
