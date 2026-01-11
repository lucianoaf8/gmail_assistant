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

    # Messages list mock
    service.users().messages().list().execute.return_value = {
        "messages": [{"id": f"msg{i}", "threadId": f"thread{i}"} for i in range(10)],
        "resultSizeEstimate": 10
    }

    # Messages get mock
    def mock_get_message(**kwargs):
        msg_id = kwargs.get('id', 'msg001')
        result = mock.MagicMock()
        result.execute.return_value = {
            "id": msg_id,
            "threadId": f"thread_{msg_id}",
            "labelIds": ["INBOX"],
            "snippet": "Email preview...",
            "sizeEstimate": 1024,
            "internalDate": "1704124800000",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": f"Test Subject {msg_id}"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 -0500"},
                ],
                "body": {"data": "VGVzdCBib2R5IGNvbnRlbnQ="},  # Base64 "Test body content"
            }
        }
        return result

    service.users().messages().get = mock_get_message

    # Messages trash mock
    service.users().messages().trash().execute.return_value = {"id": "msg001"}

    # Messages delete mock
    service.users().messages().delete().execute.return_value = {}

    return service
