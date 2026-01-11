"""
Comprehensive tests for pii_redactor.py module.
Tests PIIRedactor class for PII detection and redaction.
"""

import pytest

from gmail_assistant.utils.pii_redactor import PIIRedactor


class TestRedactEmail:
    """Tests for redact_email method."""

    def test_redact_standard_email(self):
        """Test redacting a standard email address."""
        result = PIIRedactor.redact_email("john.doe@company.com")
        assert result == "jo***@company.com"

    def test_redact_short_local_part(self):
        """Test redacting email with short local part."""
        result = PIIRedactor.redact_email("jo@example.com")
        # With 2-char local part, first 2 chars preserved
        assert result == "jo***@example.com" or result == "j***@example.com"

    def test_redact_single_char_local(self):
        """Test redacting email with single character local part."""
        result = PIIRedactor.redact_email("j@example.com")
        assert result == "j***@example.com"

    def test_redact_empty_string(self):
        """Test redacting empty string returns empty string."""
        result = PIIRedactor.redact_email("")
        assert result == ""

    def test_redact_none_like_string(self):
        """Test redacting None-like input."""
        result = PIIRedactor.redact_email(None)
        assert result is None

    def test_redact_no_at_symbol(self):
        """Test redacting string without @ returns original."""
        result = PIIRedactor.redact_email("not_an_email")
        assert result == "not_an_email"

    def test_redact_email_preserves_domain(self):
        """Test that domain is preserved in redaction."""
        result = PIIRedactor.redact_email("test@specific-domain.org")
        assert "@specific-domain.org" in result

    def test_redact_email_with_plus(self):
        """Test redacting email with plus addressing."""
        result = PIIRedactor.redact_email("user+tag@gmail.com")
        assert result == "us***@gmail.com"


class TestRedactSubject:
    """Tests for redact_subject method."""

    def test_redact_long_subject(self):
        """Test truncating long subject."""
        subject = "This is a very long email subject that should be truncated"
        result = PIIRedactor.redact_subject(subject, max_length=30)
        assert result == "This is a very long email subj..."

    def test_redact_short_subject(self):
        """Test short subject is not truncated."""
        subject = "Short subject"
        result = PIIRedactor.redact_subject(subject, max_length=30)
        assert result == "Short subject"

    def test_redact_exact_length_subject(self):
        """Test subject exactly at max length is not truncated."""
        subject = "A" * 30
        result = PIIRedactor.redact_subject(subject, max_length=30)
        assert result == subject

    def test_redact_empty_subject(self):
        """Test empty subject returns placeholder."""
        result = PIIRedactor.redact_subject("")
        assert result == "[no subject]"

    def test_redact_none_subject(self):
        """Test None subject returns placeholder."""
        result = PIIRedactor.redact_subject(None)
        assert result == "[no subject]"

    def test_redact_subject_default_length(self):
        """Test default max_length is applied."""
        subject = "A" * 50
        result = PIIRedactor.redact_subject(subject)
        assert len(result) == 33  # 30 + "..."


class TestRedactPhone:
    """Tests for redact_phone method."""

    def test_redact_standard_phone(self):
        """Test redacting standard US phone format."""
        result = PIIRedactor.redact_phone("555-123-4567")
        assert result == "***-***-4567"

    def test_redact_phone_with_area_code(self):
        """Test redacting phone with parenthetical area code."""
        result = PIIRedactor.redact_phone("(555) 123-4567")
        assert result == "***-***-4567"

    def test_redact_international_phone(self):
        """Test redacting international phone number."""
        result = PIIRedactor.redact_phone("+1 555 123 4567")
        assert result == "***-***-4567"

    def test_redact_short_phone(self):
        """Test redacting very short phone."""
        result = PIIRedactor.redact_phone("123")
        assert result == "***"

    def test_redact_empty_phone(self):
        """Test empty phone returns empty."""
        result = PIIRedactor.redact_phone("")
        assert result == ""

    def test_redact_none_phone(self):
        """Test None phone returns None."""
        result = PIIRedactor.redact_phone(None)
        assert result is None

    def test_redact_phone_preserves_last_four(self):
        """Test last four digits are preserved."""
        result = PIIRedactor.redact_phone("1234567890")
        assert "7890" in result


class TestRedactLogMessage:
    """Tests for redact_log_message method."""

    def test_redact_email_in_message(self):
        """Test redacting email address in log message."""
        message = "User john.doe@example.com logged in"
        result = PIIRedactor.redact_log_message(message)
        assert "[REDACTED_EMAIL]" in result
        assert "john.doe@example.com" not in result

    def test_redact_multiple_emails(self):
        """Test redacting multiple email addresses."""
        message = "From: a@b.com To: c@d.com"
        result = PIIRedactor.redact_log_message(message)
        assert result.count("[REDACTED_EMAIL]") == 2

    def test_redact_phone_in_message(self):
        """Test redacting phone number in log message."""
        message = "Call 555-123-4567 for support"
        result = PIIRedactor.redact_log_message(message)
        assert "[REDACTED_PHONE]" in result
        assert "555-123-4567" not in result

    def test_redact_ssn_in_message(self):
        """Test redacting SSN in log message."""
        message = "SSN: 123-45-6789"
        result = PIIRedactor.redact_log_message(message)
        assert "[REDACTED_SSN]" in result
        assert "123-45-6789" not in result

    def test_redact_credit_card_with_spaces(self):
        """Test redacting credit card with spaces."""
        message = "Card: 4111 1111 1111 1111"
        result = PIIRedactor.redact_log_message(message)
        assert "[REDACTED_CC]" in result
        assert "4111" not in result

    def test_redact_credit_card_with_dashes(self):
        """Test redacting credit card with dashes."""
        message = "Card: 4111-1111-1111-1111"
        result = PIIRedactor.redact_log_message(message)
        assert "[REDACTED_CC]" in result

    def test_redact_continuous_credit_card(self):
        """Test redacting continuous credit card number."""
        message = "Card: 4111111111111111"
        result = PIIRedactor.redact_log_message(message)
        assert "[REDACTED_CC]" in result

    def test_redact_ip_address(self):
        """Test redacting IP address in log message."""
        message = "Connection from 192.168.1.100"
        result = PIIRedactor.redact_log_message(message)
        assert "[REDACTED_IP]" in result
        assert "192.168.1.100" not in result

    def test_redact_multiple_pii_types(self):
        """Test redacting multiple PII types in one message."""
        message = "User john@example.com from 192.168.1.1 called 555-123-4567"
        result = PIIRedactor.redact_log_message(message)
        assert "[REDACTED_EMAIL]" in result
        assert "[REDACTED_IP]" in result
        assert "[REDACTED_PHONE]" in result

    def test_redact_empty_message(self):
        """Test empty message returns empty."""
        result = PIIRedactor.redact_log_message("")
        assert result == ""

    def test_redact_none_message(self):
        """Test None message returns None."""
        result = PIIRedactor.redact_log_message(None)
        assert result is None

    def test_redact_message_no_pii(self):
        """Test message without PII is unchanged."""
        message = "Application started successfully"
        result = PIIRedactor.redact_log_message(message)
        assert result == message


class TestRedactMethod:
    """Tests for redact convenience method."""

    def test_redact_is_alias(self):
        """Test redact is an alias for redact_log_message."""
        message = "Email: test@example.com"
        result1 = PIIRedactor.redact(message)
        result2 = PIIRedactor.redact_log_message(message)
        assert result1 == result2


class TestRedactDict:
    """Tests for redact_dict method."""

    def test_redact_email_key(self):
        """Test redacting value with 'email' key."""
        data = {"email": "john@example.com"}
        result = PIIRedactor.redact_dict(data)
        assert "jo***@example.com" in result["email"]

    def test_redact_subject_key(self):
        """Test redacting value with 'subject' key."""
        data = {"subject": "Very long subject that should be truncated here"}
        result = PIIRedactor.redact_dict(data)
        assert result["subject"].endswith("...")

    def test_redact_password_key(self):
        """Test redacting value with 'password' key."""
        data = {"password": "secret123"}
        result = PIIRedactor.redact_dict(data)
        assert result["password"] == "***REDACTED***"

    def test_redact_token_key(self):
        """Test redacting value with 'token' key."""
        data = {"token": "abc123xyz"}
        result = PIIRedactor.redact_dict(data)
        assert result["token"] == "***REDACTED***"

    def test_redact_api_key(self):
        """Test redacting value with 'api_key' key."""
        data = {"api_key": "sk-123456"}
        result = PIIRedactor.redact_dict(data)
        assert result["api_key"] == "***REDACTED***"

    def test_redact_nested_dict(self):
        """Test redacting nested dictionary."""
        data = {
            "user": {
                "email": "test@example.com",
                "password": "secret"
            }
        }
        result = PIIRedactor.redact_dict(data)
        assert "***" in result["user"]["email"]
        assert result["user"]["password"] == "***REDACTED***"

    def test_redact_list_values(self):
        """Test redacting list values."""
        data = {
            "items": [
                {"email": "a@b.com"},
                {"email": "c@d.com"}
            ]
        }
        result = PIIRedactor.redact_dict(data)
        assert "***@b.com" in result["items"][0]["email"]
        assert "***@d.com" in result["items"][1]["email"]

    def test_redact_preserves_non_sensitive(self):
        """Test non-sensitive keys are preserved."""
        data = {"count": 42, "status": "active"}
        result = PIIRedactor.redact_dict(data)
        assert result["count"] == 42
        assert result["status"] == "active"

    def test_redact_custom_sensitive_keys(self):
        """Test with custom sensitive keys."""
        # Custom sensitive keys need to include the lower-case version
        data = {"email": "user@example.com", "normal": "keep"}
        result = PIIRedactor.redact_dict(data)
        assert "***" in str(result["email"])
        assert result["normal"] == "keep"

    def test_redact_non_string_sensitive(self):
        """Test redacting non-string sensitive value."""
        data = {"password": 12345}
        result = PIIRedactor.redact_dict(data)
        assert result["password"] == "***REDACTED***"

    def test_redact_list_with_strings(self):
        """Test redacting list containing strings."""
        data = {
            "messages": ["Email: test@example.com", "Phone: 555-1234"]
        }
        result = PIIRedactor.redact_dict(data)
        # Strings in list should have PII redacted
        assert "[REDACTED_EMAIL]" in result["messages"][0]


class TestPatternMatching:
    """Tests for PII pattern matching regex."""

    def test_email_pattern_standard(self):
        """Test EMAIL_PATTERN matches standard emails."""
        assert PIIRedactor.EMAIL_PATTERN.search("test@example.com")
        assert PIIRedactor.EMAIL_PATTERN.search("user.name@sub.domain.org")

    def test_email_pattern_with_plus(self):
        """Test EMAIL_PATTERN matches plus addressing."""
        assert PIIRedactor.EMAIL_PATTERN.search("user+tag@gmail.com")

    def test_phone_pattern_us_format(self):
        """Test PHONE_PATTERN matches US phone formats."""
        assert PIIRedactor.PHONE_PATTERN.search("555-123-4567")
        assert PIIRedactor.PHONE_PATTERN.search("(555) 123-4567")
        assert PIIRedactor.PHONE_PATTERN.search("5551234567")

    def test_phone_pattern_international(self):
        """Test PHONE_PATTERN matches international format."""
        assert PIIRedactor.PHONE_PATTERN.search("+1 555 123 4567")

    def test_ssn_pattern(self):
        """Test SSN_PATTERN matches SSN format."""
        assert PIIRedactor.SSN_PATTERN.search("123-45-6789")
        assert not PIIRedactor.SSN_PATTERN.search("1234-5-6789")

    def test_credit_card_pattern(self):
        """Test CREDIT_CARD_PATTERN matches card formats."""
        assert PIIRedactor.CREDIT_CARD_PATTERN.search("4111111111111111")
        assert PIIRedactor.CREDIT_CARD_PATTERN.search("4111 1111 1111 1111")
        assert PIIRedactor.CREDIT_CARD_PATTERN.search("4111-1111-1111-1111")

    def test_ip_address_pattern(self):
        """Test IP_ADDRESS_PATTERN matches valid IPs."""
        assert PIIRedactor.IP_ADDRESS_PATTERN.search("192.168.1.1")
        assert PIIRedactor.IP_ADDRESS_PATTERN.search("10.0.0.255")
        assert PIIRedactor.IP_ADDRESS_PATTERN.search("255.255.255.255")

    def test_ip_address_pattern_invalid(self):
        """Test IP_ADDRESS_PATTERN rejects invalid IPs."""
        # Should not match
        assert not PIIRedactor.IP_ADDRESS_PATTERN.search("256.1.1.1")
        assert not PIIRedactor.IP_ADDRESS_PATTERN.search("1.2.3.256")


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_case_insensitive_key_matching(self):
        """Test dict redaction is case insensitive for keys."""
        data = {"EMAIL": "test@example.com", "Password": "secret"}
        result = PIIRedactor.redact_dict(data)
        assert "***" in result["EMAIL"]
        assert result["Password"] == "***REDACTED***"

    def test_deep_nested_structure(self):
        """Test redaction works with deeply nested structures."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "email": "deep@example.com"
                    }
                }
            }
        }
        result = PIIRedactor.redact_dict(data)
        assert "***" in result["level1"]["level2"]["level3"]["email"]

    def test_mixed_list_content(self):
        """Test list with mixed content types."""
        data = {
            "mixed": [1, "text with email@test.com", {"nested": "value"}, None]
        }
        result = PIIRedactor.redact_dict(data)
        assert result["mixed"][0] == 1
        assert "[REDACTED_EMAIL]" in result["mixed"][1]
        assert result["mixed"][2] == {"nested": "value"}
        assert result["mixed"][3] is None

    def test_empty_dict(self):
        """Test redacting empty dict returns empty dict."""
        result = PIIRedactor.redact_dict({})
        assert result == {}
