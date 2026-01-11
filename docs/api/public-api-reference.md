# Gmail Assistant Public API Reference

Comprehensive Python API documentation for programmatic use of gmail-assistant v2.0.0.

**Version**: 2.0.0
**Status**: Production
**Last Updated**: 2026-01-09

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Classes](#core-classes)
3. [Data Models](#data-models)
4. [Protocols](#protocols)
5. [Exception Hierarchy](#exception-hierarchy)
6. [Configuration API](#configuration-api)
7. [Constants](#constants)

---

## Quick Start

### Installation

```bash
pip install gmail-assistant
```

### Basic Usage

```python
from gmail_assistant.core.config import AppConfig
from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

# Load configuration
config = AppConfig.load()

# Create fetcher with credentials
fetcher = GmailFetcher(str(config.credentials_path))

# Authenticate
fetcher.authenticate()

# Get profile
profile = fetcher.get_profile()
print(f"Email: {profile['email']}")

# Search messages
message_ids = fetcher.search_messages(
    query="is:unread",
    max_results=100
)

# Get message details
for msg_id in message_ids[:5]:
    message = fetcher.get_message_details(msg_id)
    if message:
        print(f"Subject: {message['subject']}")
```

---

## Core Classes

### AppConfig

**Module**: `gmail_assistant.core.config`
**Inherits**: `dataclass` (frozen, immutable)
**Purpose**: Load and validate application configuration

#### Class Definition

```python
@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated, immutable application configuration."""
    credentials_path: Path
    token_path: Path
    output_dir: Path
    max_emails: int = 1000
    rate_limit_per_second: float = 10.0
    log_level: str = "INFO"
```

#### Fields

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| credentials_path | Path | N/A (required from config or env) | N/A | OAuth credentials file location |
| token_path | Path | N/A (required from config or env) | N/A | OAuth token file location |
| output_dir | Path | N/A (required from config or env) | N/A | Output directory for backups |
| max_emails | int | 1000 | 1-50000 | Maximum emails per operation |
| rate_limit_per_second | float | 10.0 | 0.1-100 | API request rate limit |
| log_level | str | "INFO" | DEBUG, INFO, WARNING, ERROR, CRITICAL | Logging level |

#### Class Methods

##### load()

```python
@classmethod
def load(
    cls,
    cli_config: Path | None = None,
    *,
    allow_repo_credentials: bool = False,
) -> "AppConfig":
    """
    Load config following resolution order.

    Args:
        cli_config: Path to config file from --config argument
        allow_repo_credentials: Allow credentials in git repository

    Returns:
        Validated AppConfig instance

    Raises:
        ConfigError: If config invalid or credentials in repo without flag
    """
```

**Resolution Order**:
1. CLI argument (`cli_config`)
2. Environment variable `gmail_assistant_CONFIG`
3. Project config `./gmail-assistant.json`
4. User config `~/.gmail-assistant/config.json`
5. Secure defaults (all in user home)

**Example**:
```python
# Load from file
config = AppConfig.load(Path("/etc/gmail-assistant/config.json"))

# Load from environment
config = AppConfig.load()  # Uses gmail_assistant_CONFIG env var if set

# Allow repo credentials (with warning)
config = AppConfig.load(allow_repo_credentials=True)
```

##### default_dir()

```python
@classmethod
def default_dir(cls) -> Path:
    """
    Return the default config directory (~/.gmail-assistant/).

    Returns:
        Path to ~/.gmail-assistant/
    """
```

**Example**:
```python
config_dir = AppConfig.default_dir()
# Returns: Path("/home/user/.gmail-assistant")
```

#### Instance Methods

##### __post_init__()

Automatically called after initialization. Validates field ranges:

```python
def __post_init__(self) -> None:
    if not 1 <= self.max_emails <= 50000:
        raise ConfigError(f"max_emails must be 1-50000, got {self.max_emails}")
    if not 0.1 <= self.rate_limit_per_second <= 100:
        raise ConfigError(f"rate_limit_per_second must be 0.1-100, got ...")
    if self.log_level not in _LOG_LEVELS:
        raise ConfigError(f"log_level must be one of {_LOG_LEVELS}")
```

---

### GmailFetcher

**Module**: `gmail_assistant.core.fetch.gmail_assistant`
**Purpose**: Fetch emails from Gmail API

#### Constructor

```python
class GmailFetcher:
    def __init__(self, credentials_file: str = 'credentials.json'):
        """
        Initialize Gmail fetcher.

        Args:
            credentials_file: Path to OAuth credentials.json file
        """
```

**Example**:
```python
from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

fetcher = GmailFetcher('~/.gmail-assistant/credentials.json')
```

#### Methods

##### authenticate()

```python
def authenticate(self) -> bool:
    """
    Authenticate with Gmail API using secure credential storage.

    Returns:
        True if successful

    Raises:
        AuthError: If authentication fails
    """
```

**Example**:
```python
if fetcher.authenticate():
    print("Authenticated successfully")
else:
    print("Authentication failed")
```

##### service (property)

```python
@property
def service(self):
    """
    Get Gmail service, authenticating if necessary.

    Returns:
        Google API service object for making API calls

    Raises:
        RuntimeError: If not authenticated
    """
```

**Example**:
```python
service = fetcher.service
profile = service.users().getProfile(userId='me').execute()
```

##### get_profile()

```python
def get_profile(self) -> Optional[Dict]:
    """
    Get Gmail profile info for authenticated user.

    Returns:
        Dictionary with:
        - email: User's email address
        - total_messages: Total message count
        - total_threads: Total thread count

        Returns None if error occurs
    """
```

**Example**:
```python
profile = fetcher.get_profile()
if profile:
    print(f"Email: {profile['email']}")
    print(f"Messages: {profile['total_messages']}")
```

##### search_messages()

```python
def search_messages(
    self,
    query: str = '',
    max_results: int = 100
) -> List[str]:
    """
    Search for messages matching query.

    Args:
        query: Gmail search query (e.g., "is:unread", "from:example.com")
        max_results: Maximum number of message IDs to return

    Returns:
        List of message IDs matching query

        Returns empty list if error occurs
    """
```

**Parameters**:
- `query`: Gmail search syntax (supports operators: is:unread, from:, subject:, etc.)
- `max_results`: Number of results to fetch (pagination handled automatically)

**Example**:
```python
# Unread emails
ids = fetcher.search_messages("is:unread", max_results=100)

# From domain
ids = fetcher.search_messages("from:work.com", max_results=50)

# Combined query
ids = fetcher.search_messages("is:unread after:2025/01/01", max_results=200)

# Pagination
all_ids = []
token = None
while len(all_ids) < 1000:
    batch = fetcher.search_messages("is:unread", max_results=100)
    all_ids.extend(batch)
    if len(batch) < 100:
        break
```

##### get_message_details()

```python
def get_message_details(
    self,
    message_id: str
) -> Optional[Dict]:
    """
    Get full message details with validation.

    Args:
        message_id: The Gmail message ID

    Returns:
        Message details dictionary containing:
        - id: Message ID
        - threadId: Thread ID
        - payload: Message content structure
        - headers: Email headers

        Returns None if error or validation fails

    Raises:
        ValueError: If response structure invalid
    """
```

**Example**:
```python
message = fetcher.get_message_details("message_id_123")
if message:
    headers = {h['name']: h['value']
               for h in message['payload']['headers']}
    print(f"Subject: {headers.get('Subject')}")
    print(f"From: {headers.get('From')}")
```

---

## Data Models

### Email

**Module**: `gmail_assistant.core.schemas`
**Base**: `pydantic.BaseModel`
**Purpose**: Canonical email model (single source of truth)

#### Fields

```python
class Email(BaseModel):
    # Identity
    gmail_id: str  # Unique Gmail message ID
    thread_id: str  # Gmail thread ID

    # Core metadata
    subject: str = ""  # Email subject line
    sender: str  # Sender email address
    recipients: List[EmailParticipant] = []  # Recipients
    date: datetime  # Email received timestamp

    # Content
    body_plain: Optional[str] = None  # Plain text body
    body_html: Optional[str] = None  # HTML body

    # Gmail-specific
    labels: List[str] = []  # Gmail labels
    snippet: str = ""  # Email preview snippet
    history_id: int = 0  # Gmail history ID for sync
    size_estimate: int = 0  # Estimated size in bytes

    # Status flags
    is_unread: bool = True
    is_starred: bool = False
    has_attachments: bool = False
```

#### Class Methods

##### from_gmail_message()

```python
@classmethod
def from_gmail_message(cls, message: Dict[str, Any]) -> 'Email':
    """
    Create Email from Gmail API message response.

    Args:
        message: Gmail API message object

    Returns:
        Email instance
    """
```

**Example**:
```python
# Get message from Gmail API
api_message = service.users().messages().get(
    userId='me',
    id='message_id',
    format='full'
).execute()

# Convert to Email model
email = Email.from_gmail_message(api_message)
print(f"Subject: {email.subject}")
print(f"From: {email.sender}")
print(f"Date: {email.date}")
```

#### Properties

##### sender_domain

```python
@property
def sender_domain(self) -> str:
    """Extract sender's domain."""
    # Returns "example.com" from "user@example.com"
```

##### year_month

```python
@property
def year_month(self) -> str:
    """Get year-month string for partitioning."""
    # Returns "2025-01" format
```

#### Instance Methods

##### to_dict()

```python
def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary representation."""
```

**Example**:
```python
email = Email(...)
data = email.to_dict()
json_str = json.dumps(data)
```

---

### EmailParticipant

**Module**: `gmail_assistant.core.schemas`
**Base**: `pydantic.BaseModel`
**Purpose**: Email participant with type and domain

#### Fields

```python
class EmailParticipant(BaseModel):
    address: str  # Email address
    type: ParticipantType  # FROM, TO, CC, BCC
    display_name: Optional[str] = None  # Display name
```

#### Enums

**ParticipantType**:
```python
class ParticipantType(str, Enum):
    FROM = "from"
    TO = "to"
    CC = "cc"
    BCC = "bcc"
```

#### Properties

##### domain

```python
@property
def domain(self) -> str:
    """Extract domain from email address."""
```

---

### EmailMetadata (DTO)

**Module**: `gmail_assistant.core.protocols`
**Base**: `dataclass`
**Status**: Deprecated (use Email class instead)
**Purpose**: Email metadata transfer object

#### Fields

```python
@dataclass
class EmailMetadata:
    id: str  # Message ID
    thread_id: str  # Thread ID
    subject: str  # Subject line
    sender: str  # Sender email
    recipients: List[str]  # Recipient emails
    date: str  # Date string
    labels: List[str]  # Gmail labels
    snippet: str = ""  # Preview snippet
    size_estimate: int = 0  # Size in bytes
```

---

### FetchResult (DTO)

**Module**: `gmail_assistant.core.protocols`
**Base**: `dataclass`
**Purpose**: Result of email fetch operation

#### Fields

```python
@dataclass
class FetchResult:
    success: bool  # Operation succeeded
    emails_fetched: int  # Number fetched
    emails_failed: int  # Number failed
    output_directory: str  # Output path
    error_message: Optional[str] = None  # Error if any
```

---

### DeleteResult (DTO)

**Module**: `gmail_assistant.core.protocols`
**Base**: `dataclass`
**Purpose**: Result of email deletion operation

#### Fields

```python
@dataclass
class DeleteResult:
    deleted: int  # Permanently deleted count
    failed: int  # Failed deletion count
    trashed: int = 0  # Moved to trash count
    error_messages: List[str] = []  # Error messages
```

---

### ParseResult (DTO)

**Module**: `gmail_assistant.core.protocols`
**Base**: `dataclass`
**Purpose**: Result of email parsing operation

#### Fields

```python
@dataclass
class ParseResult:
    success: bool  # Parsing succeeded
    markdown: str  # Parsed markdown content
    strategy: str  # Parsing strategy used
    quality: float  # Quality score (0.0-1.0)
    metadata: Dict[str, Any] = {}  # Additional metadata
    error_message: Optional[str] = None  # Error if failed
```

---

## Protocols

Protocols define structural interfaces for implementing Gmail operations. Use these for type hints and dependency injection.

### GmailClientProtocol

**Module**: `gmail_assistant.core.protocols`

```python
@runtime_checkable
class GmailClientProtocol(Protocol):
    """Protocol for Gmail API client operations."""

    def authenticate(self) -> bool:
        """Authenticate with the Gmail API."""
        ...

    def get_service(self) -> Any:
        """Get the authenticated Gmail API service object."""
        ...

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        ...

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the authenticated user."""
        ...
```

**Usage**:
```python
from gmail_assistant.core.protocols import GmailClientProtocol

def process_emails(client: GmailClientProtocol) -> int:
    """Accept any object implementing GmailClientProtocol."""
    if not client.is_authenticated:
        client.authenticate()

    user_info = client.get_user_info()
    return user_info['messagesTotal']
```

### EmailFetcherProtocol

**Module**: `gmail_assistant.core.protocols`

```python
@runtime_checkable
class EmailFetcherProtocol(Protocol):
    """Protocol for email fetching operations."""

    def search_messages(
        self,
        query: str,
        max_results: int = 100
    ) -> List[str]:
        """Search for messages matching the given query."""
        ...

    def get_message(
        self,
        message_id: str,
        format: str = "full"
    ) -> Optional[Dict[str, Any]]:
        """Get a single message by ID."""
        ...

    def get_message_metadata(
        self,
        message_id: str
    ) -> Optional[EmailMetadata]:
        """Get metadata for a single message."""
        ...

    def download_emails(
        self,
        query: str,
        max_emails: int = 100,
        output_dir: str = "gmail_backup",
        format_type: str = "both",
        organize_by: str = "date"
    ) -> FetchResult:
        """Download emails matching query to local files."""
        ...

    def get_profile(self) -> Optional[Dict[str, Any]]:
        """Get the Gmail profile for the authenticated user."""
        ...
```

### EmailDeleterProtocol

**Module**: `gmail_assistant.core.protocols`

```python
@runtime_checkable
class EmailDeleterProtocol(Protocol):
    """Protocol for email deletion operations."""

    def delete_emails(
        self,
        email_ids: List[str],
        batch_size: int = 100
    ) -> DeleteResult:
        """Permanently delete emails by ID."""
        ...

    def trash_emails(
        self,
        email_ids: List[str]
    ) -> DeleteResult:
        """Move emails to trash."""
        ...

    def get_email_count(self, query: str) -> int:
        """Get count of emails matching query."""
        ...

    def delete_by_query(
        self,
        query: str,
        dry_run: bool = True,
        max_delete: Optional[int] = None
    ) -> DeleteResult:
        """Delete emails matching a query."""
        ...
```

### EmailParserProtocol

**Module**: `gmail_assistant.core.protocols`

```python
@runtime_checkable
class EmailParserProtocol(Protocol):
    """Protocol for email parsing operations."""

    def parse_eml(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Parse an EML file and extract its contents."""
        ...

    def parse_html(
        self,
        html_content: str,
        sender: str = ""
    ) -> ParseResult:
        """Parse HTML email content."""
        ...

    def extract_headers(
        self,
        headers: List[Dict[str, str]]
    ) -> Dict[str, str]:
        """Extract and normalize email headers."""
        ...
```

---

## Exception Hierarchy

### GmailAssistantError

**Module**: `gmail_assistant.core.exceptions`
**Base**: `Exception`

```python
class GmailAssistantError(Exception):
    """Base exception for Gmail Assistant. All domain exceptions inherit from this."""
```

#### Subclasses

##### ConfigError

```python
class ConfigError(GmailAssistantError):
    """Configuration-related errors. Maps to exit code 5."""
```

**Raised By**:
- AppConfig.load() - Invalid config file, unknown keys
- AppConfig.__post_init__() - Parameter out of range

**Example**:
```python
from gmail_assistant.core.exceptions import ConfigError

try:
    config = AppConfig.load(Path("invalid.json"))
except ConfigError as e:
    print(f"Config error: {e}")  # Config file not found: invalid.json
```

##### AuthError

```python
class AuthError(GmailAssistantError):
    """Authentication/authorization errors. Maps to exit code 3."""
```

**Raised By**:
- GmailFetcher.authenticate() - OAuth flow failure
- GmailAPIClient._authenticate() - Credential invalid

##### NetworkError

```python
class NetworkError(GmailAssistantError):
    """Network connectivity errors. Maps to exit code 4."""
```

**Raised By**:
- Network timeouts, connection failures
- Gmail API unreachable

##### APIError

```python
class APIError(GmailAssistantError):
    """Gmail API errors. Maps to exit code 1 (general)."""
```

**Raised By**:
- Gmail API returns error
- Invalid message ID

### Exception Handling

```python
from gmail_assistant.core.exceptions import (
    ConfigError,
    AuthError,
    NetworkError,
    GmailAssistantError,
)

try:
    config = AppConfig.load()
    fetcher = GmailFetcher(str(config.credentials_path))
    fetcher.authenticate()
except ConfigError as e:
    print(f"Configuration problem: {e}")
except AuthError as e:
    print(f"Authentication failed: {e}")
except NetworkError as e:
    print(f"Network problem: {e}")
except GmailAssistantError as e:
    print(f"Other error: {e}")
```

---

## Configuration API

### Loading Configuration

```python
from gmail_assistant.core.config import AppConfig

# Load with automatic resolution
config = AppConfig.load()

# Load from specific file
from pathlib import Path
config = AppConfig.load(Path("/etc/gmail-assistant/config.json"))

# Allow repo credentials
config = AppConfig.load(allow_repo_credentials=True)
```

### Accessing Configuration Values

```python
config = AppConfig.load()

# Access fields
print(config.credentials_path)      # Path("/home/user/.gmail-assistant/credentials.json")
print(config.max_emails)            # 1000
print(config.rate_limit_per_second) # 10.0
print(config.log_level)             # "INFO"

# Note: AppConfig is immutable
# config.max_emails = 2000  # ❌ TypeError: frozen dataclass
```

### Default Configuration Directory

```python
from gmail_assistant.core.config import AppConfig

config_dir = AppConfig.default_dir()
print(config_dir)  # Path("/home/user/.gmail-assistant")

# Create if needed
config_dir.mkdir(parents=True, exist_ok=True)
```

---

## Constants

### Application Metadata

**Module**: `gmail_assistant.core.constants`

```python
APP_NAME: str = "gmail-assistant"
APP_VERSION: str = "2.0.0"
```

### OAuth Scopes

**Read-Only Scope**:
```python
GMAIL_READONLY_SCOPE: str = "https://www.googleapis.com/auth/gmail.readonly"
SCOPES_READONLY: List[str] = [GMAIL_READONLY_SCOPE]
```

**Modify Scope**:
```python
GMAIL_MODIFY_SCOPE: str = "https://www.googleapis.com/auth/gmail.modify"
SCOPES_MODIFY: List[str] = [GMAIL_MODIFY_SCOPE]
SCOPES_FULL: List[str] = ['https://www.googleapis.com/auth/gmail.modify']
```

**Default**:
```python
DEFAULT_SCOPES: List[str] = SCOPES_READONLY
```

### Rate Limiting

```python
DEFAULT_RATE_LIMIT: float = 10.0  # requests per second
CONSERVATIVE_REQUESTS_PER_SECOND: float = 8.0
MAX_RATE_LIMIT: float = 100.0
BATCH_SIZE: int = 100
MAX_EMAILS_LIMIT: int = 100000
DEFAULT_MAX_EMAILS: int = 1000
```

### Output Formats

```python
SUPPORTED_OUTPUT_FORMATS: List[str] = ['eml', 'markdown', 'both']
DEFAULT_OUTPUT_FORMAT: str = 'both'

SUPPORTED_ORGANIZATION_TYPES: List[str] = ['date', 'sender', 'none']
DEFAULT_ORGANIZATION: str = 'date'
```

### Keyring Configuration

```python
KEYRING_SERVICE: str = "gmail_assistant"
KEYRING_USERNAME: str = "oauth_credentials"
```

### Logging

```python
DEFAULT_LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL: str = 'INFO'
```

---

## Best Practices

### Configuration Management

```python
# Good: Handle configuration errors
try:
    config = AppConfig.load()
except ConfigError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(5)

# Good: Use config values consistently
fetcher = GmailFetcher(str(config.credentials_path))
for message_id in fetcher.search_messages("is:unread", config.max_emails):
    # Process message
    pass

# Bad: Hardcoding paths
fetcher = GmailFetcher("./credentials.json")  # ❌ Fragile
```

### Error Handling

```python
from gmail_assistant.core.exceptions import (
    AuthError,
    NetworkError,
    ConfigError,
)

# Good: Specific exception handling
try:
    config = AppConfig.load()
    fetcher = GmailFetcher(str(config.credentials_path))
    fetcher.authenticate()
except ConfigError as e:
    handle_config_error(e)
except AuthError as e:
    handle_auth_error(e)
except NetworkError as e:
    handle_network_error(e)

# Bad: Catching generic Exception
try:
    config = AppConfig.load()
except Exception:  # ❌ Too broad
    pass
```

### Type Hints

```python
# Good: Use protocols for type hints
from gmail_assistant.core.protocols import EmailFetcherProtocol

def backup_inbox(fetcher: EmailFetcherProtocol) -> int:
    """Accept any object implementing EmailFetcherProtocol."""
    result = fetcher.download_emails(
        query="is:unread",
        max_emails=1000,
        format_type="eml"
    )
    return result.emails_fetched

# Bad: Hardcoding concrete types
def backup_inbox(fetcher: GmailFetcher) -> int:  # ❌ Less flexible
    pass
```

---

## See Also

- [CLI Reference](0109-1500_CLI_REFERENCE.md) - Command-line usage
- [Configuration Reference](0109-1600_CONFIGURATION_REFERENCE.md) - Configuration file schema
- [Constants Reference](0109-1800_CONSTANTS_REFERENCE.md) - All built-in constants

