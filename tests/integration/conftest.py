"""Shared fixtures for integration tests."""

import json
import tempfile
from pathlib import Path
from typing import Generator
from unittest import mock

import pytest


@pytest.fixture
def integration_temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for integration tests."""
    with tempfile.TemporaryDirectory(prefix="gmail_int_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_credentials_file(integration_temp_dir: Path) -> Path:
    """Create a mock credentials.json file."""
    creds_path = integration_temp_dir / "credentials.json"
    creds_path.write_text(json.dumps({
        "installed": {
            "client_id": "test-client-id.apps.googleusercontent.com",
            "client_secret": "test-client-secret",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }))
    return creds_path


@pytest.fixture
def mock_token_file(integration_temp_dir: Path) -> Path:
    """Create a mock token.json file."""
    token_path = integration_temp_dir / "token.json"
    token_path.write_text(json.dumps({
        "token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test-client-id.apps.googleusercontent.com",
        "client_secret": "test-client-secret",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
    }))
    return token_path


@pytest.fixture
def mock_config_file(integration_temp_dir: Path, mock_credentials_file: Path) -> Path:
    """Create a mock config.json file."""
    config_path = integration_temp_dir / "config.json"
    config_path.write_text(json.dumps({
        "credentials_path": str(mock_credentials_file),
        "token_path": str(integration_temp_dir / "token.json"),
        "output_dir": str(integration_temp_dir / "backups"),
        "max_emails": 100,
        "rate_limit_per_second": 5.0,
        "log_level": "DEBUG"
    }))
    return config_path


@pytest.fixture
def sample_email_files(integration_temp_dir: Path) -> Path:
    """Create sample email files for analysis tests."""
    emails_dir = integration_temp_dir / "emails"
    emails_dir.mkdir()

    # Create sample JSON email files
    for i in range(5):
        email_data = {
            "id": f"msg{i:05d}",
            "threadId": f"thread{i:05d}",
            "subject": f"Test Email {i}",
            "sender": f"sender{i}@example.com",
            "date": f"2024-01-{15+i:02d}T10:00:00Z",
            "labels": ["INBOX"],
            "body": f"This is test email {i}"
        }
        (emails_dir / f"email_{i:05d}.json").write_text(json.dumps(email_data))

    return emails_dir


@pytest.fixture
def sample_markdown_files(integration_temp_dir: Path) -> Path:
    """Create sample markdown email files."""
    md_dir = integration_temp_dir / "markdown"
    md_dir.mkdir()

    for i in range(3):
        md_content = f"""# Email

| Field | Value |
| --- | --- |
| Date | Mon, {15+i} Jan 2024 10:00:00 +0000 |
| From | sender{i}@example.com |
| To | recipient@example.com |
| Subject | Test Email {i} |
| Gmail ID | msg{i:05d} |
| Thread ID | thread{i:05d} |
| Labels | INBOX |

## Message Content

This is the content of test email {i}.
"""
        (md_dir / f"2024-01-{15+i:02d}_100000_test_{i:05d}.md").write_text(md_content)

    return md_dir


@pytest.fixture
def mock_gmail_service_full():
    """Create a comprehensive mock Gmail API service."""
    service = mock.MagicMock()

    # Profile mock
    service.users().getProfile().execute.return_value = {
        "emailAddress": "test@gmail.com",
        "messagesTotal": 10000,
        "threadsTotal": 5000,
        "historyId": "123456"
    }

    # Labels mock
    service.users().labels().list().execute.return_value = {
        "labels": [
            {"id": "INBOX", "name": "INBOX", "type": "system"},
            {"id": "SENT", "name": "SENT", "type": "system"},
            {"id": "DRAFT", "name": "DRAFT", "type": "system"},
            {"id": "TRASH", "name": "TRASH", "type": "system"},
            {"id": "Label_1", "name": "Newsletter", "type": "user"},
            {"id": "Label_2", "name": "Important", "type": "user"}
        ]
    }

    # Messages list mock - respects maxResults parameter
    def mock_list_messages(**kwargs):
        max_results = kwargs.get('maxResults', 100)
        query = kwargs.get('q', '')
        result = mock.MagicMock()

        # Generate different message sets based on query
        all_messages = [{"id": f"msg{i:05d}", "threadId": f"thread{i:05d}"} for i in range(100)]

        # Filter messages based on query (simple simulation)
        if 'from:' in query or 'subject:' in query or 'has:attachment' in query:
            # Simulate fewer results for specific queries
            all_messages = all_messages[:20]
        elif query == '':
            # Empty query returns all
            pass

        # Respect maxResults parameter
        messages = all_messages[:min(max_results, len(all_messages))]
        result.execute.return_value = {
            "messages": messages,
            "resultSizeEstimate": len(messages)
        }
        return result

    service.users().messages().list = mock_list_messages

    # Messages get mock
    def mock_get_message(**kwargs):
        msg_id = kwargs.get('id', 'msg00001')
        msg_format = kwargs.get('format', 'full')
        result = mock.MagicMock()

        # Generate varied content based on message ID
        msg_num = int(msg_id.replace('msg', ''))

        result.execute.return_value = {
            "id": msg_id,
            "threadId": f"thread_{msg_id}",
            "labelIds": ["INBOX", "UNREAD"] if msg_num % 3 == 0 else ["INBOX"],
            "snippet": f"Email preview for {msg_id}...",
            "sizeEstimate": 1024 * (1 + msg_num % 10),
            "internalDate": str(1704124800000 + msg_num * 86400000),
            "payload": {
                "headers": [
                    {"name": "From", "value": f"sender{msg_num % 5}@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": f"Test Subject {msg_id}"},
                    {"name": "Date", "value": f"Mon, {1 + msg_num % 28} Jan 2024 12:00:00 -0500"},
                    {"name": "Message-ID", "value": f"<{msg_id}@mail.example.com>"},
                    {"name": "Content-Type", "value": "multipart/alternative"},
                ],
                "mimeType": "multipart/alternative",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": "VGVzdCBib2R5IGNvbnRlbnQgZm9yIHRoaXMgZW1haWw="}  # Base64 encoded
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": "PGh0bWw+PGJvZHk+PHA+VGVzdCBib2R5IGNvbnRlbnQgZm9yIHRoaXMgZW1haWw8L3A+PC9ib2R5PjwvaHRtbD4="}  # Base64 encoded
                    }
                ]
            }
        }
        return result

    service.users().messages().get = mock_get_message

    # Messages trash mock
    def mock_trash_message(**kwargs):
        msg_id = kwargs.get('id', 'msg00001')
        result = mock.MagicMock()
        result.execute.return_value = {
            "id": msg_id,
            "threadId": f"thread_{msg_id}",
            "labelIds": ["TRASH"]
        }
        return result

    service.users().messages().trash = mock_trash_message

    # Messages delete mock
    def mock_delete_message(**kwargs):
        result = mock.MagicMock()
        result.execute.return_value = {}
        return result

    service.users().messages().delete = mock_delete_message

    return service


@pytest.fixture
def mock_gmail_fetcher(mock_credentials_file, mock_gmail_service_full):
    """Create a fully mocked GmailFetcher instance."""
    from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

    fetcher = GmailFetcher(str(mock_credentials_file))

    # Mock authentication
    with mock.patch.object(fetcher.auth, 'authenticate', return_value=True):
        with mock.patch.object(type(fetcher.auth), 'service', new_callable=mock.PropertyMock, return_value=mock_gmail_service_full):
            fetcher.authenticate()
            yield fetcher


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory(prefix="gmail_test_") as tmpdir:
        yield Path(tmpdir)
