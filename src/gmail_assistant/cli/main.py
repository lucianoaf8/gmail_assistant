"""
Gmail Assistant CLI - Click-based command line interface.

Exit Codes:
    0: Success
    1: General error
    2: Usage/argument error (Click default)
    3: Authentication error
    4: Network error
    5: Configuration error

CORRECTED: All exceptions imported from gmail_assistant.core.exceptions
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path
from typing import Callable, TypeVar

import click

from gmail_assistant import __version__
from gmail_assistant.core.config import AppConfig
# CORRECTED: Import ALL exceptions from the single authoritative source
from gmail_assistant.core.exceptions import (
    ConfigError,
    AuthError,
    NetworkError,
    GmailAssistantError,
)

F = TypeVar("F", bound=Callable[..., None])


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
@click.pass_context
@handle_errors
def fetch(
    ctx: click.Context,
    query: str,
    max_emails: int | None,
    output_dir: Path | None,
    output_format: str,
) -> None:
    """Fetch emails from Gmail."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        allow_repo_credentials=ctx.obj["allow_repo_credentials"],
    )

    # Use CLI options if provided, otherwise use config defaults
    effective_max = max_emails if max_emails is not None else cfg.max_emails
    effective_output = output_dir if output_dir is not None else cfg.output_dir

    click.echo(f"Fetching emails (max: {effective_max}, format: {output_format})")
    click.echo(f"Query: {query or '(all)'}")
    click.echo(f"Output: {effective_output}")
    # NOTE: Functional implementation deferred to v2.1.0 (see §1.5)
    click.echo("[INFO] Functional fetch implementation is deferred to v2.1.0")


@main.command()
@click.option("--query", "-q", required=True, help="Gmail search query for emails to delete.")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting.")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
@handle_errors
def delete(
    ctx: click.Context,
    query: str,
    dry_run: bool,
    confirm: bool,
) -> None:
    """Delete emails matching query."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        allow_repo_credentials=ctx.obj["allow_repo_credentials"],
    )

    click.echo(f"Delete query: {query}")
    click.echo(f"Dry run: {dry_run}")
    # NOTE: Functional implementation deferred to v2.1.0 (see §1.5)
    click.echo("[INFO] Functional delete implementation is deferred to v2.1.0")


@main.command()
@click.option("--input-dir", "-i", type=click.Path(exists=True, path_type=Path), help="Directory with fetched emails.")
@click.option("--report", "-r", type=click.Choice(["summary", "detailed", "json"]), default="summary")
@click.pass_context
@handle_errors
def analyze(
    ctx: click.Context,
    input_dir: Path | None,
    report: str,
) -> None:
    """Analyze fetched emails."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        allow_repo_credentials=ctx.obj["allow_repo_credentials"],
    )

    source = input_dir or cfg.output_dir
    click.echo(f"Analyzing emails in: {source}")
    click.echo(f"Report type: {report}")
    # NOTE: Functional implementation deferred to v2.1.0 (see §1.5)
    click.echo("[INFO] Functional analyze implementation is deferred to v2.1.0")


@main.command()
@click.pass_context
@handle_errors
def auth(ctx: click.Context) -> None:
    """Authenticate with Gmail API."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        allow_repo_credentials=ctx.obj["allow_repo_credentials"],
    )

    click.echo(f"Credentials: {cfg.credentials_path}")
    click.echo(f"Token: {cfg.token_path}")
    click.echo("Starting OAuth flow...")
    # NOTE: Functional implementation deferred to v2.1.0 (see §1.5)
    click.echo("[INFO] Functional auth implementation is deferred to v2.1.0")


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
