"""
Comprehensive tests for secure_logger.py module.
Tests SecureLogger class for PII-redacting logging.
"""

import logging
import pytest
from unittest import mock

from gmail_assistant.utils.secure_logger import SecureLogger, get_secure_logger


class TestSecureLogger:
    """Tests for SecureLogger class."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger instance for testing."""
        return SecureLogger("test_logger")

    def test_secure_logger_init(self, logger):
        """Test SecureLogger initialization."""
        assert logger._logger is not None
        assert logger._redactor is not None

    def test_secure_logger_name(self, logger):
        """Test SecureLogger uses correct logger name."""
        assert logger._logger.name == "test_logger"


class TestDebugMethod:
    """Tests for debug logging method."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger with mocked underlying logger."""
        secure_logger = SecureLogger("test")
        secure_logger._logger = mock.Mock()
        return secure_logger

    def test_debug_redacts_email(self, logger):
        """Test debug method redacts email addresses."""
        logger.debug("User test@example.com logged in")
        call_args = logger._logger.debug.call_args[0][0]
        assert "test@example.com" not in call_args
        assert "[REDACTED_EMAIL]" in call_args

    def test_debug_passes_args(self, logger):
        """Test debug passes additional args to underlying logger."""
        logger.debug("Message %s", "arg1", extra={"key": "value"})
        logger._logger.debug.assert_called_once()


class TestInfoMethod:
    """Tests for info logging method."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger with mocked underlying logger."""
        secure_logger = SecureLogger("test")
        secure_logger._logger = mock.Mock()
        return secure_logger

    def test_info_redacts_phone(self, logger):
        """Test info method redacts phone numbers."""
        logger.info("Contact at 555-123-4567")
        call_args = logger._logger.info.call_args[0][0]
        assert "555-123-4567" not in call_args
        assert "[REDACTED_PHONE]" in call_args

    def test_info_passes_kwargs(self, logger):
        """Test info passes kwargs to underlying logger."""
        logger.info("Message", exc_info=True)
        logger._logger.info.assert_called_once()


class TestWarningMethod:
    """Tests for warning logging method."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger with mocked underlying logger."""
        secure_logger = SecureLogger("test")
        secure_logger._logger = mock.Mock()
        return secure_logger

    def test_warning_redacts_ip(self, logger):
        """Test warning method redacts IP addresses."""
        logger.warning("Connection from 192.168.1.100 failed")
        call_args = logger._logger.warning.call_args[0][0]
        assert "192.168.1.100" not in call_args
        assert "[REDACTED_IP]" in call_args

    def test_warning_preserves_message_structure(self, logger):
        """Test warning preserves non-PII message content."""
        logger.warning("System error occurred")
        call_args = logger._logger.warning.call_args[0][0]
        assert "System error occurred" == call_args


class TestErrorMethod:
    """Tests for error logging method."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger with mocked underlying logger."""
        secure_logger = SecureLogger("test")
        secure_logger._logger = mock.Mock()
        return secure_logger

    def test_error_redacts_ssn(self, logger):
        """Test error method redacts SSN patterns."""
        logger.error("Invalid SSN: 123-45-6789")
        call_args = logger._logger.error.call_args[0][0]
        assert "123-45-6789" not in call_args
        assert "[REDACTED_SSN]" in call_args

    def test_error_called(self, logger):
        """Test error method calls underlying logger."""
        logger.error("Error message")
        logger._logger.error.assert_called_once()


class TestCriticalMethod:
    """Tests for critical logging method."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger with mocked underlying logger."""
        secure_logger = SecureLogger("test")
        secure_logger._logger = mock.Mock()
        return secure_logger

    def test_critical_redacts_credit_card(self, logger):
        """Test critical method redacts credit card numbers."""
        logger.critical("Card 4111-1111-1111-1111 compromised")
        call_args = logger._logger.critical.call_args[0][0]
        assert "4111-1111-1111-1111" not in call_args
        assert "[REDACTED_CC]" in call_args

    def test_critical_called(self, logger):
        """Test critical method calls underlying logger."""
        logger.critical("Critical error")
        logger._logger.critical.assert_called_once()


class TestExceptionMethod:
    """Tests for exception logging method."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger with mocked underlying logger."""
        secure_logger = SecureLogger("test")
        secure_logger._logger = mock.Mock()
        return secure_logger

    def test_exception_redacts_pii(self, logger):
        """Test exception method redacts PII."""
        logger.exception("Failed for user@example.com")
        call_args = logger._logger.exception.call_args[0][0]
        assert "user@example.com" not in call_args
        assert "[REDACTED_EMAIL]" in call_args

    def test_exception_called(self, logger):
        """Test exception method calls underlying logger."""
        logger.exception("Exception occurred")
        logger._logger.exception.assert_called_once()


class TestSetLevel:
    """Tests for setLevel method."""

    def test_set_level(self):
        """Test setLevel method sets logging level."""
        logger = SecureLogger("test")
        logger.setLevel(logging.DEBUG)
        assert logger._logger.level == logging.DEBUG

    def test_set_level_warning(self):
        """Test setLevel to WARNING."""
        logger = SecureLogger("test")
        logger.setLevel(logging.WARNING)
        assert logger._logger.level == logging.WARNING


class TestLevelProperty:
    """Tests for level property."""

    def test_level_property(self):
        """Test level property returns current level."""
        logger = SecureLogger("test")
        logger.setLevel(logging.ERROR)
        assert logger.level == logging.ERROR

    def test_level_default(self):
        """Test default level is inherited from root."""
        logger = SecureLogger("test_default_level")
        # Level should be inherited or NOTSET
        assert logger.level >= 0


class TestLoggerProperty:
    """Tests for logger property."""

    def test_logger_property_returns_underlying(self):
        """Test logger property returns underlying logging.Logger."""
        secure_logger = SecureLogger("test")
        underlying = secure_logger.logger
        assert isinstance(underlying, logging.Logger)
        assert underlying.name == "test"

    def test_logger_property_allows_handler_addition(self):
        """Test underlying logger can have handlers added."""
        secure_logger = SecureLogger("test_handlers")
        handler = logging.StreamHandler()
        secure_logger.logger.addHandler(handler)
        assert handler in secure_logger.logger.handlers


class TestGetSecureLogger:
    """Tests for get_secure_logger factory function."""

    def test_get_secure_logger_returns_secure_logger(self):
        """Test get_secure_logger returns SecureLogger instance."""
        logger = get_secure_logger("factory_test")
        assert isinstance(logger, SecureLogger)

    def test_get_secure_logger_uses_name(self):
        """Test get_secure_logger uses provided name."""
        logger = get_secure_logger("custom_name")
        assert logger._logger.name == "custom_name"


class TestRedactionMethod:
    """Tests for internal _redact method."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger instance."""
        return SecureLogger("test")

    def test_redact_converts_to_string(self, logger):
        """Test _redact converts non-strings to strings."""
        result = logger._redact(12345)
        assert isinstance(result, str)

    def test_redact_handles_none_like_values(self, logger):
        """Test _redact handles None-like values safely."""
        result = logger._redact(None)
        assert isinstance(result, str)

    def test_redact_preserves_non_pii(self, logger):
        """Test _redact preserves non-PII content."""
        message = "Application started successfully"
        result = logger._redact(message)
        assert result == message


class TestMultiplePIITypes:
    """Tests for redacting multiple PII types in single message."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger with mocked underlying logger."""
        secure_logger = SecureLogger("test")
        secure_logger._logger = mock.Mock()
        return secure_logger

    def test_multiple_pii_types_redacted(self, logger):
        """Test message with multiple PII types all redacted."""
        message = "User john@example.com from 192.168.1.1 called 555-123-4567"
        logger.info(message)
        call_args = logger._logger.info.call_args[0][0]

        assert "john@example.com" not in call_args
        assert "192.168.1.1" not in call_args
        assert "555-123-4567" not in call_args
        assert "[REDACTED_EMAIL]" in call_args
        assert "[REDACTED_IP]" in call_args
        assert "[REDACTED_PHONE]" in call_args

    def test_multiple_emails_redacted(self, logger):
        """Test multiple email addresses are all redacted."""
        message = "From: sender@example.com To: recipient@example.org"
        logger.info(message)
        call_args = logger._logger.info.call_args[0][0]

        assert "sender@example.com" not in call_args
        assert "recipient@example.org" not in call_args
        assert call_args.count("[REDACTED_EMAIL]") == 2


class TestLogMessageFormatting:
    """Tests for log message formatting with arguments."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger with mocked underlying logger."""
        secure_logger = SecureLogger("test")
        secure_logger._logger = mock.Mock()
        return secure_logger

    def test_message_with_format_args(self, logger):
        """Test log message with format arguments."""
        logger.info("User %s logged in from %s", "test", "location")
        # The first argument (message) should be redacted
        logger._logger.info.assert_called()

    def test_message_with_extra_kwarg(self, logger):
        """Test log message with extra kwarg."""
        logger.info("Test message", extra={"custom": "data"})
        logger._logger.info.assert_called()


class TestIntegrationWithLogging:
    """Integration tests with real logging module."""

    def test_real_logging_output(self, caplog):
        """Test SecureLogger works with real logging capture."""
        logger = SecureLogger("integration_test")
        logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.INFO, logger="integration_test"):
            logger.info("Test message without PII")

        assert "Test message without PII" in caplog.text

    def test_pii_redacted_in_real_output(self, caplog):
        """Test PII is redacted in real logging output."""
        logger = SecureLogger("integration_redact")
        logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.INFO, logger="integration_redact"):
            logger.info("Email: test@example.com")

        assert "test@example.com" not in caplog.text
        assert "[REDACTED_EMAIL]" in caplog.text


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def logger(self):
        """Create SecureLogger with mocked underlying logger."""
        secure_logger = SecureLogger("test")
        secure_logger._logger = mock.Mock()
        return secure_logger

    def test_empty_message(self, logger):
        """Test logging empty message."""
        logger.info("")
        logger._logger.info.assert_called_with("")

    def test_whitespace_message(self, logger):
        """Test logging whitespace-only message."""
        logger.info("   ")
        logger._logger.info.assert_called_with("   ")

    def test_unicode_message(self, logger):
        """Test logging unicode message."""
        logger.info("Unicode: \u00e9\u00e8 \u4e2d\u6587")
        logger._logger.info.assert_called()

    def test_very_long_message(self, logger):
        """Test logging very long message."""
        long_message = "A" * 10000
        logger.info(long_message)
        call_args = logger._logger.info.call_args[0][0]
        assert len(call_args) == 10000
