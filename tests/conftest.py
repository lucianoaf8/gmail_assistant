"""Shared test fixtures for Gmail Assistant."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any
from unittest import mock

import pytest


# ==============================================================================
# Pytest Markers Configuration
# ==============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (requires credentials)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# ==============================================================================
# Directory and File Fixtures
# ==============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_dir: Path) -> dict:
    """Return a sample configuration dictionary."""
    return {
        "credentials_path": str(temp_dir / "credentials.json"),
        "token_path": str(temp_dir / "token.json"),
        "output_dir": str(temp_dir / "backups"),
        "max_emails": 100,
        "rate_limit_per_second": 5.0,
        "log_level": "DEBUG",
    }


@pytest.fixture
def config_file(temp_dir: Path, sample_config: dict) -> Path:
    """Create a temporary config file."""
    config_path = temp_dir / "config.json"
    config_path.write_text(json.dumps(sample_config))
    return config_path


@pytest.fixture
def mock_credentials(temp_dir: Path) -> Path:
    """Create mock credentials file."""
    creds_path = temp_dir / "credentials.json"
    creds_path.write_text(json.dumps({
        "installed": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
        }
    }))
    return creds_path


# ==============================================================================
# Sample Email Data Fixtures
# ==============================================================================

@pytest.fixture
def sample_email_metadata() -> Dict[str, Any]:
    """Return sample email metadata."""
    return {
        "id": "msg123456",
        "threadId": "thread789",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "This is a preview of the email content...",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "recipient@example.com"},
                {"name": "Subject", "value": "Test Email Subject"},
                {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 -0500"},
            ]
        },
        "sizeEstimate": 1024,
        "internalDate": "1704124800000",
    }


@pytest.fixture
def sample_email_list() -> list:
    """Return a list of sample email IDs."""
    return [
        {"id": f"msg{i:03d}", "threadId": f"thread{i:03d}"}
        for i in range(10)
    ]


@pytest.fixture
def sample_email_content() -> str:
    """Return sample email HTML content."""
    return """
    <html>
    <head><title>Test Email</title></head>
    <body>
        <h1>Test Newsletter</h1>
        <p>This is a test email with some content.</p>
        <a href="https://example.com">Click here</a>
    </body>
    </html>
    """


# ==============================================================================
# Mock Service Fixtures
# ==============================================================================

@pytest.fixture
def mock_gmail_service():
    """Create a mock Gmail API service."""
    service = mock.Mock()

    # Mock users().getProfile()
    profile_response = {
        "emailAddress": "test@gmail.com",
        "messagesTotal": 10000,
        "threadsTotal": 5000,
    }
    service.users().getProfile().execute.return_value = profile_response

    # Mock users().messages().list()
    list_response = {
        "messages": [{"id": f"msg{i}", "threadId": f"thread{i}"} for i in range(10)],
        "resultSizeEstimate": 10,
    }
    service.users().messages().list().execute.return_value = list_response

    # Mock users().messages().get()
    get_response = {
        "id": "msg001",
        "threadId": "thread001",
        "labelIds": ["INBOX"],
        "snippet": "Email preview...",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Test Subject"},
            ],
            "body": {"data": "VGVzdCBib2R5"},  # Base64 "Test body"
        },
    }
    service.users().messages().get().execute.return_value = get_response

    return service


@pytest.fixture
def mock_auth():
    """Create a mock authentication instance."""
    auth = mock.Mock()
    auth.is_authenticated = True
    auth.authenticate.return_value = True
    auth.service = mock.Mock()
    auth.user_info = {
        "email": "test@gmail.com",
        "messages_total": 10000,
    }
    return auth


# ==============================================================================
# Error Simulation Fixtures
# ==============================================================================

@pytest.fixture
def mock_http_error_429():
    """Create a mock HTTP 429 (rate limit) error."""
    from googleapiclient.errors import HttpError
    from unittest.mock import Mock

    resp = Mock()
    resp.status = 429
    resp.headers = {"Retry-After": "60"}
    return HttpError(resp, b"Rate limit exceeded")


@pytest.fixture
def mock_http_error_500():
    """Create a mock HTTP 500 (server error) error."""
    from googleapiclient.errors import HttpError
    from unittest.mock import Mock

    resp = Mock()
    resp.status = 500
    resp.headers = {}
    return HttpError(resp, b"Internal server error")


@pytest.fixture
def mock_http_error_401():
    """Create a mock HTTP 401 (authentication) error."""
    from googleapiclient.errors import HttpError
    from unittest.mock import Mock

    resp = Mock()
    resp.status = 401
    resp.headers = {}
    return HttpError(resp, b"Unauthorized")
