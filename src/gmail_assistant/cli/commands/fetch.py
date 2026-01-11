"""Fetch command implementation (C-2 fix)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from gmail_assistant.core.exceptions import AuthError
from gmail_assistant.core.fetch.checkpoint import CheckpointManager
from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher
from gmail_assistant.utils.secure_logger import SecureLogger

logger = SecureLogger(__name__)


def fetch_emails(
    query: str,
    max_emails: int,
    output_dir: Path,
    output_format: str,
    credentials_path: Path,
    resume: bool = False
) -> dict[str, Any]:
    """
    Fetch emails from Gmail (C-2 implementation).

    Args:
        query: Gmail search query
        max_emails: Maximum emails to fetch
        output_dir: Output directory
        output_format: json, mbox, or eml
        credentials_path: Path to credentials.json
        resume: Resume from last checkpoint

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

    # Initialize fetcher
    fetcher = GmailFetcher(str(credentials_path))
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
    """Save email in the specified format."""
    # Generate safe filename
    subject = email_data.get('subject', 'no_subject')[:50]
    import re
    safe_subject = re.sub(r'[<>:"/\\|?*]', '_', subject)
    msg_id = email_data.get('id', str(index))[:16]

    if output_format == 'json':
        filename = f"{index:05d}_{safe_subject}_{msg_id}.json"
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, indent=2, default=str)

    elif output_format == 'eml':
        filename = f"{index:05d}_{safe_subject}_{msg_id}.eml"
        filepath = output_dir / filename
        raw_content = email_data.get('raw_content', '')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(raw_content)

    elif output_format == 'mbox':
        # Append to single mbox file
        mbox_path = output_dir / "emails.mbox"
        raw_content = email_data.get('raw_content', '')
        with open(mbox_path, 'a', encoding='utf-8') as f:
            # mbox format requires From line
            f.write(f"From {email_data.get('sender', 'unknown')}\n")
            f.write(raw_content)
            f.write("\n\n")


__all__ = ['fetch_emails']
