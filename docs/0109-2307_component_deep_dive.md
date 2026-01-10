# Gmail Assistant - Component Deep Dive

**Version**: 2.0.0
**Document Date**: 2026-01-09
**Companion Document**: `0109-2307_architecture_overview.md`

---

## Table of Contents

1. [Core Module Components](#1-core-module-components)
2. [Authentication Subsystem](#2-authentication-subsystem)
3. [Fetch Subsystem](#3-fetch-subsystem)
4. [Processing Subsystem](#4-processing-subsystem)
5. [Parser Components](#5-parser-components)
6. [Utility Components](#6-utility-components)
7. [CLI Components](#7-cli-components)
8. [Data Models](#8-data-models)

---

## 1. Core Module Components

### 1.1 Configuration System (`core/config.py`)

**Class**: `AppConfig`

**Purpose**: Immutable configuration loader with secure defaults and strict validation.

**Attributes**:
```python
@dataclass(frozen=True, slots=True)
class AppConfig:
    credentials_path: Path      # OAuth credentials file location
    token_path: Path           # OAuth token storage location
    output_dir: Path           # Email backup directory
    max_emails: int = 1000     # Maximum emails per operation
    rate_limit_per_second: float = 10.0  # API rate limit
    log_level: str = "INFO"    # Logging verbosity
```

**Key Methods**:

`AppConfig.load(cli_config: Path | None, *, allow_repo_credentials: bool = False) -> AppConfig`
- Loads configuration following priority order
- Validates paths and creates directories
- Performs security checks for repo-relative credentials
- Returns immutable configuration object

`AppConfig.default_dir() -> Path`
- Returns default configuration directory: `~/.gmail-assistant/`

**Configuration Resolution Priority**:
1. CLI argument: `--config /path/to/config.json`
2. Environment variable: `$GMAIL_ASSISTANT_CONFIG`
3. Project config: `./gmail-assistant.json`
4. User config: `~/.gmail-assistant/config.json`
5. Built-in defaults

**Validation Logic**:
```python
def __post_init__(self) -> None:
    # Validates max_emails: 1-50000
    # Validates rate_limit_per_second: 0.1-100
    # Validates log_level in {DEBUG, INFO, WARNING, ERROR, CRITICAL}
    # Raises ConfigError if validation fails
```

**Security Features**:
- Detects git repository context
- Warns if credentials inside repository
- Requires explicit `--allow-repo-credentials` flag to override
- Prevents accidental credential commits

**Usage Example**:
```python
from gmail_assistant.core.config import AppConfig

# Load with defaults
config = AppConfig.load()

# Load with custom config file
config = AppConfig.load(Path("/custom/config.json"))

# Allow repo-relative credentials (development only)
config = AppConfig.load(allow_repo_credentials=True)
```

---

### 1.2 Exception Hierarchy (`core/exceptions.py`)

**Purpose**: Single source of truth for all domain exceptions with exit code mapping.

**Exception Classes**:

```python
class GmailAssistantError(Exception):
    """Base exception - exit code 1"""
    pass

class ConfigError(GmailAssistantError):
    """Configuration errors - exit code 5"""
    # Invalid config files, missing required keys, type errors
    pass

class AuthError(GmailAssistantError):
    """Authentication/authorization errors - exit code 3"""
    # OAuth failures, invalid credentials, expired tokens
    pass

class NetworkError(GmailAssistantError):
    """Network connectivity errors - exit code 4"""
    # Connection timeouts, DNS failures, proxy errors
    pass

class APIError(GmailAssistantError):
    """Gmail API errors - exit code 1"""
    # API rate limits, quota exceeded, invalid requests
    pass
```

**Design Rationale**:
- Centralized exception definitions prevent duplicate definitions
- Clear inheritance hierarchy for exception handling
- Explicit exit code mapping for CLI error reporting
- Imported by all modules from single authoritative source

**Usage**:
```python
from gmail_assistant.core.exceptions import ConfigError

def load_config(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
```

---

### 1.3 Protocol Definitions (`core/protocols.py`)

**Purpose**: Define structural interfaces for all major components using `typing.Protocol`.

**Key Protocols**:

#### GmailClientProtocol
```python
@runtime_checkable
class GmailClientProtocol(Protocol):
    def authenticate(self) -> bool: ...
    def get_service(self) -> Any: ...
    @property
    def is_authenticated(self) -> bool: ...
    def get_user_info(self) -> Optional[Dict[str, Any]]: ...
```

**Purpose**: Interface for Gmail API client operations.

**Implementations**: `ReadOnlyGmailAuth`, `GmailModifyAuth`, `FullGmailAuth`

#### EmailFetcherProtocol
```python
@runtime_checkable
class EmailFetcherProtocol(Protocol):
    def search_messages(self, query: str, max_results: int = 100) -> List[str]: ...
    def get_message(self, message_id: str, format: str = "full") -> Optional[Dict]: ...
    def download_emails(self, query: str, ...) -> FetchResult: ...
    def get_profile(self) -> Optional[Dict[str, Any]]: ...
```

**Purpose**: Interface for email fetching operations.

**Implementations**: `GmailFetcher`, `AsyncGmailFetcher`, `StreamingGmailFetcher`

#### EmailParserProtocol
```python
@runtime_checkable
class EmailParserProtocol(Protocol):
    def parse_eml(self, file_path: Union[str, Path]) -> Dict[str, Any]: ...
    def parse_html(self, html_content: str, sender: str = "") -> ParseResult: ...
    def extract_headers(self, headers: List[Dict[str, str]]) -> Dict[str, str]: ...
```

**Purpose**: Interface for email parsing operations.

**Implementations**: `EmailContentParser`, `AdvancedEmailParser`

#### Data Transfer Objects (DTOs)
```python
@dataclass
class EmailMetadata:
    id: str
    thread_id: str
    subject: str
    sender: str
    recipients: List[str]
    date: str
    labels: List[str]
    snippet: str = ""
    size_estimate: int = 0

@dataclass
class FetchResult:
    success: bool
    emails_fetched: int
    emails_failed: int
    output_directory: str
    error_message: Optional[str] = None

@dataclass
class ParseResult:
    success: bool
    markdown: str
    strategy: str
    quality: float
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
```

**Design Benefits**:
- Duck typing with type safety
- Easier testing with mock objects
- Clear API contracts
- No inheritance required
- Runtime type checking with `@runtime_checkable`

---

### 1.4 Data Schemas (`core/schemas.py`)

**Purpose**: Canonical Pydantic models for email data with validation.

**Primary Model**: `Email`

```python
class Email(BaseModel):
    # Identity
    gmail_id: str = Field(..., description="Unique Gmail message ID")
    thread_id: str = Field(..., description="Gmail thread ID")

    # Core metadata
    subject: str = Field(default="", description="Email subject line")
    sender: str = Field(..., description="Sender email address")
    recipients: List[EmailParticipant] = Field(default_factory=list)
    date: datetime = Field(..., description="Email received timestamp")

    # Content
    body_plain: Optional[str] = Field(default=None)
    body_html: Optional[str] = Field(default=None)

    # Gmail-specific
    labels: List[str] = Field(default_factory=list)
    snippet: str = Field(default="", description="Email preview snippet")
    history_id: int = Field(default=0)
    size_estimate: int = Field(default=0)

    # Status flags
    is_unread: bool = Field(default=True)
    is_starred: bool = Field(default=False)
    has_attachments: bool = Field(default=False)
```

**Key Methods**:

`Email.from_gmail_message(message: Dict[str, Any]) -> Email`
- Creates Email from Gmail API response
- Parses headers and extracts metadata
- Handles multiple recipient types (To, CC, BCC)
- Validates and normalizes data

`Email.parse_date(v)` (field validator)
- Handles multiple date formats from Gmail
- Supports RFC 2822, ISO 8601, custom formats
- Removes timezone names in parentheses
- Returns normalized datetime object

**Properties**:

`sender_domain: str`
- Extracts domain from sender email address
- Returns empty string if no @ symbol

`year_month: str`
- Returns YYYY-MM format for partitioning
- Uses email date field

**Supporting Models**:

```python
class EmailParticipant(BaseModel):
    address: str
    type: ParticipantType  # FROM, TO, CC, BCC
    display_name: Optional[str] = None

    @property
    def domain(self) -> str:
        return self.address.split("@")[1] if "@" in self.address else ""
```

**Backward Compatibility**:
- `EmailMetadataCompat`: Legacy EmailMetadata replacement
- `EmailDataCompat`: Legacy EmailData replacement
- `to_email_metadata()`, `to_email_data()`: Conversion methods (deprecated)
- Factory function: `create_email_from_dict()` for flexible parsing

---

### 1.5 Dependency Injection Container (`core/container.py`)

**Class**: `ServiceContainer`

**Purpose**: Lightweight dependency injection with singleton/transient/scoped lifetimes.

**Core Methods**:

```python
def register(self, service_type: Type[T], instance: T,
             lifetime: str = ServiceLifetime.SINGLETON) -> 'ServiceContainer':
    """Register a service instance."""

def register_factory(self, service_type: Type[T], factory: Callable[[], T],
                    lifetime: str = ServiceLifetime.SINGLETON) -> 'ServiceContainer':
    """Register a factory function for lazy instantiation."""

def register_type(self, service_type: Type[T], implementation_type: Type[T],
                 lifetime: str = ServiceLifetime.TRANSIENT) -> 'ServiceContainer':
    """Register a type for auto-instantiation."""

def resolve(self, service_type: Type[T]) -> T:
    """Resolve a service by type."""

def create_scope(self) -> 'ServiceContainer':
    """Create a new scoped container inheriting from parent."""
```

**Service Lifetimes**:

`ServiceLifetime.SINGLETON`
- One instance per container
- Instance created on first resolve
- Subsequent resolves return same instance
- Used for: Cache managers, rate limiters, error handlers

`ServiceLifetime.TRANSIENT`
- New instance on each resolve
- No caching
- Used for: Validators, builders, formatters

`ServiceLifetime.SCOPED`
- One instance per scope
- New instance when scope created
- Used for: Database connections, request-scoped services

**Factory Functions**:

`create_default_container() -> ServiceContainer`
- Core utilities only
- Registers: CacheManager, GmailRateLimiter, InputValidator, ErrorHandler

`create_readonly_container(credentials_file: str) -> ServiceContainer`
- Read-only Gmail operations
- Includes: All default services + ReadOnlyGmailAuth + GmailFetcher

`create_modify_container(credentials_file: str) -> ServiceContainer`
- Modify/delete operations
- Includes: All default services + GmailModifyAuth

`create_full_container(credentials_file: str) -> ServiceContainer`
- All Gmail capabilities
- Includes: All default services + FullGmailAuth + GmailFetcher + EmailContentParser

**Thread Safety**:
- Uses `threading.RLock()` for concurrent access
- Safe for multi-threaded service resolution

**Circular Dependency Detection**:
```python
def resolve(self, service_type: Type[T]) -> T:
    if service_type in self._resolving:
        raise CircularDependencyError(f"Circular dependency detected for {service_type}")
    # ... resolution logic
```

**Usage Example**:
```python
from gmail_assistant.core.container import create_readonly_container

container = create_readonly_container("credentials.json")
fetcher = container.resolve(GmailFetcher)
cache = container.resolve(CacheManager)
```

---

### 1.6 Constants (`core/constants.py`)

**Purpose**: Centralized constant definitions with environment variable override support.

**Categories**:

**Application Metadata**:
```python
APP_NAME: str = "gmail-assistant"
APP_VERSION: str = "2.0.0"
```

**OAuth Scopes**:
```python
GMAIL_READONLY_SCOPE: str = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_MODIFY_SCOPE: str = "https://www.googleapis.com/auth/gmail.modify"

SCOPES_READONLY: List[str] = [GMAIL_READONLY_SCOPE]
SCOPES_MODIFY: List[str] = [GMAIL_MODIFY_SCOPE]
SCOPES_FULL: List[str] = [GMAIL_MODIFY_SCOPE]  # Includes compose
DEFAULT_SCOPES: List[str] = SCOPES_READONLY
```

**Default Paths** (with environment overrides):
```python
# L-1 Security Fix: Environment variable override support
def _get_env_path(env_var: str, default: Path) -> Path:
    env_value = os.environ.get(env_var)
    if env_value:
        return Path(env_value)
    return default

CONFIG_DIR: Path = _get_env_path('GMAIL_ASSISTANT_CONFIG_DIR', PROJECT_ROOT / 'config')
DATA_DIR: Path = _get_env_path('GMAIL_ASSISTANT_DATA_DIR', PROJECT_ROOT / 'data')
BACKUP_DIR: Path = _get_env_path('GMAIL_ASSISTANT_BACKUP_DIR', PROJECT_ROOT / 'backups')
CREDENTIALS_DIR: Path = _get_env_path('GMAIL_ASSISTANT_CREDENTIALS_DIR', CONFIG_DIR / 'security')
CACHE_DIR: Path = _get_env_path('GMAIL_ASSISTANT_CACHE_DIR', Path.home() / '.gmail_assistant_cache')
```

**API Rate Limits**:
```python
DEFAULT_RATE_LIMIT: float = 10.0  # requests per second
CONSERVATIVE_REQUESTS_PER_SECOND: float = 8.0
MAX_RATE_LIMIT: float = 100.0
BATCH_SIZE: int = 100
MAX_EMAILS_LIMIT: int = 100000
MAX_EMAILS_DEFAULT: int = 1000
```

**Keyring Configuration**:
```python
KEYRING_SERVICE: str = "gmail_assistant"
KEYRING_USERNAME: str = "oauth_credentials"
```

**Output Formats**:
```python
SUPPORTED_OUTPUT_FORMATS: List[str] = ['eml', 'markdown', 'both']
DEFAULT_OUTPUT_FORMAT: str = 'both'

SUPPORTED_ORGANIZATION_TYPES: List[str] = ['date', 'sender', 'none']
DEFAULT_ORGANIZATION: str = 'date'
```

---

## 2. Authentication Subsystem

### 2.1 Base Authentication (`core/auth/base.py`)

**Abstract Class**: `AuthenticationBase`

**Purpose**: Template method pattern for authentication workflow with security features.

**Constructor**:
```python
def __init__(self, credentials_file: str = 'credentials.json',
             required_scopes: Optional[List[str]] = None):
    self.credentials_file = credentials_file
    self.required_scopes = required_scopes or SCOPES_READONLY
    self.credential_manager = SecureCredentialManager(credentials_file)
    self.error_handler = ErrorHandler()
    self._authenticated = False
    self._service = None
    self._user_info = None
```

**Key Methods**:

`authenticate() -> bool`
- **Rate Limiting** (L-2 Security Fix):
  - Checks authentication rate limiter before attempt
  - Blocks if >5 failures in 15 minutes
  - Records all attempts (success/failure)

- **Authentication Flow**:
  1. Check if already authenticated
  2. Call `credential_manager.authenticate()`
  3. Build Gmail API service
  4. Fetch user profile information
  5. Record success/failure for rate limiting

- **Error Handling**:
  - Catches all exceptions
  - Uses ErrorHandler for consistent error processing
  - Returns False on failure, never raises

`reset_authentication() -> bool`
- Clears current authentication state
- Calls `credential_manager.reset_credentials()`
- Forces re-authentication on next call

`validate_scopes() -> bool`
- Tests scope access by fetching user profile
- Returns True if scopes are valid
- Used for troubleshooting permission issues

`get_authentication_status() -> Dict[str, Any]`
- Returns detailed status information:
  ```python
  {
      'authenticated': bool,
      'credentials_file': str,
      'required_scopes': List[str],
      'user_email': Optional[str],
      'messages_total': Optional[int],
      'service_available': bool
  }
  ```

**Concrete Implementations**:

```python
class ReadOnlyGmailAuth(AuthenticationBase):
    """Read-only access - fetching and reading only"""
    def get_required_scopes(self) -> List[str]:
        return ['https://www.googleapis.com/auth/gmail.readonly']

class GmailModifyAuth(AuthenticationBase):
    """Modify access - reading, labeling, deleting"""
    def get_required_scopes(self) -> List[str]:
        return ['https://www.googleapis.com/auth/gmail.modify']

class FullGmailAuth(AuthenticationBase):
    """Full access - all operations including compose"""
    def get_required_scopes(self) -> List[str]:
        return [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.compose'
        ]
```

**Factory Pattern**:

```python
class AuthenticationFactory:
    @staticmethod
    def create_auth(auth_type: str, credentials_file: str) -> AuthenticationBase:
        auth_classes = {
            'readonly': ReadOnlyGmailAuth,
            'modify': GmailModifyAuth,
            'full': FullGmailAuth
        }
        if auth_type not in auth_classes:
            raise ValueError(f"Invalid auth type: {auth_type}")
        return auth_classes[auth_type](credentials_file)
```

---

### 2.2 Credential Manager (`core/auth/credential_manager.py`)

**Class**: `SecureCredentialManager`

**Purpose**: Secure credential storage using system keyring instead of filesystem.

**Security Improvements** (L-1 Fix):
- Stores OAuth tokens in system keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- Never stores tokens in plaintext files
- Automatic migration from legacy `token.json` to keyring
- Secure token refresh mechanism

**Key Methods**:

`authenticate() -> bool`
- Checks keyring for existing token
- Validates token expiry
- Refreshes token if expired
- Initiates OAuth flow if no token
- Stores new tokens in keyring

`get_service() -> Any`
- Returns authenticated Gmail API service
- Builds service using `googleapiclient.discovery.build()`

`get_user_info() -> Optional[Dict[str, Any]]`
- Fetches Gmail profile information
- Returns email, messagesTotal, threadsTotal

`reset_credentials() -> bool`
- Removes tokens from keyring
- Forces re-authentication

**OAuth Flow Implementation**:
```python
def _initiate_oauth_flow(self) -> Optional[Credentials]:
    flow = InstalledAppFlow.from_client_secrets_file(
        self.credentials_file,
        scopes=self.scopes
    )
    # Launches local server on port 8080
    # Opens browser for user consent
    # Receives authorization code
    # Exchanges for access/refresh tokens
    creds = flow.run_local_server(port=8080)
    self._store_credentials_in_keyring(creds)
    return creds
```

---

### 2.3 Authentication Rate Limiter (`core/auth/rate_limiter.py`)

**Purpose**: Prevent brute force attacks on authentication (L-2 Security Fix).

**Configuration**:
```python
MAX_ATTEMPTS: int = 5           # Maximum failed attempts
LOCKOUT_DURATION: int = 900     # 15 minutes in seconds
RESET_WINDOW: int = 900         # Time window for attempt counting
```

**Key Methods**:

`check_rate_limit(identifier: str) -> bool`
- Returns True if authentication allowed
- Returns False if locked out

`record_attempt(identifier: str, success: bool) -> None`
- Records authentication attempt
- Increments failure counter if unsuccessful
- Resets counter on success
- Triggers lockout after MAX_ATTEMPTS

`get_remaining_attempts(identifier: str) -> int`
- Returns number of attempts before lockout
- Returns 0 if already locked out

`get_lockout_remaining(identifier: str) -> int`
- Returns seconds remaining in lockout
- Returns 0 if not locked out

**Implementation Details**:
- Uses in-memory storage (resets on application restart)
- Identifier typically: credentials file path
- Thread-safe with locking

---

## 3. Fetch Subsystem

### 3.1 Gmail Fetcher (`core/fetch/gmail_assistant.py`)

**Class**: `GmailFetcher`

**Purpose**: Main email fetching implementation with multiple output formats.

**Constructor**:
```python
def __init__(self, credentials_file: str = 'credentials.json'):
    self.auth = ReadOnlyGmailAuth(credentials_file)
    self.memory_tracker = MemoryTracker()
    self.streaming_processor = StreamingEmailProcessor()
    self.progressive_loader = ProgressiveLoader()
    self.html_converter = html2text.HTML2Text()
    self.logger = logging.getLogger(__name__)
```

**Key Methods**:

`authenticate() -> bool`
- Delegates to `self.auth.authenticate()`
- Returns True on success

`get_profile() -> Dict[str, Any]`
- Fetches Gmail profile information
- Returns email address, total messages, total threads

`search_messages(query: str = '', max_results: int = 100) -> List[str]`
- Searches Gmail using query syntax
- Handles pagination automatically
- Returns list of message IDs
- **API Call**: `users().messages().list()`

`get_message_details(message_id: str) -> Optional[Dict]`
- **M-3 Security Fix**: Validates API response structure
- Fetches full message details
- Returns message data or None on error
- **API Call**: `users().messages().get(userId='me', id=message_id, format='full')`

`_validate_api_response(response: Optional[Dict], required_fields: List[str], context: str) -> Dict`
- **Purpose**: Prevent null pointer exceptions from malformed API responses
- Validates response is not None
- Validates response is dictionary
- Checks for required fields: `['id', 'threadId', 'payload']`
- Raises ValueError with context on validation failure

`decode_base64(data: str) -> str`
- Handles URL-safe base64 decoding
- Adds missing padding automatically
- Handles encoding errors gracefully

`extract_headers(headers: List[Dict]) -> Dict[str, str]`
- Converts Gmail header list to dictionary
- Lowercases header names for consistency

`get_message_body(payload: Dict) -> Tuple[str, str]`
- Extracts plain text and HTML bodies
- Recursively processes multipart messages
- Returns (plain_text, html_body) tuple

**HTML Converter Configuration**:
```python
self.html_converter.ignore_links = False
self.html_converter.ignore_images = False
self.html_converter.ignore_tables = False
self.html_converter.body_width = 80
self.html_converter.unicode_snob = True
```

---

### 3.2 Gmail API Client (`core/fetch/gmail_api_client.py`)

**Class**: `GmailAPIClient`

**Purpose**: Direct Gmail API wrapper with batch operations and deletion support.

**Key Features**:
- Live Gmail API integration
- Batch email fetching
- Trash vs. permanent deletion
- Dry-run mode for safety
- Comprehensive error handling

**Key Methods** (inferred from architecture):

`fetch_emails(query: str, max_emails: int) -> List[Dict]`
- Fetches emails matching query
- Returns list of email data dictionaries

`batch_fetch(message_ids: List[str]) -> List[Dict]`
- Fetches multiple emails in single API call
- More efficient than individual fetches

`trash_emails(message_ids: List[str]) -> int`
- Moves emails to trash (recoverable)
- Returns count of trashed emails

`delete_emails(message_ids: List[str]) -> int`
- Permanently deletes emails (not recoverable)
- Returns count of deleted emails

---

### 3.3 Streaming Fetcher (`core/fetch/streaming.py`)

**Class**: `StreamingGmailFetcher`

**Purpose**: Memory-efficient email fetching for large operations.

**Key Features**:
- Generator-based message streaming
- Configurable batch sizes
- Memory optimization
- Progressive loading

**Key Methods** (inferred from protocols):

`stream_messages(query: str, batch_size: int = 100) -> Iterator[Dict[str, Any]]`
- Yields messages one at a time
- Fetches in batches to reduce API calls
- Memory-efficient for large result sets

`stream_message_ids(query: str, batch_size: int = 500) -> Iterator[str]`
- Yields message IDs only
- Useful for counting or filtering before full fetch

---

### 3.4 Async Fetcher (`core/fetch/async_fetcher.py`)

**Class**: `AsyncGmailFetcher`

**Purpose**: Asynchronous email fetching for concurrent operations.

**Dependencies** (from pyproject.toml):
- `aiohttp>=3.9.5`: Async HTTP client
- `asyncio-throttle>=1.0.2`: Rate limiting for async operations
- `psutil>=5.9.8`: System resource monitoring

**Key Features**:
- Concurrent email fetching
- Async/await pattern
- Resource-aware throttling
- Progress tracking

---

### 3.5 Incremental Fetcher (`core/fetch/incremental.py`)

**Class**: `IncrementalFetcher`

**Purpose**: Incremental synchronization using Gmail history API.

**Key Features**:
- Uses Gmail `historyId` for delta sync
- Only fetches new/modified emails
- Efficient for ongoing backups
- Checkpoint-based resume

**Key Concepts**:

`historyId`
- Monotonically increasing identifier
- Changes when mailbox changes
- Used to fetch only deltas since last sync

**Key Methods** (inferred):

`sync_since_history_id(history_id: int) -> List[Dict]`
- Fetches changes since specified history ID
- Returns list of modified emails

`get_current_history_id() -> int`
- Gets current mailbox history ID
- Used as checkpoint for next sync

---

### 3.6 Checkpoint System (`core/fetch/checkpoint.py`)

**Purpose**: Progress tracking and resume capability for long-running operations.

**Key Features**:
- Saves progress periodically
- Enables resume after interruption
- Tracks failed operations
- Atomic checkpoint writes

**Checkpoint Data Structure** (inferred):
```python
{
    "last_message_id": str,
    "processed_count": int,
    "failed_count": int,
    "history_id": Optional[int],
    "timestamp": str
}
```

---

### 3.7 Dead Letter Queue (`core/fetch/dead_letter_queue.py`)

**Purpose**: Handles failed operations for later retry or manual review.

**Key Features**:
- Stores failed email operations
- Includes error context
- Enables bulk retry
- Prevents data loss on transient errors

**Queue Entry** (inferred):
```python
{
    "message_id": str,
    "operation": str,  # "fetch", "parse", "save"
    "error_message": str,
    "error_category": ErrorCategory,
    "timestamp": datetime,
    "retry_count": int,
    "metadata": Dict[str, Any]
}
```

---

## 4. Processing Subsystem

### 4.1 Email Classifier (`core/processing/classifier.py`)

**Class**: `EmailClassifier`

**Purpose**: Categorize emails based on content, sender, and metadata.

**Classification Categories** (inferred):
- Newsletter
- Marketing
- Notification
- Personal
- Automated/System
- Social Media
- Transactional

**Key Methods** (inferred):

`classify(email: Email) -> str`
- Returns classification category
- Uses multiple signals: sender domain, subject patterns, content structure

`batch_classify(emails: List[Email]) -> Dict[str, List[Email]]`
- Classifies multiple emails
- Returns dictionary mapping categories to email lists

---

### 4.2 Email Data Extractor (`core/processing/extractor.py`)

**Class**: `EmailDataExtractor`

**Purpose**: Extract structured data from email content.

**Extraction Capabilities** (inferred):
- Email addresses
- Phone numbers
- Dates and times
- URLs and links
- Tracking IDs
- Order numbers
- Prices and currencies

**Key Methods** (inferred):

`extract_all(email: Email) -> Dict[str, List[Any]]`
- Extracts all data types
- Returns dictionary of extracted data

`extract_links(content: str) -> List[str]`
- Extracts all URLs from content
- Removes tracking parameters

---

### 4.3 Email Plaintext Processor (`core/processing/plaintext.py`)

**Class**: `EmailPlaintextProcessor`

**Purpose**: Convert HTML emails to clean plain text.

**Key Features**:
- HTML tag removal
- Entity decoding
- Whitespace normalization
- Link preservation

**Key Methods** (inferred):

`to_plaintext(html_content: str) -> str`
- Converts HTML to clean plain text
- Preserves readability

---

### 4.4 Email Database Importer (`core/processing/database.py`)

**Class**: `EmailDatabaseImporter`

**Purpose**: Import emails into SQLite database for analysis.

**Database Schema** (inferred):
```sql
CREATE TABLE emails (
    gmail_id TEXT PRIMARY KEY,
    thread_id TEXT,
    subject TEXT,
    sender TEXT,
    date DATETIME,
    labels TEXT,  -- JSON array
    snippet TEXT,
    body_plain TEXT,
    body_html TEXT,
    is_unread BOOLEAN,
    is_starred BOOLEAN,
    has_attachments BOOLEAN
);

CREATE INDEX idx_sender ON emails(sender);
CREATE INDEX idx_date ON emails(date);
CREATE INDEX idx_labels ON emails(labels);
```

**Key Methods** (inferred):

`import_emails(emails: List[Email], db_path: Path) -> int`
- Imports emails into database
- Returns count of imported emails

`batch_import(emails: List[Email], batch_size: int = 1000) -> int`
- Imports in batches for efficiency

---

## 5. Parser Components

### 5.1 Advanced Email Parser (`parsers/advanced_email_parser.py`)

**Class**: `EmailContentParser`

**Purpose**: Multi-strategy HTML to Markdown conversion with quality scoring.

**Parsing Strategies**:

1. **Smart Strategy**
   - Sender-specific rules
   - Newsletter patterns for known domains
   - Custom content selectors
   - Targeted element removal

2. **Readability Strategy** (optional dependency)
   - Uses `readability-lxml` library
   - Extracts main content
   - Removes boilerplate
   - Best for article-style emails

3. **Trafilatura Strategy** (optional dependency)
   - Uses `trafilatura` library
   - Optimized for news/blog content
   - Advanced content extraction

4. **HTML2Text Strategy**
   - Uses `html2text` library
   - Configurable conversion settings
   - Good general-purpose converter

5. **Markdownify Strategy**
   - Uses `markdownify` library
   - Alternative conversion approach
   - Different formatting style

**Configuration Structure**:
```python
{
    "strategies": ["smart", "readability", "trafilatura", "html2text", "markdownify"],
    "newsletter_patterns": {
        "theresanaiforthat.com": {
            "content_selectors": [".email-content", "#main-content"],
            "remove_selectors": [".unsubscribe", ".footer"],
            "title_selector": "h1, .newsletter-title"
        }
    },
    "cleaning_rules": {
        "remove_tags": ["script", "style", "meta", "link"],
        "remove_attributes": ["style", "class", "id", "onclick"],
        "preserve_attributes": ["href", "src", "alt", "title"],
        "max_image_width": 800,
        "convert_tables": True
    },
    "formatting": {
        "max_line_length": 80,
        "preserve_whitespace": False,
        "add_section_breaks": True,
        "clean_links": True,
        "remove_tracking": True
    }
}
```

**Key Methods**:

`__init__(config_file: Optional[str] = None)`
- Loads configuration from file or uses defaults
- Initializes all available parsers
- Sets up validator

`detect_email_type(html_content: str, sender: str = "") -> str`
- Analyzes HTML structure
- Checks sender patterns
- Returns type: newsletter, notification, marketing, simple

`clean_html(html_content: str, sender: str = "") -> str`
- Removes script/style/meta tags
- Strips tracking pixels
- Removes invisible elements
- Normalizes whitespace
- Applies sender-specific rules

`parse(html_content: str, sender: str = "") -> ParseResult`
- Tries strategies in order
- Scores quality of each result
- Returns best result above threshold

`score_quality(markdown: str) -> float`
- Content length check
- Markdown structure presence
- Link density
- Special character ratio
- Returns 0.0-1.0 score

**Quality Scoring Metrics**:
```python
# Too short content
if len(markdown) < 100:
    score -= 0.3

# Too long content
if len(markdown) > 50000:
    score -= 0.2

# Has headings
if re.search(r'^#{1,6}\s+', markdown, re.MULTILINE):
    score += 0.2

# Has lists
if re.search(r'^\s*[-*+]\s+', markdown, re.MULTILINE):
    score += 0.1

# Link density
link_count = len(re.findall(r'\[.*?\]\(.*?\)', markdown))
total_chars = len(markdown)
link_density = link_count / (total_chars / 100)
if link_density > 5:  # Too many links
    score -= 0.2
```

**HTML2Text Configuration**:
```python
self.html2text_parser.ignore_links = False
self.html2text_parser.ignore_images = False
self.html2text_parser.ignore_tables = False
self.html2text_parser.body_width = 80
self.html2text_parser.unicode_snob = True
self.html2text_parser.bypass_tables = False
self.html2text_parser.default_image_alt = "[Image]"
```

**Markdownify Configuration**:
```python
self.markdownify_settings = {
    'heading_style': 'ATX',      # # Heading instead of underline
    'bullets': '-',              # Use - for bullets
    'strong_style': '**',        # **bold**
    'emphasis_style': '*',       # *italic*
    'link_style': 'INLINE',      # [text](url)
    'convert': ['b', 'strong', 'i', 'em', 'a', 'img', 'h1-h6', ...]
}
```

---

### 5.2 EML to Markdown Cleaner (`parsers/gmail_eml_to_markdown_cleaner.py`)

**Purpose**: Convert EML files to clean Markdown with YAML front matter.

**Key Features**:
- Preserves email metadata in front matter
- Handles attachments
- Processes inline images (CID references)
- Configurable cleaning rules
- Batch conversion support

**Output Format**:
```markdown
---
from: sender@example.com
to: recipient@example.com
subject: Email Subject
date: 2025-03-31 12:00:00
message_id: <unique-id@example.com>
---

# Email Subject

Email body content converted to markdown...

## Attachments
- document.pdf (245 KB)
- image.png (128 KB)
```

---

### 5.3 Robust EML Converter (`parsers/robust_eml_converter.py`)

**Purpose**: Fault-tolerant EML file conversion with error recovery.

**Key Features**:
- Multiple encoding detection
- Malformed email recovery
- Character set fallbacks
- Error logging and reporting

---

## 6. Utility Components

### 6.1 Error Handler (`utils/error_handler.py`)

**Class**: `ErrorHandler`

**Purpose**: Centralized error classification, recovery, and reporting.

**Error Classification**:

```python
class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    API_QUOTA = "api_quota"
    RATE_LIMIT = "rate_limit"
    DATA_VALIDATION = "data_validation"
    FILE_SYSTEM = "file_system"
    MEMORY = "memory"
    CONFIGURATION = "configuration"
    PARSING = "parsing"
    UNKNOWN = "unknown"
```

**Data Structures**:

```python
@dataclass
class ErrorContext:
    operation: str
    user_id: Optional[str] = None
    email_id: Optional[str] = None
    file_path: Optional[str] = None
    query: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class StandardError:
    error_id: str                    # ERR_{timestamp}
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    original_exception: Optional[Exception]
    context: Optional[ErrorContext]
    timestamp: datetime
    recoverable: bool
    user_message: str               # User-friendly message
    technical_details: Optional[str]
    suggested_actions: Optional[List[str]]
```

**Key Methods**:

`ErrorClassifier.classify_exception(exception: Exception, context: Optional[ErrorContext]) -> StandardError`
- Classifies exception into StandardError
- Determines severity and recoverability
- Generates user-friendly messages
- Suggests recovery actions

**HTTP Error Classification**:
```python
def _classify_http_error(exception: HttpError, ...) -> StandardError:
    status_code = exception.resp.status
    if status_code == 401:
        category = ErrorCategory.AUTHENTICATION
        severity = ErrorSeverity.HIGH
        user_message = "Authentication failed. Please re-authenticate."
        suggested_actions = ["Run auth command", "Check credentials file"]
    elif status_code == 403:
        category = ErrorCategory.AUTHORIZATION
        severity = ErrorSeverity.HIGH
        user_message = "Access denied. Check OAuth scopes."
    elif status_code == 429:
        category = ErrorCategory.RATE_LIMIT
        severity = ErrorSeverity.MEDIUM
        user_message = "API rate limit exceeded. Wait before retrying."
    # ... more status codes
```

**Memory Error Handling**:
```python
elif isinstance(exception, MemoryError):
    return StandardError(
        category=ErrorCategory.MEMORY,
        severity=ErrorSeverity.CRITICAL,
        recoverable=True,
        user_message="System low on memory. Reduce batch size.",
        suggested_actions=[
            "Reduce emails processed at once",
            "Enable streaming mode",
            "Close other applications",
            "Restart application"
        ]
    )
```

---

### 6.2 Input Validator (`utils/input_validator.py`)

**Class**: `InputValidator`

**Purpose**: Validate all user inputs before processing.

**Validation Methods** (inferred):

`validate_email(email: str) -> str`
- Validates email address format
- Returns normalized email
- Raises ValidationError on invalid format

`validate_gmail_query(query: str) -> str`
- Validates Gmail search query syntax
- Prevents injection attacks
- Returns validated query

`validate_file_path(path: Union[str, Path], must_exist: bool = False) -> Path`
- Validates file path
- Checks existence if required
- Prevents directory traversal
- Returns normalized Path

`validate_batch_size(size: int, max_allowed: int = 1000) -> int`
- Validates batch size range
- Returns validated size
- Raises ValidationError on invalid range

---

### 6.3 Rate Limiter (`utils/rate_limiter.py`)

**Class**: `GmailRateLimiter`

**Purpose**: API rate limiting to prevent quota exhaustion.

**Configuration**:
```python
requests_per_second: float = 10.0
burst_capacity: int = 50  # Allow short bursts
```

**Key Methods**:

`wait_if_needed(quota_cost: int = 1) -> float`
- Blocks until rate limit allows operation
- Returns time waited in seconds

`check_quota() -> Dict[str, Any]`
- Returns current quota status
- Shows requests remaining, time to reset

**Implementation**: Token bucket algorithm with configurable refill rate.

---

### 6.4 Cache Manager (`utils/cache_manager.py`)

**Class**: `CacheManager`

**Purpose**: Caching for API responses and computed results.

**Key Features**:
- In-memory caching with TTL
- Cache eviction policies (LRU, TTL)
- Statistics tracking
- Thread-safe operations

**Key Methods**:

`get(key: str, default: Optional[T] = None) -> Optional[T]`
- Retrieves cached value
- Returns default if not found or expired

`put(key: str, value: T, ttl: Optional[int] = None) -> bool`
- Stores value in cache
- Optional TTL in seconds

`invalidate(key: str) -> bool`
- Removes specific cache entry

`clear() -> None`
- Clears entire cache

---

### 6.5 Memory Manager (`utils/memory_manager.py`)

**Classes**: `MemoryTracker`, `StreamingEmailProcessor`, `ProgressiveLoader`

**Purpose**: Monitor and optimize memory usage during operations.

**MemoryTracker**:
- Monitors current memory usage
- Triggers garbage collection when needed
- Warns on high memory consumption

**StreamingEmailProcessor**:
- Processes emails one at a time
- Minimal memory footprint
- Generator-based processing

**ProgressiveLoader**:
- Loads data in chunks
- Configurable chunk sizes
- Memory-aware loading

---

### 6.6 Circuit Breaker (`utils/circuit_breaker.py`)

**Class**: `CircuitBreaker`

**Purpose**: Prevent cascading failures when downstream services fail.

**States**:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests blocked
- HALF_OPEN: Testing if service recovered

**Configuration**:
```python
failure_threshold: int = 5      # Failures before opening
recovery_timeout: int = 60      # Seconds before testing recovery
success_threshold: int = 2      # Successes to close circuit
```

**State Transitions**:
```
CLOSED -> (failures >= threshold) -> OPEN
OPEN -> (timeout expired) -> HALF_OPEN
HALF_OPEN -> (success >= threshold) -> CLOSED
HALF_OPEN -> (any failure) -> OPEN
```

---

### 6.7 Secure Logger (`utils/secure_logger.py`)

**Purpose**: PII-safe logging with automatic redaction.

**Key Features**:
- Automatic PII detection and redaction
- Email address masking: `user@example.com` -> `u***@example.com`
- Token redaction: Never logs OAuth tokens
- Structured logging with context

---

### 6.8 PII Redactor (`utils/pii_redactor.py`)

**Purpose**: Detect and redact personally identifiable information.

**Detection Patterns**:
- Email addresses
- Phone numbers (US/international)
- Social Security Numbers
- Credit card numbers
- IP addresses
- Custom patterns (configurable)

**Redaction Strategies**:
- Complete removal: `[REDACTED]`
- Partial masking: `user@example.com` -> `u***@e*****.com`
- Hashing: Deterministic hash for debugging

---

### 6.9 Secure File Handler (`utils/secure_file.py`)

**Purpose**: Secure file operations with atomic writes.

**Key Features**:
- Atomic writes (write to temp, then rename)
- Permission validation
- Safe cleanup
- Directory traversal prevention

**Key Methods**:

`atomic_write(path: Path, content: str) -> bool`
- Writes to temporary file
- Validates write success
- Renames to final path (atomic operation)
- Cleans up temp file on error

---

## 7. CLI Components

### 7.1 Main CLI (`cli/main.py`)

**Framework**: Click

**Entry Point**: `gmail-assistant` command (registered in pyproject.toml)

**Global Options**:
```python
@click.group()
@click.version_option(version=__version__)
@click.option("--config", "-c", type=Path, help="Config file path")
@click.option("--allow-repo-credentials", is_flag=True, help="Allow repo credentials")
@click.pass_context
def main(ctx, config, allow_repo_credentials):
    ctx.obj["config_path"] = config
    ctx.obj["allow_repo_credentials"] = allow_repo_credentials
```

**Error Handler Decorator**:
```python
def handle_errors(func):
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
        # ... more exception types
    return wrapper
```

**Commands**:

1. `fetch`: Fetch emails from Gmail
2. `delete`: Delete emails matching query
3. `analyze`: Analyze fetched emails
4. `auth`: Authenticate with Gmail API
5. `config`: Manage configuration

**Current Implementation Status** (v2.0.0):
- CLI framework complete
- Commands defined with full option parsing
- Functional implementation deferred to v2.1.0
- Placeholder messages inform users of deferred implementation

---

### 7.2 Fetch Command (`cli/commands/fetch.py`)

**Status**: Stub implementation (v2.1.0 planned)

**Options**:
```python
@click.option("--query", "-q", default="", help="Gmail search query")
@click.option("--max-emails", "-m", type=int, help="Maximum emails")
@click.option("--output-dir", "-o", type=Path, help="Output directory")
@click.option("--format", type=click.Choice(["json", "mbox", "eml"]), default="json")
```

---

### 7.3 Delete Command (`cli/commands/delete.py`)

**Status**: Stub implementation (v2.1.0 planned)

**Options**:
```python
@click.option("--query", "-q", required=True, help="Gmail search query")
@click.option("--dry-run", is_flag=True, help="Preview without deleting")
@click.option("--confirm", is_flag=True, help="Skip confirmation")
```

---

### 7.4 Analyze Command (`cli/commands/analyze.py`)

**Status**: Stub implementation (v2.1.0 planned)

**Options**:
```python
@click.option("--input-dir", "-i", type=Path, help="Directory with emails")
@click.option("--report", "-r", type=click.Choice(["summary", "detailed", "json"]))
```

---

### 7.5 Auth Command (`cli/commands/auth.py`)

**Status**: Stub implementation (v2.1.0 planned)

**Purpose**: Initiate OAuth authentication flow.

---

### 7.6 Config Command (`cli/commands/config_cmd.py`)

**Status**: Fully implemented

**Options**:
```python
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--validate", is_flag=True, help="Validate configuration")
@click.option("--init", is_flag=True, help="Create default configuration")
```

**Functionality**:
- `--init`: Creates `~/.gmail-assistant/config.json` with defaults
- `--show`: Displays current configuration
- `--validate`: Validates configuration file

---

## 8. Data Models

### 8.1 Email Model

**Location**: `core/schemas.py`

**Full Schema**:
```python
class Email(BaseModel):
    # Identity
    gmail_id: str                   # Unique Gmail message ID
    thread_id: str                  # Gmail thread ID

    # Core metadata
    subject: str = ""               # Email subject
    sender: str                     # Sender email address
    recipients: List[EmailParticipant] = []  # To, CC, BCC
    date: datetime                  # Received timestamp

    # Content
    body_plain: Optional[str] = None
    body_html: Optional[str] = None

    # Gmail-specific
    labels: List[str] = []          # Gmail labels
    snippet: str = ""               # Preview text
    history_id: int = 0             # For incremental sync
    size_estimate: int = 0          # Bytes

    # Status flags
    is_unread: bool = True
    is_starred: bool = False
    has_attachments: bool = False
```

### 8.2 EmailParticipant Model

```python
class EmailParticipant(BaseModel):
    address: str                    # Email address
    type: ParticipantType          # FROM, TO, CC, BCC
    display_name: Optional[str] = None

    @property
    def domain(self) -> str:
        return self.address.split("@")[1] if "@" in self.address else ""
```

### 8.3 FetchResult Model

```python
@dataclass
class FetchResult:
    success: bool
    emails_fetched: int
    emails_failed: int
    output_directory: str
    error_message: Optional[str] = None
```

### 8.4 ParseResult Model

```python
@dataclass
class ParseResult:
    success: bool
    markdown: str                   # Converted content
    strategy: str                   # Strategy used
    quality: float                  # Quality score 0.0-1.0
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
```

---

## Appendix: Cross-Reference Index

### Authentication Components
- `core/auth/base.py`: Authentication base classes and factory
- `core/auth/credential_manager.py`: Keyring-based credential storage
- `core/auth/rate_limiter.py`: Authentication rate limiting

### Fetching Components
- `core/fetch/gmail_assistant.py`: Main fetcher implementation
- `core/fetch/gmail_api_client.py`: Direct API wrapper
- `core/fetch/streaming.py`: Memory-efficient streaming
- `core/fetch/async_fetcher.py`: Async concurrent fetching
- `core/fetch/incremental.py`: Delta synchronization
- `core/fetch/checkpoint.py`: Progress tracking
- `core/fetch/dead_letter_queue.py`: Failed operation handling

### Parsing Components
- `parsers/advanced_email_parser.py`: Multi-strategy HTML parser
- `parsers/gmail_eml_to_markdown_cleaner.py`: EML to Markdown
- `parsers/robust_eml_converter.py`: Fault-tolerant conversion

### Utility Components
- `utils/error_handler.py`: Error classification and recovery
- `utils/input_validator.py`: Input validation
- `utils/rate_limiter.py`: API rate limiting
- `utils/cache_manager.py`: Response caching
- `utils/memory_manager.py`: Memory optimization
- `utils/circuit_breaker.py`: Failure prevention
- `utils/secure_logger.py`: PII-safe logging
- `utils/pii_redactor.py`: PII detection and redaction
- `utils/secure_file.py`: Atomic file operations

### Configuration Components
- `core/config.py`: Configuration loader
- `core/constants.py`: System-wide constants
- `core/container.py`: Dependency injection

### Data Components
- `core/schemas.py`: Pydantic data models
- `core/protocols.py`: Protocol definitions
- `core/exceptions.py`: Exception hierarchy

---

**End of Component Deep Dive**
