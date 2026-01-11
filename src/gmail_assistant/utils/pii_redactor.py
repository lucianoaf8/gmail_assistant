"""
PII Redaction utilities for Gmail Assistant.
Provides functions to redact personally identifiable information from logs.

Security: Prevents sensitive data exposure in logs (M-4 fix)
"""

import logging
import re

logger = logging.getLogger(__name__)


class PIIRedactor:
    """Utility for redacting PII from log messages (M-4 security fix)"""

    # Patterns for PII detection
    EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w.-]+\.\w+')
    # Phone patterns - multiple formats including international
    PHONE_PATTERN = re.compile(
        r'(?:\+\d{1,3}[-.\s]?)?'  # International prefix
        r'(?:\(?\d{3}\)?[-.\s]?)?'  # Area code with optional parens
        r'\d{3}[-.\s]?\d{4}\b'  # Main number
    )
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    # Credit card patterns - common formats
    CREDIT_CARD_PATTERN = re.compile(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b|'  # 4111-1111-1111-1111 or spaces
        r'\b\d{16}\b'  # 16 digits continuous
    )
    # IP address pattern
    IP_ADDRESS_PATTERN = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
        r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
    )

    @staticmethod
    def redact_email(email: str) -> str:
        """
        Redact email address preserving structure hint.

        Example: "john.doe@company.com" -> "jo***@company.com"

        Args:
            email: Email address to redact

        Returns:
            Redacted email address
        """
        if not email or '@' not in email:
            return email

        try:
            local, domain = email.rsplit('@', 1)
            if len(local) <= 2:
                redacted_local = local[0] + '***' if local else '***'
            else:
                redacted_local = local[:2] + '***'
            return f"{redacted_local}@{domain}"
        except Exception:
            return "***@***"

    @staticmethod
    def redact_subject(subject: str, max_length: int = 30) -> str:
        """
        Redact email subject, showing only first part.

        Example: "Your bank statement for January" -> "Your bank stat..."

        Args:
            subject: Email subject to redact
            max_length: Maximum visible length

        Returns:
            Redacted subject
        """
        if not subject:
            return "[no subject]"

        if len(subject) <= max_length:
            return subject

        return subject[:max_length] + "..."

    @staticmethod
    def redact_phone(phone: str) -> str:
        """
        Redact phone number.

        Example: "555-123-4567" -> "***-***-4567"

        Args:
            phone: Phone number to redact

        Returns:
            Redacted phone number
        """
        if not phone:
            return phone

        # Keep last 4 digits
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 4:
            return "***-***-" + digits[-4:]
        return "***"

    @classmethod
    def redact_log_message(cls, message: str) -> str:
        """
        Redact all PII from a log message.

        Args:
            message: Log message to redact

        Returns:
            Message with PII redacted
        """
        if not message:
            return message

        # Order matters! Redact longer/more specific patterns first

        # Redact credit card numbers FIRST (before phone which might match parts)
        message = cls.CREDIT_CARD_PATTERN.sub("[REDACTED_CC]", message)

        # Redact SSN-like patterns (before phone)
        message = cls.SSN_PATTERN.sub("[REDACTED_SSN]", message)

        # Redact email addresses
        message = cls.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", message)

        # Redact phone numbers (after CC and SSN)
        message = cls.PHONE_PATTERN.sub("[REDACTED_PHONE]", message)

        # Redact IP addresses
        message = cls.IP_ADDRESS_PATTERN.sub("[REDACTED_IP]", message)

        return message

    @classmethod
    def redact(cls, text: str) -> str:
        """
        Convenience method to redact all PII from text.
        Alias for redact_log_message.

        Args:
            text: Text to redact

        Returns:
            Text with PII redacted
        """
        return cls.redact_log_message(text)

    @classmethod
    def redact_dict(cls, data: dict, sensitive_keys: set | None = None) -> dict:
        """
        Redact sensitive values from a dictionary.

        Args:
            data: Dictionary to redact
            sensitive_keys: Set of keys to redact (default: common sensitive keys)

        Returns:
            Dictionary with sensitive values redacted
        """
        if sensitive_keys is None:
            sensitive_keys = {
                'email', 'sender', 'from', 'to', 'cc', 'bcc',
                'subject', 'body', 'content', 'snippet',
                'password', 'token', 'api_key', 'secret'
            }

        redacted = {}
        for key, value in data.items():
            key_lower = key.lower()
            if key_lower in sensitive_keys:
                if isinstance(value, str):
                    if '@' in value:
                        redacted[key] = cls.redact_email(value)
                    elif key_lower in ('password', 'token', 'api_key', 'secret'):
                        redacted[key] = "***REDACTED***"
                    else:
                        redacted[key] = cls.redact_subject(value)
                else:
                    redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = cls.redact_dict(value, sensitive_keys)
            elif isinstance(value, list):
                redacted[key] = [
                    cls.redact_dict(item, sensitive_keys) if isinstance(item, dict)
                    else cls.redact_log_message(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                redacted[key] = value

        return redacted
