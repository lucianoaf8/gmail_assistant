"""
Centralized constants for Gmail Fetcher.
Contains all shared configuration values, OAuth scopes, and path definitions.
"""

from pathlib import Path
from typing import List

# =============================================================================
# Gmail API OAuth Scopes
# =============================================================================

# Read-only access - for fetching and reading emails
SCOPES_READONLY: List[str] = ['https://www.googleapis.com/auth/gmail.readonly']

# Modify access - for reading, labeling, and deleting emails
SCOPES_MODIFY: List[str] = ['https://www.googleapis.com/auth/gmail.modify']

# Full access - for all operations including sending
SCOPES_FULL: List[str] = ['https://www.googleapis.com/auth/gmail.modify']

# Default scope for most operations
DEFAULT_SCOPES: List[str] = SCOPES_READONLY


# =============================================================================
# Default Paths
# =============================================================================

# Project root directory
PROJECT_ROOT: Path = Path(__file__).parent.parent.parent

# Configuration paths
CONFIG_DIR: Path = PROJECT_ROOT / 'config'
DEFAULT_CONFIG_PATH: Path = CONFIG_DIR / 'gmail_assistant_config.json'
AI_CONFIG_PATH: Path = CONFIG_DIR / 'config.json'

# Data paths
DATA_DIR: Path = PROJECT_ROOT / 'data'
DEFAULT_DB_PATH: Path = DATA_DIR / 'databases' / 'emails_final.db'
BACKUP_DIR: Path = PROJECT_ROOT / 'backups'

# Credentials paths
DEFAULT_CREDENTIALS_PATH: str = 'credentials.json'
DEFAULT_TOKEN_PATH: str = 'token.json'

# Cache paths
CACHE_DIR: Path = Path.home() / '.gmail_assistant_cache'


# =============================================================================
# API Rate Limits
# =============================================================================

# Gmail API rate limits
DEFAULT_REQUESTS_PER_SECOND: float = 10.0
CONSERVATIVE_REQUESTS_PER_SECOND: float = 8.0
BATCH_SIZE: int = 100
MAX_EMAILS_DEFAULT: int = 1000


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
