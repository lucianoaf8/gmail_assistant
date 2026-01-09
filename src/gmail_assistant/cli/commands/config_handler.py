"""
Configuration handler for Gmail Fetcher main interface.
Handles configuration management operations.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def handle_config_command(args: Any) -> None:
    """
    Handle configuration management.

    Args:
        args: Parsed command line arguments
    """
    config_dir = Path(__file__).parent.parent.parent / "config"

    if args.show:
        _show_configuration(config_dir)

    if args.setup:
        _setup_configuration(config_dir)


def _show_configuration(config_dir: Path) -> None:
    """
    Display current configuration.

    Args:
        config_dir: Configuration directory path
    """
    print("Current configuration:")
    print(f"  Config directory: {config_dir}")

    if config_dir.exists():
        app_configs = list((config_dir / 'app').glob('*.json')) if (config_dir / 'app').exists() else []
        security_files = list((config_dir / 'security').glob('*.json')) if (config_dir / 'security').exists() else []

        print(f"  App configs: {app_configs}")
        print(f"  Security files: {security_files}")
    else:
        print("  Configuration directory does not exist")


def _setup_configuration(config_dir: Path) -> None:
    """
    Set up initial configuration structure.

    Args:
        config_dir: Configuration directory path
    """
    print("Setting up initial configuration...")

    try:
        # Create config structure
        config_dir.mkdir(exist_ok=True)
        (config_dir / "app").mkdir(exist_ok=True)
        (config_dir / "security").mkdir(exist_ok=True)

        print("Success: Configuration directories created")
        print("Place your credentials.json file in config/security/")

        logger.info("Configuration directories created successfully")

    except Exception as e:
        error_msg = f"Error creating configuration directories: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")