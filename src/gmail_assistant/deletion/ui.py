#!/usr/bin/env python3
"""
Gmail Unread Inbox Cleaner
Specifically designed to clean unread emails for a fresh start.
"""

import sys
import io

# UTF-8 support will be handled by Rich Console when needed

from gmail_assistant.deletion.deleter import GmailDeleter
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import argparse

def clean_unread_inbox(deleter: GmailDeleter, dry_run: bool = True, keep_recent_days: int = 0):
    """Clean unread inbox with options to keep recent emails"""
    console = Console(force_terminal=True, legacy_windows=False)

    # Header panel
    console.print(Panel(
        "[bold blue]🧹 Gmail Unread Inbox Cleaner[/bold blue]\n"
        "[dim]Clean up your unread emails for a fresh start[/dim]",
        title="📧 Inbox Cleaner",
        border_style="blue"
    ))

    # Build query
    if keep_recent_days > 0:
        query = f"is:unread older_than:{keep_recent_days}d"
        target_desc = f"Unread emails older than {keep_recent_days} days"
    else:
        query = "is:unread"
        target_desc = "ALL unread emails"

    # Query panel
    console.print(Panel(
        f"[cyan]Target:[/cyan] [bold]{target_desc}[/bold]\n"
        f"[cyan]Query:[/cyan] [yellow]{query}[/yellow]",
        title="🎯 Deletion Target",
        border_style="cyan"
    ))

    # Get counts for different categories
    total_unread = deleter.get_email_count("is:unread")

    if total_unread == 0:
        console.print(Panel(
            "✅ [green]Inbox already clean - no unread emails found![/green]",
            title="🎉 Already Clean",
            border_style="green"
        ))
        return {'deleted': 0, 'failed': 0}

    # Show breakdown by common categories
    categories = {
        'Financial': 'is:unread (payment OR invoice OR bill OR receipt OR bank OR card)',
        'Notifications': 'is:unread (notification OR alert OR backup OR report)',
        'Marketing': 'is:unread (unsubscribe OR newsletter OR marketing OR offer)',
        'Social': 'is:unread (social OR friend OR follow)',
        'Large emails': 'is:unread larger:1M'
    }

    # Create breakdown table
    breakdown_table = Table(title="📊 Unread Email Breakdown", box=box.ROUNDED)
    breakdown_table.add_column("Category", style="cyan", no_wrap=True)
    breakdown_table.add_column("Count", style="magenta", justify="right")
    breakdown_table.add_column("Percentage", style="yellow", justify="right")

    breakdown_table.add_row("Total Unread", f"{total_unread:,}", "100.0%")

    for category, cat_query in categories.items():
        count = deleter.get_email_count(cat_query)
        if count > 0:
            percentage = (count / total_unread) * 100 if total_unread > 0 else 0
            breakdown_table.add_row(category, f"{count:,}", f"{percentage:.1f}%")

    console.print(breakdown_table)

    # Target emails for deletion
    target_count = deleter.get_email_count(query)

    if target_count == 0:
        console.print(Panel(
            "✅ [green]No emails match deletion criteria![/green]",
            title="🎉 Nothing to Delete",
            border_style="green"
        ))
        return {'deleted': 0, 'failed': 0}

    # Target info panel
    console.print(Panel(
        f"📧 [bold]{target_count:,}[/bold] emails will be deleted\n"
        f"📊 {(target_count/total_unread)*100:.1f}% of total unread emails",
        title="🎯 Deletion Summary",
        border_style="yellow"
    ))

    if dry_run:
        console.print(Panel(
            f"🧪 [bold green]DRY RUN MODE[/bold green]\n\n"
            f"Would delete: [bold]{target_count:,}[/bold] unread emails\n"
            f"Query: [cyan]{query}[/cyan]\n\n"
            f"[dim]No emails will actually be deleted in dry-run mode[/dim]",
            title="🧪 Dry Run Results",
            border_style="green"
        ))
        return {'deleted': 0, 'failed': 0}

    # Safety confirmation
    console.print(Panel(
        f"⚠️  [bold red]CONFIRMATION REQUIRED[/bold red]\n\n"
        f"About to permanently delete [bold]{target_count:,}[/bold] unread emails\n"
        f"{f'(Keeping emails from last {keep_recent_days} days)' if keep_recent_days > 0 else ''}\n\n"
        f"[dim]Emails will be moved to Trash (recoverable for 30 days)[/dim]",
        title="🚨 Final Warning",
        border_style="red"
    ))

    confirm = input("\nType 'DELETE' to confirm (case sensitive): ")
    if confirm != 'DELETE':
        console.print(Panel(
            "❌ [red]Deletion cancelled - confirmation not matched[/red]",
            title="❌ Cancelled",
            border_style="red"
        ))
        return {'deleted': 0, 'failed': 0}

    # Perform deletion
    console.print(f"\n🗑️  [bold cyan]Starting deletion of {target_count:,} emails...[/bold cyan]")
    result = deleter.delete_by_query(query, dry_run=False)

    # Final status
    remaining_unread = deleter.get_email_count("is:unread")
    success_rate = (result['deleted'] / (result['deleted'] + result['failed']) * 100) if (result['deleted'] + result['failed']) > 0 else 0

    console.print(Panel(
        f"✅ [green]Successfully deleted:[/green] [bold]{result['deleted']:,}[/bold] emails\n"
        f"❌ [red]Failed to delete:[/red] [bold]{result['failed']:,}[/bold] emails\n"
        f"📊 [blue]Success rate:[/blue] [bold]{success_rate:.1f}%[/bold]\n"
        f"📨 [yellow]Remaining unread:[/yellow] [bold]{remaining_unread:,}[/bold] emails",
        title="🎉 Cleanup Complete",
        border_style="green"
    ))

    return result

def main():
    parser = argparse.ArgumentParser(description='Clean Gmail unread inbox')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted')
    parser.add_argument('--keep-recent', type=int, default=0,
                       help='Keep emails from last N days (default: 0 = delete all)')
    parser.add_argument('--force', action='store_true', help='Skip interactive confirmation')

    args = parser.parse_args()

    try:
        # Initialize deleter
        deleter = GmailDeleter()

        # Run cleanup
        result = clean_unread_inbox(
            deleter=deleter,
            dry_run=args.dry_run,
            keep_recent_days=args.keep_recent
        )

        if not args.dry_run and result['deleted'] > 0:
            console = Console(force_terminal=True, legacy_windows=False)
            console.print(Panel(
                f"🎉 [bold green]Fresh start achieved![/bold green]\n"
                f"Successfully deleted [bold]{result['deleted']:,}[/bold] unread emails",
                title="🌟 Success",
                border_style="green"
            ))

    except KeyboardInterrupt:
        console = Console(force_terminal=True, legacy_windows=False)
        console.print(Panel(
            "⚠️  [yellow]Operation cancelled by user[/yellow]",
            title="⚠️ Cancelled",
            border_style="yellow"
        ))
    except Exception as e:
        console = Console(force_terminal=True, legacy_windows=False)
        console.print(Panel(
            f"❌ [red]Error: {e}[/red]",
            title="❌ Error",
            border_style="red"
        ))

if __name__ == "__main__":
    main()