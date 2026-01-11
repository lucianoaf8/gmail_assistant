#!/usr/bin/env python3
"""
Test script for Rich progress bars in Gmail deletion workflow
Simulates the deletion process without actually deleting emails
"""

import sys
import io
import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.panel import Panel
from rich.table import Table
from rich import box


def test_rich_progress():
    """Test the Rich progress bar implementation"""
    # Force UTF-8 encoding for Windows - scoped to function to avoid breaking pytest capture
    original_stdout = sys.stdout
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        _run_rich_progress_tests()
    finally:
        sys.stdout = original_stdout


def _run_rich_progress_tests():
    """Internal function containing the actual test logic"""
    console = Console(force_terminal=True, legacy_windows=False)

    # Test 1: Beautiful header
    console.print(Panel(
        "[bold magenta]Gmail Deletion Progress Test[/bold magenta]\n"
        "[dim]Testing beautiful Rich progress bars for email deletion[/dim]",
        title="🧪 Rich Progress Test",
        border_style="magenta"
    ))

    # Test 2: Query panel
    query_panel = Panel(
        f"[cyan]Search Query:[/cyan] [bold]is:unread[/bold]",
        title="🔍 Gmail Query",
        border_style="blue"
    )
    console.print(query_panel)

    # Test 3: Status spinner
    with console.status("[bold green]Counting matching emails...") as status:
        time.sleep(2)  # Simulate API call

    # Test 4: Count info panel
    count_panel = Panel(
        f"📧 [bold]2,783[/bold] emails found matching query",
        title="📊 Search Results",
        border_style="yellow"
    )
    console.print(count_panel)

    # Test 5: Dry run panel
    dry_run_panel = Panel(
        f"🧪 [bold green]DRY RUN MODE[/bold green]\n\n"
        f"Would delete: [bold]2,783[/bold] emails\n"
        f"Query: [cyan]is:unread[/cyan]\n\n"
        f"[dim]No emails will actually be deleted in dry-run mode[/dim]",
        title="🧪 Dry Run Results",
        border_style="green"
    )
    console.print(dry_run_panel)

    # Test 6: Simulated deletion progress
    console.print("\n[bold cyan]Simulating deletion progress...[/bold cyan]")

    # Simulate batch deletion with beautiful progress
    total_emails = 2783
    batch_size = 100
    total_batches = (total_emails + batch_size - 1) // batch_size

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold blue]Deleting emails..."),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        console=console,
        transient=False
    ) as progress:

        # Add main deletion task
        deletion_task = progress.add_task(
            f"[cyan]Processing {total_emails} emails in batches of {batch_size}",
            total=total_batches
        )

        # Simulate batch processing
        deleted_count = 0
        failed_count = 0

        for i in range(0, total_emails, batch_size):
            batch_emails = min(batch_size, total_emails - i)
            batch_num = (i // batch_size) + 1

            # Update progress description
            progress.update(
                deletion_task,
                description=f"[cyan]Batch {batch_num}/{total_batches} ({batch_emails} emails)"
            )

            # Simulate processing time
            time.sleep(0.3)

            # Simulate success/failure
            if batch_num == 15:  # Simulate one failed batch
                failed_count += batch_emails
                # Simulate individual deletion fallback
                individual_task = progress.add_task(
                    f"[yellow]Individual deletion fallback",
                    total=batch_emails
                )

                for j in range(batch_emails):
                    time.sleep(0.02)
                    if j < batch_emails - 5:  # Most succeed
                        deleted_count += 1
                        failed_count -= 1
                    progress.advance(individual_task)

                progress.remove_task(individual_task)
            else:
                deleted_count += batch_emails

            progress.advance(deletion_task)

    # Test 7: Final results panel
    success_rate = (deleted_count / (deleted_count + failed_count) * 100) if (deleted_count + failed_count) > 0 else 0
    result_panel = Panel(
        f"✅ [green]Successfully deleted:[/green] [bold]{deleted_count}[/bold] emails\n"
        f"❌ [red]Failed to delete:[/red] [bold]{failed_count}[/bold] emails\n"
        f"📊 [blue]Success rate:[/blue] [bold]{success_rate:.1f}%[/bold]",
        title="🎉 Deletion Complete",
        border_style="green"
    )
    console.print(result_panel)

    # Test 8: Interactive menu table
    console.print("\n[bold cyan]Testing interactive menu...[/bold cyan]")

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

    # Test 9: Error panel
    console.print("\n[bold cyan]Testing error display...[/bold cyan]")

    error_panel = Panel(
        f"❌ [red]Error processing parquet file:[/red]\nFile not found: data.parquet",
        title="🚨 Error",
        border_style="red"
    )
    console.print(error_panel)

    # Test 10: Final success message
    console.print("\n🎉 [bold green]All Rich progress bar tests completed successfully![/bold green]")
    console.print("[dim]The Gmail deletion workflow now uses beautiful Rich progress bars[/dim]")

if __name__ == "__main__":
    test_rich_progress()