# Gmail Assistant - Comprehensive Remediation Action Plan

**Document ID**: 0110-0300_remediation_action_plan.md
**Generated**: 2026-01-10 03:00
**Based on**: 0110-0215_master_comprehensive_assessment.md
**Total Estimated Effort**: 240-330 hours (6-8 weeks @ 1 FTE)

---

## Table of Contents
1. [Phase 1: Critical Performance (Weeks 1-2)](#phase-1-critical-performance)
2. [Phase 2: Code Quality (Weeks 3-4)](#phase-2-code-quality)
3. [Phase 3: Architecture Debt (Weeks 5-6)](#phase-3-architecture-debt)
4. [Phase 4: Security Hardening (Week 7)](#phase-4-security-hardening)
5. [Final Validation Checklist](#final-validation-checklist)

---

## Phase 1: Critical Performance

### C-1: Implement Gmail Batch API Integration

**Status**: 🔴 CRITICAL
**Effort**: 24-32 hours
**Files**: `core/fetch/gmail_api_client.py`, `core/fetch/batch_api.py`
**Dependency**: None (can start immediately)

**Current State**:
- `batch_api.py` is FULLY IMPLEMENTED with `GmailBatchClient` class
- `gmail_api_client.py` uses sequential API calls at lines 99-124

**Implementation Steps**:

- [ ] **1.1 Add batch_api import to gmail_api_client.py**
  ```
  File: src/gmail_assistant/core/fetch/gmail_api_client.py
  Line: 17 (after existing imports)
  Action: Add import statement
  ```
  - [ ] Add: `from .batch_api import GmailBatchClient, BatchResult`

- [ ] **1.2 Initialize GmailBatchClient in GmailAPIClient.__init__**
  ```
  File: src/gmail_assistant/core/fetch/gmail_api_client.py
  Line: 36-38 (after self.service initialization)
  ```
  - [ ] Add after `self.service = None`:
    ```python
    self.batch_client = None
    ```
  - [ ] Add after `self._authenticate()`:
    ```python
    if self.service:
        self.batch_client = GmailBatchClient(self.service)
    ```

- [ ] **1.3 Replace sequential _fetch_email_batch with batch API**
  ```
  File: src/gmail_assistant/core/fetch/gmail_api_client.py
  Lines: 95-124
  Action: Replace entire method
  ```
  - [ ] Replace current `_fetch_email_batch` method:
    ```python
    def _fetch_email_batch(self, message_ids: List[Dict]) -> List[EmailData]:
        """Fetch a batch of emails using Batch API (C-1 fix)"""
        if not self.batch_client:
            logger.warning("Batch client not initialized, falling back to sequential")
            return self._fetch_email_batch_sequential(message_ids)

        try:
            # Extract IDs from dicts
            ids = [msg['id'] for msg in message_ids]

            # Use batch API
            emails = self.batch_client.batch_get_messages(
                ids,
                format='metadata',
                metadata_headers=['From', 'Subject', 'Date']
            )

            # Convert Email objects to EmailData for backward compatibility
            return [
                EmailData(
                    id=email.gmail_id,
                    subject=email.subject,
                    sender=email.sender,
                    date=email.date.isoformat() if email.date else '',
                    thread_id=email.thread_id,
                    labels=email.labels,
                    body_snippet=email.snippet
                )
                for email in emails
            ]
        except Exception as e:
            logger.warning(f"Batch API failed, using sequential: {e}")
            return self._fetch_email_batch_sequential(message_ids)
    ```

- [ ] **1.4 Keep original method as fallback**
  - [ ] Rename original `_fetch_email_batch` to `_fetch_email_batch_sequential`
  - [ ] Keep existing implementation unchanged as fallback

- [ ] **1.5 Replace sequential delete_emails with batch API**
  ```
  File: src/gmail_assistant/core/fetch/gmail_api_client.py
  Lines: 126-148
  ```
  - [ ] Update `delete_emails` method to use `self.batch_client.batch_delete_messages`
  - [ ] Keep sequential as fallback if batch_client unavailable

- [ ] **1.6 Replace sequential trash_emails with batch API**
  ```
  File: src/gmail_assistant/core/fetch/gmail_api_client.py
  Lines: 150-172
  ```
  - [ ] Update `trash_emails` method to use `self.batch_client.batch_trash_messages`
  - [ ] Keep sequential as fallback if batch_client unavailable

**Validation Criteria**:
- [ ] `pytest tests/ -k "batch" -v` passes
- [ ] Performance test: Fetch 100 emails takes <10s (was ~60s sequential)
- [ ] Fallback to sequential works when batch fails

**Acceptance Criteria**:
- [ ] Batch API used for all bulk operations
- [ ] 80-90% performance improvement on bulk fetches
- [ ] Graceful degradation to sequential on failure
- [ ] No functional regressions in existing tests

---

### C-2: Complete CLI Command Implementations

**Status**: 🔴 CRITICAL
**Effort**: 60-80 hours
**Files**: `cli/commands/fetch.py`, `cli/commands/delete.py`, `cli/commands/analyze.py`, `cli/commands/auth.py`
**Dependency**: C-1 (batch API for performance)

#### C-2.1: Implement `fetch` Command

- [ ] **2.1.1 Add imports to fetch.py**
  ```
  File: src/gmail_assistant/cli/commands/fetch.py
  ```
  - [ ] Add complete imports:
    ```python
    from __future__ import annotations
    import json
    from pathlib import Path
    from typing import Optional
    import click

    from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher
    from gmail_assistant.core.fetch.batch_api import GmailBatchClient
    from gmail_assistant.core.fetch.checkpoint import CheckpointManager
    from gmail_assistant.core.config import AppConfig
    from gmail_assistant.core.exceptions import AuthError, NetworkError
    ```

- [ ] **2.1.2 Implement fetch_emails function**
  ```
  File: src/gmail_assistant/cli/commands/fetch.py
  ```
  - [ ] Create main fetch function:
    ```python
    def fetch_emails(
        query: str,
        max_emails: int,
        output_dir: Path,
        output_format: str,
        credentials_path: Path,
        resume: bool = False
    ) -> dict:
        """
        Fetch emails from Gmail.

        Args:
            query: Gmail search query
            max_emails: Maximum emails to fetch
            output_dir: Output directory
            output_format: json, mbox, or eml
            credentials_path: Path to credentials.json
            resume: Resume from last checkpoint

        Returns:
            Dict with fetch statistics
        """
        checkpoint_mgr = CheckpointManager()

        # Check for resumable checkpoint
        if resume:
            checkpoint = checkpoint_mgr.get_latest_checkpoint(query=query)
            if checkpoint:
                click.echo(f"Resuming from checkpoint: {checkpoint.sync_id}")
                resume_info = checkpoint_mgr.get_resume_info(checkpoint)
                # Adjust starting point
            else:
                click.echo("No checkpoint found, starting fresh")

        # Initialize fetcher
        fetcher = GmailFetcher(str(credentials_path))
        if not fetcher.authenticate():
            raise AuthError("Gmail authentication failed")

        # Create checkpoint
        checkpoint = checkpoint_mgr.create_checkpoint(
            query=query,
            output_directory=str(output_dir),
            metadata={'format': output_format}
        )

        try:
            # Search for messages
            message_ids = fetcher.search_messages(query=query, max_results=max_emails)
            checkpoint_mgr.update_progress(checkpoint, processed=0)
            checkpoint.total_messages = len(message_ids)

            output_dir.mkdir(parents=True, exist_ok=True)

            # Fetch with progress tracking
            fetched = 0
            for i, msg_id in enumerate(message_ids):
                email_data = fetcher.get_message_details(msg_id)
                if email_data:
                    # Save based on format
                    _save_email(email_data, output_dir, output_format, i)
                    fetched += 1

                # Update checkpoint every 50 emails
                if (i + 1) % 50 == 0:
                    checkpoint_mgr.update_progress(
                        checkpoint,
                        processed=i + 1,
                        last_message_id=msg_id
                    )

            checkpoint_mgr.mark_completed(checkpoint)
            return {'fetched': fetched, 'total': len(message_ids)}

        except Exception as e:
            checkpoint_mgr.mark_interrupted(checkpoint)
            raise
    ```

- [ ] **2.1.3 Implement _save_email helper**
  - [ ] Add helper function for saving in different formats

- [ ] **2.1.4 Export function for CLI registration**
  - [ ] Add `__all__ = ['fetch_emails']`

#### C-2.2: Implement `delete` Command

- [ ] **2.2.1 Add imports to delete.py**
  ```
  File: src/gmail_assistant/cli/commands/delete.py
  ```
  - [ ] Add imports for GmailAPIClient, batch operations

- [ ] **2.2.2 Implement delete_emails function**
  - [ ] Add dry-run support
  - [ ] Add confirmation prompt
  - [ ] Add batch delete using GmailBatchClient
  - [ ] Add detailed logging

- [ ] **2.2.3 Add safety checks**
  - [ ] Require --confirm flag for actual deletion
  - [ ] Show count before deletion
  - [ ] Log all deleted message IDs

#### C-2.3: Implement `analyze` Command

- [ ] **2.3.1 Add imports to analyze.py**
  - [ ] Import from analysis modules

- [ ] **2.3.2 Implement analyze_emails function**
  - [ ] Support summary, detailed, json report types
  - [ ] Integrate with existing email_analyzer.py

- [ ] **2.3.3 Generate report output**
  - [ ] Console output for summary
  - [ ] JSON file output for json format

#### C-2.4: Implement `auth` Command

- [ ] **2.4.1 Add imports to auth.py**
  - [ ] Import ReadOnlyGmailAuth, SecureCredentialManager

- [ ] **2.4.2 Implement auth flow**
  - [ ] Check for existing credentials
  - [ ] Run OAuth flow if needed
  - [ ] Store credentials securely
  - [ ] Display authenticated email

- [ ] **2.4.3 Add auth status check**
  - [ ] Add `--status` flag to check current auth state

**Validation Criteria**:
- [ ] `gmail-assistant fetch --query "is:unread" --max-emails 10` works
- [ ] `gmail-assistant delete --query "subject:test" --dry-run` works
- [ ] `gmail-assistant analyze --report summary` works
- [ ] `gmail-assistant auth` completes OAuth flow

**Acceptance Criteria**:
- [ ] All 4 CLI commands fully functional
- [ ] Help text accurate and complete
- [ ] Error handling with appropriate exit codes
- [ ] Integration tests pass

---

### C-3: Implement Checkpoint/Resume for Fetches

**Status**: 🔴 CRITICAL
**Effort**: 16-24 hours
**Files**: `core/fetch/incremental.py`, `core/fetch/checkpoint.py`
**Dependency**: None (checkpoint.py already implemented)

**Current State**:
- `checkpoint.py` is FULLY IMPLEMENTED with `CheckpointManager` and `SyncCheckpoint`
- `incremental.py` does NOT use checkpoint system

**Implementation Steps**:

- [ ] **3.1 Add checkpoint import to incremental.py**
  ```
  File: src/gmail_assistant/core/fetch/incremental.py
  Line: 28 (after existing imports)
  ```
  - [ ] Add: `from .checkpoint import CheckpointManager, SyncCheckpoint, SyncState`

- [ ] **3.2 Add CheckpointManager to IncrementalGmailFetcher.__init__**
  ```
  File: src/gmail_assistant/core/fetch/incremental.py
  Line: 43-44
  ```
  - [ ] Add after `self.fetcher = None`:
    ```python
    self.checkpoint_manager = CheckpointManager()
    self.current_checkpoint: Optional[SyncCheckpoint] = None
    ```

- [ ] **3.3 Create checkpoint at fetch start**
  ```
  File: src/gmail_assistant/core/fetch/incremental.py
  Method: fetch_incremental_emails
  Line: ~107 (after query construction)
  ```
  - [ ] Add after `logger.info(f"Fetching emails with query: {query}")`:
    ```python
    # Check for resumable checkpoint
    existing = self.checkpoint_manager.get_latest_checkpoint(
        query=query,
        resumable_only=True
    )
    if existing:
        logger.info(f"Found resumable checkpoint: {existing.sync_id}")
        resume_info = self.checkpoint_manager.get_resume_info(existing)
        self.current_checkpoint = existing
        # Skip already processed messages
        skip_count = resume_info['skip_count']
    else:
        self.current_checkpoint = self.checkpoint_manager.create_checkpoint(
            query=query,
            output_directory=str(output_path),
            metadata={'max_emails': max_emails}
        )
        skip_count = 0
    ```

- [ ] **3.4 Update checkpoint during fetch loop**
  ```
  File: src/gmail_assistant/core/fetch/incremental.py
  Method: fetch_incremental_emails
  Line: ~132 (inside for loop)
  ```
  - [ ] Add checkpoint update every 25 emails:
    ```python
    # Update checkpoint progress
    if successful_downloads > 0 and successful_downloads % 25 == 0:
        self.checkpoint_manager.update_progress(
            self.current_checkpoint,
            processed=successful_downloads,
            last_message_id=message_id
        )
    ```

- [ ] **3.5 Mark checkpoint complete on success**
  ```
  File: src/gmail_assistant/core/fetch/incremental.py
  Line: ~170 (after successful completion)
  ```
  - [ ] Add before return:
    ```python
    if self.current_checkpoint:
        self.checkpoint_manager.mark_completed(self.current_checkpoint)
    ```

- [ ] **3.6 Mark checkpoint interrupted on failure**
  ```
  File: src/gmail_assistant/core/fetch/incremental.py
  Line: ~173 (in except block)
  ```
  - [ ] Add in exception handler:
    ```python
    if self.current_checkpoint:
        self.checkpoint_manager.mark_interrupted(self.current_checkpoint)
    ```

- [ ] **3.7 Add --resume flag to CLI**
  - [ ] Add `--resume` flag to `run_incremental_fetch` method
  - [ ] Pass through to `fetch_incremental_emails`

- [ ] **3.8 Add checkpoint cleanup**
  - [ ] Call `checkpoint_manager.cleanup_old_checkpoints()` after successful runs

**Validation Criteria**:
- [ ] Checkpoint files created in `data/checkpoints/`
- [ ] Interrupt mid-fetch → checkpoint saved
- [ ] Rerun → resumes from last checkpoint
- [ ] Completed runs → checkpoint marked complete

**Acceptance Criteria**:
- [ ] Failed fetches resume from last successful point
- [ ] No duplicate downloads on resume
- [ ] Checkpoint cleanup removes old checkpoints
- [ ] Progress percentage accurate

---

## Phase 2: Code Quality

### H-1: Unify Duplicate Data Structures

**Status**: 🟠 HIGH
**Effort**: 16-24 hours
**Files**: `core/protocols.py`, `core/ai/newsletter_cleaner.py`, `core/schemas.py`
**Dependency**: None

**Current State**:
- `protocols.py:43-55`: `EmailMetadata` dataclass
- `newsletter_cleaner.py:37-46`: `EmailData` dataclass
- `schemas.py`: Canonical `Email` Pydantic model with deprecation wrappers

**Implementation Steps**:

- [ ] **1.1 Update newsletter_cleaner.py to use schemas.Email**
  ```
  File: src/gmail_assistant/core/ai/newsletter_cleaner.py
  Lines: 37-46 (EmailData dataclass)
  ```
  - [ ] Replace import:
    ```python
    # Before
    @dataclass
    class EmailData:
        ...

    # After
    from ..schemas import Email, EmailDataCompat as EmailData
    ```

- [ ] **1.2 Update AINewsletterDetector.is_ai_newsletter signature**
  - [ ] Change parameter type hint: `email: EmailData` → `email: Email`
  - [ ] Update attribute access for any schema differences

- [ ] **1.3 Deprecate EmailMetadata in protocols.py**
  ```
  File: src/gmail_assistant/core/protocols.py
  Lines: 43-55
  ```
  - [ ] Add deprecation warning:
    ```python
    import warnings

    @dataclass
    class EmailMetadata:
        """
        DEPRECATED: Use gmail_assistant.core.schemas.Email instead.
        """
        def __post_init__(self):
            warnings.warn(
                "EmailMetadata is deprecated. Use Email from core.schemas.",
                DeprecationWarning,
                stacklevel=2
            )
        ...
    ```

- [ ] **1.4 Update all importers of EmailMetadata**
  - [ ] Search: `from.*protocols.*import.*EmailMetadata`
  - [ ] Replace with: `from gmail_assistant.core.schemas import Email`

- [ ] **1.5 Update gmail_api_client.py to use schemas.Email**
  ```
  File: src/gmail_assistant/core/fetch/gmail_api_client.py
  Line: 14
  ```
  - [ ] Change: `from ..ai.newsletter_cleaner import EmailData`
  - [ ] To: `from ..schemas import Email as EmailData`

- [ ] **1.6 Run deprecation warning scan**
  - [ ] `python -W default::DeprecationWarning -c "import gmail_assistant"`
  - [ ] Fix all warnings

**Validation Criteria**:
- [ ] No duplicate class definitions
- [ ] All imports use `core.schemas.Email`
- [ ] Deprecation warnings for legacy usage
- [ ] All tests pass

**Acceptance Criteria**:
- [ ] Single source of truth in `schemas.py`
- [ ] Backward compatibility via compat classes
- [ ] Clear deprecation path documented

---

### H-2: Consolidate Exception Hierarchy

**Status**: 🟠 HIGH
**Effort**: 8-16 hours
**Files**: `core/exceptions.py`, various modules
**Dependency**: None

**Current State**:
- `exceptions.py` defines 5 exceptions (correct)
- Other modules may define local exceptions

**Implementation Steps**:

- [ ] **2.1 Search for exception definitions outside core/exceptions.py**
  ```bash
  grep -r "class.*Error.*Exception" src/gmail_assistant --include="*.py" | grep -v exceptions.py
  grep -r "class.*Exception" src/gmail_assistant --include="*.py" | grep -v exceptions.py
  ```

- [ ] **2.2 Add missing exception types to core/exceptions.py**
  - [ ] Add `ValidationError` if needed
  - [ ] Add `ParseError` if needed
  - [ ] Add `BatchAPIError` if needed (move from batch_api.py)
  - [ ] Add `RateLimitError` if needed

- [ ] **2.3 Move BatchAPIError from batch_api.py**
  ```
  File: src/gmail_assistant/core/fetch/batch_api.py
  Lines: 28-34
  ```
  - [ ] Move `BatchAPIError` class to `exceptions.py`
  - [ ] Import in batch_api.py: `from ..exceptions import BatchAPIError`

- [ ] **2.4 Update exceptions.py with complete hierarchy**
  ```python
  __all__ = [
      "GmailAssistantError",
      "ConfigError",
      "AuthError",
      "NetworkError",
      "APIError",
      "BatchAPIError",
      "ValidationError",
      "ParseError",
  ]

  class GmailAssistantError(Exception):
      """Base exception for Gmail Assistant."""
      pass

  class ConfigError(GmailAssistantError):
      """Configuration errors. Exit code: 5"""
      pass

  class AuthError(GmailAssistantError):
      """Authentication errors. Exit code: 3"""
      pass

  class NetworkError(GmailAssistantError):
      """Network errors. Exit code: 4"""
      pass

  class APIError(GmailAssistantError):
      """API errors. Exit code: 1"""
      pass

  class BatchAPIError(APIError):
      """Batch API operation errors."""
      def __init__(self, message: str, failed_ids: list = None):
          self.failed_ids = failed_ids or []
          super().__init__(message)

  class ValidationError(GmailAssistantError):
      """Input validation errors. Exit code: 2"""
      pass

  class ParseError(GmailAssistantError):
      """Parsing errors."""
      pass
  ```

- [ ] **2.5 Update all modules to import from core/exceptions.py**
  - [ ] Search: `class.*Error.*Exception`
  - [ ] Move to exceptions.py or import from there

**Validation Criteria**:
- [ ] Single exceptions.py file defines all exceptions
- [ ] All modules import from exceptions.py
- [ ] Exception hierarchy is logical (inheritance)
- [ ] CLI exit codes documented

**Acceptance Criteria**:
- [ ] No local exception definitions
- [ ] Clear inheritance hierarchy
- [ ] Consistent naming (all end in Error)
- [ ] ADR-0004 compliance

---

### H-3: Fix Bare Exception Handlers

**Status**: 🟠 HIGH
**Effort**: 16-24 hours
**Files**: Multiple (145 occurrences of `except Exception`)
**Dependency**: H-2 (exception hierarchy)

**Current State**: 145 `except Exception` handlers across 41 files

**Implementation Steps**:

- [ ] **3.1 Prioritize parsers directory (most critical)**
  ```
  Files:
  - parsers/gmail_eml_to_markdown_cleaner.py (15 occurrences)
  - parsers/robust_eml_converter.py (10 occurrences)
  - parsers/advanced_email_parser.py (6 occurrences)
  ```
  - [ ] Replace `except Exception` with specific types:
    - `except (ValueError, TypeError)` for parsing
    - `except (IOError, OSError)` for file operations
    - `except KeyError` for dict access
    - `except UnicodeDecodeError` for encoding

- [ ] **3.2 Fix core/fetch modules**
  ```
  Files:
  - core/fetch/gmail_api_client.py (6)
  - core/fetch/incremental.py (4)
  - core/fetch/async_fetcher.py (4)
  - core/fetch/streaming.py (4)
  ```
  - [ ] Replace with: `except (HttpError, NetworkError, TimeoutError)`

- [ ] **3.3 Fix core/auth modules**
  ```
  Files:
  - core/auth/credential_manager.py (7)
  - core/auth/base.py (7)
  ```
  - [ ] Replace with: `except (AuthError, ConfigError, IOError)`

- [ ] **3.4 Fix core/processing modules**
  ```
  Files:
  - core/processing/classifier.py (6)
  - core/processing/plaintext.py (6)
  - core/processing/database.py (2)
  ```
  - [ ] Replace with specific types

- [ ] **3.5 Fix utils modules**
  ```
  Files:
  - utils/cache_manager.py (6)
  - utils/error_handler.py (6)
  - utils/secure_file.py (5)
  - utils/manifest.py (4)
  - utils/memory_manager.py (4)
  ```
  - [ ] Replace with specific types

- [ ] **3.6 For legitimate catch-all handlers, add logging**
  - [ ] Pattern for genuine catch-all:
    ```python
    except Exception as e:
        logger.exception(f"Unexpected error in {context}: {e}")
        raise  # Re-raise after logging
    ```

- [ ] **3.7 Verify no bare `except:` statements**
  ```bash
  grep -r "except:" src/gmail_assistant --include="*.py" | grep -v "except:$"
  ```

**Validation Criteria**:
- [ ] `ruff check --select=E722` passes (no bare except)
- [ ] All handlers catch specific exception types
- [ ] Genuine catch-alls re-raise after logging
- [ ] All tests still pass

**Acceptance Criteria**:
- [ ] <20 `except Exception` handlers (down from 145)
- [ ] All catch-alls properly logged
- [ ] Debugging improved with specific errors
- [ ] Stack traces preserved

---

### H-4: Consolidate Duplicate Analysis Modules

**Status**: 🟠 HIGH
**Effort**: 24-32 hours
**Files**: `analysis/daily_email_analysis.py`, `analysis/daily_email_analyzer.py`, `analysis/email_analyzer.py`
**Dependency**: None

**Current State**:
- `daily_email_analysis.py`: 851 lines
- `daily_email_analyzer.py`: 1316 lines
- `email_analyzer.py`: 851 lines
- Total: 3018 lines with ~70% overlap

**Implementation Steps**:

- [ ] **4.1 Analyze common functionality**
  - [ ] Diff the three files to identify:
    - Common base functionality
    - Unique features per module
    - Naming conflicts

- [ ] **4.2 Create unified EmailAnalyzer with Strategy pattern**
  ```
  File: src/gmail_assistant/analysis/unified_analyzer.py (new)
  ```
  - [ ] Create abstract base:
    ```python
    from abc import ABC, abstractmethod
    from typing import Protocol

    class AnalysisStrategy(Protocol):
        """Strategy for email analysis."""
        def analyze(self, emails: list) -> dict: ...

    class DailyAnalysisStrategy(AnalysisStrategy):
        """Daily email analysis."""
        pass

    class DetailedAnalysisStrategy(AnalysisStrategy):
        """Detailed email analysis."""
        pass

    class EmailAnalyzer:
        """Unified email analyzer with pluggable strategies."""
        def __init__(self, strategy: AnalysisStrategy = None):
            self.strategy = strategy or DailyAnalysisStrategy()

        def set_strategy(self, strategy: AnalysisStrategy):
            self.strategy = strategy

        def analyze(self, emails: list) -> dict:
            return self.strategy.analyze(emails)
    ```

- [ ] **4.3 Extract common code into base classes**
  - [ ] Identify shared methods
  - [ ] Create `BaseEmailAnalysis` class
  - [ ] Move common logic there

- [ ] **4.4 Refactor daily_email_analysis.py**
  - [ ] Keep unique daily summary features
  - [ ] Inherit from unified analyzer
  - [ ] Reduce to ~200 lines

- [ ] **4.5 Refactor email_analyzer.py**
  - [ ] Keep unique detailed analysis features
  - [ ] Inherit from unified analyzer
  - [ ] Reduce to ~200 lines

- [ ] **4.6 Deprecate daily_email_analyzer.py**
  - [ ] Add deprecation warning
  - [ ] Forward to unified_analyzer.py
  - [ ] Plan removal in v2.2.0

- [ ] **4.7 Update imports across codebase**
  - [ ] Search for analysis module imports
  - [ ] Update to use unified_analyzer

- [ ] **4.8 Update __init__.py exports**
  ```
  File: src/gmail_assistant/analysis/__init__.py
  ```
  - [ ] Export unified analyzer
  - [ ] Maintain backward compatibility aliases

**Validation Criteria**:
- [ ] Total lines reduced from 3018 to <1000
- [ ] All existing functionality preserved
- [ ] Strategy pattern working
- [ ] All tests pass

**Acceptance Criteria**:
- [ ] Single unified analyzer
- [ ] ~70% code reduction
- [ ] Clear strategy pattern
- [ ] Backward compatible imports

---

## Phase 3: Architecture Debt

### M-1: Refactor GmailFetcher God Object

**Status**: 🟡 MEDIUM
**Effort**: 32-40 hours
**Files**: `core/fetch/gmail_assistant.py`
**Dependency**: C-1, C-2, C-3

**Current State**: GmailFetcher has 18+ responsibilities

**Implementation Steps**:

- [ ] **1.1 Identify responsibilities in GmailFetcher**
  - [ ] Authentication (→ move to auth module)
  - [ ] Search (→ keep)
  - [ ] Fetch (→ keep)
  - [ ] Save EML (→ move to output plugin)
  - [ ] Convert to Markdown (→ move to output plugin)
  - [ ] Progress tracking (→ move to utils)
  - [ ] Memory management (→ keep reference, delegate)

- [ ] **1.2 Extract AuthenticationService**
  - [ ] Already exists: `auth/base.py`, `auth/credential_manager.py`
  - [ ] Ensure GmailFetcher delegates properly

- [ ] **1.3 Create OutputPluginManager**
  ```
  File: src/gmail_assistant/core/output/plugin_manager.py (new)
  ```
  - [ ] Implement `OutputPluginProtocol` from protocols.py
  - [ ] Create EMLOutputPlugin
  - [ ] Create MarkdownOutputPlugin
  - [ ] Create JSONOutputPlugin

- [ ] **1.4 Reduce GmailFetcher to core responsibilities**
  - [ ] Authentication delegation
  - [ ] Search messages
  - [ ] Fetch messages
  - [ ] Coordinate with output plugins
  - [ ] Target: <300 lines

- [ ] **1.5 Update CLI to use new structure**
  - [ ] Inject output plugins via DI container

**Validation Criteria**:
- [ ] GmailFetcher <300 lines
- [ ] Single Responsibility per class
- [ ] All tests pass
- [ ] CLI works unchanged

---

### M-5: Integrate Async Fetcher into CLI

**Status**: 🟡 MEDIUM
**Effort**: 8-16 hours
**Files**: `core/fetch/async_fetcher.py`, `cli/commands/fetch.py`
**Dependency**: C-2 (CLI implementation)

**Implementation Steps**:

- [ ] **5.1 Add --async flag to fetch command**
  ```
  File: src/gmail_assistant/cli/main.py
  ```
  - [ ] Add option: `@click.option("--async", "use_async", is_flag=True)`

- [ ] **5.2 Import async fetcher in CLI**
  ```
  File: src/gmail_assistant/cli/commands/fetch.py
  ```
  - [ ] Add: `from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher`

- [ ] **5.3 Implement async fetch path**
  - [ ] When `use_async=True`, use `AsyncGmailFetcher`
  - [ ] Run with `asyncio.run()`

- [ ] **5.4 Add concurrency option**
  - [ ] Add: `@click.option("--concurrency", type=int, default=10)`
  - [ ] Pass to async fetcher

**Validation Criteria**:
- [ ] `gmail-assistant fetch --async --query "is:unread"` works
- [ ] Async 2-3x faster than sync for large fetches
- [ ] Error handling works in async mode

---

### M-9: Complete Repository Pattern

**Status**: 🟡 MEDIUM
**Effort**: 8-16 hours
**Files**: `core/processing/database.py`, `core/protocols.py`
**Dependency**: None

**Implementation Steps**:

- [ ] **9.1 Add EmailRepositoryProtocol to protocols.py**
  ```python
  @runtime_checkable
  class EmailRepositoryProtocol(Protocol):
      """Protocol for email storage."""

      def save(self, email: EmailMetadata) -> bool: ...
      def get(self, email_id: str) -> Optional[EmailMetadata]: ...
      def find(self, query: str) -> List[EmailMetadata]: ...
      def delete(self, email_id: str) -> bool: ...
      def count(self) -> int: ...
  ```

- [ ] **9.2 Implement protocol in database.py**
  - [ ] Ensure DatabaseManager implements EmailRepositoryProtocol
  - [ ] Add missing methods

- [ ] **9.3 Register in DI container**
  ```
  File: src/gmail_assistant/core/container.py
  ```
  - [ ] Register EmailRepositoryProtocol → DatabaseManager

---

## Phase 4: Security Hardening

### L-7: Create SECURITY.md

**Status**: 🟢 LOW
**Effort**: 2-4 hours
**Files**: `SECURITY.md` (new, root directory)
**Dependency**: None

- [ ] **7.1 Create SECURITY.md with:**
  - [ ] Security contact information
  - [ ] Vulnerability disclosure policy
  - [ ] Supported versions
  - [ ] Security features summary

### L-4: Pin Transitive Dependencies

**Status**: 🟢 LOW
**Effort**: 2-4 hours
**Files**: `requirements.lock` (new), `pyproject.toml`
**Dependency**: None

- [ ] **4.1 Generate requirements.lock**
  ```bash
  pip freeze > requirements.lock
  ```

- [ ] **4.2 Add to CI/CD to verify lock file matches**

### L-2: Universal SecureLogger Adoption

**Status**: 🟢 LOW
**Effort**: 8-16 hours
**Files**: All modules using `logging.getLogger`
**Dependency**: None

- [ ] **2.1 Identify modules not using SecureLogger**
  ```bash
  grep -l "logging.getLogger" src/gmail_assistant --include="*.py"
  ```

- [ ] **2.2 Replace with SecureLogger**
  ```python
  # Before
  import logging
  logger = logging.getLogger(__name__)

  # After
  from gmail_assistant.utils.secure_logger import SecureLogger
  logger = SecureLogger(__name__)
  ```

---

## Final Validation Checklist

### Pre-Release Verification

**Critical (C-1, C-2, C-3)**:
- [ ] Batch API integration working (C-1)
  - Command: `python -c "from gmail_assistant.core.fetch.batch_api import GmailBatchClient; print('OK')"`
- [ ] CLI commands functional (C-2)
  - Command: `gmail-assistant fetch --help` (shows usage, not stub message)
  - Command: `gmail-assistant delete --help` (shows usage, not stub message)
  - Command: `gmail-assistant analyze --help` (shows usage, not stub message)
  - Command: `gmail-assistant auth --help` (shows usage, not stub message)
- [ ] Checkpoint/resume working (C-3)
  - Command: `ls data/checkpoints/` shows checkpoint files after fetch

**High (H-1, H-2, H-3, H-4)**:
- [ ] Single Email schema (H-1)
  - Command: `python -c "from gmail_assistant.core.schemas import Email; print('OK')"`
  - No deprecation warnings in normal usage
- [ ] Exception hierarchy consolidated (H-2)
  - Command: `grep -r "class.*Error.*Exception" src | wc -l` = 1 file
- [ ] Bare exceptions fixed (H-3)
  - Command: `ruff check --select=E722 src/` passes
  - `except Exception` count < 20
- [ ] Analysis modules consolidated (H-4)
  - Command: `wc -l src/gmail_assistant/analysis/*.py` total < 1500 lines

### Test Suite

- [ ] **Unit tests pass**:
  ```bash
  pytest tests/unit/ -v
  ```

- [ ] **Integration tests pass**:
  ```bash
  pytest tests/integration/ -v
  ```

- [ ] **Security tests pass**:
  ```bash
  pytest tests/security/ -v
  ```

- [ ] **Coverage maintained**:
  ```bash
  pytest tests/ --cov=gmail_assistant --cov-report=term-missing
  # Coverage should be ≥90%
  ```

### Code Quality

- [ ] **Linting passes**:
  ```bash
  ruff check src/
  ```

- [ ] **Type checking passes**:
  ```bash
  mypy src/gmail_assistant
  ```

- [ ] **No TODO/FIXME in critical paths**:
  ```bash
  grep -r "TODO\|FIXME" src/gmail_assistant/core src/gmail_assistant/cli | wc -l
  # Should be 0 or documented exceptions
  ```

### Documentation

- [ ] `CLAUDE.md` updated with v2.1.0 status
- [ ] `README.md` CLI examples work
- [ ] SECURITY.md exists
- [ ] API documentation generated

### Performance

- [ ] Batch fetch 100 emails < 15 seconds (was ~90s sequential)
- [ ] Memory usage stable during large fetches
- [ ] Checkpoint files < 10KB each

---

## Task Dependency Graph

```
C-1 (Batch API) ─────────┐
                         ├──→ C-2 (CLI Commands)
C-3 (Checkpoint) ────────┘

H-2 (Exceptions) ───────→ H-3 (Bare Handlers)

H-1 (Schemas) ──────────→ (independent)

H-4 (Analysis) ─────────→ (independent)

M-1 (God Object) ───────→ M-5 (Async CLI) ───→ M-9 (Repository)

L-* (Security) ─────────→ (can run in parallel)
```

## Parallel Execution Opportunities

**Can run in parallel**:
- C-1 + C-3 (independent)
- H-1 + H-4 (independent)
- All L-* tasks
- H-2 + H-1

**Must be sequential**:
- C-1 → C-2 (CLI needs batch API)
- H-2 → H-3 (need hierarchy before fixing handlers)
- M-1 → M-5 → M-9 (architectural dependencies)

---

*End of Remediation Action Plan*
