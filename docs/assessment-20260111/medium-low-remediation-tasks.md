# Medium and Low Priority Remediation Plan

**Document**: `0112-1430_medium-low-remediation-tasks.md`
**Version**: 1.0.0
**Created**: 2026-01-12
**Scope**: Gmail Assistant v2.0.0

---

## Executive Summary

This document provides actionable remediation tasks for 16 MEDIUM and 9 LOW priority issues identified in the Gmail Assistant v2.0.0 assessment. The issues span six categories:

| Category | MEDIUM | LOW | Total |
|----------|--------|-----|-------|
| Quality | 4 | 3 | 7 |
| Architecture | 2 | 2 | 4 |
| Patterns | 2 | 0 | 2 |
| Scalability | 4 | 1 | 5 |
| Configuration | 2 | 2 | 4 |
| Security | 2 | 1 | 3 |

**Estimated Total Effort**: 8-12 developer days

---

## Table of Contents

1. [Quality Improvements](#1-quality-improvements)
2. [Architecture Improvements](#2-architecture-improvements)
3. [Pattern Standardization](#3-pattern-standardization)
4. [Scalability Improvements](#4-scalability-improvements)
5. [Configuration Consolidation](#5-configuration-consolidation)
6. [Security Hardening](#6-security-hardening)
7. [Recommended Execution Order](#7-recommended-execution-order)

---

## 1. Quality Improvements

### M-1: Consolidate Local Exception Classes

**Effort**: Small (2-4 hours)

**Files Affected**:
- `src/gmail_assistant/core/container.py` (lines 41-48)
- `src/gmail_assistant/utils/circuit_breaker.py` (line 24)
- `src/gmail_assistant/utils/config_schema.py` (line 14)
- `src/gmail_assistant/export/parquet_exporter.py` (line 38)
- `src/gmail_assistant/core/exceptions.py` (centralized source)

**Current State**:
Four modules define their own exception classes that duplicate the centralized hierarchy in `core/exceptions.py`:
- `container.py`: `ServiceNotFoundError`, `CircularDependencyError`
- `circuit_breaker.py`: `CircuitBreakerError`
- `config_schema.py`: `ConfigValidationError`
- `parquet_exporter.py`: `ParquetExportError`

**Implementation Steps**:

1. **Add missing exceptions to `core/exceptions.py`** (if not already present):

```python
# In src/gmail_assistant/core/exceptions.py

class ConfigValidationError(ConfigError):
    """Configuration validation failed."""
    pass

class ParquetExportError(ExportError):
    """Parquet export operation failed."""
    pass
```

2. **Update `container.py`**:

```python
# Replace local definitions with imports
from gmail_assistant.core.exceptions import (
    ServiceNotFoundError,
    CircularDependencyError,
)

# Remove lines 41-48 (local class definitions)
```

3. **Update `circuit_breaker.py`**:

```python
# At top of file, add import
from gmail_assistant.core.exceptions import CircuitBreakerError

# Remove lines 24-28 (local CircuitBreakerError class)
```

4. **Update `config_schema.py`**:

```python
# At top of file, add import
from gmail_assistant.core.exceptions import ConfigValidationError

# Remove lines 14-16 (local ConfigValidationError class)
```

5. **Update `parquet_exporter.py`**:

```python
# At top of file, add import
from gmail_assistant.core.exceptions import ParquetExportError

# Remove lines 38-40 (local ParquetExportError class)
```

**Verification**:
```bash
# Run grep to confirm no local exception definitions remain
grep -r "class.*Error.*Exception" src/gmail_assistant --include="*.py" | grep -v "core/exceptions.py"

# Run tests to ensure no breakage
pytest tests/ -v
```

**Dependencies**: None

---

### M-2: Replace Bare Exception Handlers

**Effort**: Trivial (1-2 hours)

**Files Affected**:
- `src/gmail_assistant/core/fetch/gmail_assistant.py` (lines 333, 359)

**Current State**:
```python
# Line ~333 (in download_emails)
except Exception as e:
    self.logger.error(f"Error processing email: {e}")

# Line ~359 (elsewhere)
except Exception as e:
    # bare handler
```

**Implementation Steps**:

1. **Identify specific exception types expected**:
   - `HttpError` from Google API
   - `OSError` for file operations
   - `ValueError`, `KeyError` for parsing errors

2. **Replace bare handlers in `gmail_assistant.py`**:

```python
# In download_emails method (around line 600-610)
# Replace:
except Exception as e:
    self.logger.error(f"API error downloading email: {e}")

# With specific handlers:
except HttpError as e:
    self.logger.error(f"API error downloading email: {e}")
    errors += 1
except OSError as e:
    self.logger.error(f"File system error: {e}")
    errors += 1
except (ValueError, KeyError) as e:
    self.logger.warning(f"Email parsing error: {e}")
    errors += 1
```

3. **Review any remaining bare `except Exception` and document if intentional**:

```python
# If truly need to catch all exceptions (e.g., plugin loading), add comment:
except Exception as e:  # Intentional: catch-all for third-party plugin errors
    self.logger.error(f"Unexpected error: {e}")
```

**Verification**:
```bash
# Check for remaining bare exception handlers
grep -n "except Exception" src/gmail_assistant/core/fetch/gmail_assistant.py

# Run tests
pytest tests/unit/fetch/ -v
```

**Dependencies**: None

---

### M-3: Refactor Large `parse_email_content` Method

**Effort**: Medium (4-6 hours)

**Files Affected**:
- `src/gmail_assistant/parsers/advanced_email_parser.py` (lines 558-659)

**Current State**:
The `parse_email_content` method is 100+ lines with multiple responsibilities:
- Input validation
- Strategy iteration
- Result collection
- Best result selection
- Metadata enrichment

**Implementation Steps**:

1. **Extract input validation to separate method**:

```python
def _validate_parse_inputs(
    self,
    html_content: str,
    plain_text: str,
    sender: str,
    subject: str
) -> tuple[str, str, str, str]:
    """Validate and sanitize parse inputs."""
    try:
        if html_content:
            html_content = self.validator.validate_string(html_content, max_length=5000000)
        if plain_text:
            plain_text = self.validator.validate_string(plain_text, max_length=1000000)
        if sender:
            sender = self.validator.validate_string(sender, max_length=500)
        if subject:
            subject = self.validator.validate_string(subject, max_length=1000)
        return html_content, plain_text, sender, subject
    except ValidationError as e:
        raise ValueError(f"Input validation failed: {e}") from e
```

2. **Extract strategy execution to separate method**:

```python
def _execute_parsing_strategies(
    self,
    html_content: str,
    sender: str
) -> list[dict[str, Any]]:
    """Execute all configured parsing strategies."""
    results = []
    for strategy in self.config["strategies"]:
        logger.info(f"Trying strategy: {strategy}")
        markdown, quality = self._execute_strategy(strategy, html_content, sender)
        if markdown and quality > 0:
            results.append({
                "markdown": markdown,
                "strategy": strategy,
                "quality": quality,
                "length": len(markdown)
            })
    return results

def _execute_strategy(
    self,
    strategy: str,
    html_content: str,
    sender: str
) -> tuple[str, float]:
    """Execute a single parsing strategy."""
    strategy_map = {
        "smart": lambda: self.parse_with_smart_strategy(html_content, sender),
        "readability": lambda: self.parse_with_readability(html_content),
        "trafilatura": lambda: self.parse_with_trafilatura(html_content),
        "html2text": lambda: self.parse_with_html2text(html_content),
        "markdownify": lambda: self.parse_with_markdownify(html_content),
    }
    executor = strategy_map.get(strategy)
    if executor:
        return executor()
    return "", 0.0
```

3. **Extract result selection to separate method**:

```python
def _select_best_result(
    self,
    results: list[dict[str, Any]],
    html_content: str,
    sender: str,
    subject: str
) -> dict[str, Any]:
    """Select best parsing result and add metadata."""
    best_result = max(results, key=lambda x: x["quality"])
    best_result["metadata"] = {
        "email_type": self.detect_email_type(html_content, sender),
        "sender": sender,
        "subject": subject,
        "strategies_tried": len(results),
        "alternative_results": len(results) - 1
    }
    return best_result
```

4. **Refactor main method to use extracted methods**:

```python
def parse_email_content(
    self,
    html_content: str,
    plain_text: str = "",
    sender: str = "",
    subject: str = ""
) -> dict[str, str | float]:
    """Main parsing method - now simplified coordinator."""
    # Validate inputs
    try:
        html_content, plain_text, sender, subject = self._validate_parse_inputs(
            html_content, plain_text, sender, subject
        )
    except ValueError as e:
        return {"markdown": "", "strategy": "none", "quality": 0.0,
                "metadata": {"error": str(e)}}

    # Handle empty content
    if not html_content and not plain_text:
        return {"markdown": "", "strategy": "none", "quality": 0.0,
                "metadata": {"error": "No content provided"}}

    # Plain text only
    if plain_text and not html_content:
        return {"markdown": plain_text, "strategy": "plain_text",
                "quality": 0.8, "metadata": {"type": "plain_text"}}

    # Execute strategies
    results = self._execute_parsing_strategies(html_content, sender)

    # Handle no results
    if not results:
        if plain_text:
            return {"markdown": plain_text, "strategy": "fallback_plain",
                    "quality": 0.6, "metadata": {"type": "fallback"}}
        return {"markdown": "*(Content could not be parsed)*",
                "strategy": "failed", "quality": 0.0,
                "metadata": {"error": "All parsing strategies failed"}}

    # Select and return best result
    return self._select_best_result(results, html_content, sender, subject)
```

**Verification**:
```bash
# Test the refactored parser
python -c "from gmail_assistant.parsers.advanced_email_parser import EmailContentParser; p = EmailContentParser(); print('OK')"

# Run parser tests
pytest tests/ -k "parser" -v
```

**Dependencies**: None

---

### M-4: Document Global Mutable State Thread Safety

**Effort**: Small (2-3 hours)

**Files Affected**:
- `src/gmail_assistant/utils/error_handler.py` (lines 245-253, 515-523)
- `src/gmail_assistant/core/container.py` (lines 567-579)

**Current State**:
Global mutable state exists without thread safety documentation:
```python
# error_handler.py
_global_error_handler: ErrorHandler | None = None
_integrated_handler: IntegratedErrorHandler | None = None

# container.py
_global_container: ServiceContainer | None = None
```

**Implementation Steps**:

1. **Add thread safety documentation to `error_handler.py`**:

```python
# Replace lines 244-258 with:
# =============================================================================
# Global Error Handler Instance
# =============================================================================
#
# Thread Safety: The global error handler uses lazy initialization with a
# module-level variable. While Python's GIL provides some protection during
# initialization, concurrent access in multi-threaded scenarios should use
# `get_error_handler()` which performs atomic initialization.
#
# For multi-threaded applications, consider:
# 1. Initialize handler at startup before spawning threads
# 2. Use thread-local handlers via `threading.local()`
# 3. Pass handler explicitly to avoid global state

_global_error_handler: ErrorHandler | None = None
_global_error_handler_lock = threading.Lock()


def get_error_handler() -> ErrorHandler:
    """
    Get global error handler instance (thread-safe lazy initialization).

    Returns:
        Singleton ErrorHandler instance.

    Note:
        For multi-threaded applications, consider initializing at startup
        or using dependency injection instead of global state.
    """
    global _global_error_handler
    if _global_error_handler is None:
        with _global_error_handler_lock:
            if _global_error_handler is None:  # Double-check locking
                _global_error_handler = ErrorHandler()
    return _global_error_handler
```

2. **Add similar documentation to `container.py`**:

```python
# Replace lines 567-579 with:
# =============================================================================
# Global Container Instance
# =============================================================================
#
# Thread Safety: The global container uses lazy initialization. While the
# ServiceContainer class itself is thread-safe (uses RLock for operations),
# the global variable initialization is protected by a separate lock.
#
# Recommended patterns:
# 1. Call set_global_container() at application startup before threads
# 2. Use explicit container passing for better testability
# 3. Consider scoped containers for request-based isolation

_global_container: ServiceContainer | None = None
_global_container_lock = threading.Lock()


def set_global_container(container: ServiceContainer) -> None:
    """
    Set the global container (thread-safe).

    Args:
        container: ServiceContainer instance to use globally.

    Note:
        Should be called once at application startup before spawning threads.
    """
    global _global_container
    with _global_container_lock:
        _global_container = container


def get_global_container() -> ServiceContainer | None:
    """
    Get the global container (thread-safe).

    Returns:
        Global ServiceContainer or None if not set.
    """
    return _global_container
```

3. **Add import for threading at top of both files** (if not present):

```python
import threading
```

**Verification**:
```bash
# Run tests
pytest tests/ -v

# Check documentation renders correctly
python -c "from gmail_assistant.utils.error_handler import get_error_handler; help(get_error_handler)"
```

**Dependencies**: None

---

### L-1: Standardize Logging Initialization

**Effort**: Small (2-3 hours)

**Files Affected**:
Multiple files with inconsistent patterns:
- Module-level: `logger = logging.getLogger(__name__)`
- Instance-level: `self.logger = logging.getLogger(__name__)`

**Implementation Steps**:

1. **Create a logging utility module** at `src/gmail_assistant/utils/logging_utils.py`:

```python
"""
Standardized logging utilities for Gmail Assistant.

Usage:
    from gmail_assistant.utils.logging_utils import get_logger

    logger = get_logger(__name__)  # Module-level, preferred
"""

import logging
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger for the given module.

    Args:
        name: Module name, typically __name__
        level: Optional log level override

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger


def configure_root_logger(
    level: int = logging.INFO,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """
    Configure the root logger for the application.

    Should be called once at application startup.
    """
    logging.basicConfig(level=level, format=format_string)
```

2. **Document the standard pattern in CLAUDE.md** under Development Notes:

```markdown
### Logging Convention

Use module-level loggers for consistency:

```python
from gmail_assistant.utils.logging_utils import get_logger

logger = get_logger(__name__)  # At module level, not in __init__
```

Avoid instance-level `self.logger` unless the class needs dynamic log configuration.
```

3. **Gradually update files during other maintenance** (not a blocking change):
   - Priority: Core modules first (`gmail_assistant.py`, `config.py`)
   - Lower priority: Parser and utility modules

**Verification**:
```bash
# Check for inconsistent patterns
grep -r "self.logger = logging" src/gmail_assistant --include="*.py" | wc -l
grep -r "logger = logging.getLogger" src/gmail_assistant --include="*.py" | wc -l
```

**Dependencies**: None

---

### L-2: Add Removal Version to Deprecated EmailMetadata

**Effort**: Trivial (15 minutes)

**Files Affected**:
- `src/gmail_assistant/core/protocols.py` (lines 40-59)

**Current State**:
```python
@dataclass
class EmailMetadata:
    """
    .. deprecated:: 2.0.0
        Use :class:`Email` from :mod:`gmail_assistant.core.schemas` instead.
        Will be removed in version 3.0.0.
    """
```

The docstring mentions 3.0.0 but the warning message doesn't.

**Implementation Steps**:

Update the `__post_init__` warning message to match:

```python
def __post_init__(self) -> None:
    import warnings
    warnings.warn(
        "EmailMetadata is deprecated since v2.0.0 and will be removed in v3.0.0. "
        "Use Email from gmail_assistant.core.schemas instead.",
        DeprecationWarning,
        stacklevel=2
    )
```

Also add `@deprecated` decorator if using Python 3.13+ or document for future:

```python
# For Python 3.13+:
# from warnings import deprecated
# @deprecated("Use Email from gmail_assistant.core.schemas instead", category=DeprecationWarning)
```

**Verification**:
```bash
python -c "from gmail_assistant.core.protocols import EmailMetadata; EmailMetadata('id', 'tid', 's', 'f', [], 'd', [])"
# Should show deprecation warning with version info
```

**Dependencies**: None

---

### L-3: Add Docstrings to Private Methods

**Effort**: Small (1-2 hours)

**Files Affected**:
Various files with undocumented private methods. Priority targets:
- `src/gmail_assistant/core/fetch/gmail_assistant.py`
- `src/gmail_assistant/parsers/advanced_email_parser.py`
- `src/gmail_assistant/utils/error_handler.py`

**Implementation Steps**:

1. **Identify undocumented private methods**:
```bash
# Find private methods without docstrings
grep -n "def _[a-z]" src/gmail_assistant/core/fetch/gmail_assistant.py
```

2. **Add docstrings following Google style**:

```python
# Example for gmail_assistant.py
def _parse_email_date(self, date_str: str) -> tuple[str, str]:
    """
    Parse email date string into filename prefix and folder path.

    Args:
        date_str: RFC 2822 formatted date string from email headers.

    Returns:
        Tuple of (date_prefix, folder_date) where:
        - date_prefix: Formatted as 'YYYY-MM-DD_HHMMSS' for filenames
        - folder_date: Formatted as 'YYYY/MM' for directory organization

    Example:
        >>> self._parse_email_date("Mon, 31 Mar 2025 12:00:00 +0000")
        ('2025-03-31_120000', '2025/03')
    """
```

3. **Priority list for documentation**:
   - `_validate_api_response`
   - `_parse_email_date`
   - `_get_output_path`
   - `_save_email_files`
   - `_check_memory_and_optimize`

**Verification**:
```bash
# Check docstring coverage
pydocstyle src/gmail_assistant/core/fetch/gmail_assistant.py --select=D100,D101,D102,D103
```

**Dependencies**: None

---

## 2. Architecture Improvements

### M-5: Split `utils/` Module by Domain

**Effort**: Medium (4-6 hours)

**Files Affected**:
- `src/gmail_assistant/utils/` (12 modules)

**Current State**:
The `utils/` package is a catch-all with unrelated modules:
- Rate limiting: `rate_limiter.py`
- Caching: `cache_manager.py`
- Memory: `memory_manager.py`
- Security: `secure_file.py`, `secure_logger.py`, `pii_redactor.py`
- Validation: `input_validator.py`, `config_schema.py`
- Error handling: `error_handler.py`, `error_classifier.py`, `circuit_breaker.py`
- Other: `metrics.py`, `manifest.py`

**Implementation Steps**:

1. **Create new domain-specific packages**:

```
src/gmail_assistant/
  resilience/          # NEW: Rate limiting, circuit breaker, retry logic
    __init__.py
    rate_limiter.py    # Move from utils/
    circuit_breaker.py # Move from utils/

  caching/             # NEW: Caching and memory management
    __init__.py
    cache_manager.py   # Move from utils/
    memory_manager.py  # Move from utils/

  security/            # NEW: Security utilities
    __init__.py
    secure_file.py     # Move from utils/
    secure_logger.py   # Move from utils/
    pii_redactor.py    # Move from utils/

  validation/          # NEW: Input validation
    __init__.py
    input_validator.py # Move from utils/
    config_schema.py   # Move from utils/
```

2. **Create `__init__.py` files with backward-compatible imports**:

```python
# src/gmail_assistant/resilience/__init__.py
"""Resilience patterns: rate limiting, circuit breaker, retry logic."""

from gmail_assistant.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    gmail_circuit_breaker,
    with_circuit_breaker,
)
from gmail_assistant.resilience.rate_limiter import (
    GmailRateLimiter,
    QuotaTracker,
    retry_on_rate_limit,
)

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "GmailRateLimiter",
    "QuotaTracker",
    "gmail_circuit_breaker",
    "retry_on_rate_limit",
    "with_circuit_breaker",
]
```

3. **Update `utils/__init__.py` for backward compatibility**:

```python
# src/gmail_assistant/utils/__init__.py
"""
Utility modules (DEPRECATED - use domain-specific packages).

This package re-exports from new locations for backward compatibility.
Direct imports from utils.* are deprecated as of v2.1.0.
"""

import warnings

# Re-export with deprecation warning
def __getattr__(name: str):
    _migrations = {
        'GmailRateLimiter': 'gmail_assistant.resilience',
        'CircuitBreaker': 'gmail_assistant.resilience',
        'CacheManager': 'gmail_assistant.caching',
        'MemoryTracker': 'gmail_assistant.caching',
        'InputValidator': 'gmail_assistant.validation',
        # ... etc
    }
    if name in _migrations:
        warnings.warn(
            f"Importing {name} from gmail_assistant.utils is deprecated. "
            f"Use {_migrations[name]} instead.",
            DeprecationWarning,
            stacklevel=2
        )
    raise AttributeError(f"module 'gmail_assistant.utils' has no attribute '{name}'")
```

4. **Update internal imports** (can be done incrementally):

```python
# Before:
from gmail_assistant.utils.rate_limiter import GmailRateLimiter

# After:
from gmail_assistant.resilience import GmailRateLimiter
```

**Verification**:
```bash
# Run full test suite
pytest tests/ -v

# Check import paths
python -c "from gmail_assistant.resilience import GmailRateLimiter; print('OK')"
python -c "from gmail_assistant.caching import CacheManager; print('OK')"
```

**Dependencies**: M-1 (consolidate exceptions first)

---

### M-6: Complete Analysis Module Integration

**Effort**: Small (2-3 hours)

**Files Affected**:
- `src/gmail_assistant/analysis/` (5 modules)
- `src/gmail_assistant/core/__init__.py`

**Current State**:
The `analysis/` package has 5 modules but no imports in `core/`, yet `core` exports analysis-related classes. This indicates incomplete modularization.

**Implementation Steps**:

1. **Review what `core/__init__.py` exports from analysis**:

```python
# Check current exports
python -c "from gmail_assistant.core import *; print(dir())"
```

2. **Create proper `analysis/__init__.py` with public API**:

```python
# src/gmail_assistant/analysis/__init__.py
"""Email analysis and reporting tools."""

from gmail_assistant.analysis.email_analyzer import EmailAnalyzer
from gmail_assistant.analysis.daily_email_analyzer import DailyEmailAnalyzer
from gmail_assistant.analysis.email_data_converter import EmailDataConverter

__all__ = [
    "EmailAnalyzer",
    "DailyEmailAnalyzer",
    "EmailDataConverter",
]
```

3. **Update `core/__init__.py` to import from `analysis/`** (if it re-exports):

```python
# If core re-exports analysis classes, use explicit import
from gmail_assistant.analysis import EmailAnalyzer
```

4. **Document the module relationship** in package docstrings.

**Verification**:
```bash
# Check imports work correctly
python -c "from gmail_assistant.analysis import EmailAnalyzer; print('OK')"
```

**Dependencies**: None

---

### L-4: Merge Single-Module Export Package

**Effort**: Trivial (30 minutes)

**Files Affected**:
- `src/gmail_assistant/export/` (contains only `parquet_exporter.py`)
- `src/gmail_assistant/core/output/plugin_manager.py`

**Current State**:
The `export/` package contains only `parquet_exporter.py`. This could be integrated into the output plugin system.

**Implementation Steps**:

1. **Option A: Merge into output plugins** (recommended):

```python
# In src/gmail_assistant/core/output/plugin_manager.py
# Add ParquetPlugin class

class ParquetPlugin(OutputPlugin):
    """Parquet format output plugin for analytics."""

    @property
    def name(self) -> str:
        return "parquet"

    @property
    def extension(self) -> str:
        return ".parquet"

    def generate(self, email_data: dict[str, Any]) -> bytes:
        # Defer to ParquetExporter
        from gmail_assistant.export.parquet_exporter import ParquetExporter
        # ... implementation
```

2. **Option B: Keep separate but document** (if specialized functionality needed):

Add documentation explaining that `export/` is for analytics-specific exports that don't fit the plugin model.

**Verification**:
```bash
# If merged, test new plugin
python -c "from gmail_assistant.core.output.plugin_manager import OutputPluginManager; m = OutputPluginManager(); print(m.get_available_formats())"
```

**Dependencies**: None (can defer)

---

### L-5: Standardize Import Style

**Effort**: Small (1-2 hours)

**Files Affected**:
Project-wide - mix of absolute and relative imports

**Current State**:
```python
# Some files use absolute imports:
from gmail_assistant.core.exceptions import ConfigError

# Others use relative imports:
from .exceptions import ConfigError
from ..utils.rate_limiter import GmailRateLimiter
```

**Implementation Steps**:

1. **Establish convention**: Use absolute imports for public API, relative for internal sibling modules.

2. **Add to CLAUDE.md**:

```markdown
### Import Convention

- **Public API imports**: Use absolute imports
  ```python
  from gmail_assistant.core.exceptions import ConfigError
  ```
- **Internal sibling imports**: Use relative imports
  ```python
  from .config import AppConfig  # Within same package
  from ..utils.input_validator import InputValidator  # One level up
  ```
- **Never mix styles in the same file**
```

3. **Configure ruff for enforcement**:

```toml
# In pyproject.toml [tool.ruff.lint.isort]
force-single-line = false
known-first-party = ["gmail_assistant"]
relative-imports-order = "closest-to-furthest"
```

4. **Run ruff to auto-fix**:
```bash
ruff check src/ --fix --select I
```

**Verification**:
```bash
ruff check src/ --select I
```

**Dependencies**: None

---

## 3. Pattern Standardization

### M-7: Add Protocol Validation at Runtime

**Effort**: Small (2-3 hours)

**Files Affected**:
- All protocol consumers in `src/gmail_assistant/core/`

**Current State**:
Protocols are defined with `@runtime_checkable` but no `isinstance()` checks in consuming code:

```python
# protocols.py
@runtime_checkable
class EmailFetcherProtocol(Protocol):
    ...

# Consuming code doesn't validate
def process_emails(fetcher):  # No type check
    fetcher.search_messages(...)
```

**Implementation Steps**:

1. **Add validation utility to `protocols.py`** (already exists as `assert_protocol`):

```python
# Already in protocols.py - promote usage
def assert_protocol(obj: Any, protocol: type, name: str = "object") -> None:
    """Assert that an object implements a protocol."""
    if not isinstance(obj, protocol):
        raise TypeError(
            f"{name} must implement {protocol.__name__}, "
            f"got {type(obj).__name__}"
        )
```

2. **Add validation at key integration points**:

```python
# In container.py - register methods
def register(self, service_type: type[T], instance: T, ...) -> 'ServiceContainer':
    # Add validation for protocol types
    if hasattr(service_type, '__protocol_attrs__'):
        from gmail_assistant.core.protocols import implements_protocol
        if not implements_protocol(instance, service_type):
            raise TypeError(
                f"Instance does not implement {service_type.__name__}"
            )
    ...
```

3. **Add validation in output plugin manager** (already implemented):

```python
# Already in plugin_manager.py:
def register(self, plugin: Any) -> None:
    if not isinstance(plugin, OutputPluginProtocol):
        raise TypeError(...)
```

4. **Document pattern for external plugin development**.

**Verification**:
```bash
# Test protocol validation
python -c "
from gmail_assistant.core.protocols import assert_protocol, EmailFetcherProtocol

class BadFetcher:
    pass

try:
    assert_protocol(BadFetcher(), EmailFetcherProtocol, 'fetcher')
except TypeError as e:
    print(f'Validation works: {e}')
"
```

**Dependencies**: None

---

### M-8: Standardize ABC vs Protocol Usage

**Effort**: Small (2-3 hours)

**Files Affected**:
- `src/gmail_assistant/core/output/plugin_manager.py`
- `src/gmail_assistant/core/protocols.py`

**Current State**:
Mixed usage of ABC (Abstract Base Class) and Protocol patterns:
- `OutputPlugin` uses concrete base class with `NotImplementedError`
- `OutputPluginProtocol` uses Protocol pattern
- Both exist for the same abstraction

**Implementation Steps**:

1. **Decide on single pattern**: Protocol is preferred for structural typing.

2. **Update `plugin_manager.py` to use Protocol only**:

```python
# Remove OutputPlugin base class, rely on Protocol
from gmail_assistant.core.protocols import OutputPluginProtocol

# Plugins implement the protocol directly without inheritance
class EMLPlugin:  # No base class
    """EML format output plugin."""

    @property
    def name(self) -> str:
        return "eml"

    @property
    def extension(self) -> str:
        return ".eml"

    def generate(self, email_data: dict[str, Any]) -> str:
        ...

    def save(self, content: str, path: Path) -> bool:
        ...  # Implement directly, no super()
```

3. **Create mixin for common save() logic** (optional):

```python
class AtomicSaveMixin:
    """Mixin providing atomic file save capability."""

    def atomic_save(self, content: str, path: Path) -> bool:
        """Save content atomically using temp file + rename."""
        # Implementation from current OutputPlugin.save()
        ...
```

4. **Update documentation to show Protocol-first pattern**.

**Verification**:
```bash
# Verify plugins still work
python -c "
from gmail_assistant.core.output.plugin_manager import OutputPluginManager
from gmail_assistant.core.protocols import OutputPluginProtocol

m = OutputPluginManager()
for name in m.get_available_formats():
    plugin = m.get_plugin(name)
    print(f'{name}: implements protocol = {isinstance(plugin, OutputPluginProtocol)}')
"
```

**Dependencies**: M-7

---

## 4. Scalability Improvements

### M-9: Make Concurrency Limits Configurable

**Effort**: Small (2-3 hours)

**Files Affected**:
- `src/gmail_assistant/core/fetch/async_fetcher.py`
- `src/gmail_assistant/core/config.py`

**Current State**:
```python
# async_fetcher.py line 52-53
def __init__(
    self,
    credentials_file: str = 'credentials.json',
    max_concurrent: int = 10,  # Hardcoded
    max_workers: int = 4,      # Hardcoded
```

**Implementation Steps**:

1. **Add to AppConfig in `config.py`**:

```python
@dataclass(frozen=True, slots=True)
class AppConfig:
    # ... existing fields ...

    # Concurrency settings
    max_concurrent_requests: int = 10
    max_worker_threads: int = 4
    async_batch_size: int = 100

    def __post_init__(self) -> None:
        # ... existing validation ...
        if not 1 <= self.max_concurrent_requests <= 50:
            raise ConfigError(f"max_concurrent_requests must be 1-50")
        if not 1 <= self.max_worker_threads <= 16:
            raise ConfigError(f"max_worker_threads must be 1-16")
```

2. **Update `_ALLOWED_KEYS`**:

```python
_ALLOWED_KEYS = frozenset({
    # ... existing keys ...
    "max_concurrent_requests",
    "max_worker_threads",
    "async_batch_size",
})
```

3. **Update `AsyncGmailFetcher` to accept config**:

```python
def __init__(
    self,
    credentials_file: str = 'credentials.json',
    max_concurrent: int | None = None,
    max_workers: int | None = None,
    config: AppConfig | None = None,
    use_native_async: bool | None = None,
):
    # Use config values with fallback to parameters
    if config:
        max_concurrent = max_concurrent or config.max_concurrent_requests
        max_workers = max_workers or config.max_worker_threads
    else:
        max_concurrent = max_concurrent or 10
        max_workers = max_workers or 4
```

**Verification**:
```bash
# Test configuration loading
python -c "
from gmail_assistant.core.config import AppConfig
c = AppConfig.load()
print(f'Concurrent: {c.max_concurrent_requests}, Workers: {c.max_worker_threads}')
"
```

**Dependencies**: None

---

### M-10: Add Backpressure to Streaming Fetcher

**Effort**: Medium (3-4 hours)

**Files Affected**:
- `src/gmail_assistant/core/fetch/streaming.py`

**Current State**:
`StreamingGmailFetcher` yields indefinitely without backpressure, risking consumer overwhelm.

**Implementation Steps**:

1. **Add configurable buffer limits**:

```python
class StreamingGmailFetcher:
    def __init__(
        self,
        credentials_file: str = 'credentials.json',
        batch_size: int = 100,
        max_buffer_size: int = 1000,  # NEW: Max items before pause
        backpressure_threshold: float = 0.8,  # NEW: Pause at 80% full
    ):
        self.max_buffer_size = max_buffer_size
        self.backpressure_threshold = backpressure_threshold
        self._pending_count = 0
```

2. **Add backpressure check method**:

```python
def _check_backpressure(self) -> bool:
    """
    Check if backpressure should be applied.

    Returns:
        True if should pause/slow down, False otherwise.
    """
    if self._pending_count >= self.max_buffer_size * self.backpressure_threshold:
        self.logger.warning(
            f"Backpressure: {self._pending_count} items pending "
            f"(threshold: {self.max_buffer_size * self.backpressure_threshold})"
        )
        return True
    return False

def _apply_backpressure(self) -> None:
    """Apply backpressure by waiting."""
    import time
    while self._pending_count >= self.max_buffer_size * self.backpressure_threshold:
        time.sleep(0.1)
        # Check memory and maybe force GC
        memory_status = self.memory_tracker.check_memory()
        if memory_status['status'] == 'critical':
            self.memory_tracker.force_gc()
```

3. **Integrate into streaming methods**:

```python
def process_emails_streaming(self, query: str, ...) -> Iterator[dict[str, Any]]:
    # ... existing code ...

    for result in self.streaming_processor.process_emails_streaming(...):
        # Check backpressure before yielding
        if self._check_backpressure():
            self._apply_backpressure()

        yield result
        self._pending_count -= 1  # Consumer processed item
```

4. **Add acknowledgment mechanism for async scenarios**:

```python
def acknowledge(self, count: int = 1) -> None:
    """Acknowledge that consumer has processed items."""
    self._pending_count = max(0, self._pending_count - count)
```

**Verification**:
```bash
# Test backpressure with mock consumer
python -c "
from gmail_assistant.core.fetch.streaming import StreamingGmailFetcher
f = StreamingGmailFetcher(max_buffer_size=10)
print(f'Buffer size: {f.max_buffer_size}')
"
```

**Dependencies**: None

---

### M-11: Make Memory Thresholds Configurable

**Effort**: Small (1-2 hours)

**Files Affected**:
- `src/gmail_assistant/utils/memory_manager.py` (lines 24-25)

**Current State**:
```python
class MemoryTracker:
    def __init__(self) -> None:
        self.threshold_warning = 500 * 1024 * 1024  # 500MB fixed
        self.threshold_critical = 1024 * 1024 * 1024  # 1GB fixed
```

**Implementation Steps**:

1. **Update `MemoryTracker` to use percentage-based thresholds**:

```python
class MemoryTracker:
    """Track memory usage with configurable thresholds."""

    def __init__(
        self,
        warning_percent: float = 50.0,  # 50% of available RAM
        critical_percent: float = 75.0,  # 75% of available RAM
        min_warning_mb: int = 256,  # Minimum thresholds
        min_critical_mb: int = 512,
    ) -> None:
        self.initial_memory = self._get_memory_usage()
        self.peak_memory = self.initial_memory

        # Calculate thresholds based on available memory
        available_memory = self._get_available_memory()

        self.threshold_warning = max(
            int(available_memory * warning_percent / 100),
            min_warning_mb * 1024 * 1024
        )
        self.threshold_critical = max(
            int(available_memory * critical_percent / 100),
            min_critical_mb * 1024 * 1024
        )

        logger.info(
            f"Memory thresholds: warning={self.threshold_warning / 1024 / 1024:.0f}MB, "
            f"critical={self.threshold_critical / 1024 / 1024:.0f}MB"
        )

    def _get_available_memory(self) -> int:
        """Get total available system memory in bytes."""
        try:
            import psutil
            return psutil.virtual_memory().total
        except ImportError:
            # Fallback to 4GB assumption if psutil unavailable
            return 4 * 1024 * 1024 * 1024
```

2. **Add configuration option**:

```python
# Can also accept explicit byte values for testing
def __init__(
    self,
    warning_percent: float = 50.0,
    critical_percent: float = 75.0,
    warning_bytes: int | None = None,  # Override for testing
    critical_bytes: int | None = None,
):
    if warning_bytes is not None:
        self.threshold_warning = warning_bytes
    else:
        # Calculate from percentage
        ...
```

**Verification**:
```bash
python -c "
from gmail_assistant.utils.memory_manager import MemoryTracker
t = MemoryTracker()
print(f'Warning: {t.threshold_warning / 1024 / 1024:.0f}MB')
print(f'Critical: {t.threshold_critical / 1024 / 1024:.0f}MB')
"
```

**Dependencies**: None

---

### M-12: Parallelize Batch Request Preparation

**Effort**: Medium (3-4 hours)

**Files Affected**:
- `src/gmail_assistant/core/fetch/batch_api.py`

**Current State**:
Batch requests are prepared sequentially:
```python
for msg_id in batch_ids:
    request = self.service.users().messages().get(...)
    batch.add(request, callback=self._create_get_callback(msg_id))
```

**Implementation Steps**:

1. **Use ThreadPoolExecutor for request preparation**:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

class GmailBatchClient:
    def __init__(
        self,
        service,
        rate_limiter: Any | None = None,
        on_error: Callable[[str, Exception], None] | None = None,
        preparation_workers: int = 4,  # NEW
    ):
        self.preparation_workers = preparation_workers
        # ...

    def _prepare_get_requests(
        self,
        batch_ids: list[str],
        format: str,
        metadata_headers: list[str] | None
    ) -> list[tuple[str, Any]]:
        """Prepare get requests in parallel."""
        requests = []

        def prepare_one(msg_id: str):
            return (
                msg_id,
                self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format=format,
                    metadataHeaders=metadata_headers if format == 'metadata' else None
                )
            )

        with ThreadPoolExecutor(max_workers=self.preparation_workers) as executor:
            futures = {executor.submit(prepare_one, mid): mid for mid in batch_ids}
            for future in as_completed(futures):
                try:
                    requests.append(future.result())
                except Exception as e:
                    msg_id = futures[future]
                    logger.warning(f"Failed to prepare request for {msg_id}: {e}")

        return requests
```

2. **Update batch_get_messages to use parallel preparation**:

```python
def batch_get_messages(self, message_ids: list[str], ...):
    # ... existing code ...

    for i in range(0, total, self.MAX_BATCH_SIZE):
        batch_ids = message_ids[i:i + self.MAX_BATCH_SIZE]

        # Parallel request preparation
        prepared_requests = self._prepare_get_requests(
            batch_ids, format, metadata_headers
        )

        batch = self.service.new_batch_http_request()
        for msg_id, request in prepared_requests:
            batch.add(request, callback=self._create_get_callback(msg_id))

        # ... rest of execution ...
```

3. **Add performance monitoring**:

```python
import time

def batch_get_messages(self, message_ids: list[str], ...):
    prep_start = time.time()
    prepared_requests = self._prepare_get_requests(...)
    prep_time = time.time() - prep_start
    logger.debug(f"Request preparation took {prep_time:.2f}s for {len(batch_ids)} requests")
```

**Verification**:
```bash
# Benchmark comparison (needs real API access)
pytest tests/integration/test_batch_api.py -v -k performance
```

**Dependencies**: None

---

### L-6: Add Connection Pooling

**Effort**: Medium (3-4 hours)

**Files Affected**:
- `src/gmail_assistant/core/fetch/async_gmail_client.py`
- `src/gmail_assistant/core/auth/base.py`

**Current State**:
Each API operation creates new HTTP connections without pooling.

**Implementation Steps**:

1. **Use httpx connection pooling** (already available if httpx installed):

```python
# In async_gmail_client.py
import httpx

class AsyncGmailClient:
    def __init__(self, credentials, pool_size: int = 10):
        self._client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=pool_size,
                max_connections=pool_size * 2,
            ),
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
```

2. **For sync client, configure httplib2 connection reuse**:

```python
# In auth/base.py
from httplib2 import Http

def _create_http_client(self) -> Http:
    """Create HTTP client with connection caching."""
    http = Http(cache=".cache", timeout=30)
    http.follow_redirects = True
    return http
```

3. **Document connection management in CLAUDE.md**.

**Verification**:
```bash
# Check connection reuse with debug logging
HTTPLIB2_DEBUG=1 python -c "
from gmail_assistant.core.auth.base import ReadOnlyGmailAuth
auth = ReadOnlyGmailAuth('credentials.json')
auth.authenticate()
" 2>&1 | grep -i "connection"
```

**Dependencies**: None (can defer)

---

## 5. Configuration Consolidation

### M-13: Consolidate Config Modules

**Effort**: Medium (4-6 hours)

**Files Affected**:
- `src/gmail_assistant/core/config.py`
- `src/gmail_assistant/core/config_schemas.py`
- `src/gmail_assistant/utils/config_schema.py`

**Current State**:
Three separate config-related modules:
- `core/config.py`: `AppConfig` dataclass with validation
- `core/config_schemas.py`: Pydantic models for various configs
- `utils/config_schema.py`: `ConfigSchema` class with validation methods

**Implementation Steps**:

1. **Consolidate into single `core/config/` package**:

```
src/gmail_assistant/core/config/
    __init__.py           # Re-exports public API
    app_config.py         # AppConfig (from core/config.py)
    schemas.py            # Pydantic schemas (from core/config_schemas.py)
    validation.py         # Validation utilities (from utils/config_schema.py)
```

2. **Create package `__init__.py`**:

```python
# src/gmail_assistant/core/config/__init__.py
"""Configuration management for Gmail Assistant."""

from gmail_assistant.core.config.app_config import AppConfig
from gmail_assistant.core.config.schemas import (
    AIKeywordsConfig,
    AnalysisConfig,
    DatabaseConfig,
    DeletionConfig,
    GmailAssistantConfig,
    RateLimitConfig,
)
from gmail_assistant.core.config.validation import (
    ConfigSchema,
    ConfigValidator,
    validate_config_file,
)

__all__ = [
    "AppConfig",
    "AIKeywordsConfig",
    "AnalysisConfig",
    "ConfigSchema",
    "ConfigValidator",
    "DatabaseConfig",
    "DeletionConfig",
    "GmailAssistantConfig",
    "RateLimitConfig",
    "validate_config_file",
]
```

3. **Move files and update imports**:

```bash
mkdir -p src/gmail_assistant/core/config
mv src/gmail_assistant/core/config.py src/gmail_assistant/core/config/app_config.py
mv src/gmail_assistant/core/config_schemas.py src/gmail_assistant/core/config/schemas.py
mv src/gmail_assistant/utils/config_schema.py src/gmail_assistant/core/config/validation.py
```

4. **Update all imports across codebase**:

```python
# Before:
from gmail_assistant.core.config import AppConfig
from gmail_assistant.utils.config_schema import ConfigValidator

# After (still works via re-export):
from gmail_assistant.core.config import AppConfig, ConfigValidator
```

5. **Add backward compatibility layer**:

```python
# src/gmail_assistant/core/config.py (shim file)
"""Backward compatibility - import from config package."""
from gmail_assistant.core.config import *  # noqa
```

**Verification**:
```bash
# Test imports
python -c "
from gmail_assistant.core.config import AppConfig, ConfigValidator, GmailAssistantConfig
print('All imports successful')
"

# Run tests
pytest tests/ -v
```

**Dependencies**: None

---

### M-14: Add Config Migration Support

**Effort**: Medium (4-6 hours)

**Files Affected**:
- `src/gmail_assistant/core/config/` (new module)

**Current State**:
No config migration path - schema changes break existing configs.

**Implementation Steps**:

1. **Create `migration.py` module**:

```python
# src/gmail_assistant/core/config/migration.py
"""Configuration migration utilities."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Version history with migration functions
MIGRATIONS = {
    "1.0.0": lambda c: c,  # Initial version, no changes
    "2.0.0": migrate_1_to_2,
    "2.1.0": migrate_2_to_2_1,
}

CURRENT_VERSION = "2.1.0"


def migrate_1_to_2(config: dict[str, Any]) -> dict[str, Any]:
    """Migrate from v1.x to v2.0.0 config format."""
    # Add new required fields with defaults
    if "output_plugins" not in config:
        config["output_plugins"] = ["eml", "markdown"]
    if "default_output_format" not in config:
        config["default_output_format"] = "both"

    # Rename deprecated fields
    if "max_results" in config:
        config["max_emails"] = config.pop("max_results")

    config["_config_version"] = "2.0.0"
    return config


def migrate_2_to_2_1(config: dict[str, Any]) -> dict[str, Any]:
    """Migrate from v2.0.0 to v2.1.0 config format."""
    # Add concurrency settings
    if "max_concurrent_requests" not in config:
        config["max_concurrent_requests"] = 10
    if "max_worker_threads" not in config:
        config["max_worker_threads"] = 4

    config["_config_version"] = "2.1.0"
    return config


def get_config_version(config: dict[str, Any]) -> str:
    """Detect config version from content."""
    if "_config_version" in config:
        return config["_config_version"]

    # Heuristic detection
    if "output_plugins" in config:
        return "2.0.0"
    return "1.0.0"


def migrate_config(
    config: dict[str, Any],
    target_version: str = CURRENT_VERSION
) -> dict[str, Any]:
    """
    Migrate config to target version.

    Args:
        config: Configuration dictionary
        target_version: Target version string

    Returns:
        Migrated configuration
    """
    current = get_config_version(config)
    logger.info(f"Migrating config from {current} to {target_version}")

    versions = list(MIGRATIONS.keys())
    current_idx = versions.index(current) if current in versions else 0
    target_idx = versions.index(target_version)

    for version in versions[current_idx + 1:target_idx + 1]:
        migration_func = MIGRATIONS[version]
        config = migration_func(config)
        logger.debug(f"Applied migration to {version}")

    return config


def migrate_config_file(
    path: Path,
    backup: bool = True,
    target_version: str = CURRENT_VERSION
) -> None:
    """
    Migrate a config file in place.

    Args:
        path: Path to config file
        backup: Create .bak backup before migration
        target_version: Target version
    """
    with open(path, encoding='utf-8') as f:
        config = json.load(f)

    if backup:
        backup_path = path.with_suffix(f".{get_config_version(config)}.bak")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Created backup: {backup_path}")

    migrated = migrate_config(config, target_version)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(migrated, f, indent=2)

    logger.info(f"Migrated {path} to {target_version}")
```

2. **Integrate with AppConfig loading**:

```python
# In app_config.py
from gmail_assistant.core.config.migration import migrate_config, CURRENT_VERSION

@classmethod
def _load_from_file(cls, config_path: Path, allow_repo_credentials: bool) -> AppConfig:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON: {e}") from e

    # Auto-migrate if needed
    data = migrate_config(data, CURRENT_VERSION)

    # ... rest of loading logic ...
```

3. **Add CLI command for migration**:

```python
# In cli/commands/config_cmd.py
@config.command()
@click.option('--migrate', type=click.Path(exists=True), help='Migrate config file')
def migrate(migrate: str):
    """Migrate config file to current version."""
    from gmail_assistant.core.config.migration import migrate_config_file
    migrate_config_file(Path(migrate))
    click.echo("Migration complete")
```

**Verification**:
```bash
# Test migration
echo '{"max_results": 100}' > /tmp/test_config.json
python -c "
from gmail_assistant.core.config.migration import migrate_config_file
from pathlib import Path
migrate_config_file(Path('/tmp/test_config.json'))
"
cat /tmp/test_config.json  # Should have new fields
```

**Dependencies**: M-13

---

### L-7: Move Hardcoded Paths to Configuration

**Effort**: Small (2-3 hours)

**Files Affected**:
- `src/gmail_assistant/core/constants.py`
- Various files referencing `AI_CONFIG_PATH`, `KEYRING_SERVICE`, etc.

**Current State**:
```python
# constants.py
AI_CONFIG_PATH = Path("config/config.json")
KEYRING_SERVICE = "gmail_assistant"
```

**Implementation Steps**:

1. **Add path configuration to `AppConfig`**:

```python
@dataclass(frozen=True, slots=True)
class AppConfig:
    # ... existing fields ...

    # Path configuration
    ai_config_path: Path = Path("~/.gmail-assistant/ai_config.json")
    keyring_service: str = "gmail-assistant"

    def __post_init__(self) -> None:
        # Expand user paths
        object.__setattr__(self, 'ai_config_path',
                          self.ai_config_path.expanduser())
```

2. **Update constants to use defaults**:

```python
# constants.py
from gmail_assistant.core.config import AppConfig

def get_ai_config_path() -> Path:
    """Get AI config path from config or default."""
    try:
        config = AppConfig.load()
        return config.ai_config_path
    except Exception:
        return Path.home() / ".gmail-assistant" / "ai_config.json"
```

3. **Update consumers to use config**:

```python
# Before:
from gmail_assistant.core.constants import AI_CONFIG_PATH

# After:
from gmail_assistant.core.constants import get_ai_config_path
config_path = get_ai_config_path()
```

**Verification**:
```bash
python -c "
from gmail_assistant.core.constants import get_ai_config_path
print(f'AI config path: {get_ai_config_path()}')
"
```

**Dependencies**: M-13

---

### L-8: Make Rate Limits Configurable

**Effort**: Small (1-2 hours)

**Files Affected**:
- `src/gmail_assistant/utils/rate_limiter.py` (line 34)
- `src/gmail_assistant/core/config.py`

**Current State**:
```python
class GmailRateLimiter:
    def __init__(self, requests_per_second: float = 10.0, ...):  # Hardcoded
```

**Implementation Steps**:

1. **Already have `rate_limit_per_second` in AppConfig** - verify it's used:

```python
# In config.py - already exists:
rate_limit_per_second: float = 10.0
```

2. **Update rate limiter to accept config**:

```python
class GmailRateLimiter:
    def __init__(
        self,
        requests_per_second: float | None = None,
        config: AppConfig | None = None,
        max_retries: int = 5,
        ...
    ):
        if config:
            requests_per_second = config.rate_limit_per_second
        self.requests_per_second = requests_per_second or 10.0
```

3. **Update container factory to pass config**:

```python
# In container.py
def create_default_container(config: AppConfig | None = None) -> ServiceContainer:
    if config is None:
        config = AppConfig.load()

    container.register_factory(
        GmailRateLimiter,
        lambda: GmailRateLimiter(config=config)
    )
```

**Verification**:
```bash
python -c "
from gmail_assistant.core.config import AppConfig
from gmail_assistant.utils.rate_limiter import GmailRateLimiter

config = AppConfig.load()
limiter = GmailRateLimiter(config=config)
print(f'Rate limit: {limiter.requests_per_second} req/s')
"
```

**Dependencies**: M-13

---

## 6. Security Hardening

### M-16: Pin Dependency Versions

**Effort**: Small (1-2 hours)

**Files Affected**:
- `pyproject.toml` (lines 31-39)

**Current State**:
```toml
dependencies = [
    "click>=8.1.0",  # No upper bound
    "google-api-python-client>=2.140.0",  # No upper bound
    ...
]
```

**Implementation Steps**:

1. **Add upper bounds for critical dependencies**:

```toml
dependencies = [
    "click>=8.1.0,<9.0",
    "google-api-python-client>=2.140.0,<3.0",
    "google-auth>=2.27.0,<3.0",
    "google-auth-oauthlib>=1.2.0,<2.0",
    "google-auth-httplib2>=0.2.0,<1.0",
    "html2text>=2024.2.26,<2025.0",
    "tenacity>=8.2.0,<9.0",
]
```

2. **Add upper bounds for optional dependencies**:

```toml
[project.optional-dependencies]
analysis = [
    "pandas>=2.1.0,<3.0",
    "numpy>=1.26.0,<2.0",
    "pyarrow>=15.0.0,<16.0",
]
# ... similar for other groups
```

3. **Create `requirements.txt` for reproducible builds**:

```bash
# Generate pinned requirements
pip freeze > requirements-lock.txt
```

4. **Document update policy** in CONTRIBUTING.md or CLAUDE.md:

```markdown
### Dependency Updates

Dependencies use semantic versioning bounds:
- Patch updates: Applied automatically via `>=X.Y.Z`
- Minor updates: Allowed within major version
- Major updates: Require explicit testing and version bump

Run `pip-compile` quarterly to update pinned versions.
```

**Verification**:
```bash
# Test installation with bounds
pip install -e . --dry-run

# Check for conflicts
pip check
```

**Dependencies**: None

---

### L-9: Add File Path Validation Wrapper

**Effort**: Small (2-3 hours)

**Files Affected**:
- `src/gmail_assistant/cli/commands/fetch.py` (lines 140-158)
- `src/gmail_assistant/utils/input_validator.py`

**Current State**:
```python
# In _save_email
filepath = output_dir / filename
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(email_data, f, indent=2, default=str)
# No path validation before write
```

**Implementation Steps**:

1. **Add secure file write utility**:

```python
# In utils/input_validator.py or utils/secure_file.py
from pathlib import Path

def validate_write_path(
    path: Path,
    base_dir: Path,
    allowed_extensions: set[str] | None = None
) -> Path:
    """
    Validate a file path is safe for writing.

    Args:
        path: Target file path
        base_dir: Must be within this directory
        allowed_extensions: Allowed file extensions (e.g., {'.json', '.eml'})

    Returns:
        Validated absolute path

    Raises:
        ValueError: If path is unsafe
    """
    path = Path(path).resolve()
    base_dir = Path(base_dir).resolve()

    # Check path traversal
    try:
        path.relative_to(base_dir)
    except ValueError:
        raise ValueError(f"Path {path} is outside base directory {base_dir}")

    # Check extension
    if allowed_extensions and path.suffix not in allowed_extensions:
        raise ValueError(f"Extension {path.suffix} not allowed")

    # Check parent exists
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    return path


def secure_write_file(
    path: Path,
    content: str | bytes,
    base_dir: Path,
    encoding: str = 'utf-8'
) -> Path:
    """
    Write file with path validation.

    Args:
        path: Target file path
        content: Content to write
        base_dir: Security boundary
        encoding: File encoding for string content

    Returns:
        Path to written file
    """
    validated_path = validate_write_path(path, base_dir)

    if isinstance(content, str):
        with open(validated_path, 'w', encoding=encoding) as f:
            f.write(content)
    else:
        with open(validated_path, 'wb') as f:
            f.write(content)

    return validated_path
```

2. **Update fetch.py to use secure write**:

```python
# In _save_email
from gmail_assistant.utils.secure_file import secure_write_file

def _save_email(email_data: dict[str, Any], output_dir: Path, output_format: str, index: int) -> None:
    """Save email in the specified format with path validation."""
    subject = email_data.get('subject', 'no_subject')[:50]
    safe_subject = re.sub(r'[<>:"/\\|?*]', '_', subject)
    msg_id = email_data.get('id', str(index))[:16]

    if output_format == 'json':
        filename = f"{index:05d}_{safe_subject}_{msg_id}.json"
        content = json.dumps(email_data, indent=2, default=str)
        secure_write_file(output_dir / filename, content, output_dir)

    # ... similar for other formats
```

**Verification**:
```bash
# Test path traversal protection
python -c "
from pathlib import Path
from gmail_assistant.utils.secure_file import validate_write_path

try:
    validate_write_path(Path('/tmp/../../etc/passwd'), Path('/tmp/output'))
except ValueError as e:
    print(f'Protected: {e}')
"
```

**Dependencies**: None

---

## 7. Recommended Execution Order

Based on dependencies and impact, execute in this order:

### Phase 1: Foundation (Days 1-2)
Low-risk changes that enable later work.

| Order | Task ID | Effort | Dependencies |
|-------|---------|--------|--------------|
| 1 | M-1 | Small | None |
| 2 | M-2 | Trivial | None |
| 3 | L-2 | Trivial | None |
| 4 | M-4 | Small | None |
| 5 | L-1 | Small | None |

### Phase 2: Architecture (Days 3-5)
Structural improvements.

| Order | Task ID | Effort | Dependencies |
|-------|---------|--------|--------------|
| 6 | M-13 | Medium | None |
| 7 | M-14 | Medium | M-13 |
| 8 | M-5 | Medium | M-1 |
| 9 | L-7 | Small | M-13 |
| 10 | L-8 | Small | M-13 |

### Phase 3: Patterns (Days 6-7)
Code quality and consistency.

| Order | Task ID | Effort | Dependencies |
|-------|---------|--------|--------------|
| 11 | M-3 | Medium | None |
| 12 | M-7 | Small | None |
| 13 | M-8 | Small | M-7 |
| 14 | L-3 | Small | None |
| 15 | L-5 | Small | None |

### Phase 4: Scalability (Days 8-10)
Performance improvements.

| Order | Task ID | Effort | Dependencies |
|-------|---------|--------|--------------|
| 16 | M-9 | Small | M-13 |
| 17 | M-11 | Small | None |
| 18 | M-10 | Medium | None |
| 19 | M-12 | Medium | None |
| 20 | L-6 | Medium | None |

### Phase 5: Security (Days 11-12)
Final hardening.

| Order | Task ID | Effort | Dependencies |
|-------|---------|--------|--------------|
| 21 | M-16 | Small | None |
| 22 | L-9 | Small | None |
| 23 | M-6 | Small | None |
| 24 | L-4 | Trivial | None |

---

## Effort Summary

| Effort Level | Count | Estimated Hours |
|--------------|-------|-----------------|
| Trivial | 4 | 2-4 hours |
| Small | 14 | 28-42 hours |
| Medium | 7 | 28-42 hours |
| **Total** | **25** | **58-88 hours** (8-12 days) |

---

## Appendix: Verification Checklist

After completing all tasks, verify:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check src/`
- [ ] Type checking passes: `mypy src/gmail_assistant`
- [ ] No duplicate exceptions: `grep -r "class.*Error.*Exception" src/ --include="*.py" | grep -v core/exceptions.py`
- [ ] Documentation builds: Review CLAUDE.md updates
- [ ] Import consistency: `ruff check src/ --select I`
- [ ] Dependency check: `pip check`
