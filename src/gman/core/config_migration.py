"""
Configuration migration utilities.

Provides version detection and migration for configuration files.
Ensures backward compatibility when config schema changes.

Usage:
    from gman.core.config_migration import migrate_config

    # Migrate config dict to current version
    migrated = migrate_config(old_config)

    # Migrate config file in place
    migrate_config_file(Path("config.json"))
"""

import json
import logging
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Current config version
CURRENT_VERSION = "2.1.0"

# Type alias for migration functions
MigrationFunc = Callable[[dict[str, Any]], dict[str, Any]]


def _migrate_1_to_2(config: dict[str, Any]) -> dict[str, Any]:
    """
    Migrate from v1.x to v2.0.0 config format.

    Changes:
    - Rename max_results -> max_emails
    - Add output_plugins with defaults
    - Add default_output_format
    """
    # Rename deprecated fields
    if "max_results" in config:
        config["max_emails"] = config.pop("max_results")
        logger.info("Migrated: max_results -> max_emails")

    # Add new required fields with defaults
    if "output_plugins" not in config:
        config["output_plugins"] = ["eml", "markdown"]
        logger.info("Added default output_plugins")

    if "default_output_format" not in config:
        config["default_output_format"] = "both"
        logger.info("Added default_output_format")

    config["_config_version"] = "2.0.0"
    return config


def _migrate_2_to_2_1(config: dict[str, Any]) -> dict[str, Any]:
    """
    Migrate from v2.0.0 to v2.1.0 config format.

    Changes:
    - Add max_concurrent_requests
    - Add max_worker_threads
    - Add async_batch_size
    """
    # Add concurrency settings
    if "max_concurrent_requests" not in config:
        config["max_concurrent_requests"] = 10
        logger.info("Added max_concurrent_requests=10")

    if "max_worker_threads" not in config:
        config["max_worker_threads"] = 4
        logger.info("Added max_worker_threads=4")

    if "async_batch_size" not in config:
        config["async_batch_size"] = 100
        logger.info("Added async_batch_size=100")

    config["_config_version"] = "2.1.0"
    return config


# Ordered migration registry
# Key is target version, value is (from_version, migration_func)
MIGRATIONS: dict[str, tuple[str, MigrationFunc]] = {
    "2.0.0": ("1.0.0", _migrate_1_to_2),
    "2.1.0": ("2.0.0", _migrate_2_to_2_1),
}

# Version ordering for migration path calculation
VERSION_ORDER = ["1.0.0", "2.0.0", "2.1.0"]


def get_config_version(config: dict[str, Any]) -> str:
    """
    Detect config version from content.

    Args:
        config: Configuration dictionary

    Returns:
        Version string (e.g., "2.0.0")
    """
    # Check explicit version marker
    if "_config_version" in config:
        return config["_config_version"]

    # Heuristic detection based on field presence
    if "max_concurrent_requests" in config:
        return "2.1.0"
    if "output_plugins" in config:
        return "2.0.0"
    if "max_results" in config:
        return "1.0.0"

    # Default to latest if can't detect
    return "1.0.0"


def needs_migration(config: dict[str, Any], target_version: str = CURRENT_VERSION) -> bool:
    """
    Check if config needs migration.

    Args:
        config: Configuration dictionary
        target_version: Target version to check against

    Returns:
        True if migration is needed
    """
    current = get_config_version(config)
    return current != target_version


def migrate_config(
    config: dict[str, Any],
    target_version: str = CURRENT_VERSION
) -> dict[str, Any]:
    """
    Migrate config to target version.

    Args:
        config: Configuration dictionary
        target_version: Target version string (default: current)

    Returns:
        Migrated configuration dictionary

    Raises:
        ValueError: If migration path cannot be found
    """
    current = get_config_version(config)

    if current == target_version:
        logger.debug(f"Config already at version {current}")
        return config

    logger.info(f"Migrating config from {current} to {target_version}")

    # Find migration path
    try:
        current_idx = VERSION_ORDER.index(current)
        target_idx = VERSION_ORDER.index(target_version)
    except ValueError as e:
        raise ValueError(f"Unknown config version: {e}") from e

    if current_idx > target_idx:
        raise ValueError(
            f"Cannot downgrade config from {current} to {target_version}"
        )

    # Apply migrations in order
    result = config.copy()
    for version in VERSION_ORDER[current_idx + 1:target_idx + 1]:
        if version in MIGRATIONS:
            _, migration_func = MIGRATIONS[version]
            logger.debug(f"Applying migration to {version}")
            result = migration_func(result)

    logger.info(f"Config migrated to {target_version}")
    return result


def migrate_config_file(
    path: Path,
    backup: bool = True,
    target_version: str = CURRENT_VERSION
) -> bool:
    """
    Migrate a config file in place.

    Args:
        path: Path to config file
        backup: Create .bak backup before migration
        target_version: Target version

    Returns:
        True if migration was performed, False if already current

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    # Load current config
    with open(path, encoding='utf-8') as f:
        config = json.load(f)

    # Check if migration needed
    if not needs_migration(config, target_version):
        logger.info(f"Config {path} already at version {target_version}")
        return False

    # Create backup
    if backup:
        current_version = get_config_version(config)
        backup_path = path.with_suffix(f".{current_version}.bak")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Created backup: {backup_path}")

    # Migrate
    migrated = migrate_config(config, target_version)

    # Write migrated config
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(migrated, f, indent=2)

    logger.info(f"Migrated {path} to {target_version}")
    return True


def validate_migration_path(
    from_version: str,
    to_version: str
) -> list[str]:
    """
    Get the migration path between versions.

    Args:
        from_version: Starting version
        to_version: Target version

    Returns:
        List of intermediate versions to migrate through

    Raises:
        ValueError: If path cannot be found
    """
    try:
        from_idx = VERSION_ORDER.index(from_version)
        to_idx = VERSION_ORDER.index(to_version)
    except ValueError as e:
        raise ValueError(f"Unknown version: {e}") from e

    if from_idx > to_idx:
        raise ValueError(f"Cannot downgrade from {from_version} to {to_version}")

    return VERSION_ORDER[from_idx + 1:to_idx + 1]
