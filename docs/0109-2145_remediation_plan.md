# Gmail Assistant Data Architecture Remediation Plan

**Document ID**: 0109-2145_remediation_plan.md
**Created**: 2026-01-09 21:45
**Project**: Gmail Assistant
**Version**: 1.0

---

## Executive Summary

This remediation plan addresses critical data architecture issues identified in the Gmail Assistant project, including duplicate data structures, missing batch API usage, lack of checkpoint/resume capability, and database denormalization. The plan is structured in 4 phases over an estimated 6-8 weeks.

**Key Metrics**:
- Estimated effort: 120-160 hours
- Risk level: Medium (incremental changes with rollback capability)
- Performance improvement potential: 80-90% latency reduction with batch API
- Data integrity improvement: Full normalization and idempotent operations

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Phase 1: Foundation (Week 1-2)](#phase-1-foundation-week-1-2)
3. [Phase 2: Core Infrastructure (Week 3-4)](#phase-2-core-infrastructure-week-3-4)
4. [Phase 3: Advanced Features (Week 5-6)](#phase-3-advanced-features-week-5-6)
5. [Phase 4: Optimization & Observability (Week 7-8)](#phase-4-optimization--observability-week-7-8)
6. [Risk Mitigation](#risk-mitigation)
7. [Testing Strategy](#testing-strategy)
8. [Rollback Procedures](#rollback-procedures)

---

## Current State Analysis

### Issue 1: Duplicate Email Data Structures

**Location**:
- `src/gmail_assistant/core/protocols.py` (lines 43-55): `EmailMetadata` dataclass
- `src/gmail_assistant/core/ai/newsletter_cleaner.py` (lines 21-29): `EmailData` dataclass

**Impact**: Code duplication, inconsistent field naming, maintenance burden

**Current Structures**:
```python
# protocols.py - EmailMetadata
@dataclass
class EmailMetadata:
    id: str
    thread_id: str
    subject: str
    sender: str
    recipients: List[str]
    date: str
    labels: List[str]
    snippet: str = ""
    size_estimate: int = 0

# newsletter_cleaner.py - EmailData
@dataclass
class EmailData:
    id: str
    subject: str
    sender: str
    date: str
    labels: List[str] = None
    thread_id: str = None
    body_snippet: str = ""
```

### Issue 2: No Gmail Batch API Usage

**Location**: `src/gmail_assistant/core/fetch/gmail_api_client.py` (lines 95-124)

**Current Implementation**: Sequential API calls in `_fetch_email_batch()` method
```python
for msg_id in message_ids:
    message = self.service.users().messages().get(...)  # Sequential!
```

**Impact**: Up to 90% performance loss on bulk operations

### Issue 3: No Checkpoint/Resume for Incremental Sync

**Location**: `src/gmail_assistant/core/fetch/incremental.py`

**Missing Features**:
- No state persistence between runs
- No failure recovery mechanism
- No progress tracking that survives interruption

### Issue 4: Database Denormalization

**Location**: `src/gmail_assistant/core/processing/database.py` (lines 41-63)

**Current Schema Issues**:
- `labels TEXT` - comma-separated string
- `recipient TEXT` - single recipient only
- `sender TEXT` - no domain extraction
- No proper foreign key relationships

---

## Phase 1: Foundation (Week 1-2)

### Task 1.1: Create Unified Email Schema with Pydantic

**Effort**: 8 hours
**Priority**: Critical
**Dependencies**: None

**Implementation Steps**:

1. Create new file: `src/gmail_assistant/core/schemas.py`

```python
"""
Canonical email data models using Pydantic for validation.
Single source of truth for all email data structures.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ParticipantType(str, Enum):
    FROM = "from"
    TO = "to"
    CC = "cc"
    BCC = "bcc"

class EmailParticipant(BaseModel):
    """Email participant with type and parsed domain."""
    address: EmailStr
    type: ParticipantType
    display_name: Optional[str] = None

    @property
    def domain(self) -> str:
        return self.address.split("@")[1] if "@" in self.address else ""

class Email(BaseModel):
    """
    Canonical email model - single source of truth.
    Replaces: EmailMetadata (protocols.py), EmailData (newsletter_cleaner.py)
    """
    gmail_id: str = Field(..., description="Unique Gmail message ID")
    thread_id: str = Field(..., description="Gmail thread ID")
    subject: str = Field(default="", description="Email subject line")
    sender: EmailStr = Field(..., description="Sender email address")
    recipients: List[EmailParticipant] = Field(default_factory=list)
    date: datetime = Field(..., description="Email received timestamp")
    body_plain: Optional[str] = Field(default=None, description="Plain text body")
    body_html: Optional[str] = Field(default=None, description="HTML body")
    labels: List[str] = Field(default_factory=list, description="Gmail labels")
    snippet: str = Field(default="", description="Email preview snippet")
    history_id: int = Field(default=0, description="Gmail history ID for sync")
    size_estimate: int = Field(default=0, description="Estimated size in bytes")

    # Metadata
    is_unread: bool = Field(default=True)
    is_starred: bool = Field(default=False)
    has_attachments: bool = Field(default=False)

    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            # Handle multiple date formats from Gmail
            for fmt in [
                '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S',
            ]:
                try:
                    return datetime.strptime(v.split(' (')[0].strip(), fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {v}")
        return v

    @property
    def sender_domain(self) -> str:
        return self.sender.split("@")[1] if "@" in self.sender else ""

    def to_email_metadata(self) -> 'EmailMetadata':
        """Convert to legacy EmailMetadata for backward compatibility."""
        from .protocols import EmailMetadata
        return EmailMetadata(
            id=self.gmail_id,
            thread_id=self.thread_id,
            subject=self.subject,
            sender=self.sender,
            recipients=[p.address for p in self.recipients if p.type == ParticipantType.TO],
            date=self.date.isoformat(),
            labels=self.labels,
            snippet=self.snippet,
            size_estimate=self.size_estimate
        )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmailBatch(BaseModel):
    """Batch of emails for bulk operations."""
    emails: List[Email]
    total_count: int
    next_page_token: Optional[str] = None
    history_id: Optional[int] = None
```

2. Update imports across the codebase (adapter pattern for backward compatibility)

3. Add deprecation warnings to old classes

**Validation Criteria**:
- [ ] All existing tests pass with new schema
- [ ] Pydantic validation catches invalid email formats
- [ ] Backward compatibility maintained via adapter methods
- [ ] Type hints work correctly in IDE

**Files to Modify**:
- Create: `src/gmail_assistant/core/schemas.py`
- Update: `src/gmail_assistant/core/__init__.py`
- Update: `src/gmail_assistant/core/ai/newsletter_cleaner.py` (add deprecation)
- Update: `src/gmail_assistant/core/protocols.py` (add deprecation)

---

### Task 1.2: Add Config Schema Validation

**Effort**: 4 hours
**Priority**: Medium
**Dependencies**: Task 1.1

**Implementation Steps**:

1. Create Pydantic models for all config files:

```python
# src/gmail_assistant/core/config_schemas.py

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
from pathlib import Path

class AIKeywordsConfig(BaseModel):
    """Configuration for AI newsletter detection."""
    ai_keywords: List[str] = Field(default_factory=list)
    ai_newsletter_domains: List[str] = Field(default_factory=list)
    newsletter_patterns: List[str] = Field(default_factory=list)
    unsubscribe_patterns: List[str] = Field(default_factory=list)
    confidence_weights: Dict[str, int] = Field(default_factory=dict)
    decision_threshold: Dict[str, int] = Field(default_factory=dict)

    @field_validator('confidence_weights')
    @classmethod
    def validate_weights(cls, v):
        required = {'ai_keywords_subject', 'ai_keywords_sender', 'known_domain'}
        if not required.issubset(v.keys()):
            raise ValueError(f"Missing required weights: {required - v.keys()}")
        return v

class GmailAssistantConfig(BaseModel):
    """Main application configuration."""
    default_max_emails: int = Field(default=100, ge=1, le=10000)
    default_format: str = Field(default="both")
    default_organize_by: str = Field(default="date")
    output_directory: str = Field(default="gmail_backup")
    predefined_queries: Dict[str, str] = Field(default_factory=dict)

    @field_validator('default_format')
    @classmethod
    def validate_format(cls, v):
        valid = {'eml', 'markdown', 'both'}
        if v not in valid:
            raise ValueError(f"Format must be one of {valid}")
        return v

class DeletionConfig(BaseModel):
    """Deletion operation configuration."""
    require_confirmation: bool = Field(default=True)
    default_dry_run: bool = Field(default=True)
    batch_size: int = Field(default=100, ge=1, le=1000)
    rate_limit_delay: float = Field(default=0.1, ge=0)


def load_validated_config(path: Path, model: type[BaseModel]) -> BaseModel:
    """Load and validate a config file against its schema."""
    import json
    with open(path) as f:
        data = json.load(f)
    return model.model_validate(data)
```

2. Add validation on config load

3. Generate JSON Schema files for documentation

**Validation Criteria**:
- [ ] All existing config files pass validation
- [ ] Invalid configs raise clear error messages
- [ ] JSON Schema generated for each config type

---

### Task 1.3: Implement Idempotent Writes via Message ID

**Effort**: 6 hours
**Priority**: High
**Dependencies**: None

**Implementation Steps**:

1. Add unique constraint on `gmail_id` in database schema:

```sql
-- Migration: 001_add_gmail_id_unique.sql
ALTER TABLE emails ADD CONSTRAINT IF NOT EXISTS emails_gmail_id_unique UNIQUE (gmail_id);

-- Add upsert support
CREATE INDEX IF NOT EXISTS idx_emails_gmail_id_hash ON emails(gmail_id);
```

2. Implement upsert method in database.py:

```python
def upsert_email(self, email: Email) -> Tuple[bool, str]:
    """
    Insert or update email by gmail_id (idempotent).

    Returns:
        Tuple of (was_inserted: bool, action: str)
    """
    try:
        # Check if exists
        existing = self.conn.execute(
            "SELECT id, updated_at FROM emails WHERE gmail_id = ?",
            (email.gmail_id,)
        ).fetchone()

        if existing:
            # Update existing record
            self.conn.execute("""
                UPDATE emails SET
                    subject = ?, sender = ?, parsed_date = ?,
                    labels = ?, message_content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE gmail_id = ?
            """, (email.subject, email.sender, email.date.isoformat(),
                  ','.join(email.labels), email.body_plain, email.gmail_id))
            self.conn.commit()
            return (False, 'updated')
        else:
            # Insert new record
            self.conn.execute("""
                INSERT INTO emails (gmail_id, thread_id, subject, sender, ...)
                VALUES (?, ?, ?, ?, ...)
            """, (...))
            self.conn.commit()
            return (True, 'inserted')

    except sqlite3.IntegrityError as e:
        # Handle race condition with concurrent inserts
        logger.warning(f"Concurrent insert detected for {email.gmail_id}: {e}")
        return (False, 'skipped')
```

3. Add batch upsert for efficiency:

```python
def upsert_emails_batch(self, emails: List[Email]) -> Dict[str, int]:
    """Batch upsert with transaction."""
    stats = {'inserted': 0, 'updated': 0, 'skipped': 0}

    with self.conn:  # Transaction context
        for email in emails:
            was_inserted, action = self.upsert_email(email)
            stats[action if action in stats else 'skipped'] += 1

    return stats
```

**Validation Criteria**:
- [ ] Duplicate inserts are handled gracefully
- [ ] Updates preserve original insert timestamp
- [ ] Batch operations are atomic (all or nothing)
- [ ] Concurrent access is handled safely

---

## Phase 2: Core Infrastructure (Week 3-4)

### Task 2.1: Implement Gmail Batch API

**Effort**: 16 hours
**Priority**: Critical
**Dependencies**: Task 1.1

**Implementation Steps**:

1. Create new batch API module: `src/gmail_assistant/core/fetch/batch_api.py`

```python
"""
Gmail Batch API implementation for high-performance bulk operations.
Reduces API latency by 80-90% compared to sequential calls.
"""

import logging
from typing import List, Dict, Callable, Optional, Any
from googleapiclient.http import BatchHttpRequest
from googleapiclient.errors import HttpError
from ..schemas import Email, EmailBatch
from ...utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class BatchAPIError(Exception):
    """Batch API operation error."""
    def __init__(self, message: str, failed_ids: List[str]):
        self.message = message
        self.failed_ids = failed_ids
        super().__init__(message)


class GmailBatchClient:
    """
    Gmail Batch API client for efficient bulk operations.

    The Gmail API supports batching up to 100 requests per batch call,
    significantly reducing HTTP overhead and latency.

    Usage:
        client = GmailBatchClient(service)
        emails = client.batch_get_messages(message_ids)
    """

    MAX_BATCH_SIZE = 100  # Gmail API limit

    def __init__(self, service, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize batch client.

        Args:
            service: Authenticated Gmail API service
            rate_limiter: Optional rate limiter for quota management
        """
        self.service = service
        self.rate_limiter = rate_limiter
        self._results: Dict[str, Any] = {}
        self._errors: Dict[str, Exception] = {}

    def batch_get_messages(
        self,
        message_ids: List[str],
        format: str = 'metadata',
        metadata_headers: Optional[List[str]] = None,
        callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Email]:
        """
        Fetch multiple messages in batched requests.

        Args:
            message_ids: List of Gmail message IDs
            format: Message format ('minimal', 'metadata', 'full', 'raw')
            metadata_headers: Headers to include when format='metadata'
            callback: Progress callback(current, total)

        Returns:
            List of Email objects
        """
        if metadata_headers is None:
            metadata_headers = ['From', 'To', 'Subject', 'Date', 'Cc', 'Bcc']

        emails = []
        total = len(message_ids)

        # Process in batches of MAX_BATCH_SIZE
        for i in range(0, total, self.MAX_BATCH_SIZE):
            batch_ids = message_ids[i:i + self.MAX_BATCH_SIZE]

            # Rate limiting
            if self.rate_limiter:
                self.rate_limiter.wait_if_needed(len(batch_ids))

            # Create batch request
            batch = self.service.new_batch_http_request()
            self._results.clear()
            self._errors.clear()

            for msg_id in batch_ids:
                request = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format=format,
                    metadataHeaders=metadata_headers
                )
                batch.add(request, callback=self._create_callback(msg_id))

            # Execute batch
            try:
                batch.execute()
            except HttpError as e:
                logger.error(f"Batch request failed: {e}")
                raise BatchAPIError(str(e), batch_ids)

            # Process results
            for msg_id in batch_ids:
                if msg_id in self._results:
                    email = self._parse_message(self._results[msg_id])
                    if email:
                        emails.append(email)
                elif msg_id in self._errors:
                    logger.warning(f"Failed to fetch {msg_id}: {self._errors[msg_id]}")

            # Progress callback
            if callback:
                callback(min(i + self.MAX_BATCH_SIZE, total), total)

        return emails

    def _create_callback(self, msg_id: str) -> Callable:
        """Create callback for batch request."""
        def callback(request_id, response, exception):
            if exception:
                self._errors[msg_id] = exception
            else:
                self._results[msg_id] = response
        return callback

    def _parse_message(self, message: Dict) -> Optional[Email]:
        """Parse Gmail API message to Email model."""
        try:
            headers = {h['name']: h['value']
                      for h in message.get('payload', {}).get('headers', [])}

            return Email(
                gmail_id=message['id'],
                thread_id=message.get('threadId', ''),
                subject=headers.get('Subject', ''),
                sender=headers.get('From', '').split('<')[-1].rstrip('>').strip(),
                date=headers.get('Date', ''),
                labels=message.get('labelIds', []),
                snippet=message.get('snippet', ''),
                history_id=int(message.get('historyId', 0)),
                size_estimate=message.get('sizeEstimate', 0),
                is_unread='UNREAD' in message.get('labelIds', []),
                is_starred='STARRED' in message.get('labelIds', [])
            )
        except Exception as e:
            logger.error(f"Failed to parse message {message.get('id')}: {e}")
            return None

    def batch_delete_messages(
        self,
        message_ids: List[str],
        callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, int]:
        """
        Delete multiple messages in batched requests.

        Args:
            message_ids: List of message IDs to delete
            callback: Progress callback(current, total)

        Returns:
            Dict with 'deleted' and 'failed' counts
        """
        stats = {'deleted': 0, 'failed': 0}
        total = len(message_ids)

        for i in range(0, total, self.MAX_BATCH_SIZE):
            batch_ids = message_ids[i:i + self.MAX_BATCH_SIZE]

            if self.rate_limiter:
                self.rate_limiter.wait_if_needed(len(batch_ids))

            batch = self.service.new_batch_http_request()
            self._errors.clear()

            for msg_id in batch_ids:
                request = self.service.users().messages().delete(
                    userId='me', id=msg_id
                )
                batch.add(request, callback=self._create_delete_callback(msg_id, stats))

            try:
                batch.execute()
            except HttpError as e:
                logger.error(f"Batch delete failed: {e}")
                stats['failed'] += len(batch_ids)
                continue

            if callback:
                callback(min(i + self.MAX_BATCH_SIZE, total), total)

        return stats

    def _create_delete_callback(self, msg_id: str, stats: Dict) -> Callable:
        """Create callback for delete request."""
        def callback(request_id, response, exception):
            if exception:
                self._errors[msg_id] = exception
                stats['failed'] += 1
            else:
                stats['deleted'] += 1
        return callback

    def batch_modify_labels(
        self,
        message_ids: List[str],
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Modify labels on multiple messages in batch.

        Args:
            message_ids: List of message IDs
            add_labels: Labels to add
            remove_labels: Labels to remove

        Returns:
            Dict with 'modified' and 'failed' counts
        """
        stats = {'modified': 0, 'failed': 0}
        body = {
            'addLabelIds': add_labels or [],
            'removeLabelIds': remove_labels or []
        }

        for i in range(0, len(message_ids), self.MAX_BATCH_SIZE):
            batch_ids = message_ids[i:i + self.MAX_BATCH_SIZE]

            batch = self.service.new_batch_http_request()

            for msg_id in batch_ids:
                request = self.service.users().messages().modify(
                    userId='me', id=msg_id, body=body
                )
                batch.add(request, callback=self._create_modify_callback(msg_id, stats))

            try:
                batch.execute()
            except HttpError as e:
                logger.error(f"Batch modify failed: {e}")
                stats['failed'] += len(batch_ids)

        return stats

    def _create_modify_callback(self, msg_id: str, stats: Dict) -> Callable:
        """Create callback for modify request."""
        def callback(request_id, response, exception):
            if exception:
                stats['failed'] += 1
            else:
                stats['modified'] += 1
        return callback
```

2. Update `gmail_api_client.py` to use batch client:

```python
# In GmailAPIClient class

def __init__(self, credentials_path: str = 'credentials.json'):
    # ... existing init ...
    self.batch_client = None

def _init_batch_client(self):
    """Initialize batch client after authentication."""
    if self.service and not self.batch_client:
        from .batch_api import GmailBatchClient
        self.batch_client = GmailBatchClient(
            self.service,
            rate_limiter=self._rate_limiter  # If using rate limiter
        )

def _fetch_email_batch(self, message_ids: List[Dict]) -> List[EmailData]:
    """Fetch emails using batch API (replaces sequential implementation)."""
    if not self.batch_client:
        self._init_batch_client()

    ids = [m['id'] for m in message_ids]
    emails = self.batch_client.batch_get_messages(
        ids,
        format='metadata',
        metadata_headers=['From', 'Subject', 'Date']
    )

    # Convert to legacy EmailData format for backward compatibility
    return [self._email_to_email_data(e) for e in emails]

def _email_to_email_data(self, email: Email) -> EmailData:
    """Convert new Email model to legacy EmailData."""
    return EmailData(
        id=email.gmail_id,
        subject=email.subject,
        sender=email.sender,
        date=email.date.strftime('%a, %d %b %Y %H:%M:%S %z'),
        thread_id=email.thread_id,
        labels=email.labels,
        body_snippet=email.snippet
    )
```

**Validation Criteria**:
- [ ] Batch operations complete 80%+ faster than sequential
- [ ] Partial failures are handled gracefully
- [ ] Rate limiting is respected
- [ ] All existing tests pass
- [ ] New tests cover batch edge cases (empty list, errors, partial success)

**Testing Requirements**:
```python
# tests/test_batch_api.py

def test_batch_get_messages_performance():
    """Verify batch API is faster than sequential."""
    # Implementation

def test_batch_handles_partial_failure():
    """Verify graceful handling when some messages fail."""
    # Implementation

def test_batch_respects_rate_limits():
    """Verify rate limiter integration."""
    # Implementation
```

---

### Task 2.2: Add Checkpoint Persistence for Incremental Sync

**Effort**: 12 hours
**Priority**: High
**Dependencies**: Task 1.3

**Implementation Steps**:

1. Create checkpoint manager: `src/gmail_assistant/core/fetch/checkpoint.py`

```python
"""
Checkpoint persistence for incremental sync operations.
Enables resume capability after interruptions.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from enum import Enum

logger = logging.getLogger(__name__)


class SyncState(str, Enum):
    """Sync operation states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass
class SyncCheckpoint:
    """
    Checkpoint data for sync operations.

    Persists:
    - Current sync progress
    - Last successful message ID
    - Gmail history ID for incremental sync
    - Retry information for failed items
    """
    sync_id: str
    state: SyncState
    started_at: datetime
    updated_at: datetime

    # Progress tracking
    total_messages: int = 0
    processed_messages: int = 0
    failed_messages: int = 0

    # Resume information
    last_message_id: Optional[str] = None
    last_page_token: Optional[str] = None
    history_id: Optional[int] = None

    # Query context
    query: str = ""
    output_directory: str = ""

    # Failed items for retry
    failed_ids: List[str] = field(default_factory=list)

    # Metadata
    error_message: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        if self.total_messages == 0:
            return 0.0
        return (self.processed_messages / self.total_messages) * 100

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['state'] = self.state.value
        data['started_at'] = self.started_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncCheckpoint':
        data['state'] = SyncState(data['state'])
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class CheckpointManager:
    """
    Manages sync checkpoints for failure recovery.

    Features:
    - Atomic writes (write to temp, then rename)
    - Automatic cleanup of old checkpoints
    - Multiple concurrent syncs support
    """

    DEFAULT_DIR = Path("data/checkpoints")
    MAX_CHECKPOINTS = 10  # Keep last N checkpoints

    def __init__(self, checkpoint_dir: Optional[Path] = None):
        self.checkpoint_dir = checkpoint_dir or self.DEFAULT_DIR
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self,
        query: str,
        output_directory: str,
        total_messages: int = 0
    ) -> SyncCheckpoint:
        """Create new sync checkpoint."""
        now = datetime.now()
        sync_id = f"sync_{now.strftime('%Y%m%d_%H%M%S')}_{hash(query) % 10000:04d}"

        checkpoint = SyncCheckpoint(
            sync_id=sync_id,
            state=SyncState.PENDING,
            started_at=now,
            updated_at=now,
            query=query,
            output_directory=output_directory,
            total_messages=total_messages
        )

        self.save_checkpoint(checkpoint)
        logger.info(f"Created checkpoint: {sync_id}")
        return checkpoint

    def save_checkpoint(self, checkpoint: SyncCheckpoint) -> None:
        """Save checkpoint atomically."""
        checkpoint.updated_at = datetime.now()
        filepath = self.checkpoint_dir / f"{checkpoint.sync_id}.json"
        temp_filepath = filepath.with_suffix('.tmp')

        try:
            # Write to temp file first
            with open(temp_filepath, 'w') as f:
                json.dump(checkpoint.to_dict(), f, indent=2)

            # Atomic rename
            temp_filepath.rename(filepath)
            logger.debug(f"Saved checkpoint: {checkpoint.sync_id}")

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            if temp_filepath.exists():
                temp_filepath.unlink()
            raise

    def load_checkpoint(self, sync_id: str) -> Optional[SyncCheckpoint]:
        """Load checkpoint by ID."""
        filepath = self.checkpoint_dir / f"{sync_id}.json"

        if not filepath.exists():
            return None

        try:
            with open(filepath) as f:
                data = json.load(f)
            return SyncCheckpoint.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load checkpoint {sync_id}: {e}")
            return None

    def get_latest_checkpoint(self, query: Optional[str] = None) -> Optional[SyncCheckpoint]:
        """Get most recent checkpoint, optionally filtered by query."""
        checkpoints = self.list_checkpoints()

        if query:
            checkpoints = [c for c in checkpoints if c.query == query]

        # Filter for resumable states
        resumable = [c for c in checkpoints
                    if c.state in (SyncState.IN_PROGRESS, SyncState.INTERRUPTED)]

        if resumable:
            return max(resumable, key=lambda c: c.updated_at)
        return None

    def list_checkpoints(self) -> List[SyncCheckpoint]:
        """List all checkpoints."""
        checkpoints = []
        for filepath in self.checkpoint_dir.glob("sync_*.json"):
            checkpoint = self.load_checkpoint(filepath.stem)
            if checkpoint:
                checkpoints.append(checkpoint)
        return sorted(checkpoints, key=lambda c: c.updated_at, reverse=True)

    def update_progress(
        self,
        checkpoint: SyncCheckpoint,
        processed: int,
        last_message_id: Optional[str] = None,
        last_page_token: Optional[str] = None
    ) -> None:
        """Update checkpoint progress."""
        checkpoint.processed_messages = processed
        checkpoint.state = SyncState.IN_PROGRESS

        if last_message_id:
            checkpoint.last_message_id = last_message_id
        if last_page_token:
            checkpoint.last_page_token = last_page_token

        self.save_checkpoint(checkpoint)

    def mark_completed(self, checkpoint: SyncCheckpoint, history_id: int) -> None:
        """Mark sync as completed."""
        checkpoint.state = SyncState.COMPLETED
        checkpoint.history_id = history_id
        self.save_checkpoint(checkpoint)
        logger.info(f"Sync completed: {checkpoint.sync_id}")

    def mark_failed(self, checkpoint: SyncCheckpoint, error: str, failed_ids: List[str] = None) -> None:
        """Mark sync as failed."""
        checkpoint.state = SyncState.FAILED
        checkpoint.error_message = error
        if failed_ids:
            checkpoint.failed_ids.extend(failed_ids)
        self.save_checkpoint(checkpoint)
        logger.error(f"Sync failed: {checkpoint.sync_id} - {error}")

    def mark_interrupted(self, checkpoint: SyncCheckpoint) -> None:
        """Mark sync as interrupted (for graceful shutdown)."""
        checkpoint.state = SyncState.INTERRUPTED
        self.save_checkpoint(checkpoint)
        logger.warning(f"Sync interrupted: {checkpoint.sync_id}")

    def cleanup_old_checkpoints(self) -> int:
        """Remove old checkpoints beyond MAX_CHECKPOINTS."""
        checkpoints = self.list_checkpoints()

        # Keep completed checkpoints separately
        completed = [c for c in checkpoints if c.state == SyncState.COMPLETED]
        others = [c for c in checkpoints if c.state != SyncState.COMPLETED]

        removed = 0

        # Remove old completed checkpoints
        for checkpoint in completed[self.MAX_CHECKPOINTS:]:
            filepath = self.checkpoint_dir / f"{checkpoint.sync_id}.json"
            filepath.unlink()
            removed += 1

        # Remove old failed/other checkpoints
        for checkpoint in others[self.MAX_CHECKPOINTS:]:
            filepath = self.checkpoint_dir / f"{checkpoint.sync_id}.json"
            filepath.unlink()
            removed += 1

        if removed:
            logger.info(f"Cleaned up {removed} old checkpoints")
        return removed

    def get_resume_info(self, checkpoint: SyncCheckpoint) -> Dict[str, Any]:
        """Get information needed to resume a sync."""
        return {
            'sync_id': checkpoint.sync_id,
            'query': checkpoint.query,
            'output_directory': checkpoint.output_directory,
            'skip_count': checkpoint.processed_messages,
            'last_page_token': checkpoint.last_page_token,
            'failed_ids': checkpoint.failed_ids,
            'history_id': checkpoint.history_id
        }
```

2. Integrate with incremental fetcher:

```python
# Update src/gmail_assistant/core/fetch/incremental.py

from .checkpoint import CheckpointManager, SyncCheckpoint, SyncState

class IncrementalGmailFetcher:
    def __init__(self, db_path: str = "data/databases/emails_final.db"):
        self.db_path = Path(db_path)
        self.fetcher = None
        self.checkpoint_manager = CheckpointManager()
        self._current_checkpoint: Optional[SyncCheckpoint] = None

    def fetch_incremental_emails(
        self,
        max_emails: int = 1000,
        output_dir: str = "incremental_backup",
        resume: bool = True
    ) -> Tuple[bool, str]:
        """
        Fetch emails with checkpoint support.

        Args:
            max_emails: Maximum emails to fetch
            output_dir: Output directory
            resume: Whether to resume interrupted syncs
        """
        # Check for resumable checkpoint
        if resume:
            existing = self.checkpoint_manager.get_latest_checkpoint()
            if existing and existing.state in (SyncState.IN_PROGRESS, SyncState.INTERRUPTED):
                logger.info(f"Resuming from checkpoint: {existing.sync_id}")
                return self._resume_fetch(existing)

        # Start new fetch
        latest_date = self.get_latest_email_date()
        if not latest_date:
            return False, ""

        query = f"after:{latest_date}"

        # Create checkpoint
        self._current_checkpoint = self.checkpoint_manager.create_checkpoint(
            query=query,
            output_directory=output_dir
        )

        try:
            return self._execute_fetch(query, max_emails, output_dir)
        except KeyboardInterrupt:
            logger.warning("Fetch interrupted by user")
            if self._current_checkpoint:
                self.checkpoint_manager.mark_interrupted(self._current_checkpoint)
            return False, ""
        except Exception as e:
            logger.error(f"Fetch failed: {e}")
            if self._current_checkpoint:
                self.checkpoint_manager.mark_failed(self._current_checkpoint, str(e))
            raise

    def _execute_fetch(self, query: str, max_emails: int, output_dir: str) -> Tuple[bool, str]:
        """Execute fetch with progress tracking."""
        # ... implementation with checkpoint updates ...

        # Update checkpoint after each batch
        self.checkpoint_manager.update_progress(
            self._current_checkpoint,
            processed=successful_downloads,
            last_message_id=last_id
        )

        # Mark completed
        self.checkpoint_manager.mark_completed(
            self._current_checkpoint,
            history_id=latest_history_id
        )

        return True, str(output_path)

    def _resume_fetch(self, checkpoint: SyncCheckpoint) -> Tuple[bool, str]:
        """Resume fetch from checkpoint."""
        resume_info = self.checkpoint_manager.get_resume_info(checkpoint)
        logger.info(f"Resuming from message {resume_info['skip_count']}")

        self._current_checkpoint = checkpoint

        # Continue from last position
        return self._execute_fetch(
            query=resume_info['query'],
            max_emails=1000,  # Or from checkpoint
            output_dir=resume_info['output_directory'],
            skip_count=resume_info['skip_count'],
            page_token=resume_info['last_page_token']
        )
```

**Validation Criteria**:
- [ ] Interrupted syncs can be resumed
- [ ] Progress is persisted every N messages
- [ ] Failed message IDs are recorded for retry
- [ ] Atomic writes prevent corruption
- [ ] Old checkpoints are cleaned up automatically

---

### Task 2.3: Implement Dead Letter Queue for Failures

**Effort**: 8 hours
**Priority**: Medium
**Dependencies**: Task 1.1, Task 2.2

**Implementation Steps**:

1. Create DLQ module: `src/gmail_assistant/core/fetch/dead_letter_queue.py`

```python
"""
Dead Letter Queue for handling persistent failures.
Failed operations are stored for later retry or manual inspection.
"""

import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class FailureType(str, Enum):
    """Types of failures."""
    FETCH_ERROR = "fetch_error"
    PARSE_ERROR = "parse_error"
    SAVE_ERROR = "save_error"
    DELETE_ERROR = "delete_error"
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    UNKNOWN = "unknown"


@dataclass
class DeadLetterItem:
    """Item in the dead letter queue."""
    id: int
    message_id: str
    failure_type: FailureType
    error_message: str
    error_details: Optional[str]
    attempt_count: int
    first_failure: datetime
    last_failure: datetime
    next_retry: Optional[datetime]
    resolved: bool
    context: Dict[str, Any]


class DeadLetterQueue:
    """
    SQLite-backed dead letter queue for failed operations.

    Features:
    - Automatic retry scheduling with exponential backoff
    - Failure categorization
    - Resolution tracking
    - Statistics and reporting
    """

    DEFAULT_DB = Path("data/databases/dead_letters.db")
    MAX_RETRIES = 5
    BASE_RETRY_DELAY = 300  # 5 minutes

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self.DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize DLQ database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS dead_letters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    failure_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    error_details TEXT,
                    attempt_count INTEGER DEFAULT 1,
                    first_failure DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_failure DATETIME DEFAULT CURRENT_TIMESTAMP,
                    next_retry DATETIME,
                    resolved BOOLEAN DEFAULT FALSE,
                    context TEXT,

                    UNIQUE(message_id, failure_type)
                );

                CREATE INDEX IF NOT EXISTS idx_dlq_next_retry
                    ON dead_letters(next_retry) WHERE resolved = FALSE;
                CREATE INDEX IF NOT EXISTS idx_dlq_message_id
                    ON dead_letters(message_id);
                CREATE INDEX IF NOT EXISTS idx_dlq_failure_type
                    ON dead_letters(failure_type);
            """)

    def add_failure(
        self,
        message_id: str,
        failure_type: FailureType,
        error_message: str,
        error_details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add or update a failed operation.

        Returns:
            DLQ item ID
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check if already exists
            existing = conn.execute(
                "SELECT id, attempt_count FROM dead_letters WHERE message_id = ? AND failure_type = ?",
                (message_id, failure_type.value)
            ).fetchone()

            if existing:
                # Update existing entry
                item_id, attempt_count = existing
                new_attempt = attempt_count + 1
                next_retry = self._calculate_next_retry(new_attempt)

                conn.execute("""
                    UPDATE dead_letters SET
                        error_message = ?,
                        error_details = ?,
                        attempt_count = ?,
                        last_failure = CURRENT_TIMESTAMP,
                        next_retry = ?,
                        context = ?
                    WHERE id = ?
                """, (error_message, error_details, new_attempt,
                      next_retry.isoformat() if next_retry else None,
                      json.dumps(context) if context else None, item_id))

                if new_attempt >= self.MAX_RETRIES:
                    logger.warning(f"Message {message_id} exceeded max retries")

                return item_id
            else:
                # Insert new entry
                next_retry = self._calculate_next_retry(1)
                cursor = conn.execute("""
                    INSERT INTO dead_letters
                    (message_id, failure_type, error_message, error_details, next_retry, context)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (message_id, failure_type.value, error_message, error_details,
                      next_retry.isoformat() if next_retry else None,
                      json.dumps(context) if context else None))

                logger.info(f"Added to DLQ: {message_id} ({failure_type.value})")
                return cursor.lastrowid

    def _calculate_next_retry(self, attempt: int) -> Optional[datetime]:
        """Calculate next retry time with exponential backoff."""
        if attempt >= self.MAX_RETRIES:
            return None  # No more retries

        delay = self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
        return datetime.now() + timedelta(seconds=delay)

    def get_ready_for_retry(self, limit: int = 100) -> List[DeadLetterItem]:
        """Get items ready for retry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM dead_letters
                WHERE resolved = FALSE
                  AND next_retry IS NOT NULL
                  AND next_retry <= datetime('now')
                ORDER BY next_retry ASC
                LIMIT ?
            """, (limit,)).fetchall()

            return [self._row_to_item(row) for row in rows]

    def mark_resolved(self, item_id: int) -> None:
        """Mark an item as resolved."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE dead_letters SET resolved = TRUE WHERE id = ?",
                (item_id,)
            )
        logger.info(f"DLQ item {item_id} resolved")

    def get_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM dead_letters WHERE resolved = FALSE"
            ).fetchone()[0]

            by_type = dict(conn.execute("""
                SELECT failure_type, COUNT(*)
                FROM dead_letters
                WHERE resolved = FALSE
                GROUP BY failure_type
            """).fetchall())

            ready = conn.execute("""
                SELECT COUNT(*) FROM dead_letters
                WHERE resolved = FALSE AND next_retry <= datetime('now')
            """).fetchone()[0]

            exhausted = conn.execute("""
                SELECT COUNT(*) FROM dead_letters
                WHERE resolved = FALSE AND next_retry IS NULL
            """).fetchone()[0]

            return {
                'total_pending': total,
                'by_failure_type': by_type,
                'ready_for_retry': ready,
                'retries_exhausted': exhausted
            }

    def get_by_message_id(self, message_id: str) -> List[DeadLetterItem]:
        """Get all DLQ items for a message."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM dead_letters WHERE message_id = ?",
                (message_id,)
            ).fetchall()
            return [self._row_to_item(row) for row in rows]

    def _row_to_item(self, row: sqlite3.Row) -> DeadLetterItem:
        """Convert database row to DeadLetterItem."""
        return DeadLetterItem(
            id=row['id'],
            message_id=row['message_id'],
            failure_type=FailureType(row['failure_type']),
            error_message=row['error_message'],
            error_details=row['error_details'],
            attempt_count=row['attempt_count'],
            first_failure=datetime.fromisoformat(row['first_failure']),
            last_failure=datetime.fromisoformat(row['last_failure']),
            next_retry=datetime.fromisoformat(row['next_retry']) if row['next_retry'] else None,
            resolved=bool(row['resolved']),
            context=json.loads(row['context']) if row['context'] else {}
        )

    def cleanup_resolved(self, older_than_days: int = 30) -> int:
        """Clean up old resolved items."""
        cutoff = datetime.now() - timedelta(days=older_than_days)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM dead_letters
                WHERE resolved = TRUE AND last_failure < ?
            """, (cutoff.isoformat(),))
            return cursor.rowcount
```

**Validation Criteria**:
- [ ] Failed operations are persisted
- [ ] Retry scheduling works correctly
- [ ] Statistics accurately reflect queue state
- [ ] Old resolved items are cleaned up

---

## Phase 3: Advanced Features (Week 5-6)

### Task 3.1: Normalize Database Schema

**Effort**: 12 hours
**Priority**: Medium
**Dependencies**: Task 1.3

**Implementation Steps**:

1. Create migration script: `scripts/migrations/002_normalize_schema.py`

```python
"""
Database migration: Normalize schema for labels and participants.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def migrate(db_path: Path, dry_run: bool = True) -> bool:
    """
    Execute schema normalization migration.

    Changes:
    1. Create email_participants table
    2. Create email_labels table
    3. Migrate existing data
    4. Add sync_state table for history ID tracking
    """

    migration_sql = """
    -- Email participants table (normalized)
    CREATE TABLE IF NOT EXISTS email_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id INTEGER NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
        type TEXT NOT NULL CHECK(type IN ('from', 'to', 'cc', 'bcc')),
        address TEXT NOT NULL,
        display_name TEXT,
        domain TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        UNIQUE(email_id, type, address)
    );

    CREATE INDEX IF NOT EXISTS idx_participants_email_id ON email_participants(email_id);
    CREATE INDEX IF NOT EXISTS idx_participants_address ON email_participants(address);
    CREATE INDEX IF NOT EXISTS idx_participants_domain ON email_participants(domain);

    -- Email labels table (normalized)
    CREATE TABLE IF NOT EXISTS email_labels (
        email_id INTEGER NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
        label TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        PRIMARY KEY (email_id, label)
    );

    CREATE INDEX IF NOT EXISTS idx_labels_label ON email_labels(label);

    -- Sync state for Gmail history API
    CREATE TABLE IF NOT EXISTS sync_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL UNIQUE,
        last_history_id INTEGER,
        last_sync_at DATETIME,
        total_synced INTEGER DEFAULT 0,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Add updated_at and deleted_at to emails if not exists
    -- (SQLite doesn't support ADD COLUMN IF NOT EXISTS, so we check first)
    """

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        if dry_run:
            logger.info("DRY RUN - No changes will be made")

        # Execute schema changes
        conn.executescript(migration_sql)

        # Migrate existing data
        _migrate_labels(conn, dry_run)
        _migrate_participants(conn, dry_run)

        if not dry_run:
            conn.commit()
            logger.info("Migration completed successfully")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def _migrate_labels(conn: sqlite3.Connection, dry_run: bool) -> int:
    """Migrate comma-separated labels to normalized table."""
    cursor = conn.execute("""
        SELECT id, labels FROM emails
        WHERE labels IS NOT NULL AND labels != ''
    """)

    count = 0
    for row in cursor:
        email_id = row['id']
        labels_str = row['labels']

        # Parse comma-separated labels
        labels = [l.strip() for l in labels_str.split(',') if l.strip()]

        for label in labels:
            if not dry_run:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO email_labels (email_id, label) VALUES (?, ?)",
                        (email_id, label)
                    )
                    count += 1
                except sqlite3.IntegrityError:
                    pass  # Already exists
            else:
                count += 1

    logger.info(f"Migrated {count} label entries")
    return count


def _migrate_participants(conn: sqlite3.Connection, dry_run: bool) -> int:
    """Migrate sender/recipient to normalized participants table."""
    cursor = conn.execute("""
        SELECT id, sender, recipient FROM emails
        WHERE sender IS NOT NULL OR recipient IS NOT NULL
    """)

    count = 0
    for row in cursor:
        email_id = row['id']

        # Migrate sender
        if row['sender']:
            address = _extract_email(row['sender'])
            domain = address.split('@')[1] if '@' in address else ''
            display_name = _extract_display_name(row['sender'])

            if not dry_run:
                _insert_participant(conn, email_id, 'from', address, display_name, domain)
            count += 1

        # Migrate recipients
        if row['recipient']:
            recipients = row['recipient'].split(',')
            for recipient in recipients:
                address = _extract_email(recipient.strip())
                domain = address.split('@')[1] if '@' in address else ''
                display_name = _extract_display_name(recipient.strip())

                if not dry_run:
                    _insert_participant(conn, email_id, 'to', address, display_name, domain)
                count += 1

    logger.info(f"Migrated {count} participant entries")
    return count


def _extract_email(header_value: str) -> str:
    """Extract email address from header value."""
    if '<' in header_value and '>' in header_value:
        return header_value.split('<')[1].split('>')[0].strip()
    return header_value.strip()


def _extract_display_name(header_value: str) -> str:
    """Extract display name from header value."""
    if '<' in header_value:
        return header_value.split('<')[0].strip().strip('"')
    return ''


def _insert_participant(conn, email_id, ptype, address, display_name, domain):
    """Insert participant record."""
    try:
        conn.execute("""
            INSERT OR IGNORE INTO email_participants
            (email_id, type, address, display_name, domain)
            VALUES (?, ?, ?, ?, ?)
        """, (email_id, ptype, address, display_name, domain))
    except sqlite3.IntegrityError:
        pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize database schema")
    parser.add_argument("--db", required=True, help="Database path")
    parser.add_argument("--execute", action="store_true", help="Execute migration (not dry run)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    migrate(Path(args.db), dry_run=not args.execute)
```

2. Update database.py to use normalized tables

3. Add backward compatibility layer for queries

**Validation Criteria**:
- [ ] Migration runs without data loss
- [ ] Queries work with both old and new schema
- [ ] Performance improved for label/participant queries
- [ ] Rollback script available

---

### Task 3.2: Implement True Incremental Sync with History API

**Effort**: 16 hours
**Priority**: Medium
**Dependencies**: Task 2.2, Task 3.1

**Implementation Steps**:

1. Create history API module: `src/gmail_assistant/core/fetch/history_sync.py`

```python
"""
True incremental sync using Gmail History API.
Only fetches changes since last sync, not all matching messages.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from googleapiclient.errors import HttpError
from ..schemas import Email
from .batch_api import GmailBatchClient

logger = logging.getLogger(__name__)


class HistoryEventType(str, Enum):
    MESSAGE_ADDED = "messageAdded"
    MESSAGE_DELETED = "messageDeleted"
    LABELS_ADDED = "labelsAdded"
    LABELS_REMOVED = "labelsRemoved"


@dataclass
class HistoryEvent:
    """Single history event."""
    type: HistoryEventType
    message_id: str
    labels: List[str]
    history_id: int


@dataclass
class HistorySyncResult:
    """Result of history sync operation."""
    success: bool
    new_history_id: int
    events: List[HistoryEvent]
    added_message_ids: List[str]
    deleted_message_ids: List[str]
    label_changes: List[Dict]
    error: Optional[str] = None


class HistorySyncClient:
    """
    Gmail History API client for efficient incremental sync.

    The History API returns only changes since a given historyId,
    making it far more efficient than re-scanning all messages.

    Workflow:
    1. Initial full sync - store final historyId
    2. Subsequent syncs - use history.list() from last historyId
    3. Process only changed messages
    """

    def __init__(self, service, batch_client: Optional[GmailBatchClient] = None):
        self.service = service
        self.batch_client = batch_client or GmailBatchClient(service)

    def get_current_history_id(self) -> int:
        """Get current history ID from profile."""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return int(profile.get('historyId', 0))
        except HttpError as e:
            logger.error(f"Failed to get history ID: {e}")
            raise

    def sync_from_history(
        self,
        start_history_id: int,
        label_filter: Optional[str] = None
    ) -> HistorySyncResult:
        """
        Sync changes from a given history ID.

        Args:
            start_history_id: History ID to start from
            label_filter: Optional label to filter by (e.g., 'INBOX')

        Returns:
            HistorySyncResult with all changes
        """
        events = []
        added_ids = set()
        deleted_ids = set()
        label_changes = []

        page_token = None
        latest_history_id = start_history_id

        try:
            while True:
                # Build request
                request_params = {
                    'userId': 'me',
                    'startHistoryId': start_history_id,
                    'historyTypes': ['messageAdded', 'messageDeleted', 'labelAdded', 'labelRemoved']
                }

                if label_filter:
                    request_params['labelId'] = label_filter
                if page_token:
                    request_params['pageToken'] = page_token

                # Execute
                response = self.service.users().history().list(**request_params).execute()

                # Process history records
                for record in response.get('history', []):
                    record_id = int(record.get('id', 0))
                    latest_history_id = max(latest_history_id, record_id)

                    # Process message additions
                    for msg in record.get('messagesAdded', []):
                        msg_id = msg['message']['id']
                        labels = msg['message'].get('labelIds', [])
                        added_ids.add(msg_id)
                        events.append(HistoryEvent(
                            type=HistoryEventType.MESSAGE_ADDED,
                            message_id=msg_id,
                            labels=labels,
                            history_id=record_id
                        ))

                    # Process message deletions
                    for msg in record.get('messagesDeleted', []):
                        msg_id = msg['message']['id']
                        deleted_ids.add(msg_id)
                        events.append(HistoryEvent(
                            type=HistoryEventType.MESSAGE_DELETED,
                            message_id=msg_id,
                            labels=[],
                            history_id=record_id
                        ))

                    # Process label additions
                    for change in record.get('labelsAdded', []):
                        msg_id = change['message']['id']
                        labels = change.get('labelIds', [])
                        label_changes.append({
                            'message_id': msg_id,
                            'added': labels,
                            'removed': []
                        })
                        events.append(HistoryEvent(
                            type=HistoryEventType.LABELS_ADDED,
                            message_id=msg_id,
                            labels=labels,
                            history_id=record_id
                        ))

                    # Process label removals
                    for change in record.get('labelsRemoved', []):
                        msg_id = change['message']['id']
                        labels = change.get('labelIds', [])
                        label_changes.append({
                            'message_id': msg_id,
                            'added': [],
                            'removed': labels
                        })
                        events.append(HistoryEvent(
                            type=HistoryEventType.LABELS_REMOVED,
                            message_id=msg_id,
                            labels=labels,
                            history_id=record_id
                        ))

                # Check for more pages
                page_token = response.get('nextPageToken')
                if not page_token:
                    break

            # Remove deleted from added (net result)
            net_added = list(added_ids - deleted_ids)
            net_deleted = list(deleted_ids)

            logger.info(f"History sync: {len(net_added)} added, {len(net_deleted)} deleted, "
                       f"{len(label_changes)} label changes")

            return HistorySyncResult(
                success=True,
                new_history_id=latest_history_id,
                events=events,
                added_message_ids=net_added,
                deleted_message_ids=net_deleted,
                label_changes=label_changes
            )

        except HttpError as e:
            if e.resp.status == 404:
                # History ID expired - need full sync
                logger.warning("History ID expired, full sync required")
                return HistorySyncResult(
                    success=False,
                    new_history_id=0,
                    events=[],
                    added_message_ids=[],
                    deleted_message_ids=[],
                    label_changes=[],
                    error="HISTORY_EXPIRED"
                )
            raise

    def fetch_added_messages(self, message_ids: List[str]) -> List[Email]:
        """Fetch full message details for added messages."""
        if not message_ids:
            return []

        return self.batch_client.batch_get_messages(
            message_ids,
            format='full'
        )

    def perform_incremental_sync(
        self,
        last_history_id: int,
        on_messages_added: callable = None,
        on_messages_deleted: callable = None,
        on_labels_changed: callable = None
    ) -> Tuple[int, Dict]:
        """
        Perform complete incremental sync with callbacks.

        Args:
            last_history_id: Last synced history ID
            on_messages_added: Callback for new messages
            on_messages_deleted: Callback for deleted messages
            on_labels_changed: Callback for label changes

        Returns:
            Tuple of (new_history_id, stats_dict)
        """
        stats = {
            'added': 0,
            'deleted': 0,
            'label_changes': 0
        }

        # Sync history
        result = self.sync_from_history(last_history_id)

        if not result.success:
            if result.error == "HISTORY_EXPIRED":
                raise ValueError("History expired - full sync required")
            raise RuntimeError(f"History sync failed: {result.error}")

        # Process additions
        if result.added_message_ids:
            messages = self.fetch_added_messages(result.added_message_ids)
            stats['added'] = len(messages)
            if on_messages_added:
                on_messages_added(messages)

        # Process deletions
        if result.deleted_message_ids:
            stats['deleted'] = len(result.deleted_message_ids)
            if on_messages_deleted:
                on_messages_deleted(result.deleted_message_ids)

        # Process label changes
        if result.label_changes:
            stats['label_changes'] = len(result.label_changes)
            if on_labels_changed:
                on_labels_changed(result.label_changes)

        return result.new_history_id, stats
```

**Validation Criteria**:
- [ ] History sync fetches only changes
- [ ] Expired history ID triggers full sync
- [ ] All event types are handled correctly
- [ ] Performance significantly better than full scan

---

### Task 3.3: Integrate Circuit Breaker with Error Handler

**Effort**: 6 hours
**Priority**: Medium
**Dependencies**: None

**Implementation Steps**:

1. Update error_handler.py to integrate circuit breaker:

```python
# Add to error_handler.py

from ..utils.circuit_breaker import CircuitBreaker, CircuitBreakerError

class IntegratedErrorHandler(ErrorHandler):
    """Error handler with circuit breaker integration."""

    def __init__(self, log_dir: Optional[Path] = None):
        super().__init__(log_dir)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0
        )

        # Register circuit breaker recovery for API errors
        self.register_recovery_handler(
            ErrorCategory.RATE_LIMIT,
            self._handle_rate_limit_recovery
        )
        self.register_recovery_handler(
            ErrorCategory.NETWORK,
            self._handle_network_recovery
        )

    def handle_api_error(self, exception: Exception, context: Optional[ErrorContext] = None) -> StandardError:
        """Handle API error with circuit breaker."""
        # Record failure in circuit breaker
        self.circuit_breaker._record_failure()

        # Check if circuit should open
        if self.circuit_breaker.is_open:
            logger.warning("Circuit breaker opened - API calls will be rejected")

        return self.handle_error(exception, context)

    def _handle_rate_limit_recovery(self, error: StandardError) -> bool:
        """Recovery handler for rate limit errors."""
        import time

        # Wait for rate limit to clear
        wait_time = self._extract_retry_after(error) or 60
        logger.info(f"Rate limit recovery: waiting {wait_time}s")
        time.sleep(wait_time)

        return True

    def _handle_network_recovery(self, error: StandardError) -> bool:
        """Recovery handler for network errors."""
        # Check if circuit breaker should transition
        if self.circuit_breaker.state.value == 'open':
            logger.info("Waiting for circuit breaker recovery timeout")
            return False
        return True

    def _extract_retry_after(self, error: StandardError) -> Optional[int]:
        """Extract Retry-After header from error."""
        if error.original_exception and hasattr(error.original_exception, 'resp'):
            retry_after = error.original_exception.resp.get('retry-after')
            if retry_after:
                return int(retry_after)
        return None
```

**Validation Criteria**:
- [ ] Circuit breaker trips after N failures
- [ ] Recovery handlers are invoked correctly
- [ ] Rate limit errors trigger appropriate backoff
- [ ] Circuit breaker state is logged

---

## Phase 4: Optimization & Observability (Week 7-8)

### Task 4.1: Add Parquet Export for Analytics

**Effort**: 8 hours
**Priority**: Low
**Dependencies**: Task 1.1, Task 3.1

**Implementation Steps**:

1. Create Parquet exporter: `src/gmail_assistant/export/parquet_exporter.py`

```python
"""
Parquet export for email data analytics.
Optimized for analytical queries and data science workflows.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import sqlite3

logger = logging.getLogger(__name__)

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False
    logger.warning("PyArrow not installed - Parquet export unavailable")


class ParquetExporter:
    """
    Export email data to Parquet format for analytics.

    Features:
    - Columnar storage for efficient queries
    - Compression for storage efficiency
    - Partitioning by date for time-based analysis
    - Schema evolution support
    """

    def __init__(self, db_path: Path):
        if not PYARROW_AVAILABLE:
            raise ImportError("PyArrow required for Parquet export: pip install pyarrow")

        self.db_path = db_path

    def export_emails(
        self,
        output_dir: Path,
        partition_by: str = 'year_month',
        compression: str = 'snappy',
        batch_size: int = 10000
    ) -> Dict[str, Any]:
        """
        Export emails to Parquet files.

        Args:
            output_dir: Output directory for Parquet files
            partition_by: Partition column (year_month, sender_domain, etc.)
            compression: Compression codec (snappy, gzip, zstd)
            batch_size: Rows per batch

        Returns:
            Export statistics
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        stats = {
            'total_rows': 0,
            'files_created': 0,
            'total_size_bytes': 0,
            'partitions': []
        }

        # Define schema
        schema = pa.schema([
            ('gmail_id', pa.string()),
            ('thread_id', pa.string()),
            ('subject', pa.string()),
            ('sender', pa.string()),
            ('sender_domain', pa.string()),
            ('recipient', pa.string()),
            ('parsed_date', pa.timestamp('us')),
            ('year_month', pa.string()),
            ('labels', pa.list_(pa.string())),
            ('message_length', pa.int32()),
            ('has_attachments', pa.bool_()),
        ])

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Get partitions
            partitions = conn.execute(
                f"SELECT DISTINCT {partition_by} FROM emails ORDER BY {partition_by}"
            ).fetchall()

            for partition_row in partitions:
                partition_value = partition_row[0]
                if not partition_value:
                    continue

                # Export partition
                partition_stats = self._export_partition(
                    conn, output_dir, partition_by, partition_value,
                    schema, compression, batch_size
                )

                stats['total_rows'] += partition_stats['rows']
                stats['files_created'] += 1
                stats['total_size_bytes'] += partition_stats['size_bytes']
                stats['partitions'].append(partition_value)

            logger.info(f"Exported {stats['total_rows']} rows to {stats['files_created']} files")
            return stats

        finally:
            conn.close()

    def _export_partition(
        self,
        conn: sqlite3.Connection,
        output_dir: Path,
        partition_by: str,
        partition_value: str,
        schema: pa.Schema,
        compression: str,
        batch_size: int
    ) -> Dict[str, int]:
        """Export a single partition."""

        # Query data for partition
        query = f"""
            SELECT
                gmail_id, thread_id, subject, sender, recipient,
                parsed_date, year_month, labels, message_content
            FROM emails
            WHERE {partition_by} = ?
        """

        rows = conn.execute(query, (partition_value,)).fetchall()

        # Convert to Arrow table
        data = {
            'gmail_id': [],
            'thread_id': [],
            'subject': [],
            'sender': [],
            'sender_domain': [],
            'recipient': [],
            'parsed_date': [],
            'year_month': [],
            'labels': [],
            'message_length': [],
            'has_attachments': [],
        }

        for row in rows:
            data['gmail_id'].append(row['gmail_id'])
            data['thread_id'].append(row['thread_id'])
            data['subject'].append(row['subject'])
            data['sender'].append(row['sender'])
            data['sender_domain'].append(
                row['sender'].split('@')[1] if '@' in (row['sender'] or '') else ''
            )
            data['recipient'].append(row['recipient'])
            data['parsed_date'].append(
                datetime.fromisoformat(row['parsed_date']) if row['parsed_date'] else None
            )
            data['year_month'].append(row['year_month'])
            data['labels'].append(
                row['labels'].split(',') if row['labels'] else []
            )
            data['message_length'].append(
                len(row['message_content']) if row['message_content'] else 0
            )
            data['has_attachments'].append(False)  # TODO: Extract from content

        # Create Arrow table
        table = pa.table(data, schema=schema)

        # Write Parquet file
        partition_dir = output_dir / f"{partition_by}={partition_value}"
        partition_dir.mkdir(parents=True, exist_ok=True)
        output_file = partition_dir / "data.parquet"

        pq.write_table(
            table,
            output_file,
            compression=compression
        )

        return {
            'rows': len(rows),
            'size_bytes': output_file.stat().st_size
        }

    def export_summary_stats(self, output_file: Path) -> None:
        """Export summary statistics as Parquet."""
        conn = sqlite3.connect(self.db_path)

        try:
            # Monthly stats
            monthly_query = """
                SELECT
                    year_month,
                    COUNT(*) as email_count,
                    COUNT(DISTINCT sender) as unique_senders,
                    COUNT(DISTINCT recipient) as unique_recipients,
                    MIN(parsed_date) as first_email,
                    MAX(parsed_date) as last_email
                FROM emails
                GROUP BY year_month
                ORDER BY year_month
            """

            rows = conn.execute(monthly_query).fetchall()

            data = {
                'year_month': [r[0] for r in rows],
                'email_count': [r[1] for r in rows],
                'unique_senders': [r[2] for r in rows],
                'unique_recipients': [r[3] for r in rows],
                'first_email': [r[4] for r in rows],
                'last_email': [r[5] for r in rows],
            }

            table = pa.table(data)
            pq.write_table(table, output_file, compression='snappy')

            logger.info(f"Exported summary stats to {output_file}")

        finally:
            conn.close()
```

**Validation Criteria**:
- [ ] Parquet files are valid and readable
- [ ] Partitioning works correctly
- [ ] Compression reduces file size significantly
- [ ] Analytics queries perform well

---

### Task 4.2: Add Observability (Metrics, Logging)

**Effort**: 10 hours
**Priority**: Low
**Dependencies**: None

**Implementation Steps**:

1. Create metrics module: `src/gmail_assistant/utils/metrics.py`

```python
"""
Metrics and observability for Gmail Assistant.
Provides structured metrics collection and reporting.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from contextlib import contextmanager
import threading
import json

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram


class MetricsCollector:
    """
    Thread-safe metrics collector.

    Features:
    - Counter, gauge, and histogram metrics
    - Labels for dimensional analysis
    - Timer context manager
    - Periodic reporting
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)
        self._labels: Dict[str, Dict[str, str]] = {}
        self._start_time = datetime.now()

    def inc_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value
            if labels:
                self._labels[key] = labels

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge metric."""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
            if labels:
                self._labels[key] = labels

    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Record a histogram observation."""
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            if labels:
                self._labels[key] = labels

    @contextmanager
    def timer(self, name: str, labels: Dict[str, str] = None):
        """Context manager for timing operations."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.observe_histogram(f"{name}_duration_seconds", duration, labels)
            self.inc_counter(f"{name}_total", labels=labels)

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create unique key for metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        with self._lock:
            result = {
                'uptime_seconds': (datetime.now() - self._start_time).total_seconds(),
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {}
            }

            # Calculate histogram statistics
            for key, values in self._histograms.items():
                if values:
                    sorted_values = sorted(values)
                    n = len(sorted_values)
                    result['histograms'][key] = {
                        'count': n,
                        'sum': sum(values),
                        'min': sorted_values[0],
                        'max': sorted_values[-1],
                        'mean': sum(values) / n,
                        'p50': sorted_values[n // 2],
                        'p95': sorted_values[int(n * 0.95)] if n > 20 else sorted_values[-1],
                        'p99': sorted_values[int(n * 0.99)] if n > 100 else sorted_values[-1],
                    }

            return result

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._labels.clear()
            self._start_time = datetime.now()

    def report(self, output_file: Optional[str] = None) -> str:
        """Generate metrics report."""
        metrics = self.get_metrics()

        report_lines = [
            "=== Gmail Assistant Metrics Report ===",
            f"Uptime: {metrics['uptime_seconds']:.1f}s",
            "",
            "--- Counters ---"
        ]

        for name, value in sorted(metrics['counters'].items()):
            report_lines.append(f"  {name}: {value}")

        report_lines.extend(["", "--- Gauges ---"])
        for name, value in sorted(metrics['gauges'].items()):
            report_lines.append(f"  {name}: {value}")

        report_lines.extend(["", "--- Histograms ---"])
        for name, stats in sorted(metrics['histograms'].items()):
            report_lines.append(f"  {name}:")
            report_lines.append(f"    count={stats['count']}, mean={stats['mean']:.4f}, "
                              f"p50={stats['p50']:.4f}, p95={stats['p95']:.4f}")

        report = "\n".join(report_lines)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
                f.write("\n\n--- Raw JSON ---\n")
                json.dump(metrics, f, indent=2, default=str)

        return report


# Global metrics collector
_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    return _metrics


# Convenience functions
def inc_counter(name: str, value: float = 1.0, labels: Dict[str, str] = None) -> None:
    _metrics.inc_counter(name, value, labels)


def set_gauge(name: str, value: float, labels: Dict[str, str] = None) -> None:
    _metrics.set_gauge(name, value, labels)


def timer(name: str, labels: Dict[str, str] = None):
    return _metrics.timer(name, labels)
```

2. Integrate metrics throughout codebase

**Validation Criteria**:
- [ ] Metrics are collected during operations
- [ ] Timer accurately measures durations
- [ ] Reports are generated correctly
- [ ] Thread safety is maintained

---

### Task 4.3: Add Backup Manifest with Checksums

**Effort**: 6 hours
**Priority**: Low
**Dependencies**: None

**Implementation Steps**:

1. Create manifest module: `src/gmail_assistant/utils/manifest.py`

```python
"""
Backup manifest with checksums for integrity verification.
"""

import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class FileEntry:
    """Single file entry in manifest."""
    path: str
    size_bytes: int
    sha256: str
    modified_at: str
    gmail_id: Optional[str] = None


@dataclass
class BackupManifest:
    """Complete backup manifest."""
    version: str = "1.0"
    created_at: str = ""
    backup_directory: str = ""
    total_files: int = 0
    total_size_bytes: int = 0
    files: List[FileEntry] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.files is None:
            self.files = []
        if self.metadata is None:
            self.metadata = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class ManifestManager:
    """
    Manages backup manifests for integrity verification.

    Features:
    - SHA-256 checksums for all files
    - Incremental manifest updates
    - Verification of backup integrity
    - Missing/corrupted file detection
    """

    MANIFEST_FILENAME = "backup_manifest.json"

    def __init__(self, backup_dir: Path):
        self.backup_dir = Path(backup_dir)
        self.manifest_path = self.backup_dir / self.MANIFEST_FILENAME

    def create_manifest(
        self,
        file_pattern: str = "**/*.eml",
        metadata: Dict[str, Any] = None
    ) -> BackupManifest:
        """
        Create new manifest for backup directory.

        Args:
            file_pattern: Glob pattern for files to include
            metadata: Additional metadata to store

        Returns:
            BackupManifest object
        """
        manifest = BackupManifest(
            backup_directory=str(self.backup_dir),
            metadata=metadata or {}
        )

        files = list(self.backup_dir.glob(file_pattern))
        logger.info(f"Creating manifest for {len(files)} files")

        for filepath in files:
            try:
                entry = self._create_file_entry(filepath)
                manifest.files.append(entry)
                manifest.total_size_bytes += entry.size_bytes
            except Exception as e:
                logger.warning(f"Failed to process {filepath}: {e}")

        manifest.total_files = len(manifest.files)

        # Save manifest
        self.save_manifest(manifest)

        logger.info(f"Created manifest: {manifest.total_files} files, "
                   f"{manifest.total_size_bytes / 1024 / 1024:.1f} MB")

        return manifest

    def _create_file_entry(self, filepath: Path) -> FileEntry:
        """Create manifest entry for a file."""
        stat = filepath.stat()

        # Calculate SHA-256
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        # Extract gmail_id from filename if present
        gmail_id = None
        if '_' in filepath.stem:
            # Assume format: date_subject_gmailid.eml
            parts = filepath.stem.split('_')
            if len(parts) >= 3:
                gmail_id = parts[-1]

        return FileEntry(
            path=str(filepath.relative_to(self.backup_dir)),
            size_bytes=stat.st_size,
            sha256=sha256.hexdigest(),
            modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            gmail_id=gmail_id
        )

    def save_manifest(self, manifest: BackupManifest) -> None:
        """Save manifest to file."""
        data = asdict(manifest)
        with open(self.manifest_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_manifest(self) -> Optional[BackupManifest]:
        """Load existing manifest."""
        if not self.manifest_path.exists():
            return None

        with open(self.manifest_path) as f:
            data = json.load(f)

        files = [FileEntry(**f) for f in data.get('files', [])]
        data['files'] = files

        return BackupManifest(**data)

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify backup integrity against manifest.

        Returns:
            Dict with verification results
        """
        manifest = self.load_manifest()
        if not manifest:
            return {'error': 'No manifest found'}

        results = {
            'verified': 0,
            'missing': [],
            'corrupted': [],
            'extra': []
        }

        # Check each file in manifest
        for entry in manifest.files:
            filepath = self.backup_dir / entry.path

            if not filepath.exists():
                results['missing'].append(entry.path)
                continue

            # Verify checksum
            sha256 = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)

            if sha256.hexdigest() != entry.sha256:
                results['corrupted'].append({
                    'path': entry.path,
                    'expected': entry.sha256,
                    'actual': sha256.hexdigest()
                })
            else:
                results['verified'] += 1

        # Check for extra files not in manifest
        manifest_paths = {e.path for e in manifest.files}
        for filepath in self.backup_dir.glob("**/*.eml"):
            rel_path = str(filepath.relative_to(self.backup_dir))
            if rel_path not in manifest_paths:
                results['extra'].append(rel_path)

        logger.info(f"Verification complete: {results['verified']} verified, "
                   f"{len(results['missing'])} missing, {len(results['corrupted'])} corrupted")

        return results

    def update_manifest(self, new_files: List[Path]) -> BackupManifest:
        """Update manifest with new files."""
        manifest = self.load_manifest() or BackupManifest(
            backup_directory=str(self.backup_dir)
        )

        existing_paths = {e.path for e in manifest.files}

        for filepath in new_files:
            rel_path = str(filepath.relative_to(self.backup_dir))
            if rel_path not in existing_paths:
                entry = self._create_file_entry(filepath)
                manifest.files.append(entry)
                manifest.total_size_bytes += entry.size_bytes

        manifest.total_files = len(manifest.files)
        self.save_manifest(manifest)

        return manifest
```

**Validation Criteria**:
- [ ] Checksums are calculated correctly
- [ ] Corrupted files are detected
- [ ] Missing files are reported
- [ ] Incremental updates work

---

## Risk Mitigation

### High-Risk Operations

| Operation | Risk | Mitigation |
|-----------|------|------------|
| Database schema migration | Data loss | Backup before migration, dry-run mode, rollback script |
| Batch API implementation | Breaking change | Feature flag, gradual rollout, fallback to sequential |
| History API integration | Expired history IDs | Automatic full sync fallback, clear error messages |
| Email model change | Import errors | Adapter pattern, deprecation warnings, dual support |

### Rollback Procedures

1. **Database Schema Rollback**:
```sql
-- Restore from backup
cp data/databases/emails_final.db.bak data/databases/emails_final.db

-- Or drop new tables
DROP TABLE IF EXISTS email_participants;
DROP TABLE IF EXISTS email_labels;
DROP TABLE IF EXISTS sync_state;
```

2. **Code Rollback**:
```bash
# Revert to previous commit
git revert HEAD

# Or restore specific files
git checkout HEAD~1 -- src/gmail_assistant/core/schemas.py
```

3. **Feature Flags**:
```python
# In config
FEATURE_FLAGS = {
    'use_batch_api': False,  # Set True to enable
    'use_history_sync': False,
    'use_normalized_schema': False,
}
```

---

## Testing Strategy

### Unit Tests Required

| Component | Test Coverage Target | Key Tests |
|-----------|---------------------|-----------|
| schemas.py | 95% | Validation, serialization, conversion |
| batch_api.py | 90% | Batching, error handling, rate limiting |
| checkpoint.py | 90% | Persistence, resume, cleanup |
| dead_letter_queue.py | 90% | Retry logic, expiration, stats |
| history_sync.py | 85% | Event types, pagination, expired IDs |

### Integration Tests Required

1. **End-to-end fetch with checkpoints**
2. **Batch API with real Gmail service (mock)**
3. **Database migration with sample data**
4. **History sync with simulated events**

### Performance Tests

1. **Batch API vs Sequential**: Measure latency reduction
2. **Checkpoint overhead**: Ensure <5% performance impact
3. **Database query performance**: Before/after normalization

---

## Implementation Order Summary

```
Week 1-2 (Foundation):
  [x] Task 1.1: Unified Email Schema (Critical)
  [x] Task 1.2: Config Validation (Medium)
  [x] Task 1.3: Idempotent Writes (High)

Week 3-4 (Core Infrastructure):
  [x] Task 2.1: Gmail Batch API (Critical)
  [x] Task 2.2: Checkpoint Persistence (High)
  [x] Task 2.3: Dead Letter Queue (Medium)

Week 5-6 (Advanced Features):
  [x] Task 3.1: Normalize Database Schema (Medium)
  [x] Task 3.2: History API Sync (Medium)
  [x] Task 3.3: Circuit Breaker Integration (Medium)

Week 7-8 (Optimization):
  [x] Task 4.1: Parquet Export (Low)
  [x] Task 4.2: Observability/Metrics (Low)
  [x] Task 4.3: Backup Manifest (Low)
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Batch fetch latency | ~100ms/email | ~10ms/email |
| Sync resume capability | None | 100% |
| Data integrity checks | None | Full checksums |
| Schema normalization | 0% | 100% |
| Test coverage | 90.6% | 95%+ |

---

## Appendix: File Inventory

### New Files to Create

| Path | Purpose |
|------|---------|
| `src/gmail_assistant/core/schemas.py` | Canonical email models |
| `src/gmail_assistant/core/config_schemas.py` | Config validation |
| `src/gmail_assistant/core/fetch/batch_api.py` | Gmail Batch API |
| `src/gmail_assistant/core/fetch/checkpoint.py` | Sync checkpoints |
| `src/gmail_assistant/core/fetch/dead_letter_queue.py` | Failed operation handling |
| `src/gmail_assistant/core/fetch/history_sync.py` | History API integration |
| `src/gmail_assistant/export/parquet_exporter.py` | Analytics export |
| `src/gmail_assistant/utils/metrics.py` | Observability |
| `src/gmail_assistant/utils/manifest.py` | Backup integrity |
| `scripts/migrations/002_normalize_schema.py` | DB migration |

### Files to Modify

| Path | Changes |
|------|---------|
| `src/gmail_assistant/core/protocols.py` | Add deprecation warnings |
| `src/gmail_assistant/core/ai/newsletter_cleaner.py` | Use new schema |
| `src/gmail_assistant/core/fetch/gmail_api_client.py` | Use batch API |
| `src/gmail_assistant/core/fetch/incremental.py` | Add checkpoint support |
| `src/gmail_assistant/core/processing/database.py` | Normalize schema, upsert |
| `src/gmail_assistant/utils/error_handler.py` | Circuit breaker integration |

---

**Document End**

*Generated: 2026-01-09 21:45*
*Author: Project Planning Architect*
