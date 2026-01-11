# Gmail Assistant Comprehensive Remediation Plan

**Document ID**: 0110-0300_comprehensive_remediation_plan.md
**Date**: 2026-01-10
**Based On**: 0110-0215_master_comprehensive_assessment.md
**Total Estimated Effort**: 240-330 hours (6-8 weeks with 1 FTE)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Phase 1: Critical Performance (Weeks 1-2)](#phase-1-critical-performance-weeks-1-2)
3. [Phase 2: Code Quality (Weeks 3-4)](#phase-2-code-quality-weeks-3-4)
4. [Phase 3: Architecture Debt (Weeks 5-6)](#phase-3-architecture-debt-weeks-5-6)
5. [Phase 4: Security Hardening (Week 7)](#phase-4-security-hardening-week-7)
6. [Task Dependency Graph](#task-dependency-graph)
7. [Final Validation Checklist](#final-validation-checklist)

---

## Executive Summary

This plan provides step-by-step remediation for 24 issues identified in the Master Comprehensive Assessment:
- **3 CRITICAL** (C-1 to C-3): Performance and usability blockers
- **4 HIGH** (H-1 to H-4): Code quality and maintainability issues
- **9 MEDIUM** (M-1 to M-9): Architecture and security improvements
- **8 LOW** (L-1 to L-8): Polish and best practices

### Key Files Already Scaffolded (Ready for Integration)
- `src/gmail_assistant/core/fetch/batch_api.py` - GmailBatchClient (450 lines, complete)
- `src/gmail_assistant/core/fetch/checkpoint.py` - CheckpointManager (441 lines, complete)
- `src/gmail_assistant/core/schemas.py` - Canonical Email model (359 lines, complete)

---

## Phase 1: Critical Performance (Weeks 1-2)

**Total Effort**: 100-140 hours

### C-1: Integrate Gmail Batch API

**Priority**: P0 | **Effort**: 24-32 hours | **Risk**: Medium

**Current State**:
- `gmail_api_client.py:95-124` uses sequential API calls in `_fetch_email_batch()`
- `batch_api.py` already contains complete `GmailBatchClient` implementation
- Not integrated into existing fetch workflows

**Files to Modify**:
- `src/gmail_assistant/core/fetch/gmail_api_client.py`
- `src/gmail_assistant/core/fetch/gmail_assistant.py`
- `src/gmail_assistant/core/fetch/__init__.py`

**Implementation Steps**:

- [ ] **Step 1.1**: Update `gmail_api_client.py` to use `GmailBatchClient`
  ```python
  # File: src/gmail_assistant/core/fetch/gmail_api_client.py
  # Add import at line 14:
  from .batch_api import GmailBatchClient, BatchAPIError

  # In GmailAPIClient.__init__ (line 26-38), add:
  self.batch_client = None  # Lazy initialization

  # Add new method after line 38:
  def _get_batch_client(self) -> GmailBatchClient:
      """Get or create batch client."""
      if self.batch_client is None:
          self.batch_client = GmailBatchClient(self.service)
      return self.batch_client
  ```

- [ ] **Step 1.2**: Refactor `_fetch_email_batch()` to use batch API
  ```python
  # Replace lines 95-124 with:
  def _fetch_email_batch(self, message_ids: List[Dict]) -> List[EmailData]:
      """Fetch a batch of emails using Batch API (C-1 fix)."""
      try:
          batch_client = self._get_batch_client()
          ids = [msg['id'] for msg in message_ids]

          # Use batch API - 80-90% faster than sequential
          raw_results = batch_client.batch_get_messages_raw(ids)

          emails = []
          for msg_id, response in raw_results.items():
              if response:
                  headers = {h['name']: h['value']
                            for h in response['payload'].get('headers', [])}
                  emails.append(EmailData(
                      id=response['id'],
                      subject=headers.get('Subject', ''),
                      sender=headers.get('From', ''),
                      date=headers.get('Date', ''),
                      thread_id=response.get('threadId', ''),
                      labels=response.get('labelIds', []),
                      body_snippet=response.get('snippet', '')
                  ))
          return emails

      except BatchAPIError as e:
          logger.error(f"Batch API error: {e}")
          # Fallback to sequential for resilience
          return self._fetch_email_batch_sequential(message_ids)
  ```

- [ ] **Step 1.3**: Add sequential fallback method
  ```python
  # Add after the refactored _fetch_email_batch:
  def _fetch_email_batch_sequential(self, message_ids: List[Dict]) -> List[EmailData]:
      """Sequential fallback for batch API failures."""
      # (Move current lines 95-124 here as fallback)
      ...
  ```

- [ ] **Step 1.4**: Update `delete_emails()` and `trash_emails()` to use batch API
  ```python
  # Replace lines 126-148 (delete_emails):
  def delete_emails(self, email_ids: List[str]) -> Dict[str, int]:
      """Delete emails using Batch API (C-1 fix)."""
      batch_client = self._get_batch_client()
      result = batch_client.batch_delete_messages(email_ids)
      return {'deleted': result.successful, 'failed': result.failed}

  # Replace lines 150-172 (trash_emails):
  def trash_emails(self, email_ids: List[str]) -> Dict[str, int]:
      """Trash emails using Batch API (C-1 fix)."""
      batch_client = self._get_batch_client()
      result = batch_client.batch_trash_messages(email_ids)
      return {'trashed': result.successful, 'failed': result.failed}
  ```

- [ ] **Step 1.5**: Update `__init__.py` exports
  ```python
  # File: src/gmail_assistant/core/fetch/__init__.py
  # Add:
  from .batch_api import GmailBatchClient, BatchAPIError, BatchResult
  ```

- [ ] **Step 1.6**: Add integration tests
  ```python
  # File: tests/integration/test_batch_api_integration.py
  # Create tests for batch operations with mock Gmail service
  ```

**Validation Criteria**:
- [ ] `pytest tests/integration/test_batch_api_integration.py -v` passes
- [ ] Performance benchmark shows 80%+ improvement for 100+ email fetches
- [ ] Sequential fallback activates correctly on batch failure

**Acceptance Criteria**:
- Batch API used for all bulk operations (fetch, delete, trash)
- Graceful degradation to sequential on batch failures
- Logging shows batch vs sequential operation choice

**Dependencies**: None (first task)

---

### C-2: Complete CLI Command Implementations

**Priority**: P0 | **Effort**: 60-80 hours | **Risk**: Low

**Current State**:
- `cli/commands/fetch.py`, `delete.py`, `analyze.py`, `auth.py` are stub files (6 lines each)
- `cli/main.py` contains Click decorators but prints "deferred to v2.1.0"
- Core functionality exists in `core/fetch/gmail_assistant.py` (GmailFetcher class)

**Files to Modify**:
- `src/gmail_assistant/cli/commands/fetch.py`
- `src/gmail_assistant/cli/commands/delete.py`
- `src/gmail_assistant/cli/commands/analyze.py`
- `src/gmail_assistant/cli/commands/auth.py`
- `src/gmail_assistant/cli/main.py`

**Implementation Steps**:

#### C-2.1: Implement `fetch` Command (20-25 hours)

- [ ] **Step 2.1.1**: Create fetch command implementation
  ```python
  # File: src/gmail_assistant/cli/commands/fetch.py
  """Fetch command implementation."""
  from __future__ import annotations

  import logging
  from pathlib import Path
  from typing import Optional

  import click
  from rich.progress import Progress, SpinnerColumn, TextColumn

  from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher
  from gmail_assistant.core.fetch.batch_api import GmailBatchClient
  from gmail_assistant.core.fetch.checkpoint import CheckpointManager, SyncState
  from gmail_assistant.core.config import AppConfig
  from gmail_assistant.core.exceptions import AuthError, NetworkError

  logger = logging.getLogger(__name__)


  def execute_fetch(
      config: AppConfig,
      query: str,
      max_emails: int,
      output_dir: Path,
      output_format: str,
      resume: bool = False,
  ) -> int:
      """Execute fetch operation with progress display."""
      # Initialize fetcher with credentials from config
      fetcher = GmailFetcher(str(config.credentials_path))

      if not fetcher.authenticate():
          raise AuthError("Failed to authenticate with Gmail API")

      # Check for resumable checkpoint
      checkpoint_mgr = CheckpointManager()
      checkpoint = None

      if resume:
          checkpoint = checkpoint_mgr.get_latest_checkpoint(
              query=query, resumable_only=True
          )
          if checkpoint:
              click.echo(f"Resuming from checkpoint: {checkpoint.sync_id}")
              click.echo(f"Progress: {checkpoint.processed_messages}/{checkpoint.total_messages}")

      # Create new checkpoint if not resuming
      if not checkpoint:
          checkpoint = checkpoint_mgr.create_checkpoint(
              query=query,
              output_directory=str(output_dir),
              metadata={'format': output_format}
          )

      try:
          # Search for messages
          message_ids = fetcher.search_messages(query, max_emails)

          if not message_ids:
              click.echo("No emails found matching query.")
              checkpoint_mgr.mark_completed(checkpoint)
              return 0

          checkpoint.total_messages = len(message_ids)
          checkpoint_mgr.save_checkpoint(checkpoint)

          click.echo(f"Found {len(message_ids)} emails to fetch")

          # Download with progress
          with Progress(
              SpinnerColumn(),
              TextColumn("[progress.description]{task.description}"),
              transient=True
          ) as progress:
              task = progress.add_task("Fetching emails...", total=len(message_ids))

              successful = 0
              for i, msg_id in enumerate(message_ids):
                  try:
                      fetcher.download_emails(
                          query=f"rfc822msgid:{msg_id}",
                          max_emails=1,
                          output_dir=str(output_dir),
                          format_type=output_format
                      )
                      successful += 1

                      # Update checkpoint every 10 emails
                      if i % 10 == 0:
                          checkpoint_mgr.update_progress(
                              checkpoint,
                              processed=i + 1,
                              last_message_id=msg_id
                          )

                      progress.update(task, advance=1)

                  except Exception as e:
                      logger.warning(f"Failed to fetch {msg_id}: {e}")

          checkpoint_mgr.mark_completed(checkpoint)
          click.echo(f"Successfully fetched {successful}/{len(message_ids)} emails")
          click.echo(f"Output directory: {output_dir}")
          return 0

      except KeyboardInterrupt:
          click.echo("\nInterrupted - checkpoint saved for resume")
          checkpoint_mgr.mark_interrupted(checkpoint)
          return 130
      except Exception as e:
          checkpoint_mgr.mark_failed(checkpoint, str(e))
          raise
  ```

- [ ] **Step 2.1.2**: Update `main.py` fetch command to use implementation
  ```python
  # File: src/gmail_assistant/cli/main.py
  # Replace lines 88-110 (fetch command body):

  from gmail_assistant.cli.commands.fetch import execute_fetch

  @main.command()
  @click.option("--query", "-q", default="", help="Gmail search query.")
  @click.option("--max-emails", "-m", type=int, help="Maximum emails to fetch.")
  @click.option("--output-dir", "-o", type=click.Path(path_type=Path), help="Output directory.")
  @click.option("--format", "output_format", type=click.Choice(["eml", "markdown", "both"]), default="both")
  @click.option("--resume", is_flag=True, help="Resume from last checkpoint.")
  @click.pass_context
  @handle_errors
  def fetch(
      ctx: click.Context,
      query: str,
      max_emails: int | None,
      output_dir: Path | None,
      output_format: str,
      resume: bool,
  ) -> None:
      """Fetch emails from Gmail."""
      cfg = AppConfig.load(
          ctx.obj["config_path"],
          allow_repo_credentials=ctx.obj["allow_repo_credentials"],
      )

      effective_max = max_emails if max_emails is not None else cfg.max_emails
      effective_output = output_dir if output_dir is not None else cfg.output_dir

      sys.exit(execute_fetch(cfg, query, effective_max, effective_output, output_format, resume))
  ```

#### C-2.2: Implement `delete` Command (15-20 hours)

- [ ] **Step 2.2.1**: Create delete command implementation
  ```python
  # File: src/gmail_assistant/cli/commands/delete.py
  """Delete command implementation."""
  from __future__ import annotations

  import logging
  from typing import List

  import click
  from rich.console import Console
  from rich.table import Table

  from gmail_assistant.core.fetch.gmail_api_client import GmailAPIClient
  from gmail_assistant.core.config import AppConfig
  from gmail_assistant.core.exceptions import AuthError

  logger = logging.getLogger(__name__)
  console = Console()


  def execute_delete(
      config: AppConfig,
      query: str,
      dry_run: bool,
      confirm: bool,
      trash: bool = True,  # Default to trash for safety
  ) -> int:
      """Execute delete operation with confirmation."""
      client = GmailAPIClient(str(config.credentials_path))

      # Search for matching emails
      click.echo(f"Searching for emails matching: {query}")
      emails = client.fetch_unread_emails(max_results=10000)  # Get all matching

      # Filter by query (simplified - real implementation would use Gmail search)
      matching = [e for e in emails if _matches_query(e, query)]

      if not matching:
          click.echo("No emails found matching query.")
          return 0

      # Show preview
      table = Table(title=f"Emails to {'trash' if trash else 'delete'}")
      table.add_column("Subject", style="cyan", max_width=50)
      table.add_column("From", style="green", max_width=30)
      table.add_column("Date", style="yellow")

      for email in matching[:20]:  # Show first 20
          table.add_row(
              email.subject[:50],
              email.sender[:30],
              email.date[:20] if email.date else "Unknown"
          )

      if len(matching) > 20:
          table.add_row(f"... and {len(matching) - 20} more", "", "")

      console.print(table)
      click.echo(f"\nTotal: {len(matching)} emails")

      if dry_run:
          click.echo("\n[DRY RUN] No emails were actually deleted.")
          return 0

      # Confirmation
      if not confirm:
          action = "trash" if trash else "permanently delete"
          if not click.confirm(f"Are you sure you want to {action} {len(matching)} emails?"):
              click.echo("Aborted.")
              return 0

      # Execute deletion
      email_ids = [e.id for e in matching]

      if trash:
          result = client.trash_emails(email_ids)
          click.echo(f"Moved {result['trashed']} emails to trash")
      else:
          result = client.delete_emails(email_ids)
          click.echo(f"Permanently deleted {result['deleted']} emails")

      if result.get('failed', 0) > 0:
          click.echo(f"Warning: {result['failed']} emails failed to process")
          return 1

      return 0


  def _matches_query(email, query: str) -> bool:
      """Simple query matching (placeholder for full Gmail query parser)."""
      query_lower = query.lower()
      return (
          query_lower in email.subject.lower() or
          query_lower in email.sender.lower()
      )
  ```

- [ ] **Step 2.2.2**: Update `main.py` delete command

#### C-2.3: Implement `auth` Command (10-15 hours)

- [ ] **Step 2.3.1**: Create auth command implementation
  ```python
  # File: src/gmail_assistant/cli/commands/auth.py
  """Auth command implementation."""
  from __future__ import annotations

  import logging
  from pathlib import Path

  import click
  from rich.console import Console
  from rich.panel import Panel

  from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher
  from gmail_assistant.core.auth.credential_manager import SecureCredentialManager
  from gmail_assistant.core.config import AppConfig
  from gmail_assistant.core.exceptions import AuthError, ConfigError

  logger = logging.getLogger(__name__)
  console = Console()


  def execute_auth(
      config: AppConfig,
      revoke: bool = False,
      status: bool = False,
  ) -> int:
      """Execute authentication flow."""
      cred_mgr = SecureCredentialManager(str(config.credentials_path))

      if status:
          # Check authentication status
          if cred_mgr.is_authenticated():
              profile = _get_profile(cred_mgr)
              if profile:
                  console.print(Panel(
                      f"Email: {profile['email']}\n"
                      f"Messages: {profile['total_messages']:,}\n"
                      f"Threads: {profile['total_threads']:,}",
                      title="[green]Authenticated[/green]",
                      border_style="green"
                  ))
                  return 0

          console.print(Panel(
              "Not authenticated. Run 'gmail-assistant auth' to authenticate.",
              title="[yellow]Not Authenticated[/yellow]",
              border_style="yellow"
          ))
          return 1

      if revoke:
          # Revoke credentials
          if cred_mgr.revoke_credentials():
              click.echo("Credentials revoked successfully.")
              return 0
          else:
              click.echo("No credentials to revoke.", err=True)
              return 1

      # Check for credentials file
      if not config.credentials_path.exists():
          console.print(Panel(
              "Credentials file not found.\n\n"
              "To set up Gmail API access:\n"
              "1. Go to https://console.cloud.google.com/\n"
              "2. Create a project and enable Gmail API\n"
              "3. Create OAuth 2.0 credentials\n"
              "4. Download and save as 'credentials.json'",
              title="[red]Setup Required[/red]",
              border_style="red"
          ))
          return 5

      # Run OAuth flow
      click.echo("Starting OAuth authentication flow...")
      click.echo("A browser window will open for you to authorize access.")

      fetcher = GmailFetcher(str(config.credentials_path))

      if fetcher.authenticate():
          profile = fetcher.get_profile()
          console.print(Panel(
              f"Successfully authenticated!\n\n"
              f"Email: {profile['email']}\n"
              f"Total messages: {profile['total_messages']:,}",
              title="[green]Success[/green]",
              border_style="green"
          ))
          return 0
      else:
          raise AuthError("Authentication failed. Please try again.")


  def _get_profile(cred_mgr):
      """Get Gmail profile using credential manager."""
      try:
          service = cred_mgr.get_service()
          if service:
              profile = service.users().getProfile(userId='me').execute()
              return {
                  'email': profile.get('emailAddress'),
                  'total_messages': profile.get('messagesTotal', 0),
                  'total_threads': profile.get('threadsTotal', 0)
              }
      except Exception:
          pass
      return None
  ```

#### C-2.4: Implement `analyze` Command (15-20 hours)

- [ ] **Step 2.4.1**: Create analyze command implementation
  ```python
  # File: src/gmail_assistant/cli/commands/analyze.py
  """Analyze command implementation."""
  from __future__ import annotations

  import json
  import logging
  from pathlib import Path
  from collections import Counter
  from datetime import datetime
  from typing import Dict, List, Any

  import click
  from rich.console import Console
  from rich.table import Table

  from gmail_assistant.core.config import AppConfig

  logger = logging.getLogger(__name__)
  console = Console()


  def execute_analyze(
      config: AppConfig,
      input_dir: Path,
      report_type: str,
  ) -> int:
      """Analyze fetched emails and generate report."""
      # Scan for email files
      eml_files = list(input_dir.glob("**/*.eml"))
      md_files = list(input_dir.glob("**/*.md"))
      json_files = list(input_dir.glob("**/*.json"))

      total_files = len(eml_files) + len(md_files) + len(json_files)

      if total_files == 0:
          click.echo(f"No email files found in {input_dir}")
          return 1

      click.echo(f"Analyzing {total_files} files...")

      # Gather statistics
      stats = {
          'total_emails': total_files,
          'eml_count': len(eml_files),
          'md_count': len(md_files),
          'json_count': len(json_files),
          'by_year': Counter(),
          'by_month': Counter(),
          'senders': Counter(),
          'size_total': 0,
      }

      # Analyze files
      for file_path in eml_files + md_files + json_files:
          stats['size_total'] += file_path.stat().st_size

          # Extract date from path structure (YYYY/MM/)
          parts = file_path.parts
          for i, part in enumerate(parts):
              if part.isdigit() and len(part) == 4:  # Year
                  stats['by_year'][part] += 1
                  if i + 1 < len(parts) and parts[i + 1].isdigit():
                      stats['by_month'][f"{part}-{parts[i + 1]}"] += 1
                  break

      # Generate report
      if report_type == 'json':
          click.echo(json.dumps(stats, indent=2, default=str))
      elif report_type == 'detailed':
          _print_detailed_report(stats, input_dir)
      else:  # summary
          _print_summary_report(stats, input_dir)

      return 0


  def _print_summary_report(stats: Dict, input_dir: Path) -> None:
      """Print summary report."""
      console.print(f"\n[bold]Email Backup Analysis: {input_dir}[/bold]\n")
      console.print(f"Total emails: {stats['total_emails']:,}")
      console.print(f"Total size: {stats['size_total'] / (1024*1024):.2f} MB")
      console.print(f"  - EML files: {stats['eml_count']:,}")
      console.print(f"  - Markdown files: {stats['md_count']:,}")
      console.print(f"  - JSON files: {stats['json_count']:,}")

      if stats['by_year']:
          console.print("\nBy Year:")
          for year, count in sorted(stats['by_year'].items()):
              console.print(f"  {year}: {count:,}")


  def _print_detailed_report(stats: Dict, input_dir: Path) -> None:
      """Print detailed report with tables."""
      _print_summary_report(stats, input_dir)

      if stats['by_month']:
          table = Table(title="Emails by Month")
          table.add_column("Month", style="cyan")
          table.add_column("Count", justify="right", style="green")

          for month, count in sorted(stats['by_month'].items()):
              table.add_row(month, str(count))

          console.print("\n")
          console.print(table)
  ```

**Validation Criteria**:
- [ ] `gmail-assistant fetch --help` shows all options
- [ ] `gmail-assistant fetch -q "is:unread" -m 10` successfully fetches emails
- [ ] `gmail-assistant delete -q "test" --dry-run` shows preview without deleting
- [ ] `gmail-assistant auth` runs OAuth flow and saves credentials
- [ ] `gmail-assistant analyze -i ./backup` generates report

**Acceptance Criteria**:
- All four CLI commands fully functional (not stubs)
- Progress indicators for long operations
- Proper error handling with meaningful messages
- Rich console output for better UX

**Dependencies**: C-1 (uses batch API for delete)

---

### C-3: Implement Checkpoint/Resume for Fetches

**Priority**: P0 | **Effort**: 16-24 hours | **Risk**: Low

**Current State**:
- `checkpoint.py` already contains complete `CheckpointManager` implementation (441 lines)
- `incremental.py` has no checkpoint integration
- Failed fetches restart from beginning

**Files to Modify**:
- `src/gmail_assistant/core/fetch/incremental.py`
- `src/gmail_assistant/core/fetch/__init__.py`

**Implementation Steps**:

- [ ] **Step 3.1**: Integrate CheckpointManager into IncrementalGmailFetcher
  ```python
  # File: src/gmail_assistant/core/fetch/incremental.py
  # Add import after line 27:
  from gmail_assistant.core.fetch.checkpoint import CheckpointManager, SyncCheckpoint, SyncState

  # Modify __init__ (line 42-44):
  def __init__(self, db_path: str = "data/databases/emails_final.db"):
      self.db_path = Path(db_path)
      self.fetcher = None
      self.checkpoint_mgr = CheckpointManager()  # Add checkpoint manager
      self._current_checkpoint: Optional[SyncCheckpoint] = None
  ```

- [ ] **Step 3.2**: Add checkpoint creation in fetch_incremental_emails
  ```python
  # In fetch_incremental_emails() after line 118:
  # Create checkpoint for this sync
  self._current_checkpoint = self.checkpoint_mgr.create_checkpoint(
      query=query,
      output_directory=output_dir,
      total_messages=len(message_ids),
      metadata={'db_path': str(self.db_path)}
  )
  ```

- [ ] **Step 3.3**: Add progress updates during download loop
  ```python
  # In the download loop (around line 131-168):
  for i, message_id in enumerate(message_ids, 1):
      try:
          # ... existing download code ...
          successful_downloads += 1

          # Update checkpoint every 10 emails (C-3 fix)
          if i % 10 == 0 and self._current_checkpoint:
              self.checkpoint_mgr.update_progress(
                  self._current_checkpoint,
                  processed=i,
                  last_message_id=message_id
              )
      except Exception as e:
          # Track failed IDs for retry
          if self._current_checkpoint:
              self.checkpoint_mgr.update_progress(
                  self._current_checkpoint,
                  processed=i,
                  failed_ids=[message_id]
              )
          logger.error(f"Error downloading email {message_id}: {e}")
  ```

- [ ] **Step 3.4**: Add resume capability
  ```python
  # Add new method after run_incremental_fetch:
  def resume_fetch(self) -> bool:
      """
      Resume an interrupted fetch from checkpoint (C-3 fix).

      Returns:
          Success status
      """
      checkpoint = self.checkpoint_mgr.get_latest_checkpoint(resumable_only=True)

      if not checkpoint:
          logger.info("No resumable checkpoint found")
          return False

      logger.info(f"Resuming sync: {checkpoint.sync_id}")
      logger.info(f"Progress: {checkpoint.processed_messages}/{checkpoint.total_messages}")

      resume_info = self.checkpoint_mgr.get_resume_info(checkpoint)

      # Continue from where we left off
      return self.fetch_incremental_emails(
          max_emails=checkpoint.total_messages - checkpoint.processed_messages,
          output_dir=resume_info['output_directory'],
          skip_ids=set(resume_info.get('processed_ids', []))
      )
  ```

- [ ] **Step 3.5**: Mark checkpoint complete/failed on finish
  ```python
  # At end of fetch_incremental_emails:
  if self._current_checkpoint:
      if successful_downloads == len(message_ids):
          self.checkpoint_mgr.mark_completed(self._current_checkpoint)
      elif successful_downloads == 0:
          self.checkpoint_mgr.mark_failed(
              self._current_checkpoint,
              error="No emails downloaded successfully"
          )
      # Partial success keeps state as IN_PROGRESS for resume
  ```

- [ ] **Step 3.6**: Add CLI resume flag (integrate with C-2)
  ```python
  # In CLI fetch command, add --resume flag handling
  ```

**Validation Criteria**:
- [ ] Checkpoint file created in `data/checkpoints/` during fetch
- [ ] Interrupting fetch (Ctrl+C) creates resumable checkpoint
- [ ] `--resume` flag continues from last checkpoint
- [ ] Completed fetches clean up checkpoint properly

**Acceptance Criteria**:
- Failed/interrupted fetches can resume from checkpoint
- Progress persisted every 10 emails
- Failed message IDs tracked for retry
- Checkpoint cleanup after successful completion

**Dependencies**: None (can run in parallel with C-1)

---

## Phase 2: Code Quality (Weeks 3-4)

**Total Effort**: 60-80 hours

### H-1: Unify Duplicate Data Structures

**Priority**: P1 | **Effort**: 16-24 hours | **Risk**: Medium

**Current State**:
- `protocols.py:43-55` defines `EmailMetadata` dataclass
- `newsletter_cleaner.py:37-45` defines `EmailData` dataclass
- `schemas.py` contains canonical `Email` Pydantic model with compatibility wrappers

**Files to Modify**:
- `src/gmail_assistant/core/ai/newsletter_cleaner.py`
- `src/gmail_assistant/core/fetch/gmail_api_client.py`
- `src/gmail_assistant/core/protocols.py`

**Implementation Steps**:

- [ ] **Step 4.1**: Update newsletter_cleaner.py to use schemas.Email
  ```python
  # File: src/gmail_assistant/core/ai/newsletter_cleaner.py
  # Replace lines 36-45 (EmailData class) with import:

  # Remove: @dataclass class EmailData...
  # Add at line 18:
  from ..schemas import Email, EmailDataCompat as EmailData  # H-1 fix: use canonical model

  # Add deprecation warning in module docstring
  ```

- [ ] **Step 4.2**: Update gmail_api_client.py to use schemas.Email
  ```python
  # File: src/gmail_assistant/core/fetch/gmail_api_client.py
  # Replace import at line 14:
  # OLD: from ..ai.newsletter_cleaner import EmailData
  # NEW:
  from ..schemas import Email, EmailDataCompat as EmailData  # H-1 fix

  # Optionally update to use Email directly in _fetch_email_batch
  ```

- [ ] **Step 4.3**: Add deprecation notice to protocols.py EmailMetadata
  ```python
  # File: src/gmail_assistant/core/protocols.py
  # Add deprecation warning at line 43:
  import warnings

  @dataclass
  class EmailMetadata:
      """
      DEPRECATED: Use gmail_assistant.core.schemas.Email instead.
      This class remains for backward compatibility only.
      """
      def __post_init__(self):
          warnings.warn(
              "EmailMetadata is deprecated. Use Email from gmail_assistant.core.schemas",
              DeprecationWarning,
              stacklevel=2
          )
      # ... rest of class
  ```

- [ ] **Step 4.4**: Update all internal usages to schemas.Email
  ```bash
  # Find all usages:
  grep -r "EmailMetadata\|EmailData" src/gmail_assistant --include="*.py"
  # Update each file to import from schemas.py
  ```

- [ ] **Step 4.5**: Add migration guide to schemas.py
  ```python
  # Add to docstring in schemas.py:
  """
  Migration Guide:

  OLD: from gmail_assistant.core.protocols import EmailMetadata
  NEW: from gmail_assistant.core.schemas import Email

  OLD: from gmail_assistant.core.ai.newsletter_cleaner import EmailData
  NEW: from gmail_assistant.core.schemas import Email

  Compatibility:
      email.to_email_metadata()  # Returns EmailMetadataCompat
      email.to_email_data()      # Returns EmailDataCompat
  """
  ```

**Validation Criteria**:
- [ ] `pytest tests/ -v -k "email"` passes
- [ ] No import errors when using legacy names
- [ ] Deprecation warnings appear when using old classes

**Acceptance Criteria**:
- Single `Email` class in `schemas.py` is source of truth
- Legacy classes issue deprecation warnings
- All internal code uses `schemas.Email`

**Dependencies**: None

---

### H-2: Consolidate Exception Hierarchy

**Priority**: P1 | **Effort**: 8-16 hours | **Risk**: Low

**Current State**:
Exception definitions scattered across 7 files:
- `core/exceptions.py` (canonical): `GmailAssistantError`, `ConfigError`, `AuthError`, `NetworkError`, `APIError`
- `utils/input_validator.py:16`: `ValidationError`
- `utils/circuit_breaker.py:23`: `CircuitBreakerError`
- `utils/rate_limiter.py:18`: `RateLimitError`
- `utils/config_schema.py:14`: `ConfigValidationError`
- `core/auth/base.py:20`: `AuthenticationError`
- `core/fetch/batch_api.py:28`: `BatchAPIError`
- `core/container.py:54,59`: `ServiceNotFoundError`, `CircularDependencyError`
- `export/parquet_exporter.py:38`: `ParquetExportError`

**Files to Modify**:
- `src/gmail_assistant/core/exceptions.py` (add all exceptions)
- All files defining local exceptions (update imports)

**Implementation Steps**:

- [ ] **Step 5.1**: Expand core/exceptions.py with full hierarchy
  ```python
  # File: src/gmail_assistant/core/exceptions.py
  """
  Centralized exception definitions - SINGLE SOURCE OF TRUTH.

  All modules must import exceptions from here.

  Exception Hierarchy:
      GmailAssistantError (base)
      +-- ConfigError (exit code 5)
      |   +-- ConfigValidationError
      +-- AuthError (exit code 3)
      |   +-- AuthenticationError
      +-- NetworkError (exit code 4)
      |   +-- RateLimitError
      +-- APIError (exit code 1)
      |   +-- BatchAPIError
      +-- ValidationError
      +-- ServiceError
      |   +-- ServiceNotFoundError
      |   +-- CircularDependencyError
      +-- CircuitBreakerError
      +-- ExportError
          +-- ParquetExportError
  """
  from __future__ import annotations

  __all__ = [
      # Base
      "GmailAssistantError",
      # Config
      "ConfigError",
      "ConfigValidationError",
      # Auth
      "AuthError",
      "AuthenticationError",
      # Network
      "NetworkError",
      "RateLimitError",
      # API
      "APIError",
      "BatchAPIError",
      # Validation
      "ValidationError",
      # Service
      "ServiceError",
      "ServiceNotFoundError",
      "CircularDependencyError",
      # Circuit Breaker
      "CircuitBreakerError",
      # Export
      "ExportError",
      "ParquetExportError",
  ]


  class GmailAssistantError(Exception):
      """Base exception for Gmail Assistant."""
      pass


  # === Config Exceptions (exit code 5) ===
  class ConfigError(GmailAssistantError):
      """Configuration-related errors."""
      pass


  class ConfigValidationError(ConfigError):
      """Configuration validation errors."""
      pass


  # === Auth Exceptions (exit code 3) ===
  class AuthError(GmailAssistantError):
      """Authentication/authorization errors."""
      pass


  class AuthenticationError(AuthError):
      """Specific authentication errors."""
      pass


  # === Network Exceptions (exit code 4) ===
  class NetworkError(GmailAssistantError):
      """Network connectivity errors."""
      pass


  class RateLimitError(NetworkError):
      """Rate limit exceeded errors."""
      pass


  # === API Exceptions (exit code 1) ===
  class APIError(GmailAssistantError):
      """Gmail API errors."""
      pass


  class BatchAPIError(APIError):
      """Batch API operation errors."""
      def __init__(self, message: str, failed_ids: list = None):
          self.message = message
          self.failed_ids = failed_ids or []
          super().__init__(message)


  # === Validation Exceptions ===
  class ValidationError(GmailAssistantError):
      """Input validation errors."""
      pass


  # === Service Container Exceptions ===
  class ServiceError(GmailAssistantError):
      """Service container errors."""
      pass


  class ServiceNotFoundError(ServiceError):
      """Service not found in container."""
      pass


  class CircularDependencyError(ServiceError):
      """Circular dependency detected."""
      pass


  # === Circuit Breaker ===
  class CircuitBreakerError(GmailAssistantError):
      """Circuit breaker is open."""
      pass


  # === Export Exceptions ===
  class ExportError(GmailAssistantError):
      """Export operation errors."""
      pass


  class ParquetExportError(ExportError):
      """Parquet export specific errors."""
      pass
  ```

- [ ] **Step 5.2**: Update all modules to import from exceptions.py
  ```python
  # Update each file that defines its own exception:

  # utils/input_validator.py:
  # Remove: class ValidationError(Exception)
  # Add: from gmail_assistant.core.exceptions import ValidationError

  # utils/circuit_breaker.py:
  # Remove: class CircuitBreakerError(Exception)
  # Add: from gmail_assistant.core.exceptions import CircuitBreakerError

  # (Repeat for all 7 files)
  ```

- [ ] **Step 5.3**: Update CLI error handling to use hierarchy
  ```python
  # cli/main.py already handles the main exceptions correctly
  # Add handling for new exceptions if needed
  ```

**Validation Criteria**:
- [ ] `python -c "from gmail_assistant.core.exceptions import *"` succeeds
- [ ] All tests pass with new exception imports
- [ ] No duplicate exception class definitions

**Acceptance Criteria**:
- All exceptions defined in `core/exceptions.py`
- Clear hierarchy with proper inheritance
- Consistent naming (all end in `Error`)

**Dependencies**: None

---

### H-3: Fix Bare Exception Handlers

**Priority**: P1 | **Effort**: 16-24 hours | **Risk**: Low

**Current State**:
8 bare `except:` handlers found in:
- `analysis/email_data_converter.py`: lines 124, 138, 156, 165
- `core/processing/extractor.py`: line 112
- `core/fetch/gmail_assistant.py`: line 431
- `core/fetch/incremental.py`: line 144
- `core/fetch/dead_letter_queue.py`: line 16

**Files to Modify**: All files listed above

**Implementation Steps**:

- [ ] **Step 6.1**: Fix email_data_converter.py (4 instances)
  ```python
  # File: src/gmail_assistant/analysis/email_data_converter.py

  # Line 124: Date parsing
  # OLD: except:
  # NEW:
  except (ValueError, TypeError, AttributeError) as e:
      logger.debug(f"Date parsing failed: {e}")

  # Line 138: Encoding detection
  # OLD: except:
  # NEW:
  except (UnicodeDecodeError, LookupError) as e:
      logger.debug(f"Encoding detection failed: {e}")

  # Line 156: JSON parsing
  # OLD: except:
  # NEW:
  except (json.JSONDecodeError, KeyError, TypeError) as e:
      logger.debug(f"JSON parsing failed: {e}")

  # Line 165: CSV parsing
  # OLD: except:
  # NEW:
  except (csv.Error, UnicodeDecodeError) as e:
      logger.debug(f"CSV parsing failed: {e}")
  ```

- [ ] **Step 6.2**: Fix core/processing/extractor.py
  ```python
  # File: src/gmail_assistant/core/processing/extractor.py
  # Line 112
  # OLD: except:
  # NEW:
  except (ValueError, AttributeError, TypeError) as e:
      logger.warning(f"Content extraction failed: {e}")
  ```

- [ ] **Step 6.3**: Fix core/fetch/gmail_assistant.py
  ```python
  # File: src/gmail_assistant/core/fetch/gmail_assistant.py
  # Line 431 (date parsing in download_emails)
  # OLD: except:
  # NEW:
  except (ValueError, TypeError, OverflowError) as e:
      logger.debug(f"Date parsing failed: {e}")
      date_prefix = 'unknown_date'
      folder_date = 'unknown'
  ```

- [ ] **Step 6.4**: Fix core/fetch/incremental.py
  ```python
  # File: src/gmail_assistant/core/fetch/incremental.py
  # Line 144 (date parsing in fetch loop)
  # OLD: except:
  # NEW:
  except (ValueError, TypeError, OverflowError) as e:
      logger.debug(f"Date parsing failed for message: {e}")
      # Fallback logic...
  ```

- [ ] **Step 6.5**: Fix core/fetch/dead_letter_queue.py
  ```python
  # File: src/gmail_assistant/core/fetch/dead_letter_queue.py
  # Line 16
  # OLD: except:
  # NEW:
  except Exception as e:  # Catch-all with logging
      logger.error(f"Dead letter queue error: {e}")
  ```

- [ ] **Step 6.6**: Add ruff rule to prevent future bare excepts
  ```toml
  # pyproject.toml - add to [tool.ruff.lint]:
  select = [
      "E",    # pycodestyle errors
      "W",    # pycodestyle warnings
      "F",    # pyflakes
      "B",    # flake8-bugbear
      "BLE",  # flake8-blind-except (BLE001 = bare except)
  ]
  ```

**Validation Criteria**:
- [ ] `ruff check src/ --select=BLE` returns no errors
- [ ] All tests still pass
- [ ] Errors are properly logged with context

**Acceptance Criteria**:
- Zero bare `except:` handlers
- All exceptions caught with specific types
- Proper logging for debugging

**Dependencies**: None

---

### H-4: Consolidate Duplicate Analysis Modules

**Priority**: P1 | **Effort**: 24-32 hours | **Risk**: Medium

**Current State**:
Three overlapping modules with ~70% code duplication:
- `analysis/daily_email_analysis.py` (850 lines)
- `analysis/daily_email_analyzer.py` (1119 lines)
- `analysis/email_analyzer.py` (850 lines)

**Files to Modify**:
- Create: `src/gmail_assistant/analysis/unified_analyzer.py`
- Modify: `src/gmail_assistant/analysis/__init__.py`
- Deprecate: The three duplicate modules

**Implementation Steps**:

- [ ] **Step 7.1**: Analyze common functionality across modules
  ```bash
  # Identify shared patterns:
  # - Email classification
  # - Sender analysis
  # - Date-based grouping
  # - Statistics generation
  # - Report formatting
  ```

- [ ] **Step 7.2**: Create unified analyzer with strategy pattern
  ```python
  # File: src/gmail_assistant/analysis/unified_analyzer.py
  """
  Unified Email Analyzer - Consolidates analysis functionality.

  Replaces:
  - daily_email_analysis.py (deprecated)
  - daily_email_analyzer.py (deprecated)
  - email_analyzer.py (deprecated)
  """
  from __future__ import annotations

  import logging
  from abc import ABC, abstractmethod
  from dataclasses import dataclass, field
  from datetime import datetime
  from pathlib import Path
  from typing import Dict, List, Any, Optional, Protocol
  from collections import Counter

  from gmail_assistant.core.schemas import Email

  logger = logging.getLogger(__name__)


  # === Analysis Strategy Protocol ===
  class AnalysisStrategy(Protocol):
      """Protocol for analysis strategies."""

      def analyze(self, emails: List[Email]) -> Dict[str, Any]:
          """Analyze emails and return results."""
          ...

      @property
      def name(self) -> str:
          """Strategy name."""
          ...


  # === Concrete Strategies ===
  class SenderAnalysisStrategy:
      """Analyze emails by sender patterns."""

      name = "sender_analysis"

      def analyze(self, emails: List[Email]) -> Dict[str, Any]:
          sender_counts = Counter(e.sender_domain for e in emails)
          return {
              'total_senders': len(set(e.sender for e in emails)),
              'top_domains': sender_counts.most_common(20),
              'newsletters': [e for e in emails if self._is_newsletter(e)]
          }

      def _is_newsletter(self, email: Email) -> bool:
          indicators = ['newsletter', 'digest', 'weekly', 'noreply', 'no-reply']
          return any(ind in email.sender.lower() for ind in indicators)


  class TemporalAnalysisStrategy:
      """Analyze emails by time patterns."""

      name = "temporal_analysis"

      def analyze(self, emails: List[Email]) -> Dict[str, Any]:
          by_month = Counter(e.year_month for e in emails)
          by_hour = Counter(e.date.hour for e in emails if e.date)

          return {
              'by_month': dict(by_month.most_common()),
              'by_hour': dict(by_hour),
              'busiest_hour': by_hour.most_common(1)[0] if by_hour else None,
              'date_range': {
                  'start': min(e.date for e in emails if e.date),
                  'end': max(e.date for e in emails if e.date)
              }
          }


  class ContentAnalysisStrategy:
      """Analyze email content patterns."""

      name = "content_analysis"

      def analyze(self, emails: List[Email]) -> Dict[str, Any]:
          # Subject line analysis
          subject_lengths = [len(e.subject) for e in emails]

          # Label distribution
          all_labels = []
          for e in emails:
              all_labels.extend(e.labels)

          return {
              'avg_subject_length': sum(subject_lengths) / len(subject_lengths) if subject_lengths else 0,
              'label_distribution': dict(Counter(all_labels).most_common(20)),
              'unread_count': sum(1 for e in emails if e.is_unread),
              'starred_count': sum(1 for e in emails if e.is_starred)
          }


  # === Main Analyzer ===
  @dataclass
  class AnalysisResult:
      """Container for analysis results."""
      total_emails: int
      strategies_applied: List[str]
      results: Dict[str, Any]
      generated_at: datetime = field(default_factory=datetime.now)

      def to_dict(self) -> Dict[str, Any]:
          return {
              'total_emails': self.total_emails,
              'strategies': self.strategies_applied,
              'results': self.results,
              'generated_at': self.generated_at.isoformat()
          }


  class UnifiedEmailAnalyzer:
      """
      Unified email analyzer using strategy pattern.

      Usage:
          analyzer = UnifiedEmailAnalyzer()
          analyzer.add_strategy(SenderAnalysisStrategy())
          analyzer.add_strategy(TemporalAnalysisStrategy())

          result = analyzer.analyze(emails)
          print(result.to_dict())
      """

      def __init__(self):
          self.strategies: List[AnalysisStrategy] = []

      def add_strategy(self, strategy: AnalysisStrategy) -> 'UnifiedEmailAnalyzer':
          """Add analysis strategy. Returns self for chaining."""
          self.strategies.append(strategy)
          return self

      def analyze(self, emails: List[Email]) -> AnalysisResult:
          """Run all registered strategies."""
          if not emails:
              return AnalysisResult(
                  total_emails=0,
                  strategies_applied=[],
                  results={}
              )

          results = {}
          strategies_applied = []

          for strategy in self.strategies:
              try:
                  results[strategy.name] = strategy.analyze(emails)
                  strategies_applied.append(strategy.name)
              except Exception as e:
                  logger.error(f"Strategy {strategy.name} failed: {e}")
                  results[strategy.name] = {'error': str(e)}

          return AnalysisResult(
              total_emails=len(emails),
              strategies_applied=strategies_applied,
              results=results
          )

      @classmethod
      def default(cls) -> 'UnifiedEmailAnalyzer':
          """Create analyzer with default strategies."""
          return (
              cls()
              .add_strategy(SenderAnalysisStrategy())
              .add_strategy(TemporalAnalysisStrategy())
              .add_strategy(ContentAnalysisStrategy())
          )


  # === Backward Compatibility ===
  # These aliases allow existing code to keep working
  def analyze_emails_daily(*args, **kwargs):
      """DEPRECATED: Use UnifiedEmailAnalyzer instead."""
      import warnings
      warnings.warn(
          "analyze_emails_daily is deprecated. Use UnifiedEmailAnalyzer.",
          DeprecationWarning
      )
      return UnifiedEmailAnalyzer.default().analyze(*args, **kwargs)
  ```

- [ ] **Step 7.3**: Update __init__.py to expose unified analyzer
  ```python
  # File: src/gmail_assistant/analysis/__init__.py
  """Email analysis module."""

  from .unified_analyzer import (
      UnifiedEmailAnalyzer,
      AnalysisResult,
      AnalysisStrategy,
      SenderAnalysisStrategy,
      TemporalAnalysisStrategy,
      ContentAnalysisStrategy,
  )

  # Deprecated imports (with warnings)
  from .unified_analyzer import analyze_emails_daily

  __all__ = [
      'UnifiedEmailAnalyzer',
      'AnalysisResult',
      'AnalysisStrategy',
      'SenderAnalysisStrategy',
      'TemporalAnalysisStrategy',
      'ContentAnalysisStrategy',
  ]
  ```

- [ ] **Step 7.4**: Add deprecation notices to old modules
  ```python
  # At top of each deprecated module:
  import warnings
  warnings.warn(
      f"{__name__} is deprecated. Use gmail_assistant.analysis.UnifiedEmailAnalyzer",
      DeprecationWarning,
      stacklevel=2
  )
  ```

- [ ] **Step 7.5**: Update CLI analyze command to use unified analyzer

- [ ] **Step 7.6**: Create migration tests
  ```python
  # File: tests/analysis/test_unified_analyzer.py
  def test_unified_analyzer_replaces_legacy():
      """Verify unified analyzer provides same functionality."""
      ...
  ```

**Validation Criteria**:
- [ ] `UnifiedEmailAnalyzer` passes all existing analysis tests
- [ ] Deprecated modules still work with warnings
- [ ] Code coverage maintained for analysis functionality

**Acceptance Criteria**:
- Single `UnifiedEmailAnalyzer` class replaces 3 modules
- Strategy pattern allows extension without modification
- ~2000+ lines of duplicate code removed
- Backward compatibility preserved with deprecation warnings

**Dependencies**: H-1 (uses unified Email schema)

---

## Phase 3: Architecture Debt (Weeks 5-6)

**Total Effort**: 60-80 hours

### M-1: Refactor GmailFetcher God Object

**Priority**: P2 | **Effort**: 32-40 hours | **Risk**: High

**Current State**:
`core/fetch/gmail_assistant.py` has 18+ responsibilities:
- Authentication
- Search
- Download
- EML creation
- Markdown creation
- File operations
- Base64 decoding
- Header extraction
- Body parsing
- Filename sanitization
- Atomic writes
- Progress tracking
- Error handling
- HTML conversion
- Memory tracking
- Streaming
- Progressive loading
- CLI entry point

**Files to Create**:
- `src/gmail_assistant/core/fetch/message_processor.py`
- `src/gmail_assistant/core/fetch/file_writer.py`
- `src/gmail_assistant/core/fetch/formatters/eml.py`
- `src/gmail_assistant/core/fetch/formatters/markdown.py`

**Implementation Steps**:

- [ ] **Step 8.1**: Extract message processing logic
  ```python
  # File: src/gmail_assistant/core/fetch/message_processor.py
  """Message processing utilities extracted from GmailFetcher."""

  from typing import Dict, List, Tuple, Optional
  import base64
  import binascii
  import logging

  logger = logging.getLogger(__name__)


  class MessageProcessor:
      """Processes Gmail API message responses."""

      def extract_headers(self, headers: List[Dict]) -> Dict[str, str]:
          """Extract and normalize email headers."""
          return {h.get('name', '').lower(): h.get('value', '') for h in headers}

      def decode_base64(self, data: str) -> str:
          """Decode base64 email data with padding correction."""
          try:
              data = data.replace('-', '+').replace('_', '/')
              missing_padding = len(data) % 4
              if missing_padding:
                  data += '=' * (4 - missing_padding)
              return base64.b64decode(data).decode('utf-8')
          except (ValueError, UnicodeDecodeError, binascii.Error) as e:
              logger.warning(f"Base64 decode error: {e}")
              return ""

      def get_message_body(self, payload: Dict) -> Tuple[str, str]:
          """Extract plain text and HTML body from payload."""
          plain_text = ""
          html_body = ""

          def extract_parts(part):
              nonlocal plain_text, html_body
              if 'parts' in part:
                  for subpart in part['parts']:
                      extract_parts(subpart)
              else:
                  mime_type = part.get('mimeType', '')
                  body_data = part.get('body', {}).get('data', '')
                  if body_data:
                      decoded = self.decode_base64(body_data)
                      if mime_type == 'text/plain':
                          plain_text += decoded
                      elif mime_type == 'text/html':
                          html_body += decoded

          extract_parts(payload)
          return plain_text, html_body
  ```

- [ ] **Step 8.2**: Extract file writing logic
  ```python
  # File: src/gmail_assistant/core/fetch/file_writer.py
  """File writing utilities with atomic operations."""

  import os
  import re
  import tempfile
  from pathlib import Path
  from typing import Optional
  import logging

  logger = logging.getLogger(__name__)


  class SecureFileWriter:
      """Handles secure file writing operations."""

      def sanitize_filename(self, filename: str, max_length: int = 200) -> str:
          """Sanitize filename for filesystem compatibility."""
          filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
          filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
          if len(filename) > max_length:
              filename = filename[:max_length]
          return filename.strip()

      def atomic_write(
          self,
          path: Path,
          content: str,
          encoding: str = 'utf-8'
      ) -> None:
          """Write file atomically using temp file + rename."""
          dir_path = path.parent
          dir_path.mkdir(parents=True, exist_ok=True)

          fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix='.tmp')
          try:
              with os.fdopen(fd, 'w', encoding=encoding) as f:
                  f.write(content)
                  f.flush()
                  os.fsync(f.fileno())
              os.replace(tmp_path, path)
          except Exception:
              if os.path.exists(tmp_path):
                  os.unlink(tmp_path)
              raise
  ```

- [ ] **Step 8.3**: Extract format generators
  ```python
  # File: src/gmail_assistant/core/fetch/formatters/eml.py
  """EML format generator."""

  from typing import Dict
  import datetime


  class EMLFormatter:
      """Generates EML format from message data."""

      def format(self, message_data: Dict, headers: Dict, plain_text: str, html_body: str) -> str:
          """Create EML content from message data."""
          eml_lines = []

          essential_headers = [
              'message-id', 'date', 'from', 'to', 'cc', 'bcc',
              'subject', 'reply-to', 'in-reply-to', 'references'
          ]

          for header_name in essential_headers:
              if header_name in headers:
                  formatted = '-'.join(w.capitalize() for w in header_name.split('-'))
                  eml_lines.append(f"{formatted}: {headers[header_name]}")

          # Gmail specific headers
          eml_lines.append(f"X-Gmail-Message-ID: {message_data['id']}")
          eml_lines.append(f"X-Gmail-Thread-ID: {message_data['threadId']}")

          if 'labelIds' in message_data:
              eml_lines.append(f"X-Gmail-Labels: {', '.join(message_data['labelIds'])}")

          eml_lines.append("MIME-Version: 1.0")

          # Add body content (multipart if both exist)
          # ... (rest of body handling)

          return "\n".join(eml_lines)
  ```

- [ ] **Step 8.4**: Refactor GmailFetcher to use extracted classes
  ```python
  # File: src/gmail_assistant/core/fetch/gmail_assistant.py
  # Simplify to orchestration role only

  from .message_processor import MessageProcessor
  from .file_writer import SecureFileWriter
  from .formatters.eml import EMLFormatter
  from .formatters.markdown import MarkdownFormatter


  class GmailFetcher:
      """Gmail email fetcher - orchestrates fetch operations."""

      def __init__(self, credentials_file: str = 'credentials.json'):
          self.auth = ReadOnlyGmailAuth(credentials_file)
          self.processor = MessageProcessor()
          self.writer = SecureFileWriter()
          self.eml_formatter = EMLFormatter()
          self.md_formatter = MarkdownFormatter()
          # ... rest of init

      # Delegate to extracted classes
      def decode_base64(self, data: str) -> str:
          return self.processor.decode_base64(data)

      def extract_headers(self, headers: List[Dict]) -> Dict[str, str]:
          return self.processor.extract_headers(headers)

      # ... etc
  ```

**Validation Criteria**:
- [ ] All existing tests pass without modification
- [ ] `GmailFetcher` public API unchanged
- [ ] Each extracted class has unit tests

**Acceptance Criteria**:
- `GmailFetcher` reduced to <200 lines (from 500+)
- Single responsibility for each new class
- Clear dependency injection pattern

**Dependencies**: C-1, C-2 (wait for batch API and CLI completion)

---

### M-2 to M-9: Medium Priority Items

*(Abbreviated for document length - follow same pattern)*

#### M-2: Fix Deep Relative Imports
- [ ] Replace `...utils` with absolute imports
- [ ] Update 5+ core modules
- [ ] Add import linting rule

#### M-3: Type Hints Gaps
- [ ] Fix `callable` -> `Callable` in utils modules
- [ ] Add `from typing import Callable` where missing
- [ ] Run `mypy src/` to verify

#### M-4: Coverage Gaps
- [ ] Remove fetch/deletion exclusions from pyproject.toml
- [ ] Add tests for excluded modules
- [ ] Target 95% coverage

#### M-5: Async Fetcher Integration
- [ ] Create CLI `--async` flag
- [ ] Wire async_fetcher.py to CLI
- [ ] Add async progress display

#### M-6: Email Content Encryption
- [ ] Add `--encrypt` flag to fetch command
- [ ] Implement Fernet encryption for stored emails
- [ ] Store key in keyring

#### M-7: Error Disclosure in Logs
- [ ] Review error_handler.py line 184
- [ ] Sanitize stack traces before logging
- [ ] Remove sensitive data from error messages

#### M-8: Config Integrity Validation
- [ ] Add checksum to config files
- [ ] Validate on load
- [ ] Warn on tampering

#### M-9: Repository Pattern for Database
- [ ] Create `EmailRepository` protocol
- [ ] Implement for SQLite
- [ ] Add to container

---

## Phase 4: Security Hardening (Week 7)

**Total Effort**: 20-30 hours

### L-1 to L-8: Low Priority Items

*(Abbreviated - follow same pattern as above)*

#### L-1: Consistent Exception Naming
- [ ] Standardize to `*Error` suffix (done in H-2)

#### L-2: Universal SecureLogger Adoption
- [ ] Replace `logging.getLogger` with `SecureLogger` in all modules
- [ ] Add PII redaction to all log outputs

#### L-3: Secure Temp File Deletion
- [ ] Use `shutil.rmtree` with `onerror` handler
- [ ] Overwrite before delete for sensitive files

#### L-4: Pin Transitive Dependencies
- [ ] Generate `requirements.lock` with `pip-compile`
- [ ] Add to version control

#### L-5: TODO/FIXME Cleanup
- [ ] Resolve or remove all TODO markers
- [ ] File: parsers/gmail_eml_to_markdown_cleaner.py
- [ ] File: core/fetch/gmail_assistant.py (and 3 others)

#### L-6: Mutable Defaults in Dataclasses
- [ ] Change `labels: List[str] = []` to `labels: List[str] = field(default_factory=list)`
- [ ] Review all dataclasses in protocols.py

#### L-7: Create SECURITY.md
- [ ] Document security practices
- [ ] Add vulnerability reporting process
- [ ] List security features

#### L-8: Config Versioning
- [ ] Add `version` field to config schema
- [ ] Implement migration on version mismatch

---

## Task Dependency Graph

```
Phase 1 (Parallel Start):
  C-1 (Batch API) ─────┐
  C-3 (Checkpoint) ────┼──> C-2 (CLI Commands)
                       │
Phase 2 (After Phase 1):
  H-1 (Schemas) ───────┼──> H-4 (Analysis Consolidation)
  H-2 (Exceptions) ────┤
  H-3 (Bare Excepts) ──┘

Phase 3 (After Phase 2):
  M-1 (God Object Refactor) ──> M-5 (Async Integration)
  M-2..M-9 (Parallel)

Phase 4 (After Phase 3):
  L-1..L-8 (All Parallel)
```

**Parallel Execution Opportunities**:
- C-1 and C-3 can run simultaneously
- H-1, H-2, H-3 can run simultaneously
- All M-2 through M-9 can run simultaneously
- All L-* items can run simultaneously

---

## Final Validation Checklist

### Performance Verification
- [ ] Benchmark batch API vs sequential: `python -m pytest tests/performance/ -v`
- [ ] Verify 80%+ improvement on 100+ email operations
- [ ] Memory usage stays under 500MB for 10K emails

### Functionality Verification
- [ ] All CLI commands functional:
  ```bash
  gmail-assistant fetch --help
  gmail-assistant delete --help
  gmail-assistant analyze --help
  gmail-assistant auth --help
  gmail-assistant config --show
  ```
- [ ] Checkpoint resume works after Ctrl+C
- [ ] OAuth flow completes successfully

### Code Quality Verification
```bash
# Run full test suite
pytest tests/ -v --cov=gmail_assistant --cov-report=term-missing

# Verify coverage > 90%
coverage report --fail-under=90

# Run linting
ruff check src/

# Run type checking
mypy src/gmail_assistant

# Check for bare exceptions
ruff check src/ --select=BLE

# Check for TODO markers
grep -r "TODO\|FIXME" src/gmail_assistant --include="*.py" | wc -l
# Should return 0
```

### Security Verification
```bash
# Run security tests
pytest tests/security/ -v

# Check for secrets
git secrets --scan

# Verify no plaintext credentials
grep -r "token\|password\|secret\|key" src/ --include="*.py" | grep -v "keyring"
```

### Documentation Verification
- [ ] SECURITY.md exists
- [ ] All public APIs have docstrings
- [ ] CLI --help output is complete

### Deprecation Verification
- [ ] All deprecated classes emit warnings
- [ ] Migration guide in schemas.py is complete
- [ ] No code uses deprecated imports without warnings

---

## Success Metrics

| Metric | Before | Target | Verification Command |
|--------|--------|--------|---------------------|
| Batch API Performance | N/A | 80%+ faster | `pytest tests/performance/` |
| CLI Functionality | 0/4 commands | 4/4 commands | Manual test all commands |
| Test Coverage | 90.60% | >90% | `pytest --cov` |
| Bare Exceptions | 8 | 0 | `ruff check --select=BLE` |
| Duplicate Code | ~3000 lines | <500 lines | Analysis module LOC |
| Critical Issues | 3 | 0 | Manual review |
| High Issues | 4 | 0 | Manual review |

---

*Document prepared by Claude Opus 4.5*
*Last updated: 2026-01-10*
