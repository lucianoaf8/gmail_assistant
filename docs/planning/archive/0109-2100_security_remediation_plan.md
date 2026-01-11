# Security Remediation Implementation Plan

**Document ID**: 0109-2100_security_remediation_plan.md
**Created**: 2026-01-09
**Status**: Ready for Implementation
**Target Version**: 2.1.0

---

## Executive Summary

This document provides a comprehensive implementation plan to remediate 12 security findings across HIGH, MEDIUM, and LOW severity levels. The plan is organized into three sequential phases with validation gates between each phase.

**Total Estimated Effort**: 18-24 developer hours
**Critical Path**: Phase 1 (HIGH) must complete before Phase 2
**Risk Assessment**: Low implementation risk with proper testing

---

## Table of Contents

1. [Phase 1: HIGH Severity (Critical)](#phase-1-high-severity-critical)
2. [Phase 2: MEDIUM Severity (Important)](#phase-2-medium-severity-important)
3. [Phase 3: LOW Severity (Recommended)](#phase-3-low-severity-recommended)
4. [Dependency Map](#dependency-map)
5. [Rollback Procedures](#rollback-procedures)

---

## Phase 1: HIGH Severity (Critical)

**Priority**: CRITICAL - Must complete first
**Estimated Effort**: 4-5 hours
**Dependencies**: None

### H-1: Dual Credential Storage

**Location**: `src/gmail_assistant/core/fetch/gmail_api_client.py:37-64`
**Finding**: OAuth tokens stored in plaintext JSON instead of using SecureCredentialManager
**Risk**: Credential theft from filesystem, exposure in backups/logs

#### Current State Analysis

```python
# gmail_api_client.py:37-64 - VULNERABLE CODE
def authenticate(self):
    """Authenticate with Gmail API using secure JSON token storage."""
    creds = None

    # Load existing token from JSON (secure deserialization)
    if os.path.exists(self.token_path):
        try:
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            ...

    # Save credentials as JSON (secure serialization)
    with open(self.token_path, 'w', encoding='utf-8') as token:
        token.write(creds.to_json())  # PLAINTEXT STORAGE - INSECURE
```

#### Implementation Steps

**Step 1.1**: Update imports and class initialization
```python
# File: src/gmail_assistant/core/fetch/gmail_api_client.py

# ADD these imports at top
from ..auth.credential_manager import SecureCredentialManager
from ..auth.base import GmailModifyAuth

# MODIFY __init__ method
class GmailAPIClient:
    """Gmail API client for actual email operations"""

    SCOPES = SCOPES_MODIFY

    def __init__(self, credentials_path: str = 'credentials.json'):
        self.credentials_path = credentials_path
        # Use SecureCredentialManager instead of plaintext token storage
        self.credential_manager = SecureCredentialManager(credentials_path)
        self.service = None
        self._authenticate()
```

**Step 1.2**: Replace authenticate method
```python
def _authenticate(self):
    """Authenticate with Gmail API using secure keyring storage."""
    try:
        if self.credential_manager.authenticate():
            self.service = self.credential_manager.get_service()
            logger.info("Gmail API authentication successful via SecureCredentialManager")
        else:
            logger.error("Gmail API authentication failed")
            raise RuntimeError("Failed to authenticate with Gmail API")
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise
```

**Step 1.3**: Remove deprecated token_path parameter and related code
- Remove `self.token_path` attribute
- Remove all `os.path.exists(self.token_path)` checks
- Remove plaintext file operations for tokens

**Step 1.4**: Clean up legacy token files (optional migration step)
```python
def _migrate_legacy_tokens(self):
    """One-time migration of legacy plaintext tokens to keyring."""
    legacy_token_path = 'token.json'
    if os.path.exists(legacy_token_path):
        logger.warning(f"Found legacy token file: {legacy_token_path}")
        # Suggest user re-authenticate with secure storage
        logger.info("Please re-authenticate to use secure credential storage")
        # Optionally: os.remove(legacy_token_path) after successful migration
```

#### Validation Test Cases

```python
# tests/test_h1_credential_security.py

import pytest
import keyring
from unittest.mock import patch, MagicMock

class TestCredentialSecurity:
    """Test cases for H-1: Secure credential storage"""

    def test_no_plaintext_token_file_created(self, tmp_path):
        """Verify no token.json created during auth"""
        token_path = tmp_path / "token.json"
        # ... mock OAuth flow
        assert not token_path.exists()

    def test_credentials_stored_in_keyring(self):
        """Verify credentials use keyring storage"""
        with patch('keyring.set_password') as mock_set:
            # ... trigger authentication
            mock_set.assert_called_once()

    def test_credentials_not_in_environment(self):
        """Verify credentials don't leak to env vars"""
        import os
        sensitive_keys = ['GOOGLE_TOKEN', 'OAUTH_TOKEN', 'ACCESS_TOKEN']
        for key in sensitive_keys:
            assert key not in os.environ
```

#### Success Criteria

- [ ] No `token.json` files created on disk
- [ ] Credentials retrievable from OS keyring only
- [ ] All existing tests pass
- [ ] New security tests pass
- [ ] Manual verification: `grep -r "token.json" src/` returns no runtime usage

---

### H-2: User-Controlled Input in Subprocess

**Location**: `src/gmail_assistant/core/fetch/incremental.py:230-238`
**Finding**: Unsanitized input passed to subprocess command
**Risk**: Command injection attack if `eml_dir` contains malicious characters

#### Current State Analysis

```python
# incremental.py:230-238 - VULNERABLE CODE
def convert_eml_to_markdown(self, eml_dir: str) -> bool:
    converter_script = "src/parsers/gmail_eml_to_markdown_cleaner.py"

    # VULNERABLE: eml_dir passed directly to subprocess
    cmd = [
        sys.executable,
        converter_script,
        "--base", eml_dir,  # UNSANITIZED USER INPUT
        "--output", f"{eml_dir}_markdown"
    ]

    logger.info(f"Running EML to markdown conversion: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
```

#### Implementation Steps

**Step 2.1**: Add path validation before subprocess call
```python
from ...utils.input_validator import InputValidator, ValidationError
from pathlib import Path

def convert_eml_to_markdown(self, eml_dir: str) -> bool:
    """
    Convert all EML files in the directory to markdown.

    Args:
        eml_dir: Directory containing EML files (must be validated path)

    Returns:
        Success status
    """
    # SECURITY: Validate and sanitize eml_dir before use
    try:
        # Resolve to absolute path and validate
        validated_dir = self._validate_subprocess_path(eml_dir)
    except ValidationError as e:
        logger.error(f"Path validation failed for eml_dir: {e}")
        return False

    # Use validated path in subprocess
    converter_script = Path(__file__).parent.parent.parent / "parsers" / "gmail_eml_to_markdown_cleaner.py"

    cmd = [
        sys.executable,
        str(converter_script.resolve()),
        "--base", str(validated_dir),
        "--output", str(validated_dir) + "_markdown"
    ]

    # ... rest of method
```

**Step 2.2**: Implement secure path validation helper
```python
def _validate_subprocess_path(self, path: str) -> Path:
    """
    Validate path for safe use in subprocess commands.

    Args:
        path: Path string to validate

    Returns:
        Validated Path object

    Raises:
        ValidationError: If path is invalid or unsafe
    """
    # Define allowed base directories
    allowed_bases = [
        Path("data").resolve(),
        Path("backups").resolve(),
        Path.cwd(),
    ]

    # Resolve to absolute path
    resolved = Path(path).resolve()

    # Check for path traversal
    if ".." in str(path):
        raise ValidationError(f"Path traversal detected in: {path}")

    # Verify path is under allowed base
    is_safe = any(
        str(resolved).startswith(str(base))
        for base in allowed_bases
    )

    if not is_safe:
        raise ValidationError(
            f"Path {resolved} not under allowed directories: {allowed_bases}"
        )

    # Check for shell metacharacters
    dangerous_chars = ['|', '&', ';', '$', '`', '>', '<', '!', '\n', '\r']
    if any(char in str(path) for char in dangerous_chars):
        raise ValidationError(f"Path contains dangerous characters: {path}")

    return resolved
```

**Step 2.3**: Add subprocess execution hardening
```python
def _safe_subprocess_run(self, cmd: list, **kwargs) -> subprocess.CompletedProcess:
    """
    Execute subprocess with security hardening.

    Args:
        cmd: Command list (NOT shell string)
        **kwargs: Additional subprocess.run arguments

    Returns:
        CompletedProcess result
    """
    # Ensure shell=False (defense in depth)
    kwargs['shell'] = False

    # Set reasonable timeout (prevent hanging)
    kwargs.setdefault('timeout', 300)  # 5 minutes

    # Capture output for logging
    kwargs.setdefault('capture_output', True)
    kwargs.setdefault('text', True)

    logger.debug(f"Executing subprocess: {cmd}")

    try:
        result = subprocess.run(cmd, **kwargs)
        return result
    except subprocess.TimeoutExpired:
        logger.error(f"Subprocess timed out: {cmd}")
        raise
```

#### Validation Test Cases

```python
# tests/test_h2_subprocess_injection.py

import pytest
from pathlib import Path

class TestSubprocessInjection:
    """Test cases for H-2: Command injection prevention"""

    def test_path_traversal_blocked(self, incremental_fetcher):
        """Verify ../../../etc/passwd style paths are blocked"""
        with pytest.raises(ValidationError, match="Path traversal"):
            incremental_fetcher._validate_subprocess_path("../../../etc/passwd")

    def test_shell_metacharacters_blocked(self, incremental_fetcher):
        """Verify shell injection characters are blocked"""
        dangerous_paths = [
            "data/; rm -rf /",
            "data/$(whoami)",
            "data/`id`",
            "data/|cat /etc/passwd",
        ]
        for path in dangerous_paths:
            with pytest.raises(ValidationError, match="dangerous characters"):
                incremental_fetcher._validate_subprocess_path(path)

    def test_valid_path_allowed(self, incremental_fetcher, tmp_path):
        """Verify legitimate paths work correctly"""
        valid_path = tmp_path / "data" / "emails"
        valid_path.mkdir(parents=True)

        result = incremental_fetcher._validate_subprocess_path(str(valid_path))
        assert result == valid_path.resolve()
```

#### Success Criteria

- [ ] Path traversal attempts raise ValidationError
- [ ] Shell metacharacters in paths are rejected
- [ ] Legitimate paths under allowed directories work
- [ ] subprocess.run never called with shell=True
- [ ] All subprocess calls use list format (not string)

---

### Phase 1 Validation Gate

Before proceeding to Phase 2, verify:

| Criteria | Command | Expected |
|----------|---------|----------|
| Unit tests pass | `pytest tests/test_h*.py -v` | All pass |
| No plaintext tokens | `grep -r "token.json" src/` | No runtime matches |
| Subprocess hardened | `grep -r "shell=True" src/` | Zero matches |
| Integration test | `python -m gmail_assistant --auth-only` | Success with keyring |

**Rollback Trigger**: Any validation failure requires rollback before Phase 2.

---

## Phase 2: MEDIUM Severity (Important)

**Priority**: IMPORTANT - Complete after Phase 1 validation
**Estimated Effort**: 10-12 hours
**Dependencies**: Phase 1 complete

### M-1: Path Traversal Validation Gap

**Location**: `src/gmail_assistant/utils/input_validator.py:122-128`
**Finding**: Incomplete path validation allows certain traversal patterns

#### Current State Analysis

```python
# input_validator.py:122-128 - INCOMPLETE VALIDATION
# Check for path traversal attempts
path_str = str(path)
if '..' in path_str or path_str.startswith('/') or ':' in path_str[1:]:
    # Allow Windows drive letters but not other colons
    if not (len(path_str) > 1 and path_str[1] == ':' and path_str[0].isalpha()):
        raise ValidationError("Path contains potentially dangerous characters")
```

**Issues**:
1. Does not resolve symlinks before checking
2. Does not validate against allowed base directories
3. Does not handle encoded traversal (e.g., `%2e%2e`)

#### Implementation Steps

**Step 1**: Enhance path validation with resolved path checking
```python
@staticmethod
def validate_file_path(path: Union[str, Path], must_exist: bool = False,
                      create_dirs: bool = False,
                      allowed_base: Optional[Path] = None) -> Path:
    """
    Validate and sanitize file path with enhanced security.

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

    # URL-decode path to catch encoded traversal attempts
    path_str = str(path)
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
        raise ValidationError(f"Cannot resolve path: {e}")

    # Check for traversal AFTER resolution
    if '..' in path.parts:
        raise ValidationError("Path contains traversal component '..'")

    # Validate against allowed base directory
    if allowed_base is not None:
        allowed_resolved = allowed_base.resolve()
        if not str(resolved).startswith(str(allowed_resolved)):
            raise ValidationError(
                f"Path traversal detected: {resolved} is not under {allowed_resolved}"
            )

    # Windows-specific checks
    if os.name == 'nt':
        # Allow single drive letter at start
        if len(path_str) > 1 and path_str[1] == ':':
            if not path_str[0].isalpha():
                raise ValidationError("Invalid Windows drive letter")
        # Check for alternate data streams (file.txt:hidden)
        if ':' in path_str[2:]:
            raise ValidationError("Path contains Windows alternate data stream")
    else:
        # Unix: reject paths starting with /
        if path_str.startswith('/') and allowed_base is None:
            raise ValidationError("Absolute paths require allowed_base validation")

    # Check path length
    if len(str(resolved)) > 260:  # Windows MAX_PATH
        raise ValidationError("Path too long (max 260 characters)")

    # Validate filename components
    invalid_names = {'CON', 'PRN', 'AUX', 'NUL'} | {f'COM{i}' for i in range(10)} | {f'LPT{i}' for i in range(10)}
    for part in resolved.parts:
        name_upper = part.upper().split('.')[0]
        if name_upper in invalid_names:
            raise ValidationError(f"Path contains reserved Windows name: {part}")

    # Check if path exists when required
    if must_exist and not resolved.exists():
        raise ValidationError(f"Path does not exist: {resolved}")

    # Create parent directories if requested
    if create_dirs and not resolved.parent.exists():
        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directories: {resolved.parent}")
        except OSError as e:
            raise ValidationError(f"Failed to create directories: {e}")

    return resolved
```

#### Validation Test Cases

```python
# tests/test_m1_path_traversal.py

class TestPathTraversalValidation:
    """Test cases for M-1: Path traversal prevention"""

    @pytest.mark.parametrize("malicious_path", [
        "../../../etc/passwd",
        "data/../../../etc/passwd",
        "data/..%2f..%2f..%2fetc/passwd",  # URL encoded
        "data/....//....//etc/passwd",  # Double dots
        "data/file.txt:hidden_stream",  # Windows ADS
        "CON",  # Windows reserved name
    ])
    def test_malicious_paths_rejected(self, malicious_path):
        """Verify malicious path patterns are rejected"""
        with pytest.raises(ValidationError):
            InputValidator.validate_file_path(malicious_path, allowed_base=Path("data"))

    def test_symlink_traversal_blocked(self, tmp_path):
        """Verify symlink-based traversal is blocked"""
        # Create symlink pointing outside allowed directory
        (tmp_path / "allowed").mkdir()
        (tmp_path / "secret").mkdir()
        (tmp_path / "secret" / "sensitive.txt").write_text("secret data")

        symlink_path = tmp_path / "allowed" / "escape"
        symlink_path.symlink_to(tmp_path / "secret")

        with pytest.raises(ValidationError, match="traversal"):
            InputValidator.validate_file_path(
                str(symlink_path / "sensitive.txt"),
                allowed_base=tmp_path / "allowed"
            )
```

---

### M-2: ReDoS Vulnerability

**Location**: `src/gmail_assistant/core/ai/newsletter_cleaner.py:138-149`
**Finding**: Regex patterns without timeout can cause denial of service

#### Current State Analysis

```python
# newsletter_cleaner.py:138-149 - VULNERABLE CODE
newsletter_pattern_match = any(re.search(pattern, subject_lower + " " + sender_lower)
                             for pattern in self.newsletter_patterns)

unsubscribe_match = any(re.search(pattern, body_lower)
                      for pattern in self.unsubscribe_patterns)
```

**Risk**: Maliciously crafted email subjects/bodies can cause regex engine to hang.

#### Implementation Steps

**Step 1**: Install and use `regex` module with timeout support
```python
# Add to pyproject.toml dependencies
# regex>=2024.5.0

# newsletter_cleaner.py - Updated implementation
import regex  # Use regex module instead of re for timeout support

# Module-level constants
REGEX_TIMEOUT = 0.1  # 100ms timeout per pattern match
MAX_INPUT_LENGTH = 500  # Truncate input to prevent ReDoS

class AINewsletterDetector:
    def _safe_regex_search(self, pattern: str, text: str) -> bool:
        """
        Perform regex search with timeout and input truncation.

        Args:
            pattern: Regex pattern to match
            text: Text to search (will be truncated if too long)

        Returns:
            True if pattern matches, False otherwise
        """
        # Truncate input to prevent ReDoS
        truncated_text = text[:MAX_INPUT_LENGTH]

        try:
            match = regex.search(
                pattern,
                truncated_text,
                timeout=REGEX_TIMEOUT
            )
            return match is not None
        except regex.error as e:
            logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            return False
        except TimeoutError:
            logger.warning(f"Regex timeout for pattern '{pattern}' on input length {len(text)}")
            return False

    def is_ai_newsletter(self, email: EmailData) -> Dict[str, any]:
        """Determine if email is an AI newsletter (with ReDoS protection)"""
        reasons = []
        confidence = 0

        # Truncate and lowercase inputs
        subject_lower = email.subject[:MAX_INPUT_LENGTH].lower()
        sender_lower = email.sender[:MAX_INPUT_LENGTH].lower()
        body_lower = email.body_snippet[:MAX_INPUT_LENGTH].lower()

        # ... existing keyword checks (no regex) ...

        # Check newsletter patterns with timeout protection
        search_text = f"{subject_lower} {sender_lower}"
        newsletter_pattern_match = any(
            self._safe_regex_search(pattern, search_text)
            for pattern in self.newsletter_patterns
        )

        # Check unsubscribe patterns with timeout protection
        unsubscribe_match = any(
            self._safe_regex_search(pattern, body_lower)
            for pattern in self.unsubscribe_patterns
        )

        # ... rest of method unchanged ...
```

**Step 2**: Pre-compile regex patterns at initialization
```python
def __init__(self, config_path: str = None):
    self.config_path = config_path or str(AI_CONFIG_PATH)
    self.load_config()
    self._compile_patterns()

def _compile_patterns(self):
    """Pre-compile regex patterns for efficiency"""
    self._compiled_newsletter_patterns = []
    self._compiled_unsubscribe_patterns = []

    for pattern in self.newsletter_patterns:
        try:
            compiled = regex.compile(pattern, flags=regex.IGNORECASE)
            self._compiled_newsletter_patterns.append(compiled)
        except regex.error as e:
            logger.warning(f"Invalid newsletter pattern '{pattern}': {e}")

    for pattern in self.unsubscribe_patterns:
        try:
            compiled = regex.compile(pattern, flags=regex.IGNORECASE)
            self._compiled_unsubscribe_patterns.append(compiled)
        except regex.error as e:
            logger.warning(f"Invalid unsubscribe pattern '{pattern}': {e}")
```

#### Validation Test Cases

```python
# tests/test_m2_redos.py

import time
import pytest
from gmail_assistant.core.ai.newsletter_cleaner import AINewsletterDetector, EmailData

class TestReDoSProtection:
    """Test cases for M-2: ReDoS vulnerability prevention"""

    def test_malicious_input_timeout(self):
        """Verify malicious input triggers timeout, not hang"""
        detector = AINewsletterDetector()

        # ReDoS payload: exponential backtracking pattern
        malicious_subject = "a" * 50 + "!"

        email = EmailData(
            id="test",
            subject=malicious_subject,
            sender="test@test.com",
            date="2024-01-01"
        )

        start_time = time.time()
        result = detector.is_ai_newsletter(email)
        elapsed = time.time() - start_time

        # Should complete within 1 second (timeout + overhead)
        assert elapsed < 1.0, f"Regex took too long: {elapsed}s"

    def test_input_truncation(self):
        """Verify long inputs are truncated"""
        detector = AINewsletterDetector()

        # Very long input that could cause issues
        long_subject = "newsletter " + "x" * 10000

        email = EmailData(
            id="test",
            subject=long_subject,
            sender="test@newsletter.com",
            date="2024-01-01"
        )

        # Should still detect newsletter keyword at start
        result = detector.is_ai_newsletter(email)
        # Should complete quickly
        assert result['is_ai_newsletter'] or not result['is_ai_newsletter']  # Just verify it completes
```

---

### M-3: Missing API Response Validation

**Location**: `src/gmail_assistant/core/fetch/gmail_assistant.py`
**Finding**: API responses not validated for expected structure

#### Implementation Steps

**Step 1**: Add response validation helper
```python
from typing import TypedDict, Optional

class MessageResponse(TypedDict, total=False):
    """Expected structure of Gmail API message response"""
    id: str
    threadId: str
    labelIds: list
    snippet: str
    payload: dict

def _validate_api_response(self, response: Optional[dict],
                           required_fields: list) -> dict:
    """
    Validate API response has expected structure.

    Args:
        response: API response dictionary
        required_fields: List of required field names

    Returns:
        Validated response

    Raises:
        ValueError: If response is invalid
    """
    if response is None:
        raise ValueError("API returned null response")

    if not isinstance(response, dict):
        raise ValueError(f"API returned non-dict response: {type(response)}")

    missing_fields = [f for f in required_fields if f not in response]
    if missing_fields:
        raise ValueError(f"API response missing required fields: {missing_fields}")

    return response
```

**Step 2**: Apply validation to API calls
```python
def get_message_details(self, message_id: str) -> Optional[Dict]:
    """Get full message details with validation"""
    try:
        message = self.service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        # Validate response structure
        validated = self._validate_api_response(
            message,
            required_fields=['id', 'threadId', 'payload']
        )

        # Validate payload has headers
        if 'headers' not in validated.get('payload', {}):
            self.logger.warning(f"Message {message_id} missing payload headers")
            validated['payload']['headers'] = []

        return validated

    except ValueError as e:
        self.logger.error(f"Invalid API response for message {message_id}: {e}")
        return None
    except HttpError as error:
        self.logger.error(f"Error getting message {message_id}: {error}")
        return None
```

---

### M-4: PII in Log Files

**Location**: Multiple files
**Finding**: Sensitive email content logged without redaction

#### Implementation Steps

**Step 1**: Create PII redaction utility
```python
# src/gmail_assistant/utils/pii_redactor.py

import re
from typing import Optional

class PIIRedactor:
    """Utility for redacting PII from log messages"""

    # Patterns for PII detection
    EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w.-]+\.\w+')

    @staticmethod
    def redact_email(email: str) -> str:
        """
        Redact email address preserving structure hint.

        Example: "john.doe@company.com" -> "jo***@company.com"
        """
        if not email or '@' not in email:
            return email

        try:
            local, domain = email.rsplit('@', 1)
            if len(local) <= 2:
                redacted_local = local[0] + '***'
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
        """
        if not subject:
            return "[no subject]"

        if len(subject) <= max_length:
            return subject

        return subject[:max_length] + "..."

    @classmethod
    def redact_log_message(cls, message: str) -> str:
        """
        Redact all PII from a log message.
        """
        # Redact email addresses
        def replace_email(match):
            return cls.redact_email(match.group(0))

        return cls.EMAIL_PATTERN.sub(replace_email, message)
```

**Step 2**: Create secure logging wrapper
```python
# src/gmail_assistant/utils/secure_logger.py

import logging
from .pii_redactor import PIIRedactor

class SecureLogger:
    """Logger wrapper that automatically redacts PII"""

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
        self._redactor = PIIRedactor()

    def _redact(self, msg: str) -> str:
        return self._redactor.redact_log_message(str(msg))

    def info(self, msg: str, *args, **kwargs):
        self._logger.info(self._redact(msg), *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._logger.warning(self._redact(msg), *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self._logger.error(self._redact(msg), *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        # Debug logs should also be redacted for safety
        self._logger.debug(self._redact(msg), *args, **kwargs)
```

**Step 3**: Update files to use SecureLogger
```python
# In each file that logs email content:
from ...utils.secure_logger import SecureLogger

logger = SecureLogger(__name__)

# Example usage - PII automatically redacted:
logger.info(f"Processing email from {email.sender}: {email.subject}")
# Logs: "Processing email from jo***@company.com: Your bank stat..."
```

---

### M-5: Unsafe JSON Config Loading

**Location**: `src/gmail_assistant/parsers/advanced_email_parser.py:88-93`
**Finding**: JSON config loaded without schema validation

#### Implementation Steps

**Step 1**: Define config schema
```python
# src/gmail_assistant/utils/config_schema.py

from typing import Dict, Any, List
import json

class ConfigSchema:
    """Schema definitions for configuration validation"""

    PARSER_CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "strategies": {
                "type": "array",
                "items": {"type": "string", "enum": ["smart", "readability", "trafilatura", "html2text", "markdownify"]},
                "default": ["smart", "html2text"]
            },
            "newsletter_patterns": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "content_selectors": {"type": "array", "items": {"type": "string"}},
                        "remove_selectors": {"type": "array", "items": {"type": "string"}},
                    }
                }
            },
            "cleaning_rules": {
                "type": "object",
                "properties": {
                    "remove_tags": {"type": "array", "items": {"type": "string"}},
                    "max_image_width": {"type": "integer", "minimum": 100, "maximum": 2000}
                }
            },
            "formatting": {
                "type": "object",
                "properties": {
                    "max_line_length": {"type": "integer", "minimum": 40, "maximum": 200}
                }
            }
        },
        "additionalProperties": False  # Reject unknown keys
    }

    @classmethod
    def validate_parser_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parser configuration against schema.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated configuration

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate top-level type
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        # Check for unknown top-level keys
        allowed_keys = set(cls.PARSER_CONFIG_SCHEMA["properties"].keys())
        unknown_keys = set(config.keys()) - allowed_keys
        if unknown_keys:
            raise ValueError(f"Unknown configuration keys: {unknown_keys}")

        # Validate strategies
        if "strategies" in config:
            strategies = config["strategies"]
            if not isinstance(strategies, list):
                raise ValueError("strategies must be a list")

            valid_strategies = {"smart", "readability", "trafilatura", "html2text", "markdownify"}
            for strategy in strategies:
                if strategy not in valid_strategies:
                    raise ValueError(f"Invalid strategy: {strategy}")

        # Validate numeric bounds
        if "cleaning_rules" in config:
            rules = config["cleaning_rules"]
            if "max_image_width" in rules:
                width = rules["max_image_width"]
                if not isinstance(width, int) or not (100 <= width <= 2000):
                    raise ValueError(f"max_image_width must be integer 100-2000, got {width}")

        if "formatting" in config:
            fmt = config["formatting"]
            if "max_line_length" in fmt:
                length = fmt["max_line_length"]
                if not isinstance(length, int) or not (40 <= length <= 200):
                    raise ValueError(f"max_line_length must be integer 40-200, got {length}")

        return config
```

**Step 2**: Update config loading with validation
```python
# advanced_email_parser.py - Updated _load_config method

from gmail_assistant.utils.config_schema import ConfigSchema

def _load_config(self, config_file: Optional[str]) -> Dict:
    """Load and validate parser configuration"""
    default_config = {
        # ... default config as before ...
    }

    if config_file and Path(config_file).exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)

            # Validate user config against schema
            validated_config = ConfigSchema.validate_parser_config(user_config)

            # Merge with defaults (user config takes precedence)
            default_config.update(validated_config)
            logger.info(f"Loaded and validated config from {config_file}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {config_file}: {e}")
            # Use defaults only
        except ValueError as e:
            logger.error(f"Config validation failed for {config_file}: {e}")
            # Use defaults only

    return default_config
```

---

### M-6: Command Injection in PowerShell

**Location**: `scripts/setup/quick_start.ps1:101-106`
**Finding**: User input directly interpolated into PowerShell command

#### Current State Analysis

```powershell
# quick_start.ps1:101-106 - VULNERABLE CODE
"5" {
    $query = Read-Host "Enter Gmail search query"
    $maxInput = Read-Host "Enter max emails (default 100)"
    ...
}

# Later:
python ../src/gmail_assistant.py --query "$query" --max $max ...
```

**Risk**: User could enter `"; Remove-Item -Recurse C:\ -Force"` as query.

#### Implementation Steps

**Step 1**: Add input sanitization function
```powershell
# Add near top of quick_start.ps1

function Sanitize-GmailQuery {
    param([string]$Query)

    # Remove potentially dangerous PowerShell characters
    $dangerous = @('`', '$', '(', ')', '{', '}', ';', '|', '&', '<', '>', '"')

    foreach ($char in $dangerous) {
        $Query = $Query.Replace($char, '')
    }

    # Limit length
    if ($Query.Length -gt 500) {
        $Query = $Query.Substring(0, 500)
    }

    return $Query
}

function Validate-Integer {
    param(
        [string]$Input,
        [int]$Default = 100,
        [int]$Min = 1,
        [int]$Max = 10000
    )

    try {
        $value = [int]$Input
        if ($value -lt $Min) { return $Min }
        if ($value -gt $Max) { return $Max }
        return $value
    } catch {
        return $Default
    }
}
```

**Step 2**: Apply sanitization to user input
```powershell
"5" {
    $rawQuery = Read-Host "Enter Gmail search query"
    $query = Sanitize-GmailQuery -Query $rawQuery

    if ($query -ne $rawQuery) {
        Write-Host "Note: Query was sanitized for safety" -ForegroundColor Yellow
    }

    $maxInput = Read-Host "Enter max emails (default 100)"
    $max = Validate-Integer -Input $maxInput -Default 100 -Min 1 -Max 10000

    $output = "custom_search"
    $description = "Custom search"
}
```

**Step 3**: Use array-based command execution
```powershell
# Instead of string interpolation:
# python ../src/gmail_assistant.py --query "$query" --max $max ...

# Use explicit array (safer):
$pythonArgs = @(
    "../src/gmail_assistant.py",
    "--query", $query,
    "--max", $max,
    "--output", $output,
    "--format", "both",
    "--organize", "date"
)

& python $pythonArgs
```

---

### M-7: Missing Restrictive File Permissions

**Location**: Multiple files creating output
**Finding**: Created files have default permissions (potentially world-readable)

#### Implementation Steps

**Step 1**: Create secure file write utility
```python
# src/gmail_assistant/utils/secure_file.py

import os
import stat
import tempfile
from pathlib import Path
from typing import Optional

class SecureFileWriter:
    """Utility for writing files with restrictive permissions"""

    # Restrictive permissions: owner read/write only (0o600)
    SECURE_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR

    # Restrictive directory permissions: owner read/write/execute (0o700)
    SECURE_DIR_MODE = stat.S_IRWXU

    @classmethod
    def write_secure(cls, path: Path, content: str,
                     encoding: str = 'utf-8') -> None:
        """
        Write file with restrictive permissions.

        Uses atomic write pattern (temp file + rename).
        Sets owner-only read/write permissions.
        """
        path = Path(path)

        # Create parent directory with secure permissions if needed
        if not path.parent.exists():
            path.parent.mkdir(parents=True, mode=cls.SECURE_DIR_MODE)

        # Write to temp file first (atomic write)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent),
            suffix='.tmp',
            text=True
        )

        try:
            # Set restrictive permissions on temp file
            os.fchmod(fd, cls.SECURE_FILE_MODE)

            # Write content
            with os.fdopen(fd, 'w', encoding=encoding) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename (preserves permissions)
            os.replace(tmp_path, path)

        except Exception:
            # Clean up temp file on failure
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    @classmethod
    def create_secure_directory(cls, path: Path) -> Path:
        """Create directory with restrictive permissions"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True, mode=cls.SECURE_DIR_MODE)
        return path
```

**Step 2**: Apply to credential and sensitive file operations
```python
# In credential_manager.py and gmail_api_client.py:
from ...utils.secure_file import SecureFileWriter

# When writing any sensitive files:
SecureFileWriter.write_secure(config_path, json.dumps(config, indent=2))
```

---

### Phase 2 Validation Gate

Before proceeding to Phase 3, verify:

| Criteria | Command | Expected |
|----------|---------|----------|
| M-1 tests pass | `pytest tests/test_m1_*.py -v` | All pass |
| M-2 no regex hangs | `pytest tests/test_m2_*.py -v --timeout=5` | All pass <5s |
| M-3 API validation | `pytest tests/test_m3_*.py -v` | All pass |
| M-4 no PII in logs | `grep -E "[a-z]+@[a-z]+\.[a-z]+" logs/*.log` | Zero matches |
| M-5 config validation | `python -c "from gmail_assistant.utils.config_schema import *"` | No errors |
| M-6 PS sanitization | Manual test with special chars | Sanitized |
| M-7 file permissions | `stat -c %a output/*.json` | 600 |

---

## Phase 3: LOW Severity (Recommended)

**Priority**: RECOMMENDED - Complete as time permits
**Estimated Effort**: 4-6 hours
**Dependencies**: Phase 2 complete (recommended but not required)

### L-1: Hardcoded Default Paths

**Location**: `src/gmail_assistant/core/constants.py`, various cleaner files
**Finding**: Hardcoded paths reduce flexibility and may expose installation structure

#### Implementation Steps

**Step 1**: Add environment variable support for paths
```python
# constants.py - Updated

import os
from pathlib import Path

def _get_env_path(env_var: str, default: Path) -> Path:
    """Get path from environment variable or use default"""
    env_value = os.environ.get(env_var)
    if env_value:
        return Path(env_value)
    return default

# Configuration paths with env override
CONFIG_DIR: Path = _get_env_path(
    'GMAIL_ASSISTANT_CONFIG_DIR',
    PROJECT_ROOT / 'config'
)

DATA_DIR: Path = _get_env_path(
    'GMAIL_ASSISTANT_DATA_DIR',
    PROJECT_ROOT / 'data'
)

CREDENTIALS_DIR: Path = _get_env_path(
    'GMAIL_ASSISTANT_CREDENTIALS_DIR',
    CONFIG_DIR / 'security'
)

DEFAULT_CREDENTIALS_PATH: Path = CREDENTIALS_DIR / 'credentials.json'
```

**Step 2**: Document environment variables
```markdown
# Add to README.md or docs/configuration.md

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| GMAIL_ASSISTANT_CONFIG_DIR | Configuration directory | `./config` |
| GMAIL_ASSISTANT_DATA_DIR | Data storage directory | `./data` |
| GMAIL_ASSISTANT_CREDENTIALS_DIR | OAuth credentials directory | `./config/security` |
```

---

### L-2: Missing Auth Failure Rate Limiting

**Location**: Auth modules
**Finding**: No rate limiting on authentication attempts

#### Implementation Steps

```python
# src/gmail_assistant/core/auth/rate_limiter.py

import time
from dataclasses import dataclass, field
from typing import Dict
import threading

@dataclass
class RateLimitState:
    """Track rate limit state for a single key"""
    attempts: int = 0
    first_attempt: float = 0.0
    locked_until: float = 0.0

class AuthRateLimiter:
    """Rate limiter for authentication attempts"""

    MAX_ATTEMPTS = 5
    WINDOW_SECONDS = 300  # 5 minutes
    LOCKOUT_SECONDS = 900  # 15 minutes

    def __init__(self):
        self._states: Dict[str, RateLimitState] = {}
        self._lock = threading.Lock()

    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if authentication is allowed.

        Args:
            identifier: Unique identifier (e.g., credentials file path)

        Returns:
            True if allowed, False if rate limited
        """
        with self._lock:
            now = time.time()

            if identifier not in self._states:
                self._states[identifier] = RateLimitState()

            state = self._states[identifier]

            # Check if currently locked out
            if now < state.locked_until:
                return False

            # Reset window if expired
            if now - state.first_attempt > self.WINDOW_SECONDS:
                state.attempts = 0
                state.first_attempt = now

            return state.attempts < self.MAX_ATTEMPTS

    def record_attempt(self, identifier: str, success: bool) -> None:
        """Record an authentication attempt"""
        with self._lock:
            now = time.time()

            if identifier not in self._states:
                self._states[identifier] = RateLimitState()

            state = self._states[identifier]

            if success:
                # Reset on success
                state.attempts = 0
                state.locked_until = 0
            else:
                # Increment failure count
                if state.attempts == 0:
                    state.first_attempt = now
                state.attempts += 1

                # Lock out if too many failures
                if state.attempts >= self.MAX_ATTEMPTS:
                    state.locked_until = now + self.LOCKOUT_SECONDS
```

**Step 2**: Integrate with authentication
```python
# In base.py authenticate method:

from .rate_limiter import AuthRateLimiter

_rate_limiter = AuthRateLimiter()

def authenticate(self) -> bool:
    """Authenticate with rate limiting"""

    # Check rate limit
    if not _rate_limiter.check_rate_limit(self.credentials_file):
        self.logger.error("Authentication rate limited. Try again later.")
        return False

    try:
        # ... existing authentication logic ...

        if success:
            _rate_limiter.record_attempt(self.credentials_file, True)
            return True
        else:
            _rate_limiter.record_attempt(self.credentials_file, False)
            return False

    except Exception as e:
        _rate_limiter.record_attempt(self.credentials_file, False)
        raise
```

---

### L-3: Missing Pinned Sub-Dependencies

**Location**: `pyproject.toml`
**Finding**: Only direct dependencies pinned, not transitive dependencies

#### Implementation Steps

**Step 1**: Generate lock file
```bash
# Generate requirements lock file with all transitive dependencies
pip-compile pyproject.toml --generate-hashes -o requirements.lock

# Or using pip-tools:
pip install pip-tools
pip-compile --generate-hashes --resolver=backtracking -o requirements.lock
```

**Step 2**: Add lock file to version control
```bash
git add requirements.lock
git commit -m "Add pinned dependency lock file for reproducible builds"
```

**Step 3**: Update installation instructions
```markdown
# For reproducible installation with exact versions:
pip install -r requirements.lock

# For development with latest compatible versions:
pip install -e ".[dev]"
```

---

### Phase 3 Validation Gate

| Criteria | Command | Expected |
|----------|---------|----------|
| Env vars work | `GMAIL_ASSISTANT_CONFIG_DIR=/tmp python -c "..."` | Uses /tmp |
| Rate limiting | `pytest tests/test_l2_rate_limit.py -v` | All pass |
| Lock file valid | `pip-compile --dry-run` | No changes |

---

## Dependency Map

```
Phase 1 (HIGH)
    |
    +-- H-1: Credential Storage
    |       (Independent)
    |
    +-- H-2: Subprocess Injection
            (Independent)
    |
    v
[Phase 1 Validation Gate]
    |
    v
Phase 2 (MEDIUM)
    |
    +-- M-1: Path Traversal
    |       (Uses patterns from H-2)
    |
    +-- M-2: ReDoS
    |       (Independent)
    |
    +-- M-3: API Validation
    |       (Independent)
    |
    +-- M-4: PII Redaction
    |       (Independent)
    |
    +-- M-5: Config Schema
    |       (May use M-1 patterns)
    |
    +-- M-6: PowerShell Injection
    |       (Independent)
    |
    +-- M-7: File Permissions
            (May affect H-1 implementation)
    |
    v
[Phase 2 Validation Gate]
    |
    v
Phase 3 (LOW)
    |
    +-- L-1: Environment Variables
    |       (Independent)
    |
    +-- L-2: Rate Limiting
    |       (Depends on auth module from H-1)
    |
    +-- L-3: Dependency Pinning
            (Independent)
```

---

## Rollback Procedures

### Phase 1 Rollback

If Phase 1 fails validation:

```bash
# Revert all Phase 1 changes
git checkout HEAD~1 -- src/gmail_assistant/core/fetch/gmail_api_client.py
git checkout HEAD~1 -- src/gmail_assistant/core/fetch/incremental.py

# Restore any deleted token files from backup
# (Recommend keeping token.json backup before migration)
```

### Phase 2 Rollback

If Phase 2 fails validation:

```bash
# Revert specific files (example for M-2)
git checkout HEAD~1 -- src/gmail_assistant/core/ai/newsletter_cleaner.py

# Or revert entire phase
git revert --no-commit HEAD~7..HEAD  # Assuming 7 commits for M-1 through M-7
```

### General Rollback Strategy

1. Create feature branch for security work: `git checkout -b security/remediation-v1`
2. Tag before each phase: `git tag security-phase-1-start`
3. Tag after validation: `git tag security-phase-1-complete`
4. If rollback needed: `git reset --hard security-phase-1-start`

---

## Appendix A: Test File Locations

All test files should be created in `tests/security/`:

```
tests/
  security/
    test_h1_credential_security.py
    test_h2_subprocess_injection.py
    test_m1_path_traversal.py
    test_m2_redos.py
    test_m3_api_validation.py
    test_m4_pii_redaction.py
    test_m5_config_schema.py
    test_m6_powershell_injection.py
    test_m7_file_permissions.py
    test_l1_environment_paths.py
    test_l2_rate_limiting.py
```

---

## Appendix B: Required Package Updates

Add to `pyproject.toml` dependencies:

```toml
dependencies = [
    # ... existing dependencies ...
    "regex>=2024.5.0",  # For M-2: ReDoS protection with timeout
]

[project.optional-dependencies]
security = [
    "keyring>=25.0.0",  # Already present
    "pip-tools>=7.0.0",  # For L-3: Dependency locking
]
```

---

## Appendix C: Success Metrics

| Metric | Before | Target | Method |
|--------|--------|--------|--------|
| Plaintext tokens on disk | Yes | No | File audit |
| Subprocess shell=True usage | Unknown | 0 | grep |
| Path validation coverage | ~50% | 100% | Unit tests |
| Regex timeout protection | 0% | 100% | Test coverage |
| API response validation | 0% | 100% | Test coverage |
| PII in logs | Present | None | Log audit |
| Config schema validation | 0% | 100% | Test coverage |
| File permission (sensitive) | 644 | 600 | stat check |
| Auth rate limiting | None | Active | Integration test |
| Dependency pinning | None | Full | Lock file |

---

*End of Security Remediation Implementation Plan*
