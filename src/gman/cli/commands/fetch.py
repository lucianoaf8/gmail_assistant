"""Fetch command implementation (C-2 fix, H-1 DI integration, L-9 secure writes)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from gman.core.container import ServiceContainer, get_global_container
from gman.core.exceptions import AuthError
from gman.core.fetch.checkpoint import CheckpointManager
from gman.core.fetch.gman import GmailFetcher
from gman.utils.secure_file import secure_write_file, PathValidationError
from gman.utils.secure_logger import SecureLogger

if TYPE_CHECKING:
    from gman.core.container import ServiceContainer

logger = SecureLogger(__name__)


def _get_fetcher(
    credentials_path: Path,
    container: ServiceContainer | None = None,
) -> GmailFetcher:
    """
    Get a GmailFetcher instance, preferring DI container when available.

    H-1 fix: Enables testability by allowing mock fetcher injection.

    Args:
        credentials_path: Path to credentials.json
        container: Optional DI container

    Returns:
        GmailFetcher instance
    """
    # Try provided container first
    if container is not None:
        try:
            fetcher = container.try_resolve(GmailFetcher)
            if fetcher is not None:
                return fetcher
        except Exception:
            pass  # Fall through to other methods

    # Try global container
    global_container = get_global_container()
    if global_container is not None:
        try:
            fetcher = global_container.try_resolve(GmailFetcher)
            if fetcher is not None:
                return fetcher
        except Exception:
            pass  # Fall through to direct instantiation

    # Fall back to direct instantiation (maintains backward compatibility)
    return GmailFetcher(str(credentials_path))


def fetch_emails(
    query: str,
    max_emails: int,
    output_dir: Path,
    output_format: str,
    credentials_path: Path,
    resume: bool = False,
    container: ServiceContainer | None = None,
) -> dict[str, Any]:
    """
    Fetch emails from Gmail (C-2 implementation, H-1 DI integration).

    Args:
        query: Gmail search query
        max_emails: Maximum emails to fetch
        output_dir: Output directory
        output_format: json, mbox, or eml
        credentials_path: Path to credentials.json
        resume: Resume from last checkpoint
        container: Optional DI container for service resolution (H-1 fix)

    Returns:
        Dict with fetch statistics

    Raises:
        AuthError: If authentication fails
        NetworkError: If network issues occur
        APIError: If Gmail API returns error
    """
    checkpoint_mgr = CheckpointManager()
    skip_count = 0

    # Check for resumable checkpoint
    if resume:
        checkpoint = checkpoint_mgr.get_latest_checkpoint(query=query, resumable_only=True)
        if checkpoint:
            click.echo(f"Resuming from checkpoint: {checkpoint.sync_id}")
            resume_info = checkpoint_mgr.get_resume_info(checkpoint)
            skip_count = resume_info['skip_count']
        else:
            click.echo("No checkpoint found, starting fresh")

    # H-1: Use container for fetcher resolution, or fall back to direct instantiation
    fetcher = _get_fetcher(credentials_path, container)
    if not fetcher.authenticate():
        raise AuthError("Gmail authentication failed")

    click.echo("Authenticated successfully")

    # Create checkpoint for new fetch
    if not resume or not checkpoint_mgr.get_latest_checkpoint(query=query, resumable_only=True):
        checkpoint = checkpoint_mgr.create_checkpoint(
            query=query,
            output_directory=str(output_dir),
            metadata={'format': output_format, 'max_emails': max_emails}
        )
    else:
        checkpoint = checkpoint_mgr.get_latest_checkpoint(query=query, resumable_only=True)

    try:
        # Search for messages
        click.echo(f"Searching for emails with query: {query or '(all)'}")
        message_ids = fetcher.search_messages(query=query, max_results=max_emails)

        if not message_ids:
            click.echo("No emails found matching query")
            checkpoint_mgr.mark_completed(checkpoint)
            return {'fetched': 0, 'total': 0}

        click.echo(f"Found {len(message_ids)} emails")
        checkpoint.total_messages = len(message_ids)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Fetch with progress tracking
        fetched = 0
        with click.progressbar(
            enumerate(message_ids),
            length=len(message_ids),
            label="Fetching emails"
        ) as bar:
            for i, msg_id in bar:
                # Skip already processed messages when resuming
                if i < skip_count:
                    continue

                try:
                    email_data = fetcher.get_message_details(msg_id)
                    if email_data:
                        _save_email(email_data, output_dir, output_format, i)
                        fetched += 1

                    # Update checkpoint every 50 emails
                    if fetched > 0 and fetched % 50 == 0:
                        checkpoint_mgr.update_progress(
                            checkpoint,
                            processed=i + 1,
                            last_message_id=msg_id
                        )
                except Exception as e:
                    logger.warning(f"Failed to fetch email {msg_id}: {e}")
                    continue

        checkpoint_mgr.mark_completed(checkpoint)
        checkpoint_mgr.cleanup_old_checkpoints()

        return {'fetched': fetched, 'total': len(message_ids)}

    except Exception:
        checkpoint_mgr.mark_interrupted(checkpoint)
        raise


def _save_email(email_data: dict[str, Any], output_dir: Path, output_format: str, index: int) -> None:
    """
    Save email in the specified format.

    L-9 fix: Uses secure_write_file with path validation to prevent
    path traversal attacks and ensure files stay within output_dir.
    """
    import re

    # Generate safe filename - extract subject from headers if not at top level
    subject = email_data.get('subject')
    if not subject and 'payload' in email_data:
        headers = email_data.get('payload', {}).get('headers', [])
        for header in headers:
            if header.get('name', '').lower() == 'subject':
                subject = header.get('value', '')
                break
    subject = (subject or 'no_subject')[:50]
    safe_subject = re.sub(r'[<>:"/\\|?*]', '_', subject)
    msg_id = email_data.get('id', str(index))[:16]

    # L-9: Define allowed extensions per format
    allowed_extensions = {'.json', '.eml', '.mbox'}

    try:
        if output_format == 'json':
            filename = f"{index:05d}_{safe_subject}_{msg_id}.json"
            content = json.dumps(email_data, indent=2, default=str)
            secure_write_file(
                output_dir / filename,
                content,
                base_dir=output_dir,
                allowed_extensions={'.json'},
            )

        elif output_format == 'eml':
            filename = f"{index:05d}_{safe_subject}_{msg_id}.eml"
            raw_content = email_data.get('raw_content', '')
            secure_write_file(
                output_dir / filename,
                raw_content,
                base_dir=output_dir,
                allowed_extensions={'.eml'},
            )

        elif output_format == 'mbox':
            # Append to single mbox file - use secure write for initial creation
            mbox_path = output_dir / "emails.mbox"
            raw_content = email_data.get('raw_content', '')
            mbox_entry = f"From {email_data.get('sender', 'unknown')}\n{raw_content}\n\n"

            # For mbox, we need to append - validate path first
            from gman.utils.secure_file import validate_write_path
            validated_path = validate_write_path(
                mbox_path,
                base_dir=output_dir,
                allowed_extensions={'.mbox'}
            )
            # Append mode for mbox
            with open(validated_path, 'a', encoding='utf-8') as f:
                f.write(mbox_entry)

    except PathValidationError as e:
        logger.error(f"L-9 security: Path validation failed: {e}")
        raise


__all__ = ['fetch_emails']
