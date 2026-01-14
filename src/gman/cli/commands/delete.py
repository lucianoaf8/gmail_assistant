"""Delete command implementation (C-2 fix, H-1 DI integration)."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from gman.core.container import ServiceContainer, get_global_container
from gman.core.exceptions import APIError
from gman.core.fetch.gmail_api_client import GmailAPIClient
from gman.utils.secure_logger import SecureLogger

if TYPE_CHECKING:
    from gman.core.container import ServiceContainer

logger = SecureLogger(__name__)


def _get_api_client(
    credentials_path: Path,
    container: ServiceContainer | None = None,
) -> GmailAPIClient:
    """
    Get a GmailAPIClient instance, preferring DI container when available.

    H-1 fix: Enables testability by allowing mock client injection.

    Args:
        credentials_path: Path to credentials.json
        container: Optional DI container

    Returns:
        GmailAPIClient instance
    """
    # Try provided container first
    if container is not None:
        try:
            client = container.try_resolve(GmailAPIClient)
            if client is not None:
                return client
        except Exception:
            pass

    # Try global container
    global_container = get_global_container()
    if global_container is not None:
        try:
            client = global_container.try_resolve(GmailAPIClient)
            if client is not None:
                return client
        except Exception:
            pass

    # Fall back to direct instantiation
    return GmailAPIClient(str(credentials_path))


def delete_emails(
    query: str,
    credentials_path: Path,
    dry_run: bool = True,
    use_trash: bool = True,
    max_delete: int = 1000,
    container: ServiceContainer | None = None,
) -> dict[str, Any]:
    """
    Delete emails matching query (C-2 implementation, H-1 DI integration).

    Args:
        query: Gmail search query for emails to delete
        credentials_path: Path to credentials.json
        dry_run: If True, only show what would be deleted
        use_trash: If True, move to trash instead of permanent delete
        max_delete: Maximum emails to delete
        container: Optional DI container for service resolution (H-1 fix)

    Returns:
        Dict with deletion statistics

    Raises:
        AuthError: If authentication fails
        APIError: If Gmail API returns error
    """
    # H-1: Use container for client resolution, or fall back to direct instantiation
    client = _get_api_client(credentials_path, container)

    click.echo(f"Query: {query}")
    click.echo(f"Mode: {'DRY RUN' if dry_run else 'TRASH' if use_trash else 'PERMANENT DELETE'}")

    # Search for emails matching query
    click.echo("Searching for matching emails...")

    try:
        results = client.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_delete
        ).execute()

        messages = results.get('messages', [])
        total_found = len(messages)

        if not messages:
            click.echo("No emails found matching query")
            return {'found': 0, 'deleted': 0, 'failed': 0}

        click.echo(f"Found {total_found} emails matching query")

        # Dry run - just show what would be deleted
        if dry_run:
            click.echo("\nEmails that would be deleted:")
            # Show first 10 for preview
            preview_count = min(10, len(messages))
            for msg in messages[:preview_count]:
                try:
                    msg_detail = client.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()
                    headers = {h['name']: h['value'] for h in msg_detail['payload']['headers']}
                    click.echo(f"  - {headers.get('Subject', '(no subject)')[:60]}")
                    click.echo(f"    From: {headers.get('From', 'unknown')}")
                except Exception:
                    click.echo(f"  - Message ID: {msg['id']}")

            if total_found > preview_count:
                click.echo(f"  ... and {total_found - preview_count} more")

            click.echo(f"\nTotal: {total_found} emails would be {'trashed' if use_trash else 'deleted'}")
            click.echo("Run with --confirm to execute deletion")
            return {'found': total_found, 'deleted': 0, 'failed': 0, 'dry_run': True}

        # Actual deletion
        email_ids = [msg['id'] for msg in messages]

        if use_trash:
            result = client.trash_emails(email_ids)
            click.echo(f"\nTrashed {result['trashed']} emails")
            if result['failed'] > 0:
                click.echo(f"Failed: {result['failed']} emails")
            return {
                'found': total_found,
                'deleted': result['trashed'],
                'failed': result['failed']
            }
        else:
            result = client.delete_emails(email_ids)
            click.echo(f"\nPermanently deleted {result['deleted']} emails")
            if result['failed'] > 0:
                click.echo(f"Failed: {result['failed']} emails")
            return {
                'found': total_found,
                'deleted': result['deleted'],
                'failed': result['failed']
            }

    except Exception as e:
        logger.error(f"Error during delete operation: {e}")
        raise APIError(f"Delete operation failed: {e}") from e


def get_email_count(
    query: str,
    credentials_path: Path,
    container: ServiceContainer | None = None,
) -> int:
    """
    Get count of emails matching query.

    Args:
        query: Gmail search query
        credentials_path: Path to credentials.json
        container: Optional DI container for service resolution (H-1 fix)

    Returns:
        Estimated count of matching emails
    """
    client = _get_api_client(credentials_path, container)

    try:
        results = client.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=1
        ).execute()

        # Gmail doesn't provide exact count, estimate from resultSizeEstimate
        return results.get('resultSizeEstimate', 0)
    except Exception as e:
        logger.error(f"Error getting email count: {e}")
        return 0


__all__ = ['delete_emails', 'get_email_count']
