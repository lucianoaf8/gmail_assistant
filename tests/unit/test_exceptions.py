"""Unit tests for exception hierarchy in gmail_assistant.core.exceptions."""
from __future__ import annotations

import pytest

from gmail_assistant.core.exceptions import (
    GmailAssistantError,
    ConfigError,
    AuthError,
    NetworkError,
    APIError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy and inheritance."""

    def test_gmail_assistant_error_is_base_exception(self):
        """GmailAssistantError should inherit from Exception."""
        assert issubclass(GmailAssistantError, Exception)

    def test_config_error_inherits_from_base(self):
        """ConfigError should inherit from GmailAssistantError."""
        assert issubclass(ConfigError, GmailAssistantError)

    def test_auth_error_inherits_from_base(self):
        """AuthError should inherit from GmailAssistantError."""
        assert issubclass(AuthError, GmailAssistantError)

    def test_network_error_inherits_from_base(self):
        """NetworkError should inherit from GmailAssistantError."""
        assert issubclass(NetworkError, GmailAssistantError)

    def test_api_error_inherits_from_base(self):
        """APIError should inherit from GmailAssistantError."""
        assert issubclass(APIError, GmailAssistantError)


class TestExceptionInstantiation:
    """Test that exceptions can be instantiated with messages."""

    def test_gmail_assistant_error_with_message(self):
        """GmailAssistantError should preserve message."""
        error = GmailAssistantError("test message")
        assert str(error) == "test message"

    def test_config_error_with_message(self):
        """ConfigError should preserve message."""
        error = ConfigError("invalid config")
        assert str(error) == "invalid config"

    def test_auth_error_with_message(self):
        """AuthError should preserve message."""
        error = AuthError("auth failed")
        assert str(error) == "auth failed"

    def test_network_error_with_message(self):
        """NetworkError should preserve message."""
        error = NetworkError("connection failed")
        assert str(error) == "connection failed"

    def test_api_error_with_message(self):
        """APIError should preserve message."""
        error = APIError("API request failed")
        assert str(error) == "API request failed"


class TestExceptionCatching:
    """Test that exceptions can be caught by specific and base types."""

    def test_catch_config_error_by_type(self):
        """ConfigError should be catchable by its type."""
        with pytest.raises(ConfigError):
            raise ConfigError("test")

    def test_catch_config_error_by_base(self):
        """ConfigError should be catchable by base type."""
        with pytest.raises(GmailAssistantError):
            raise ConfigError("test")

    def test_catch_auth_error_by_type(self):
        """AuthError should be catchable by its type."""
        with pytest.raises(AuthError):
            raise AuthError("test")

    def test_catch_auth_error_by_base(self):
        """AuthError should be catchable by base type."""
        with pytest.raises(GmailAssistantError):
            raise AuthError("test")

    def test_catch_network_error_by_type(self):
        """NetworkError should be catchable by its type."""
        with pytest.raises(NetworkError):
            raise NetworkError("test")

    def test_catch_network_error_by_base(self):
        """NetworkError should be catchable by base type."""
        with pytest.raises(GmailAssistantError):
            raise NetworkError("test")

    def test_catch_api_error_by_type(self):
        """APIError should be catchable by its type."""
        with pytest.raises(APIError):
            raise APIError("test")

    def test_catch_api_error_by_base(self):
        """APIError should be catchable by base type."""
        with pytest.raises(GmailAssistantError):
            raise APIError("test")


class TestExceptionRepr:
    """Test exception repr and str methods."""

    def test_exception_repr(self):
        """Exception repr should include class name and message."""
        error = ConfigError("test message")
        assert "ConfigError" in repr(error)
        assert "test message" in repr(error)

    def test_exception_str(self):
        """Exception str should return the message."""
        error = AuthError("auth failed")
        assert str(error) == "auth failed"

    def test_exception_args(self):
        """Exception args should contain the message."""
        error = NetworkError("connection lost")
        assert error.args == ("connection lost",)
