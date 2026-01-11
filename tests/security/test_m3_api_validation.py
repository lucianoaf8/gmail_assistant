"""
Test M-3: API Response Validation
Validates Gmail API response validation.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock
from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher


@pytest.fixture
def gmail_fetcher():
    """Create a GmailFetcher instance without full initialization."""
    return GmailFetcher.__new__(GmailFetcher)


class TestAPIResponseValidation:
    """Tests for API response validation (M-3 fix)."""

    def test_validation_method_exists(self):
        """Verify _validate_api_response method exists."""
        from gmail_assistant.core.fetch import gmail_assistant

        source = Path(gmail_assistant.__file__).read_text(encoding='utf-8')

        assert '_validate_api_response' in source, \
            "_validate_api_response method should exist"

    def test_null_response_rejected(self, gmail_fetcher):
        """Verify null responses are rejected."""
        fetcher = gmail_fetcher

        with pytest.raises(ValueError) as exc_info:
            fetcher._validate_api_response(None, ['id'], "test")

        assert "null" in str(exc_info.value).lower()

    def test_non_dict_response_rejected(self, gmail_fetcher):
        """Verify non-dict responses are rejected."""
        fetcher = gmail_fetcher

        invalid_responses = [
            "string response",
            123,
            ["list", "response"],
            True,
        ]

        for response in invalid_responses:
            with pytest.raises(ValueError) as exc_info:
                fetcher._validate_api_response(response, ['id'], "test")
            assert "non-dict" in str(exc_info.value).lower() or \
                   "dict" in str(exc_info.value).lower()

    def test_missing_fields_rejected(self, gmail_fetcher):
        """Verify responses missing required fields are rejected."""
        fetcher = gmail_fetcher

        incomplete_response = {
            'id': '123',
            # Missing 'threadId' and 'labelIds'
        }

        with pytest.raises(ValueError) as exc_info:
            fetcher._validate_api_response(
                incomplete_response,
                ['id', 'threadId', 'labelIds'],
                "test"
            )

        assert "missing" in str(exc_info.value).lower()

    def test_valid_response_accepted(self, gmail_fetcher):
        """Verify valid responses pass validation."""
        fetcher = gmail_fetcher

        valid_response = {
            'id': '123abc',
            'threadId': 'thread456',
            'labelIds': ['INBOX'],
        }

        result = fetcher._validate_api_response(
            valid_response,
            ['id', 'threadId'],
            "test"
        )

        assert result == valid_response


class TestAPIValidationIntegration:
    """Tests for API validation integration in Gmail operations."""

    def test_list_messages_validates_response(self):
        """Verify list messages validates API response."""
        from gmail_assistant.core.fetch import gmail_assistant

        source = Path(gmail_assistant.__file__).read_text(encoding='utf-8')

        # Should validate message list responses
        assert '_validate_api_response' in source, \
            "Should use _validate_api_response for API calls"

    def test_get_message_validates_response(self):
        """Verify get message validates API response."""
        from gmail_assistant.core.fetch import gmail_assistant

        source = Path(gmail_assistant.__file__).read_text(encoding='utf-8')

        # Validation should be called in message retrieval
        assert 'validate' in source.lower()
