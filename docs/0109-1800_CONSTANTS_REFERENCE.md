# Gmail Assistant Constants Reference

Complete reference of all constants and hardcoded values in gmail-assistant v2.0.0.

**Version**: 2.0.0
**Module**: `gmail_assistant.core.constants`
**Status**: Production
**Last Updated**: 2026-01-09

---

## Table of Contents

1. [Application Metadata](#application-metadata)
2. [Gmail API OAuth Scopes](#gmail-api-oauth-scopes)
3. [Default Paths](#default-paths)
4. [Rate Limiting](#rate-limiting)
5. [API Limits](#api-limits)
6. [Output Formats](#output-formats)
7. [Organization Types](#organization-types)
8. [Keyring Configuration](#keyring-configuration)
9. [Logging Configuration](#logging-configuration)
10. [Environment Variable Overrides](#environment-variable-overrides)

---

## Application Metadata

### APP_NAME

**Type**: `str`
**Value**: `"gmail-assistant"`
**Purpose**: Application name identifier
**Usage**: Command name, error messages, logging

```python
from gmail_assistant.core.constants import APP_NAME

print(f"Running {APP_NAME}")  # "Running gmail-assistant"
```

### APP_VERSION

**Type**: `str`
**Value**: `"2.0.0"`
**Purpose**: Semantic version identifier
**Usage**: --version flag, release tracking

```python
from gmail_assistant.core.constants import APP_VERSION

print(f"Version: {APP_VERSION}")  # "Version: 2.0.0"
```

---

## Gmail API OAuth Scopes

### Scope Strings

#### GMAIL_READONLY_SCOPE

**Type**: `str`
**Value**: `"https://www.googleapis.com/auth/gmail.readonly"`
**Purpose**: OAuth scope for read-only Gmail access
**Permissions**: View emails, read labels, search messages

```python
from gmail_assistant.core.constants import GMAIL_READONLY_SCOPE

scopes = [GMAIL_READONLY_SCOPE]
```

#### GMAIL_MODIFY_SCOPE

**Type**: `str`
**Value**: `"https://www.googleapis.com/auth/gmail.modify"`
**Purpose**: OAuth scope for read-write Gmail access
**Permissions**: Read/write emails, modify labels, delete emails, trash emails

```python
from gmail_assistant.core.constants import GMAIL_MODIFY_SCOPE

scopes = [GMAIL_MODIFY_SCOPE]
```

### Scope Lists

#### SCOPES_READONLY

**Type**: `List[str]`
**Value**: `["https://www.googleapis.com/auth/gmail.readonly"]`
**Purpose**: Read-only access for fetching and reading emails
**Use Case**: Backup operations, analysis, reporting

```python
from gmail_assistant.core.constants import SCOPES_READONLY

# Use for fetcher
auth = ReadOnlyGmailAuth(credentials_file)
auth.scopes = SCOPES_READONLY
```

#### SCOPES_MODIFY

**Type**: `List[str]`
**Value**: `["https://www.googleapis.com/auth/gmail.modify"]`
**Purpose**: Full read-write access for all Gmail operations
**Use Case**: Deletion, labeling, archive operations

```python
from gmail_assistant.core.constants import SCOPES_MODIFY

# Use for deleter
client = GmailAPIClient(credentials_file)
client.SCOPES = SCOPES_MODIFY
```

#### SCOPES_FULL

**Type**: `List[str]`
**Value**: `["https://www.googleapis.com/auth/gmail.modify"]`
**Purpose**: Complete access including sending emails
**Use Case**: Full-featured Gmail operations (sending deferred to v2.1.0)

```python
from gmail_assistant.core.constants import SCOPES_FULL
```

#### DEFAULT_SCOPES

**Type**: `List[str]`
**Value**: `["https://www.googleapis.com/auth/gmail.readonly"]`
**Purpose**: Default scope for most operations
**Rationale**: Principle of least privilege - read-only by default

```python
from gmail_assistant.core.constants import DEFAULT_SCOPES

# Used if no scope explicitly specified
scopes = DEFAULT_SCOPES  # SCOPES_READONLY
```

---

## Default Paths

### Configuration Directories

#### CONFIG_DIR

**Type**: `Path`
**Value**: `PROJECT_ROOT / 'config'` (or `GMAIL_ASSISTANT_CONFIG_DIR` env var)
**Purpose**: Directory containing configuration files
**Environment Override**: `GMAIL_ASSISTANT_CONFIG_DIR`

```python
from gmail_assistant.core.constants import CONFIG_DIR

# Resolves to project config directory
print(CONFIG_DIR)  # Path("/path/to/project/config")
```

#### DEFAULT_CONFIG_PATH

**Type**: `Path`
**Value**: `CONFIG_DIR / 'gmail_assistant_config.json'`
**Purpose**: Default application configuration file location
**Contains**: Query presets, default settings

```python
from gmail_assistant.core.constants import DEFAULT_CONFIG_PATH

config_data = json.loads(DEFAULT_CONFIG_PATH.read_text())
```

#### AI_CONFIG_PATH

**Type**: `Path`
**Value**: `CONFIG_DIR / 'config.json'`
**Purpose**: AI newsletter detection configuration
**Contains**: Keywords, domains, confidence weights

```python
from gmail_assistant.core.constants import AI_CONFIG_PATH

ai_config = json.loads(AI_CONFIG_PATH.read_text())
```

### Data Directories

#### DATA_DIR

**Type**: `Path`
**Value**: `PROJECT_ROOT / 'data'` (or `GMAIL_ASSISTANT_DATA_DIR` env var)
**Purpose**: Directory for application data files
**Environment Override**: `GMAIL_ASSISTANT_DATA_DIR`

```python
from gmail_assistant.core.constants import DATA_DIR

# Create if missing
DATA_DIR.mkdir(parents=True, exist_ok=True)
```

#### DEFAULT_DB_PATH

**Type**: `Path`
**Value**: `DATA_DIR / 'databases' / 'emails_final.db'`
**Purpose**: Default database location for email storage
**Format**: SQLite database

```python
from gmail_assistant.core.constants import DEFAULT_DB_PATH

# Database path for caching/analysis
db_conn = sqlite3.connect(DEFAULT_DB_PATH)
```

### Backup Directory

#### BACKUP_DIR

**Type**: `Path`
**Value**: `PROJECT_ROOT / 'backups'` (or `GMAIL_ASSISTANT_BACKUP_DIR` env var)
**Purpose**: Default directory for email backups
**Environment Override**: `GMAIL_ASSISTANT_BACKUP_DIR`

```python
from gmail_assistant.core.constants import BACKUP_DIR

# Download emails to backup directory
output_dir = BACKUP_DIR / "2025-01"
```

### Credentials Directory

#### CREDENTIALS_DIR

**Type**: `Path`
**Value**: `CONFIG_DIR / 'security'` (or `GMAIL_ASSISTANT_CREDENTIALS_DIR` env var)
**Purpose**: Directory for OAuth credentials and tokens
**Environment Override**: `GMAIL_ASSISTANT_CREDENTIALS_DIR`
**Security**: Should be outside git repository, mode 0700

```python
from gmail_assistant.core.constants import CREDENTIALS_DIR

# Credentials stored here
credentials_file = CREDENTIALS_DIR / "credentials.json"
```

#### DEFAULT_CREDENTIALS_PATH

**Type**: `str`
**Value**: `"{CREDENTIALS_DIR / 'credentials.json'}"`
**Purpose**: Default OAuth credentials file location
**Format**: JSON from Google Cloud Console

```python
from gmail_assistant.core.constants import DEFAULT_CREDENTIALS_PATH

# String path for compatibility
fetcher = GmailFetcher(DEFAULT_CREDENTIALS_PATH)
```

#### DEFAULT_TOKEN_PATH

**Type**: `str`
**Value**: `"token.json"`
**Purpose**: Legacy token file path (deprecated)
**Status**: Deprecated in favor of keyring storage
**Rationale**: Plaintext token storage security risk

```python
from gmail_assistant.core.constants import DEFAULT_TOKEN_PATH

# Now stored in OS keyring instead
# This path maintained for backward compatibility
```

### Cache Directory

#### CACHE_DIR

**Type**: `Path`
**Value**: `~/.gmail_assistant_cache` (or `GMAIL_ASSISTANT_CACHE_DIR` env var)
**Purpose**: Directory for temporary cache files
**Environment Override**: `GMAIL_ASSISTANT_CACHE_DIR`
**Cleanup**: Not automatically cleaned

```python
from gmail_assistant.core.constants import CACHE_DIR

cache_file = CACHE_DIR / "message_cache.db"
```

---

## Rate Limiting

### DEFAULT_RATE_LIMIT

**Type**: `float`
**Value**: `10.0`
**Unit**: Requests per second
**Purpose**: Default API request rate limit
**Rationale**: Gmail API safe limit

```python
from gmail_assistant.core.constants import DEFAULT_RATE_LIMIT

# Use in rate limiter
limiter = RateLimiter(requests_per_second=DEFAULT_RATE_LIMIT)
```

### DEFAULT_REQUESTS_PER_SECOND

**Type**: `float`
**Value**: `10.0`
**Purpose**: Alias for DEFAULT_RATE_LIMIT
**Usage**: Alternative naming convention

```python
from gmail_assistant.core.constants import DEFAULT_REQUESTS_PER_SECOND
```

### CONSERVATIVE_REQUESTS_PER_SECOND

**Type**: `float`
**Value**: `8.0`
**Purpose**: Conservative/safe rate limit
**Use Case**: Production deployments, high-volume operations

```python
from gmail_assistant.core.constants import CONSERVATIVE_REQUESTS_PER_SECOND

# More conservative than default
rate = CONSERVATIVE_REQUESTS_PER_SECOND
```

### MAX_RATE_LIMIT

**Type**: `float`
**Value**: `100.0`
**Unit**: Requests per second
**Purpose**: Maximum allowed rate limit
**Enforcement**: Validated in AppConfig

```python
from gmail_assistant.core.constants import MAX_RATE_LIMIT

# Used in configuration validation
if rate > MAX_RATE_LIMIT:
    raise ConfigError(f"Rate limit {rate} exceeds maximum {MAX_RATE_LIMIT}")
```

---

## API Limits

### BATCH_SIZE

**Type**: `int`
**Value**: `100`
**Purpose**: Default batch size for batch operations
**Usage**: Fetching multiple emails, bulk deletions

```python
from gmail_assistant.core.constants import BATCH_SIZE

# Process emails in batches
for i in range(0, len(email_ids), BATCH_SIZE):
    batch = email_ids[i:i+BATCH_SIZE]
    process_batch(batch)
```

### MAX_EMAILS_LIMIT

**Type**: `int`
**Value**: `100000`
**Purpose**: Hard maximum on email operations
**Enforcement**: Validated in AppConfig

```python
from gmail_assistant.core.constants import MAX_EMAILS_LIMIT

if max_emails > MAX_EMAILS_LIMIT:
    raise ConfigError(f"max_emails {max_emails} exceeds limit {MAX_EMAILS_LIMIT}")
```

### DEFAULT_MAX_EMAILS

**Type**: `int`
**Value**: `1000`
**Purpose**: Default maximum emails per operation
**Alternative**: `MAX_EMAILS_DEFAULT` (alias)

```python
from gmail_assistant.core.constants import DEFAULT_MAX_EMAILS

# Used if not specified in config
max_fetch = DEFAULT_MAX_EMAILS
```

### MAX_EMAILS_DEFAULT

**Type**: `int`
**Value**: `1000`
**Purpose**: Alias for DEFAULT_MAX_EMAILS

```python
from gmail_assistant.core.constants import MAX_EMAILS_DEFAULT
```

---

## Output Formats

### SUPPORTED_OUTPUT_FORMATS

**Type**: `List[str]`
**Value**: `['eml', 'markdown', 'both']`
**Purpose**: Valid output format choices
**Usage**: CLI validation, format selection

```python
from gmail_assistant.core.constants import SUPPORTED_OUTPUT_FORMATS

# Validate user input
if user_format not in SUPPORTED_OUTPUT_FORMATS:
    raise ValueError(f"Format must be one of {SUPPORTED_OUTPUT_FORMATS}")
```

**Formats**:
- `'eml'`: EML format only (individual email files)
- `'markdown'`: Markdown format only (human-readable)
- `'both'`: Both EML and Markdown (default)

### DEFAULT_OUTPUT_FORMAT

**Type**: `str`
**Value**: `'both'`
**Purpose**: Default output format if not specified
**Rationale**: Preserves all data (EML) and readability (Markdown)

```python
from gmail_assistant.core.constants import DEFAULT_OUTPUT_FORMAT

format_choice = DEFAULT_OUTPUT_FORMAT  # 'both'
```

---

## Organization Types

### SUPPORTED_ORGANIZATION_TYPES

**Type**: `List[str]`
**Value**: `['date', 'sender', 'none']`
**Purpose**: Valid file organization strategies
**Usage**: CLI validation, directory structure

```python
from gmail_assistant.core.constants import SUPPORTED_ORGANIZATION_TYPES

# Validate organization choice
if org_type not in SUPPORTED_ORGANIZATION_TYPES:
    raise ValueError(f"Organization must be one of {SUPPORTED_ORGANIZATION_TYPES}")
```

**Organization Types**:
- `'date'`: Organize by date (year/month/day)
- `'sender'`: Organize by sender domain
- `'none'`: Flat directory (no organization)

### DEFAULT_ORGANIZATION

**Type**: `str`
**Value**: `'date'`
**Purpose**: Default organization strategy
**Rationale**: Temporal organization useful for archiving

```python
from gmail_assistant.core.constants import DEFAULT_ORGANIZATION

# Default: organize by date
path = output_dir / "2025" / "01" / "15" / email.eml
```

---

## Keyring Configuration

### KEYRING_SERVICE

**Type**: `str`
**Value**: `"gmail_assistant"`
**Purpose**: Keyring service identifier
**Usage**: OS credential storage key

```python
from gmail_assistant.core.constants import KEYRING_SERVICE

# Store in system keyring
keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, credentials_json)
```

### KEYRING_USERNAME

**Type**: `str`
**Value**: `"oauth_credentials"`
**Purpose**: Keyring username identifier
**Usage**: OS credential storage account

```python
from gmail_assistant.core.constants import KEYRING_USERNAME

# Retrieve from system keyring
creds = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
```

**Keyring Details**:
- Service: "gmail_assistant"
- Username: "oauth_credentials"
- Password: Full OAuth credentials JSON
- Storage: OS-dependent
  - Linux: `~/.local/share/keyring/` or secret-service
  - macOS: Keychain
  - Windows: Credential Manager

---

## Logging Configuration

### DEFAULT_LOG_FORMAT

**Type**: `str`
**Value**: `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`
**Purpose**: Default log message format string
**Format**: Python logging format
**Components**:
- `%(asctime)s`: Timestamp (ISO format)
- `%(name)s`: Logger name (module name)
- `%(levelname)s`: Log level (DEBUG, INFO, WARNING, etc.)
- `%(message)s`: Log message

```python
from gmail_assistant.core.constants import DEFAULT_LOG_FORMAT

logging.basicConfig(format=DEFAULT_LOG_FORMAT)
```

**Example Output**:
```
2025-01-09 15:30:45,123 - gmail_assistant.core.fetch - INFO - Searching for messages: 'is:unread'
```

### DEFAULT_LOG_LEVEL

**Type**: `str`
**Value**: `'INFO'`
**Purpose**: Default logging verbosity level
**Valid Values**: DEBUG, INFO, WARNING, ERROR, CRITICAL

```python
from gmail_assistant.core.constants import DEFAULT_LOG_LEVEL

logging.getLogger("gmail_assistant").setLevel(DEFAULT_LOG_LEVEL)
```

---

## Environment Variable Overrides

All path constants can be overridden via environment variables.

### Configuration Directory Override

**Variable**: `GMAIL_ASSISTANT_CONFIG_DIR`
**Overrides**: `CONFIG_DIR`

```bash
export GMAIL_ASSISTANT_CONFIG_DIR=/etc/gmail-assistant
```

### Data Directory Override

**Variable**: `GMAIL_ASSISTANT_DATA_DIR`
**Overrides**: `DATA_DIR`

```bash
export GMAIL_ASSISTANT_DATA_DIR=/var/lib/gmail-assistant
```

### Backup Directory Override

**Variable**: `GMAIL_ASSISTANT_BACKUP_DIR`
**Overrides**: `BACKUP_DIR`

```bash
export GMAIL_ASSISTANT_BACKUP_DIR=/mnt/external/gmail_backups
```

### Credentials Directory Override

**Variable**: `GMAIL_ASSISTANT_CREDENTIALS_DIR`
**Overrides**: `CREDENTIALS_DIR`

```bash
export GMAIL_ASSISTANT_CREDENTIALS_DIR=/root/.secure/gmail
```

### Cache Directory Override

**Variable**: `GMAIL_ASSISTANT_CACHE_DIR`
**Overrides**: `CACHE_DIR`

```bash
export GMAIL_ASSISTANT_CACHE_DIR=/tmp/gmail_cache
```

### Implementation

Constants are resolved at import time using helper function:

```python
def _get_env_path(env_var: str, default: Path) -> Path:
    """Get path from environment variable or use default."""
    env_value = os.environ.get(env_var)
    if env_value:
        return Path(env_value)
    return default

# Usage:
CONFIG_DIR = _get_env_path('GMAIL_ASSISTANT_CONFIG_DIR', PROJECT_ROOT / 'config')
```

---

## Complete Constants Example

```python
from gmail_assistant.core.constants import (
    # Application
    APP_NAME,
    APP_VERSION,

    # OAuth Scopes
    GMAIL_READONLY_SCOPE,
    GMAIL_MODIFY_SCOPE,
    SCOPES_READONLY,
    SCOPES_MODIFY,
    SCOPES_FULL,
    DEFAULT_SCOPES,

    # Paths
    CONFIG_DIR,
    DATA_DIR,
    BACKUP_DIR,
    CACHE_DIR,
    CREDENTIALS_DIR,
    DEFAULT_CONFIG_PATH,
    AI_CONFIG_PATH,
    DEFAULT_DB_PATH,

    # Rate Limiting
    DEFAULT_RATE_LIMIT,
    CONSERVATIVE_REQUESTS_PER_SECOND,
    MAX_RATE_LIMIT,

    # API Limits
    BATCH_SIZE,
    MAX_EMAILS_LIMIT,
    DEFAULT_MAX_EMAILS,

    # Output
    SUPPORTED_OUTPUT_FORMATS,
    DEFAULT_OUTPUT_FORMAT,
    SUPPORTED_ORGANIZATION_TYPES,
    DEFAULT_ORGANIZATION,

    # Security
    KEYRING_SERVICE,
    KEYRING_USERNAME,

    # Logging
    DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_LEVEL,
)

print(f"{APP_NAME} v{APP_VERSION}")
print(f"Config: {CONFIG_DIR}")
print(f"Backups: {BACKUP_DIR}")
print(f"Rate limit: {DEFAULT_RATE_LIMIT} req/s")
print(f"Max emails: {DEFAULT_MAX_EMAILS}")
```

---

## See Also

- [CLI Reference](0109-1500_CLI_REFERENCE.md) - Command-line interface documentation
- [Configuration Reference](0109-1600_CONFIGURATION_REFERENCE.md) - Configuration file parameters
- [Public API Reference](0109-1700_PUBLIC_API_REFERENCE.md) - Python API documentation

