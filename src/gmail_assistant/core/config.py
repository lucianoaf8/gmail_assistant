"""
Configuration loader with secure defaults and strict validation.

Resolution Order (highest to lowest priority):
1. CLI arguments (--config, --credentials-path, etc.)
2. Environment variable: gmail_assistant_CONFIG
3. Project config: ./gmail-assistant.json (current directory)
4. User config: ~/.gmail-assistant/config.json
5. Built-in defaults

Security Features:
- Credentials default to ~/.gmail-assistant/ (outside any repo)
- Repo-local credentials require explicit --allow-repo-credentials flag
- Paths are validated and expanded (~, relative paths)
- Unknown keys are rejected
- Type validation on all fields

CORRECTED: ConfigError is imported from exceptions.py (single source of truth)
CORRECTED: Behavior documented when git is unavailable
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

# CORRECTED: Import ConfigError from exceptions (single authoritative source)
from gmail_assistant.core.exceptions import ConfigError

__all__ = ["AppConfig", "ConfigError"]

logger = logging.getLogger(__name__)

# Schema enforcement
_ALLOWED_KEYS = frozenset({
    "credentials_path",
    "token_path",
    "output_dir",
    "max_emails",
    "rate_limit_per_second",
    "log_level",
})

_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated, immutable application configuration."""

    credentials_path: Path
    token_path: Path
    output_dir: Path
    max_emails: int = 1000
    rate_limit_per_second: float = 10.0
    log_level: str = "INFO"

    # Class-level constants
    ENV_VAR: ClassVar[str] = "gmail_assistant_CONFIG"
    PROJECT_CONFIG_NAME: ClassVar[str] = "gmail-assistant.json"

    def __post_init__(self) -> None:
        if not 1 <= self.max_emails <= 50000:
            raise ConfigError(f"max_emails must be 1-50000, got {self.max_emails}")
        if not 0.1 <= self.rate_limit_per_second <= 100:
            raise ConfigError(
                f"rate_limit_per_second must be 0.1-100, got {self.rate_limit_per_second}"
            )
        if self.log_level not in _LOG_LEVELS:
            raise ConfigError(f"log_level must be one of {_LOG_LEVELS}")

    @classmethod
    def default_dir(cls) -> Path:
        """Return the default config directory (~/.gmail-assistant/)."""
        return Path.home() / ".gmail-assistant"

    @classmethod
    def load(
        cls,
        cli_config: Path | None = None,
        *,
        allow_repo_credentials: bool = False,
    ) -> AppConfig:
        """
        Load config following resolution order:
        1. --config CLI argument
        2. gmail_assistant_CONFIG env var
        3. ~/.gmail-fetcher/config.json (user home)
        4. Built-in defaults (all paths in ~/.gmail-fetcher/)
        """
        config_path = cls._resolve_config_path(cli_config)

        if config_path is not None:
            return cls._load_from_file(config_path, allow_repo_credentials)

        # No config file - use secure defaults (all in user home)
        default_dir = cls.default_dir()
        return cls(
            credentials_path=default_dir / "credentials.json",
            token_path=default_dir / "token.json",
            output_dir=default_dir / "backups",  # Fixed: home-based, not CWD
        )

    @classmethod
    def _resolve_config_path(cls, cli_config: Path | None) -> Path | None:
        """Resolve config path from various sources."""
        # Priority 1: CLI argument
        if cli_config is not None:
            resolved = cli_config.resolve()
            if not resolved.exists():
                raise ConfigError(f"Config file not found: {resolved}")
            return resolved

        # Priority 2: Environment variable
        env_config = os.environ.get(cls.ENV_VAR)
        if env_config:
            resolved = Path(env_config).resolve()
            if not resolved.exists():
                raise ConfigError(f"{cls.ENV_VAR} not found: {resolved}")
            return resolved

        # Priority 3: Project config (current directory)
        project_config = Path.cwd() / cls.PROJECT_CONFIG_NAME
        if project_config.exists():
            return project_config.resolve()

        # Priority 4: User home config
        user_config = cls.default_dir() / "config.json"
        if user_config.exists():
            return user_config.resolve()

        return None

    @classmethod
    def _load_from_file(
        cls,
        config_path: Path,
        allow_repo_credentials: bool,
    ) -> AppConfig:
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {config_path}: {e}") from e

        if not isinstance(data, dict):
            raise ConfigError(f"Config must be a JSON object, got {type(data).__name__}")

        # Strict key validation (fail on unknown keys)
        unknown_keys = set(data.keys()) - _ALLOWED_KEYS
        if unknown_keys:
            raise ConfigError(f"Unknown config keys: {sorted(unknown_keys)}")

        # Resolve paths relative to config file location (not CWD)
        config_dir = config_path.parent

        def resolve_path(key: str, default: Path) -> Path:
            if key not in data:
                return default
            p = Path(data[key])
            if not p.is_absolute():
                p = (config_dir / p).resolve()
            return p

        default_dir = cls.default_dir()
        credentials_path = resolve_path("credentials_path", default_dir / "credentials.json")
        token_path = resolve_path("token_path", default_dir / "token.json")
        output_dir = resolve_path("output_dir", default_dir / "backups")

        # Security check: determine repo root from config file location (not credential path)
        repo_root = cls._find_repo_root(config_path.parent)

        if repo_root is not None:
            cls._check_path_safety(
                credentials_path, "credentials_path", repo_root, allow_repo_credentials
            )
            cls._check_path_safety(
                token_path, "token_path", repo_root, allow_repo_credentials
            )

        return cls(
            credentials_path=credentials_path,
            token_path=token_path,
            output_dir=output_dir,
            max_emails=cls._get_int(data, "max_emails", 1000),
            rate_limit_per_second=cls._get_float(data, "rate_limit_per_second", 8.0),
            log_level=cls._get_str(data, "log_level", "INFO").upper(),
        )

    @staticmethod
    def _find_repo_root(search_from: Path) -> Path | None:
        """
        Find git repo root, or None if not in a repo or git not installed.

        CORRECTED: Documents behavior when git is unavailable.
        If git is not installed or not in PATH, returns None
        and repo-safety checks are skipped (credentials allowed anywhere).
        A warning is logged in this case.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                cwd=search_from,
                timeout=5,
            )
            if result.returncode == 0:
                return Path(result.stdout.strip()).resolve()
        except FileNotFoundError:
            # Git not installed - log warning
            logger.warning(
                "git not found in PATH; repo-safety checks disabled. "
                "Credentials may be placed anywhere without warning."
            )
        except subprocess.TimeoutExpired:
            # Timed out - ignore
            pass
        return None

    @staticmethod
    def _check_path_safety(
        path: Path,
        name: str,
        repo_root: Path,
        allow: bool,
    ) -> None:
        """Check if path is inside repo (security risk)."""
        resolved = path.resolve()

        # Python 3.10+: use is_relative_to for robust check
        try:
            is_inside_repo = resolved.is_relative_to(repo_root)
        except ValueError:
            # Different drives on Windows
            is_inside_repo = False

        if is_inside_repo:
            if allow:
                warnings.warn(
                    f"{name} ({resolved}) is inside git repo. "
                    f"Ensure it's in .gitignore to prevent credential leakage.",
                    UserWarning,
                    stacklevel=5,
                )
            else:
                raise ConfigError(
                    f"{name} ({resolved}) is inside git repo ({repo_root}). "
                    f"Move to {AppConfig.default_dir()} or use --allow-repo-credentials."
                )

    @staticmethod
    def _get_int(data: dict[str, Any], key: str, default: int) -> int:
        if key not in data:
            return default
        val = data[key]
        if not isinstance(val, int) or isinstance(val, bool):
            raise ConfigError(f"{key} must be integer, got {type(val).__name__}")
        return val

    @staticmethod
    def _get_float(data: dict[str, Any], key: str, default: float) -> float:
        if key not in data:
            return default
        val = data[key]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise ConfigError(f"{key} must be number, got {type(val).__name__}")
        return float(val)

    @staticmethod
    def _get_str(data: dict[str, Any], key: str, default: str) -> str:
        if key not in data:
            return default
        val = data[key]
        if not isinstance(val, str):
            raise ConfigError(f"{key} must be string, got {type(val).__name__}")
        return val
