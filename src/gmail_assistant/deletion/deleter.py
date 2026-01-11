#!/usr/bin/env python3
"""
Gmail Bulk Deletion Tool
Safely delete emails using Gmail API with rate limiting and safety checks.
"""

import io
import logging
import sys

# Force UTF-8 encoding for Windows to support emojis and special characters
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import argparse

import pandas as pd
from googleapiclient.errors import HttpError
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from gmail_assistant.core.auth.credential_manager import SecureCredentialManager
from gmail_assistant.core.constants import SCOPES_MODIFY

# Local imports
from gmail_assistant.utils.rate_limiter import GmailRateLimiter, QuotaTracker


class GmailDeleter:
    def __init__(self, credentials_file: str = 'credentials.json'):
        """Initialize Gmail API client with secure authentication and rate limiting"""
        self.SCOPES = SCOPES_MODIFY
        self.credential_manager = SecureCredentialManager(credentials_file)
        self.rate_limiter = GmailRateLimiter(requests_per_second=8.0)  # Conservative rate
        self.quota_tracker = QuotaTracker()
        self.console = Console()
        self.logger = logging.getLogger(__name__)
        self._authenticate()

    def _authenticate(self):
        """Handle secure OAuth2 authentication with rate limiting"""
        if self.credential_manager.authenticate():
            self.console.print("✓ Gmail API authenticated successfully", style="green")
        else:
            raise RuntimeError("Failed to authenticate with Gmail API")

    @property
    def service(self):
        """Get Gmail service with automatic authentication"""
        return self.credential_manager.get_service()

    def get_email_count(self, query: str = '') -> int:
        """Get total count of emails matching query"""
        try:
            result = self.service.users().messages().list(userId='me', q=query).execute()
            return result.get('resultSizeEstimate', 0)
        except HttpError as error:
            self.console.print(f"Error getting email count: {error}", style="red")
            return 0

    def list_emails(self, query: str = '', max_results: int | None = None) -> list[str]:
        """List email IDs matching query with pagination"""
        message_ids = []

        try:
            # Initial request
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=min(500, max_results) if max_results else 500
            ).execute()

            messages = result.get('messages', [])
            message_ids.extend([msg['id'] for msg in messages])

            # Handle pagination
            while 'nextPageToken' in result and (not max_results or len(message_ids) < max_results):
                remaining = max_results - len(message_ids) if max_results else 500

                result = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=min(500, remaining),
                    pageToken=result['nextPageToken']
                ).execute()

                messages = result.get('messages', [])
                message_ids.extend([msg['id'] for msg in messages])

                if not messages:
                    break

            return message_ids[:max_results] if max_results else message_ids

        except HttpError as error:
            self.console.print(f"Error listing emails: {error}", style="red")
            return []

    def delete_emails_batch(self, message_ids: list[str], batch_size: int = 100) -> dict[str, int]:
        """Delete emails in batches with rate limiting and beautiful progress display"""
        if not message_ids:
            return {'deleted': 0, 'failed': 0}

        deleted_count = 0
        failed_count = 0

        # Create beautiful progress display
        total_batches = (len(message_ids) + batch_size - 1) // batch_size

        # Create a progress table for status display
        status_table = Table(box=box.ROUNDED, title="🗑️ Gmail Deletion Status", title_style="bold magenta")
        status_table.add_column("Metric", style="cyan", no_wrap=True)
        status_table.add_column("Value", style="green")

        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold blue]Deleting emails..."),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False
        ) as progress:

            # Add main deletion task
            deletion_task = progress.add_task(
                f"[cyan]Processing {len(message_ids)} emails in batches of {batch_size}",
                total=total_batches
            )

            # Process in batches
            for i in range(0, len(message_ids), batch_size):
                batch = message_ids[i:i + batch_size]
                batch_num = (i // batch_size) + 1

                # Update progress description
                progress.update(
                    deletion_task,
                    description=f"[cyan]Batch {batch_num}/{total_batches} ({len(batch)} emails)"
                )

                try:
                    # Use batchDelete for efficiency (up to 1000 IDs)
                    request_body = {'ids': batch}
                    self.service.users().messages().batchDelete(
                        userId='me',
                        body=request_body
                    ).execute()

                    deleted_count += len(batch)

                    # Update progress
                    progress.advance(deletion_task)

                    # Advanced rate limiting with exponential backoff
                    self.rate_limiter.wait_if_needed(quota_cost=50)  # Batch delete costs more

                except HttpError as error:
                    self.console.print(f"Batch delete failed: {error}", style="yellow")
                    failed_count += len(batch)

                    # If batch fails, try individual deletes with sub-progress
                    individual_task = progress.add_task(
                        "[yellow]Individual deletion fallback",
                        total=len(batch)
                    )

                    for msg_id in batch:
                        try:
                            self.service.users().messages().delete(userId='me', id=msg_id).execute()
                            deleted_count += 1
                            failed_count -= 1
                            progress.advance(individual_task)
                            self.rate_limiter.wait_if_needed(quota_cost=10)  # Individual delete
                        except HttpError:
                            progress.advance(individual_task)
                            pass  # Keep failed count

                    progress.remove_task(individual_task)
                    progress.advance(deletion_task)

        # Display final results in a beautiful panel
        result_panel = Panel(
            f"✅ [green]Successfully deleted:[/green] [bold]{deleted_count}[/bold] emails\n"
            f"❌ [red]Failed to delete:[/red] [bold]{failed_count}[/bold] emails\n"
            f"📊 [blue]Success rate:[/blue] [bold]{(deleted_count/(deleted_count+failed_count)*100 if (deleted_count+failed_count) > 0 else 0):.1f}%[/bold]",
            title="🎉 Deletion Complete",
            border_style="green"
        )
        self.console.print(result_panel)

        return {'deleted': deleted_count, 'failed': failed_count}

    def delete_by_query(self, query: str, dry_run: bool = True, max_delete: int | None = None) -> dict[str, int]:
        """Delete emails matching a query with safety checks and beautiful display"""

        # Create query info panel
        query_panel = Panel(
            f"[cyan]Search Query:[/cyan] [bold]{query}[/bold]",
            title="🔍 Gmail Query",
            border_style="blue"
        )
        self.console.print(query_panel)

        # Get email count first with spinner
        with self.console.status("[bold green]Counting matching emails..."):
            total_count = self.get_email_count(query)

        if total_count == 0:
            self.console.print("✅ No emails found matching the query", style="green")
            return {'deleted': 0, 'failed': 0}

        # Display count info
        count_panel = Panel(
            f"📧 [bold]{total_count:,}[/bold] emails found matching query",
            title="📊 Search Results",
            border_style="yellow"
        )
        self.console.print(count_panel)

        # Safety check for large deletions
        if total_count > 1000 and not max_delete:
            self.console.print(f"⚠️  [yellow]Large deletion detected: {total_count:,} emails[/yellow]")
            response = input("Continue with deletion? (yes/no): ")
            if response.lower() != 'yes':
                self.console.print("❌ Deletion cancelled by user", style="red")
                return {'deleted': 0, 'failed': 0}

        # Limit deletion count if specified
        delete_count = min(total_count, max_delete) if max_delete else total_count

        if dry_run:
            dry_run_panel = Panel(
                f"🧪 [bold green]DRY RUN MODE[/bold green]\n\n"
                f"Would delete: [bold]{delete_count:,}[/bold] emails\n"
                f"Query: [cyan]{query}[/cyan]\n\n"
                f"[dim]No emails will actually be deleted in dry-run mode[/dim]",
                title="🧪 Dry Run Results",
                border_style="green"
            )
            self.console.print(dry_run_panel)
            return {'deleted': 0, 'failed': 0}

        # Get message IDs with progress
        with self.console.status("[bold green]Fetching email IDs for deletion..."):
            message_ids = self.list_emails(query, delete_count)

        if not message_ids:
            self.console.print("❌ No messages found to delete", style="red")
            return {'deleted': 0, 'failed': 0}

        # Final confirmation with detailed info
        confirmation_panel = Panel(
            f"⚠️  [bold red]FINAL CONFIRMATION REQUIRED[/bold red]\n\n"
            f"About to [bold]permanently delete[/bold]: [red]{len(message_ids):,} emails[/red]\n"
            f"Query: [cyan]{query}[/cyan]\n"
            f"Recovery: Available in Gmail Trash for 30 days\n\n"
            f"[dim]This action cannot be undone except via Trash recovery[/dim]",
            title="🚨 Deletion Confirmation",
            border_style="red"
        )
        self.console.print(confirmation_panel)

        response = input("Type 'DELETE' to confirm (case sensitive): ")
        if response != 'DELETE':
            self.console.print("❌ Deletion cancelled - confirmation not matched", style="red")
            return {'deleted': 0, 'failed': 0}

        # Perform deletion with beautiful progress
        return self.delete_emails_batch(message_ids)

    def delete_from_parquet_data(self, parquet_file: str, dry_run: bool = True) -> dict[str, int]:
        """Delete emails based on gmail_ids from parquet analysis with beautiful display"""
        try:
            # Load parquet data with status
            with self.console.status("[bold green]Loading parquet analysis data..."):
                df = pd.read_parquet(parquet_file)
                gmail_ids = df['gmail_id'].dropna().tolist()

            # Display parquet info panel
            parquet_panel = Panel(
                f"📁 [bold]File:[/bold] {parquet_file}\n"
                f"📧 [bold]Email IDs found:[/bold] {len(gmail_ids):,}",
                title="📊 Parquet Analysis Data",
                border_style="blue"
            )
            self.console.print(parquet_panel)

            if dry_run:
                dry_run_panel = Panel(
                    f"🧪 [bold green]DRY RUN MODE[/bold green]\n\n"
                    f"Would delete: [bold]{len(gmail_ids):,}[/bold] emails from analysis\n"
                    f"Source: [cyan]{parquet_file}[/cyan]\n\n"
                    f"[dim]No emails will actually be deleted in dry-run mode[/dim]",
                    title="🧪 Parquet Dry Run Results",
                    border_style="green"
                )
                self.console.print(dry_run_panel)
                return {'deleted': 0, 'failed': 0}

            # Final confirmation
            confirmation_panel = Panel(
                f"⚠️  [bold red]FINAL CONFIRMATION REQUIRED[/bold red]\n\n"
                f"About to [bold]permanently delete[/bold]: [red]{len(gmail_ids):,} emails[/red]\n"
                f"Source: [cyan]{parquet_file}[/cyan]\n"
                f"Recovery: Available in Gmail Trash for 30 days\n\n"
                f"[dim]This action cannot be undone except via Trash recovery[/dim]",
                title="🚨 Parquet Deletion Confirmation",
                border_style="red"
            )
            self.console.print(confirmation_panel)

            response = input("Type 'DELETE' to confirm (case sensitive): ")
            if response != 'DELETE':
                self.console.print("❌ Deletion cancelled - confirmation not matched", style="red")
                return {'deleted': 0, 'failed': 0}

            return self.delete_emails_batch(gmail_ids)

        except Exception as e:
            error_panel = Panel(
                f"❌ [red]Error processing parquet file:[/red]\n{e!s}",
                title="🚨 Error",
                border_style="red"
            )
            self.console.print(error_panel)
            return {'deleted': 0, 'failed': 0}

def main():
    console = Console()

    # Beautiful header
    console.print(Panel(
        "[bold magenta]Gmail Bulk Deletion Tool[/bold magenta]\n"
        "[dim]Safely delete emails using Gmail API with beautiful progress tracking[/dim]",
        title="🗑️ Gmail Deleter",
        border_style="magenta"
    ))

    parser = argparse.ArgumentParser(description='Gmail Bulk Deletion Tool')
    parser.add_argument('--query', type=str, help='Gmail search query (e.g., "is:unread")')
    parser.add_argument('--parquet', type=str, help='Path to parquet file with gmail_ids')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--max-delete', type=int, help='Maximum number of emails to delete')
    parser.add_argument('--preset', type=str, choices=['unread', 'all', 'old', 'large'], help='Use preset deletion queries')

    args = parser.parse_args()

    # Preset queries
    preset_queries = {
        'unread': 'is:unread',
        'all': '',  # All emails
        'old': 'older_than:1y',  # Older than 1 year
        'large': 'larger:10M'  # Larger than 10MB
    }

    try:
        deleter = GmailDeleter()

        if args.preset:
            query = preset_queries[args.preset]
            preset_panel = Panel(
                f"[cyan]Preset:[/cyan] [bold]{args.preset}[/bold]\n"
                f"[cyan]Query:[/cyan] [bold]{query}[/bold]",
                title="🎯 Preset Selection",
                border_style="cyan"
            )
            console.print(preset_panel)
            deleter.delete_by_query(query, args.dry_run, args.max_delete)

        elif args.query:
            deleter.delete_by_query(args.query, args.dry_run, args.max_delete)

        elif args.parquet:
            deleter.delete_from_parquet_data(args.parquet, args.dry_run)

        else:
            # Interactive mode with beautiful menu
            menu_table = Table(title="📧 Gmail Deletion Options", box=box.ROUNDED)
            menu_table.add_column("Option", style="cyan", no_wrap=True)
            menu_table.add_column("Description", style="white")
            menu_table.add_column("Risk Level", style="yellow")

            menu_table.add_row("1", "Delete unread emails", "🟡 Medium")
            menu_table.add_row("2", "Delete all emails", "🔴 DANGER")
            menu_table.add_row("3", "Delete emails older than 1 year", "🟡 Medium")
            menu_table.add_row("4", "Delete large emails (>10MB)", "🟢 Low")
            menu_table.add_row("5", "Custom query", "🟠 Variable")
            menu_table.add_row("6", "Delete from parquet analysis", "🟠 Variable")

            console.print(menu_table)

            choice = input("\nEnter choice (1-6): ").strip()

            query_map = {
                '1': 'is:unread',
                '2': '',
                '3': 'older_than:1y',
                '4': 'larger:10M'
            }

            if choice in query_map:
                deleter.delete_by_query(query_map[choice], args.dry_run, args.max_delete)
            elif choice == '5':
                custom_query = input("Enter Gmail search query: ").strip()
                deleter.delete_by_query(custom_query, args.dry_run, args.max_delete)
            elif choice == '6':
                parquet_path = input("Enter path to parquet file: ").strip()
                deleter.delete_from_parquet_data(parquet_path, args.dry_run)
            else:
                console.print("❌ Invalid choice", style="red")
                return

        # Results are already displayed beautifully in the methods above

    except KeyboardInterrupt:
        console.print("\n⚠️  [yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        error_panel = Panel(
            f"❌ [red]Error:[/red] {e!s}",
            title="🚨 Unexpected Error",
            border_style="red"
        )
        console.print(error_panel)

if __name__ == "__main__":
    main()
