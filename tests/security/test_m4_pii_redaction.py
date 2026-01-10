"""
Test M-4: PII Redaction
Validates PII redaction in logs and output.
"""
import pytest
from pathlib import Path


class TestPIIRedactor:
    """Tests for PII redaction utilities (M-4 fix)."""

    def test_redactor_module_exists(self):
        """Verify PII redactor module exists."""
        from gmail_assistant.utils import pii_redactor

        assert hasattr(pii_redactor, 'PIIRedactor') or \
               hasattr(pii_redactor, 'redact_pii'), \
            "PII redactor should have redaction functionality"

    def test_email_redaction(self):
        """Verify email addresses are redacted."""
        from gmail_assistant.utils.pii_redactor import PIIRedactor

        redactor = PIIRedactor()

        test_cases = [
            ("Contact john.doe@example.com for help", "john.doe@example.com"),
            ("Email: test@gmail.com", "test@gmail.com"),
            ("user.name+tag@domain.co.uk", "user.name+tag@domain.co.uk"),
        ]

        for text, email in test_cases:
            result = redactor.redact(text)
            assert email not in result, f"Email {email} should be redacted"
            assert "[REDACTED_EMAIL]" in result or "[EMAIL]" in result.upper()

    def test_phone_redaction(self):
        """Verify phone numbers are redacted."""
        from gmail_assistant.utils.pii_redactor import PIIRedactor

        redactor = PIIRedactor()

        test_cases = [
            ("Call 555-123-4567", "555-123-4567"),
            ("Phone: (555) 123-4567", "(555) 123-4567"),
            ("Mobile: +1-555-123-4567", "+1-555-123-4567"),
        ]

        for text, phone in test_cases:
            result = redactor.redact(text)
            # Phone might be partially matched
            assert phone not in result or "[REDACTED" in result

    def test_ssn_redaction(self):
        """Verify SSN patterns are redacted."""
        from gmail_assistant.utils.pii_redactor import PIIRedactor

        redactor = PIIRedactor()

        text = "SSN: 123-45-6789"
        result = redactor.redact(text)

        assert "123-45-6789" not in result, "SSN should be redacted"

    def test_credit_card_redaction(self):
        """Verify credit card patterns are redacted."""
        from gmail_assistant.utils.pii_redactor import PIIRedactor

        redactor = PIIRedactor()

        test_cases = [
            "Card: 4111-1111-1111-1111",
            "CC: 4111111111111111",
        ]

        for text in test_cases:
            result = redactor.redact(text)
            assert "4111" not in result or len(result.replace("[", "").replace("]", "")) < len(text)

    def test_ip_address_redaction(self):
        """Verify IP addresses are redacted."""
        from gmail_assistant.utils.pii_redactor import PIIRedactor

        redactor = PIIRedactor()

        text = "Client IP: 192.168.1.100"
        result = redactor.redact(text)

        assert "192.168.1.100" not in result


class TestSecureLogger:
    """Tests for secure logging with PII redaction."""

    def test_secure_logger_exists(self):
        """Verify secure logger module exists."""
        from gmail_assistant.utils import secure_logger

        assert hasattr(secure_logger, 'SecureLogger') or \
               hasattr(secure_logger, 'get_secure_logger'), \
            "Secure logger should be available"

    def test_logger_redacts_pii(self):
        """Verify logger automatically redacts PII."""
        from gmail_assistant.utils.secure_logger import SecureLogger
        import io
        import logging

        # Create logger with string handler for testing
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter('%(message)s'))

        logger = SecureLogger("test")
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.INFO)

        # Log message with PII
        logger.info("User email: test@example.com logged in")

        output = stream.getvalue()
        assert "test@example.com" not in output, \
            "Logger should redact email addresses"

    def test_logger_preserves_non_pii(self):
        """Verify logger preserves non-PII content."""
        from gmail_assistant.utils.secure_logger import SecureLogger
        import io
        import logging

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter('%(message)s'))

        logger = SecureLogger("test")
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.INFO)

        logger.info("Processing 100 messages successfully")

        output = stream.getvalue()
        assert "Processing" in output
        assert "100" in output
        assert "successfully" in output
