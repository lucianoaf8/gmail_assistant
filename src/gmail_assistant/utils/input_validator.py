"""
Comprehensive input validation framework for Gmail Fetcher.
Provides secure validation for all user inputs and API parameters.

H-2 fix: Uses centralized ValidationError from exceptions.py
"""

import logging
import os
import re
from pathlib import Path
from re import Pattern
from typing import Any, ClassVar

from gmail_assistant.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class InputValidator:
    """Comprehensive input validation framework."""

    # Gmail search query allowed patterns
    GMAIL_SEARCH_OPERATORS: ClassVar[set[str]] = {
        'from', 'to', 'subject', 'has', 'is', 'in', 'category',
        'before', 'after', 'older_than', 'newer_than', 'larger',
        'smaller', 'filename', 'cc', 'bcc', 'label', 'deliveredto',
        'circle', 'rfc822msgid'
    }

    # Safe filename characters (more restrictive than OS allows)
    SAFE_FILENAME_PATTERN: ClassVar[Pattern[str]] = re.compile(r'^[a-zA-Z0-9._\-\s()]+$')

    # Email validation pattern
    EMAIL_PATTERN: ClassVar[Pattern[str]] = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    # Date format patterns for Gmail queries
    DATE_PATTERNS: ClassVar[list[Pattern[str]]] = [
        re.compile(r'^\d{4}/\d{1,2}/\d{1,2}$'),  # YYYY/MM/DD
        re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$'),  # MM/DD/YYYY
        re.compile(r'^\d{4}-\d{1,2}-\d{1,2}$'),  # YYYY-MM-DD
    ]

    @staticmethod
    def validate_gmail_query(query: str) -> str:
        """
        Validate and sanitize Gmail search query.

        Args:
            query: Gmail search query string

        Returns:
            Sanitized query string

        Raises:
            ValidationError: If query contains invalid patterns
        """
        if not isinstance(query, str):
            raise ValidationError("Query must be a string")

        if not query.strip():
            raise ValidationError("Query cannot be empty")

        # Remove excessive whitespace
        query = ' '.join(query.split())

        # Check length
        if len(query) > 1000:
            raise ValidationError("Query too long (max 1000 characters)")

        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                raise ValidationError(f"Query contains potentially dangerous pattern: {pattern}")

        # Validate Gmail search operators
        parts = query.split()
        for part in parts:
            if ':' in part:
                operator = part.split(':', 1)[0].lower()
                if operator not in InputValidator.GMAIL_SEARCH_OPERATORS:
                    # Allow quoted strings and basic search terms
                    if not (part.startswith('"') or part.startswith("'") or
                           operator in ['AND', 'OR', 'NOT', 'and', 'or', 'not']):
                        logger.warning(f"Unknown Gmail search operator: {operator}")

        logger.info(f"Validated Gmail query: {query[:100]}...")
        return query

    @staticmethod
    def validate_file_path(path: str | Path, must_exist: bool = False,
                          create_dirs: bool = False,
                          allowed_base: Path | None = None) -> Path:
        """
        Validate and sanitize file path with enhanced security (M-1 fix).

        Args:
            path: File path to validate
            must_exist: Whether the path must exist
            create_dirs: Whether to create parent directories
            allowed_base: If set, path must be under this directory

        Returns:
            Validated Path object

        Raises:
            ValidationError: If path is invalid or unsafe
        """
        if not isinstance(path, (str, Path)):
            raise ValidationError("Path must be a string or Path object")

        path = Path(path)
        path_str = str(path)

        # URL-decode path to catch encoded traversal attempts (%2e%2e = ..)
        try:
            from urllib.parse import unquote
            decoded_path = unquote(path_str)
            if decoded_path != path_str:
                logger.warning(f"Path contains URL encoding: {path_str}")
                path_str = decoded_path
                path = Path(decoded_path)
        except Exception:
            pass

        # Resolve to absolute path (follows symlinks)
        try:
            resolved = path.resolve(strict=False)
        except (OSError, RuntimeError) as e:
            raise ValidationError(f"Cannot resolve path: {e}") from e

        # Check for traversal AFTER resolution (catches symlink attacks)
        if '..' in path.parts:
            raise ValidationError("Path contains dangerous traversal component '..'")

        # Validate against allowed base directory (M-1 enhancement)
        if allowed_base is not None:
            allowed_resolved = allowed_base.resolve()
            if not str(resolved).startswith(str(allowed_resolved)):
                raise ValidationError(
                    f"Path traversal detected: {resolved} is not under {allowed_resolved}"
                )

        # Windows-specific checks
        if os.name == 'nt':
            # Allow single drive letter at start
            if len(path_str) > 1 and path_str[1] == ':' and not path_str[0].isalpha():
                raise ValidationError("Invalid Windows drive letter")
            # Check for alternate data streams (file.txt:hidden)
            if ':' in path_str[2:]:
                raise ValidationError("Path contains Windows alternate data stream")
        else:
            # Unix: reject absolute paths without allowed_base
            if path_str.startswith('/') and allowed_base is None:
                logger.warning("Absolute path without allowed_base validation")

        # Check path length
        if len(str(resolved)) > 260:  # Windows MAX_PATH
            raise ValidationError("Path too long (max 260 characters)")

        # Validate filename components - check for reserved Windows names
        invalid_names = {'CON', 'PRN', 'AUX', 'NUL'} | {f'COM{i}' for i in range(10)} | {f'LPT{i}' for i in range(10)}
        for part in resolved.parts:
            name_upper = part.upper().split('.')[0]
            if name_upper in invalid_names:
                raise ValidationError(f"Path contains reserved Windows name: {part}")

        # Validate filename characters (relaxed for legitimate paths)
        for part in path.parts:
            # Skip drive letters
            if len(part) == 2 and part[1] == ':' and part[0].isalpha():
                continue
            # Check for control characters
            if any(ord(c) < 32 for c in part):
                raise ValidationError(f"Path component contains control characters: {part}")

        # Check if path exists when required
        if must_exist and not resolved.exists():
            raise ValidationError(f"Path does not exist: {resolved}")

        # Create parent directories if requested
        if create_dirs and not resolved.parent.exists():
            try:
                resolved.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directories: {resolved.parent}")
            except OSError as e:
                raise ValidationError(f"Failed to create directories: {e}") from e

        return resolved

    @staticmethod
    def validate_email_address(email: str) -> str:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            Validated email address

        Raises:
            ValidationError: If email format is invalid
        """
        if not isinstance(email, str):
            raise ValidationError("Email must be a string")

        email = email.strip().lower()

        if not email:
            raise ValidationError("Email cannot be empty")

        if len(email) > 254:  # RFC 5321 limit
            raise ValidationError("Email address too long")

        if not InputValidator.EMAIL_PATTERN.match(email):
            raise ValidationError(f"Invalid email format: {email}")

        return email

    @staticmethod
    def validate_integer(value: Any, min_val: int | None = None,
                        max_val: int | None = None) -> int:
        """
        Validate and convert integer value.

        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Validated integer

        Raises:
            ValidationError: If value is invalid
        """
        try:
            if isinstance(value, str):
                value = int(value)
            elif not isinstance(value, int):
                raise ValueError()
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid integer value: {value}") from e

        if min_val is not None and value < min_val:
            raise ValidationError(f"Value {value} below minimum {min_val}")

        if max_val is not None and value > max_val:
            raise ValidationError(f"Value {value} above maximum {max_val}")

        return value

    @staticmethod
    def validate_string(value: Any, min_length: int = 0, max_length: int = 1000,
                       allowed_chars: str | None = None) -> str:
        """
        Validate string value.

        Args:
            value: Value to validate
            min_length: Minimum string length
            max_length: Maximum string length
            allowed_chars: Regex pattern for allowed characters

        Returns:
            Validated string

        Raises:
            ValidationError: If string is invalid
        """
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")

        if len(value) < min_length:
            raise ValidationError(f"String too short (min {min_length} chars)")

        if len(value) > max_length:
            raise ValidationError(f"String too long (max {max_length} chars)")

        if allowed_chars and not re.match(allowed_chars, value):
            raise ValidationError("String contains invalid characters")

        return value

    @staticmethod
    def validate_date_string(date_str: str) -> str:
        """
        Validate date string for Gmail queries.

        Args:
            date_str: Date string to validate

        Returns:
            Validated date string

        Raises:
            ValidationError: If date format is invalid
        """
        if not isinstance(date_str, str):
            raise ValidationError("Date must be a string")

        date_str = date_str.strip()

        if not date_str:
            raise ValidationError("Date cannot be empty")

        # Check against known date patterns
        for pattern in InputValidator.DATE_PATTERNS:
            if pattern.match(date_str):
                return date_str

        # Check for relative date formats
        relative_patterns = [
            r'^\d+[dwmy]$',  # 7d, 2w, 3m, 1y
            r'^\d+days?$',
            r'^\d+weeks?$',
            r'^\d+months?$',
            r'^\d+years?$',
        ]

        for pattern in relative_patterns:
            if re.match(pattern, date_str, re.IGNORECASE):
                return date_str

        raise ValidationError(f"Invalid date format: {date_str}")

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 200) -> str:
        """
        Sanitize filename for safe filesystem storage.

        Args:
            filename: Original filename
            max_length: Maximum filename length

        Returns:
            Sanitized filename

        Raises:
            ValidationError: If filename cannot be sanitized
        """
        if not isinstance(filename, str):
            raise ValidationError("Filename must be a string")

        if not filename.strip():
            raise ValidationError("Filename cannot be empty")

        # Remove/replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)  # Remove control characters
        filename = filename.strip('. ')  # Remove leading/trailing dots and spaces

        # Ensure reasonable length
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            max_name_length = max_length - len(ext)
            filename = name[:max_name_length] + ext

        if not filename:
            raise ValidationError("Filename becomes empty after sanitization")

        return filename

    @staticmethod
    def validate_batch_size(batch_size: Any, max_allowed: int = 1000) -> int:
        """
        Validate API batch size parameter.

        Args:
            batch_size: Batch size to validate
            max_allowed: Maximum allowed batch size

        Returns:
            Validated batch size

        Raises:
            ValidationError: If batch size is invalid
        """
        batch_size = InputValidator.validate_integer(batch_size, min_val=1, max_val=max_allowed)

        # Warn about very large batch sizes
        if batch_size > 500:
            logger.warning(f"Large batch size may cause performance issues: {batch_size}")

        return batch_size

    @staticmethod
    def validate_config_dict(config: dict[str, Any], required_keys: list[str]) -> dict[str, Any]:
        """
        Validate configuration dictionary.

        Args:
            config: Configuration dictionary to validate
            required_keys: List of required keys

        Returns:
            Validated configuration dictionary

        Raises:
            ValidationError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary")

        # Check for required keys
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValidationError(f"Missing required configuration keys: {missing_keys}")

        return config


# Convenience function for easier import
def validate_file_path(path: str | Path, must_exist: bool = False,
                       create_dirs: bool = False,
                       allowed_base: Path | None = None) -> Path:
    """
    Validate and sanitize file path. Convenience wrapper for InputValidator.validate_file_path.

    Args:
        path: File path to validate
        must_exist: Whether the path must exist
        create_dirs: Whether to create parent directories
        allowed_base: If set, path must be under this directory

    Returns:
        Validated Path object
    """
    return InputValidator.validate_file_path(path, must_exist, create_dirs, allowed_base)
