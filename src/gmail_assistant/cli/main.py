"""
Gmail Assistant CLI - Click-based command line interface.

Exit Codes:
    0: Success
    1: General error
    2: Usage/argument error (Click default)
    3: Authentication error
    4: Network error
    5: Configuration error

C-2 Fix: Full CLI command implementations integrated.
M-5 Fix: Async fetcher integration.
"""
from __future__ import annotations

import asyncio
import functools
import sys
from pathlib import Path
from typing import Callable, Dict, Any, TypeVar

import click

from gmail_assistant import __version__
from gmail_assistant.core.config import AppConfig
from gmail_assistant.core.exceptions import (
    ConfigError,
    AuthError,
    NetworkError,
    APIError,
    GmailAssistantError,
)

# C-2: Import command implementations
from gmail_assistant.cli.commands.fetch import fetch_emails
from gmail_assistant.cli.commands.delete import delete_emails, get_email_count
from gmail_assistant.cli.commands.analyze import analyze_emails
from gmail_assistant.cli.commands.auth import authenticate, check_auth_status, revoke_auth

F = TypeVar("F", bound=Callable[..., None])


def _fetch_async(
    query: str,
    max_emails: int,
    output_dir: Path,
    output_format: str,
    credentials_path: Path,
    concurrency: int
) -> Dict[str, Any]:
    """
    Async fetch implementation (M-5).

    Uses AsyncGmailFetcher for concurrent email fetching.
    Falls back to sync if async dependencies unavailable.
    """
    try:
        from gmail_assistant.core.fetch.async_fetcher import AsyncGmailFetcher
    except ImportError:
        click.echo("Async dependencies not installed. Falling back to sync mode.")
        click.echo("Install with: pip install gmail-assistant[async]")
        return fetch_emails(
            query=query,
            max_emails=max_emails,
            output_dir=output_dir,
            output_format=output_format,
            credentials_path=credentials_path,
            resume=False
        )

    async def _run_async():
        async with AsyncGmailFetcher(
            str(credentials_path),
            max_concurrent=concurrency
        ) as fetcher:
            # Fetch email IDs
            click.echo(f"Using async mode with concurrency={concurrency}")
            email_ids = await fetcher.fetch_email_ids_async(query, max_emails)

            if not email_ids:
                return {'fetched': 0, 'total': 0}

            click.echo(f"Found {len(email_ids)} emails, fetching...")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Fetch emails concurrently
            emails = await fetcher.fetch_emails_async(email_ids)

            # Save emails
            fetched = 0
            for i, email_data in enumerate(emails):
                if email_data:
                    _save_email_async(email_data, output_dir, output_format, i)
                    fetched += 1

            return {'fetched': fetched, 'total': len(email_ids)}

    return asyncio.run(_run_async())


def _save_email_async(email_data: Dict[str, Any], output_dir: Path, output_format: str, index: int) -> None:
    """Save email from async fetch."""
    import json
    import re

    subject = str(email_data.get('subject', 'no_subject'))[:50]
    safe_subject = re.sub(r'[<>:"/\\|?*]', '_', subject)
    msg_id = str(email_data.get('id', str(index)))[:16]

    if output_format == 'json':
        filename = f"{index:05d}_{safe_subject}_{msg_id}.json"
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, indent=2, default=str)
    elif output_format == 'eml':
        filename = f"{index:05d}_{safe_subject}_{msg_id}.eml"
        filepath = output_dir / filename
        raw_content = email_data.get('raw_content', email_data.get('raw', ''))
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(raw_content))
    elif output_format == 'mbox':
        mbox_path = output_dir / "emails.mbox"
        raw_content = email_data.get('raw_content', email_data.get('raw', ''))
        with open(mbox_path, 'a', encoding='utf-8') as f:
            f.write(f"From {email_data.get('sender', 'unknown')}\n")
            f.write(str(raw_content))
            f.write("\n\n")


def handle_errors(func: F) -> F:
    """Decorator to map exceptions to exit codes."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigError as e:
            click.echo(f"Configuration error: {e}", err=True)
            sys.exit(5)
        except AuthError as e:
            click.echo(f"Authentication error: {e}", err=True)
            sys.exit(3)
        except NetworkError as e:
            click.echo(f"Network error: {e}", err=True)
            sys.exit(4)
        except click.ClickException:
            raise  # Let Click handle its own exceptions
        except GmailAssistantError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            sys.exit(1)
    return wrapper  # type: ignore


@click.group()
@click.version_option(version=__version__, prog_name="gmail-assistant")
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file.",
)
@click.option(
    "--allow-repo-credentials",
    is_flag=True,
    help="Allow credentials inside git repository (security risk).",
)
@click.pass_context
def main(ctx: click.Context, config: Path | None, allow_repo_credentials: bool) -> None:
    """Gmail Assistant - Backup, analyze, and manage your Gmail."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["allow_repo_credentials"] = allow_repo_credentials


@main.command()
@click.option("--query", "-q", default="", help="Gmail search query.")
@click.option("--max-emails", "-m", type=int, help="Maximum emails to fetch.")
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), help="Output directory.")
@click.option("--format", "output_format", type=click.Choice(["json", "mbox", "eml"]), default="json")
@click.option("--resume", is_flag=True, help="Resume from last checkpoint.")
@click.option("--async", "use_async", is_flag=True, help="Use async fetcher for better performance (M-5).")
@click.option("--concurrency", type=int, default=10, help="Max concurrent operations for async mode.")
@click.pass_context
@handle_errors
def fetch(
    ctx: click.Context,
    query: str,
    max_emails: int | None,
    output_dir: Path | None,
    output_format: str,
    resume: bool,
    use_async: bool,
    concurrency: int,
) -> None:
    """Fetch emails from Gmail."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        allow_repo_credentials=ctx.obj["allow_repo_credentials"],
    )

    # Use CLI options if provided, otherwise use config defaults
    effective_max = max_emails if max_emails is not None else cfg.max_emails
    effective_output = output_dir if output_dir is not None else cfg.output_dir

    mode = "async" if use_async else "sync"
    click.echo(f"Fetching emails (max: {effective_max}, format: {output_format}, mode: {mode})")
    click.echo(f"Query: {query or '(all)'}")
    click.echo(f"Output: {effective_output}")

    # M-5: Use async fetcher if requested
    if use_async:
        result = _fetch_async(
            query=query,
            max_emails=effective_max,
            output_dir=Path(effective_output),
            output_format=output_format,
            credentials_path=cfg.credentials_path,
            concurrency=concurrency
        )
    else:
        # C-2: Call sync fetch implementation
        result = fetch_emails(
            query=query,
            max_emails=effective_max,
            output_dir=Path(effective_output),
            output_format=output_format,
            credentials_path=cfg.credentials_path,
            resume=resume
        )
    click.echo(f"\nFetched {result['fetched']}/{result['total']} emails")


@main.command()
@click.option("--query", "-q", required=True, help="Gmail search query for emails to delete.")
@click.option("--dry-run", is_flag=True, default=True, help="Show what would be deleted without deleting.")
@click.option("--confirm", is_flag=True, help="Actually perform deletion (disables dry-run).")
@click.option("--trash", is_flag=True, default=True, help="Move to trash instead of permanent delete.")
@click.option("--permanent", is_flag=True, help="Permanently delete (cannot be undone).")
@click.option("--max-delete", type=int, default=1000, help="Maximum emails to delete.")
@click.pass_context
@handle_errors
def delete(
    ctx: click.Context,
    query: str,
    dry_run: bool,
    confirm: bool,
    trash: bool,
    permanent: bool,
    max_delete: int,
) -> None:
    """Delete emails matching query."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        allow_repo_credentials=ctx.obj["allow_repo_credentials"],
    )

    # Determine operation mode
    is_dry_run = dry_run and not confirm
    use_trash = trash and not permanent

    if not is_dry_run and not confirm:
        # Show count and ask for confirmation
        count = get_email_count(query, cfg.credentials_path)
        if count > 0:
            action = "trash" if use_trash else "permanently delete"
            if not click.confirm(f"About to {action} up to {min(count, max_delete)} emails. Continue?"):
                click.echo("Aborted.")
                return

    # C-2: Call actual delete implementation
    result = delete_emails(
        query=query,
        credentials_path=cfg.credentials_path,
        dry_run=is_dry_run,
        use_trash=use_trash,
        max_delete=max_delete
    )

    if is_dry_run:
        click.echo(f"\nDry run complete. {result['found']} emails would be affected.")


@main.command()
@click.option("--input-dir", "-i", type=click.Path(exists=True, path_type=Path), help="Directory with fetched emails.")
@click.option("--report", "-r", type=click.Choice(["summary", "detailed", "json"]), default="summary")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file for report.")
@click.pass_context
@handle_errors
def analyze(
    ctx: click.Context,
    input_dir: Path | None,
    report: str,
    output: Path | None,
) -> None:
    """Analyze fetched emails."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        allow_repo_credentials=ctx.obj["allow_repo_credentials"],
    )

    source = input_dir or Path(cfg.output_dir)
    click.echo(f"Analyzing emails in: {source}")
    click.echo(f"Report type: {report}")

    # C-2: Call actual analyze implementation
    analyze_emails(
        input_dir=source,
        report_type=report,
        output_file=output
    )


@main.command()
@click.option("--status", is_flag=True, help="Check authentication status only.")
@click.option("--revoke", is_flag=True, help="Revoke stored credentials.")
@click.option("--force", is_flag=True, help="Force re-authentication.")
@click.pass_context
@handle_errors
def auth(
    ctx: click.Context,
    status: bool,
    revoke: bool,
    force: bool,
) -> None:
    """Authenticate with Gmail API."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        allow_repo_credentials=ctx.obj["allow_repo_credentials"],
    )

    if status:
        # C-2: Check auth status
        result = check_auth_status(cfg.credentials_path)
        click.echo(f"Status: {result['status']}")
        if result['authenticated']:
            click.echo("✓ Authenticated")
        else:
            click.echo("✗ Not authenticated")
        return

    if revoke:
        # C-2: Revoke credentials
        revoke_auth()
        return

    # C-2: Perform authentication
    authenticate(
        credentials_path=cfg.credentials_path,
        force_reauth=force
    )


@main.command("config")
@click.option("--show", is_flag=True, help="Show current configuration.")
@click.option("--validate", is_flag=True, help="Validate configuration file.")
@click.option("--init", is_flag=True, help="Create default configuration.")
@click.pass_context
@handle_errors
def config_cmd(
    ctx: click.Context,
    show: bool,
    validate: bool,
    init: bool,
) -> None:
    """Manage configuration."""
    if init:
        default_dir = AppConfig.default_dir()
        default_dir.mkdir(parents=True, exist_ok=True)
        config_file = default_dir / "config.json"

        if config_file.exists():
            click.echo(f"Config already exists: {config_file}")
            sys.exit(5)

        import json
        cfg = AppConfig.load()  # Get defaults
        config_data = {
            "credentials_path": str(cfg.credentials_path),
            "token_path": str(cfg.token_path),
            "output_dir": str(cfg.output_dir),
            "max_emails": cfg.max_emails,
            "rate_limit_per_second": cfg.rate_limit_per_second,
            "log_level": cfg.log_level,
        }
        config_file.write_text(json.dumps(config_data, indent=2))
        click.echo(f"Created: {config_file}")
        return

    try:
        cfg = AppConfig.load(
            ctx.obj["config_path"],
            allow_repo_credentials=ctx.obj["allow_repo_credentials"],
        )
    except ConfigError as e:
        if validate:
            click.echo(f"Configuration invalid: {e}", err=True)
            sys.exit(5)
        raise

    if validate:
        click.echo("Configuration valid.")
        return

    if show:
        click.echo(f"credentials_path: {cfg.credentials_path}")
        click.echo(f"token_path: {cfg.token_path}")
        click.echo(f"output_dir: {cfg.output_dir}")
        click.echo(f"max_emails: {cfg.max_emails}")
        click.echo(f"rate_limit_per_second: {cfg.rate_limit_per_second}")
        click.echo(f"log_level: {cfg.log_level}")
        return

    # Default: show help
    click.echo(ctx.get_help())


if __name__ == "__main__":
    main()
