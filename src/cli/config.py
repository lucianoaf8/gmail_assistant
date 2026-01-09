"""
Config command for Gmail Fetcher CLI.

Manages configuration settings and validation.
"""

import json
import logging
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def setup_parser(subparsers: _SubParsersAction) -> ArgumentParser:
    """
    Setup the config command parser.

    Args:
        subparsers: Parent subparsers object

    Returns:
        Configured ArgumentParser for config command
    """
    parser = subparsers.add_parser(
        'config',
        help='Configuration management',
        description='Manage Gmail Fetcher configuration'
    )

    # Config subcommands
    config_subparsers = parser.add_subparsers(
        dest='config_action',
        title='config actions',
        description='Available configuration actions'
    )

    # Show config
    show_parser = config_subparsers.add_parser(
        'show',
        help='Show current configuration',
        description='Display current configuration settings'
    )
    show_parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )

    # Setup config
    setup_parser_cfg = config_subparsers.add_parser(
        'setup',
        help='Setup initial configuration',
        description='Create initial configuration files and directories'
    )
    setup_parser_cfg.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing configuration'
    )

    # Validate config
    validate_parser = config_subparsers.add_parser(
        'validate',
        help='Validate configuration',
        description='Check configuration files for errors'
    )

    # Edit config
    edit_parser = config_subparsers.add_parser(
        'edit',
        help='Edit configuration',
        description='Open configuration in editor'
    )
    edit_parser.add_argument(
        '--file',
        choices=['main', 'ai', 'all'],
        default='main',
        help='Configuration file to edit (default: main)'
    )

    return parser


def handle(args: Any) -> int:
    """
    Handle the config command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    if args.config_action is None:
        # Default to show
        return _handle_show(args)

    if args.config_action == 'show':
        return _handle_show(args)
    elif args.config_action == 'setup':
        return _handle_setup(args)
    elif args.config_action == 'validate':
        return _handle_validate(args)
    elif args.config_action == 'edit':
        return _handle_edit(args)
    else:
        logger.error(f"Unknown config action: {args.config_action}")
        return 1


def _get_config_paths() -> dict:
    """Get configuration file paths."""
    from src.core.constants import PROJECT_ROOT, CONFIG_DIR, DEFAULT_CONFIG_PATH

    return {
        'project_root': PROJECT_ROOT,
        'config_dir': CONFIG_DIR,
        'main_config': DEFAULT_CONFIG_PATH,
        'ai_config': CONFIG_DIR / 'config.json',
        'credentials': PROJECT_ROOT / 'credentials.json',
        'token': PROJECT_ROOT / 'token.json'
    }


def _handle_show(args: Any) -> int:
    """Show current configuration."""
    try:
        paths = _get_config_paths()

        if getattr(args, 'format', 'text') == 'json':
            config = {
                'paths': {k: str(v) for k, v in paths.items()},
                'files_exist': {k: v.exists() if hasattr(v, 'exists') else False
                               for k, v in paths.items()},
            }

            # Load main config if exists
            if paths['main_config'].exists():
                with open(paths['main_config'], 'r') as f:
                    config['main_config'] = json.load(f)

            print(json.dumps(config, indent=2))

        else:
            print("Gmail Fetcher Configuration")
            print("=" * 40)
            print(f"\nProject Root: {paths['project_root']}")
            print(f"Config Directory: {paths['config_dir']}")

            print("\nConfiguration Files:")
            for name, path in paths.items():
                if hasattr(path, 'exists'):
                    status = "OK" if path.exists() else "MISSING"
                    print(f"  - {name}: {status}")
                    if path.exists():
                        print(f"    Path: {path}")

            # Show main config summary
            if paths['main_config'].exists():
                print("\nMain Config Summary:")
                try:
                    with open(paths['main_config'], 'r') as f:
                        config = json.load(f)

                    if 'queries' in config:
                        print(f"  - Predefined queries: {len(config['queries'])}")
                    if 'defaults' in config:
                        defaults = config['defaults']
                        print(f"  - Max emails: {defaults.get('max_emails', 'not set')}")
                        print(f"  - Output format: {defaults.get('format', 'not set')}")
                except json.JSONDecodeError:
                    print("  - Error: Invalid JSON")

        return 0

    except Exception as e:
        logger.error(f"Error showing config: {e}")
        return 1


def _handle_setup(args: Any) -> int:
    """Setup initial configuration."""
    try:
        paths = _get_config_paths()
        created = []

        # Create directories
        paths['config_dir'].mkdir(parents=True, exist_ok=True)
        created.append(f"Directory: {paths['config_dir']}")

        # Create main config if not exists
        if not paths['main_config'].exists() or getattr(args, 'force', False):
            default_config = {
                "queries": {
                    "unread": "is:unread",
                    "newsletters": "is:unread (newsletter OR unsubscribe)",
                    "important": "is:important",
                    "starred": "is:starred"
                },
                "defaults": {
                    "max_emails": 1000,
                    "format": "both",
                    "organize_by": "date",
                    "output_dir": "gmail_backup"
                },
                "cleanup_suggestions": [
                    "is:unread older_than:30d",
                    "category:promotions older_than:7d",
                    "category:updates older_than:14d"
                ]
            }

            with open(paths['main_config'], 'w') as f:
                json.dump(default_config, f, indent=2)

            created.append(f"Config: {paths['main_config']}")

        print("Configuration setup complete!")
        print("\nCreated:")
        for item in created:
            print(f"  - {item}")

        if not paths['credentials'].exists():
            print("\nNOTE: credentials.json not found!")
            print("Download OAuth credentials from Google Cloud Console")
            print(f"and save to: {paths['credentials']}")

        return 0

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1


def _handle_validate(args: Any) -> int:
    """Validate configuration files."""
    try:
        paths = _get_config_paths()
        issues = []

        print("Validating configuration...")
        print()

        # Check required files
        required_files = ['credentials']
        for name in required_files:
            path = paths.get(name)
            if path and not path.exists():
                issues.append(f"MISSING: {name} ({path})")
            else:
                print(f"OK: {name}")

        # Validate JSON files
        json_files = ['main_config', 'ai_config']
        for name in json_files:
            path = paths.get(name)
            if path and path.exists():
                try:
                    with open(path, 'r') as f:
                        json.load(f)
                    print(f"OK: {name} (valid JSON)")
                except json.JSONDecodeError as e:
                    issues.append(f"INVALID JSON: {name} - {e}")
            elif path:
                print(f"OPTIONAL: {name} (not found)")

        if issues:
            print("\nIssues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        else:
            print("\nAll configuration files are valid!")
            return 0

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1


def _handle_edit(args: Any) -> int:
    """Open configuration in editor."""
    import os
    import subprocess

    try:
        paths = _get_config_paths()

        file_choice = getattr(args, 'file', 'main')
        if file_choice == 'main':
            config_file = paths['main_config']
        elif file_choice == 'ai':
            config_file = paths['ai_config']
        else:
            config_file = paths['config_dir']

        if not config_file.exists():
            print(f"Config file not found: {config_file}")
            print("Run 'gmail-fetcher config setup' first")
            return 1

        # Try to open in default editor
        editor = os.environ.get('EDITOR', 'notepad' if os.name == 'nt' else 'nano')

        print(f"Opening {config_file} in {editor}...")
        subprocess.run([editor, str(config_file)])

        return 0

    except Exception as e:
        logger.error(f"Failed to open editor: {e}")
        return 1
