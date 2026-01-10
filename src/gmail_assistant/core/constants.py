"""
Centralized constants for Gmail Assistant.
Contains all shared configuration values, OAuth scopes, and path definitions.

Security: Supports environment variable overrides for paths (L-1 fix)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional


def _get_env_path(env_var: str, default: Path) -> Path:
    """
    Get path from environment variable or use default (L-1 security fix).

    Args:
        env_var: Environment variable name
        default: Default path if env var not set

    Returns:
        Path from environment or default
    """
    env_value = os.environ.get(env_var)
    if env_value:
        return Path(env_value)
    return default


# =============================================================================
# Application Metadata
# =============================================================================

APP_NAME: str = "gmail-assistant"
APP_VERSION: str = "2.0.0"

# Default paths
DEFAULT_CONFIG_DIR_NAME: str = ".gmail-assistant"
DEFAULT_CONFIG_FILE_NAME: str = "config.json"

# =============================================================================
# Gmail API OAuth Scopes
# =============================================================================

# Single scope strings
GMAIL_READONLY_SCOPE: str = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_MODIFY_SCOPE: str = "https://www.googleapis.com/auth/gmail.modify"

# Read-only access - for fetching and reading emails
SCOPES_READONLY: List[str] = [GMAIL_READONLY_SCOPE]

# Modify access - for reading, labeling, and deleting emails
SCOPES_MODIFY: List[str] = [GMAIL_MODIFY_SCOPE]

# Full access - for all operations including sending
SCOPES_FULL: List[str] = ['https://www.googleapis.com/auth/gmail.modify']

# Default scope for most operations
DEFAULT_SCOPES: List[str] = SCOPES_READONLY


# =============================================================================
# Default Paths (with environment variable override support - L-1 fix)
# =============================================================================

# Project root directory
PROJECT_ROOT: Path = Path(__file__).parent.parent.parent

# Configuration paths with env override (L-1 fix)
CONFIG_DIR: Path = _get_env_path(
    'GMAIL_ASSISTANT_CONFIG_DIR',
    PROJECT_ROOT / 'config'
)
DEFAULT_CONFIG_PATH: Path = CONFIG_DIR / 'gmail_assistant_config.json'
AI_CONFIG_PATH: Path = CONFIG_DIR / 'config.json'

# Data paths with env override (L-1 fix)
DATA_DIR: Path = _get_env_path(
    'GMAIL_ASSISTANT_DATA_DIR',
    PROJECT_ROOT / 'data'
)
DEFAULT_DB_PATH: Path = DATA_DIR / 'databases' / 'emails_final.db'

# Backup directory with env override (L-1 fix)
BACKUP_DIR: Path = _get_env_path(
    'GMAIL_ASSISTANT_BACKUP_DIR',
    PROJECT_ROOT / 'backups'
)

# Credentials directory with env override (L-1 fix)
CREDENTIALS_DIR: Path = _get_env_path(
    'GMAIL_ASSISTANT_CREDENTIALS_DIR',
    CONFIG_DIR / 'security'
)

# Credentials paths
DEFAULT_CREDENTIALS_PATH: str = str(CREDENTIALS_DIR / 'credentials.json')
DEFAULT_TOKEN_PATH: str = 'token.json'  # Deprecated: now uses keyring

# Cache paths with env override (L-1 fix)
CACHE_DIR: Path = _get_env_path(
    'GMAIL_ASSISTANT_CACHE_DIR',
    Path.home() / '.gmail_assistant_cache'
)


# =============================================================================
# API Rate Limits
# =============================================================================

# Gmail API rate limits
DEFAULT_RATE_LIMIT: float = 10.0  # requests per second
DEFAULT_REQUESTS_PER_SECOND: float = 10.0  # alias
CONSERVATIVE_REQUESTS_PER_SECOND: float = 8.0
MAX_RATE_LIMIT: float = 100.0
BATCH_SIZE: int = 100
MAX_EMAILS_LIMIT: int = 100000
MAX_EMAILS_DEFAULT: int = 1000
DEFAULT_MAX_EMAILS: int = 1000  # alias


# =============================================================================
# Keyring Configuration
# =============================================================================

KEYRING_SERVICE: str = "gmail_assistant"
KEYRING_USERNAME: str = "oauth_credentials"


# =============================================================================
# Logging Configuration
# =============================================================================

DEFAULT_LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL: str = 'INFO'


# =============================================================================
# Output Formats
# =============================================================================

SUPPORTED_OUTPUT_FORMATS: List[str] = ['eml', 'markdown', 'both']
DEFAULT_OUTPUT_FORMAT: str = 'both'

SUPPORTED_ORGANIZATION_TYPES: List[str] = ['date', 'sender', 'none']
DEFAULT_ORGANIZATION: str = 'date'
