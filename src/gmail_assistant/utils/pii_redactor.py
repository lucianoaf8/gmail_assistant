"""
PII Redaction utilities for Gmail Assistant.
Provides functions to redact personally identifiable information from logs.

Security: Prevents sensitive data exposure in logs (M-4 fix)
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PIIRedactor:
    """Utility for redacting PII from log messages (M-4 security fix)"""

    # Patterns for PII detection
    EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w.-]+\.\w+')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

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

        # Redact email addresses
        def replace_email(match):
            return cls.redact_email(match.group(0))

        message = cls.EMAIL_PATTERN.sub(replace_email, message)

        # Redact phone numbers
        def replace_phone(match):
            return cls.redact_phone(match.group(0))

        message = cls.PHONE_PATTERN.sub(replace_phone, message)

        # Redact SSN-like patterns
        message = cls.SSN_PATTERN.sub("***-**-****", message)

        return message

    @classmethod
    def redact_dict(cls, data: dict, sensitive_keys: Optional[set] = None) -> dict:
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
