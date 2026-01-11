# Gmail Assistant Architecture

**Version**: 2.0.0
**Last Updated**: 2026-01-10
**Python Requirements**: >=3.10

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Directory Structure](#directory-structure)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Module Dependencies](#module-dependencies)
6. [Configuration Management](#configuration-management)
7. [Authentication Flow](#authentication-flow)
8. [Design Patterns](#design-patterns)
9. [Security Architecture](#security-architecture)
10. [Extension Points](#extension-points)
11. [Testing Architecture](#testing-architecture)

---

## System Overview

Gmail Assistant is a Python-based email management suite that provides backup, analysis, and manipulation capabilities for Gmail accounts via the Gmail API. The system employs a modular architecture with clear separation of concerns, protocol-driven interfaces, and comprehensive security controls.

### Core Capabilities

- OAuth 2.0 authenticated Gmail API access with three permission tiers (readonly, modify, full)
- Email fetching with multiple output formats (EML, Markdown, JSON)
- Advanced HTML-to-Markdown parsing with strategy pattern
- AI-powered email classification and newsletter detection
- Dependency injection container for service management
- Comprehensive error handling and recovery mechanisms
- Rate limiting and quota management
- Security features including PII redaction and credential management

### High-Level Architecture Diagram

```
+------------------------------------------------------------------+
|                        CLI Layer (Click)                          |
|   Entry Point: gmail-assistant command                            |
|   Commands: fetch | delete | analyze | auth | config              |
+--------------------------------+---------------------------------+
                                 |
                                 v
+------------------------------------------------------------------+
|                      Core Module Layer                            |
+------------------+------------------+------------------+----------+
|      Auth        |      Fetch       |       AI         | Config   |
|   SubPackage     |   SubPackage     |   SubPackage     | Manager  |
+------------------+------------------+------------------+----------+
|   Processing     |     Output       |    Schemas       | Container|
|   SubPackage     |   SubPackage     |                  |          |
+------------------+------------------+------------------+----------+
                                 |
                                 v
+------------------------------------------------------------------+
|                    Utility & Support Layer                        |
+------------------+------------------+------------------+----------+
| Error Handler    | Rate Limiter     | Cache Manager    | Validator|
| Memory Manager   | Circuit Breaker  | Secure Logger    | PII Red. |
+------------------+------------------+------------------+----------+
                                 |
                                 v
+------------------------------------------------------------------+
|                      External Services                            |
+------------------+------------------+------------------+----------+
| Gmail API        | System Keyring   | File System      | SQLite   |
+------------------+------------------+------------------+----------+
```

---

## Directory Structure

```
gmail_assistant/
|
+-- src/gmail_assistant/              # Main package (src-layout)
|   +-- __init__.py                   # Package entry point, version info
|   +-- __main__.py                   # python -m gmail_assistant support
|   +-- py.typed                      # PEP 561 type marker
|   |
|   +-- cli/                          # Command-line interface
|   |   +-- __init__.py
|   |   +-- main.py                   # Click-based CLI entry point
|   |   +-- commands/                 # Individual command modules
|   |       +-- __init__.py
|   |       +-- fetch.py              # Email fetching command
|   |       +-- delete.py             # Email deletion command
|   |       +-- analyze.py            # Email analysis command
|   |       +-- auth.py               # Authentication command
|   |       +-- config_cmd.py         # Configuration command
|   |
|   +-- core/                         # Core business logic
|   |   +-- __init__.py               # Lazy import handler with public API
|   |   +-- config.py                 # Configuration loader
|   |   +-- config_schemas.py         # Pydantic configuration validation
|   |   +-- constants.py              # System-wide constants
|   |   +-- container.py              # Dependency injection container
|   |   +-- exceptions.py             # Exception hierarchy
|   |   +-- protocols.py              # Protocol definitions (interfaces)
|   |   +-- schemas.py                # Pydantic data models
|   |   |
|   |   +-- auth/                     # Authentication subsystem
|   |   |   +-- __init__.py
|   |   |   +-- base.py               # Base authentication classes
|   |   |   +-- credential_manager.py # Secure credential storage (keyring)
|   |   |   +-- rate_limiter.py       # Auth attempt rate limiting
|   |   |
|   |   +-- fetch/                    # Email fetching subsystem
|   |   |   +-- __init__.py
|   |   |   +-- gmail_assistant.py    # Main GmailFetcher class
|   |   |   +-- gmail_api_client.py   # Gmail API wrapper
|   |   |   +-- async_fetcher.py      # Async email fetching
|   |   |   +-- streaming.py          # Streaming fetcher for large volumes
|   |   |   +-- incremental.py        # Incremental sync support
|   |   |   +-- batch_api.py          # Batch API operations
|   |   |   +-- checkpoint.py         # Progress checkpointing
|   |   |   +-- dead_letter_queue.py  # Failed operation handling
|   |   |   +-- history_sync.py       # Gmail History API sync
|   |   |
|   |   +-- processing/               # Email processing subsystem
|   |   |   +-- __init__.py
|   |   |   +-- classifier.py         # Email classification
|   |   |   +-- extractor.py          # Data extraction
|   |   |   +-- plaintext.py          # Plain text processing
|   |   |   +-- database.py           # SQLite database importer
|   |   |   +-- database_extensions.py # Extended DB operations
|   |   |
|   |   +-- ai/                       # AI-powered processing
|   |   |   +-- __init__.py
|   |   |   +-- newsletter_cleaner.py # AI newsletter detection
|   |   |   +-- analysis_integration.py # Analysis integration
|   |   |
|   |   +-- output/                   # Output format plugins
|   |       +-- __init__.py
|   |       +-- plugin_manager.py     # Output plugin management
|   |
|   +-- parsers/                      # Format conversion
|   |   +-- __init__.py
|   |   +-- advanced_email_parser.py  # Multi-strategy HTML parsing
|   |   +-- gmail_eml_to_markdown_cleaner.py # EML to Markdown
|   |   +-- robust_eml_converter.py   # Robust EML conversion
|   |
|   +-- analysis/                     # Email analysis
|   |   +-- __init__.py               # Canonical exports with deprecation
|   |   +-- daily_email_analyzer.py   # Main analyzer (canonical)
|   |   +-- daily_email_analysis.py   # Legacy (deprecated)
|   |   +-- email_analyzer.py         # Legacy (deprecated)
|   |   +-- email_data_converter.py   # Data format conversion
|   |   +-- setup_email_analysis.py   # Analysis setup utilities
|   |
|   +-- deletion/                     # Email deletion
|   |   +-- __init__.py
|   |   +-- deleter.py                # Email deleter implementation
|   |   +-- setup.py                  # Deletion setup
|   |   +-- ui.py                     # Deletion UI helpers
|   |
|   +-- export/                       # Data export
|   |   +-- __init__.py
|   |   +-- parquet_exporter.py       # Parquet format export
|   |
|   +-- utils/                        # Shared utilities
|       +-- __init__.py
|       +-- cache_manager.py          # Caching utilities
|       +-- circuit_breaker.py        # Circuit breaker pattern
|       +-- config_schema.py          # Schema utilities
|       +-- error_handler.py          # Error handling with recovery
|       +-- input_validator.py        # Input validation
|       +-- manifest.py               # Backup manifest generation
|       +-- memory_manager.py         # Memory tracking
|       +-- metrics.py                # Metrics collection
|       +-- pii_redactor.py           # PII redaction
|       +-- rate_limiter.py           # Rate limiting utilities
|       +-- secure_file.py            # Secure file operations
|       +-- secure_logger.py          # PII-safe logging
|
+-- config/                           # Configuration files
|   +-- gmail_assistant_config.json   # Main configuration
|   +-- config.json                   # AI detection config
|   +-- deletion.json                 # Deletion rules
|   +-- analysis.json                 # Analysis config
|   +-- default.json.template         # Config template
|   +-- schema/                       # JSON schemas
|   +-- security/                     # Credentials directory
|   +-- analysis/                     # Analysis configurations
|
+-- tests/                            # Test suite
|   +-- conftest.py                   # Pytest fixtures
|   +-- unit/                         # Unit tests
|   +-- integration/                  # Integration tests
|   +-- security/                     # Security tests
|   +-- fixtures/                     # Test data
|   +-- analysis/                     # Analysis tests
|
+-- scripts/                          # Automation scripts
|   +-- setup/                        # Setup scripts
|   +-- backup/                       # Backup management
|   +-- migration/                    # Database migrations
|   +-- operations/                   # Operational scripts
|   +-- utilities/                    # Utility scripts
|   +-- validation/                   # Validation scripts
|
+-- examples/                         # Usage examples
|   +-- samples.py                    # Pre-built scenarios
|   +-- example_usage.py              # Demo scripts
|
+-- docs/                             # Documentation
|   +-- adr/                          # Architecture Decision Records
|   +-- reference/                    # Reference documentation
|   +-- testing/                      # Testing documentation
|
+-- pyproject.toml                    # Package configuration
+-- README.md                         # Project readme
+-- ARCHITECTURE.md                   # This file
+-- CHANGELOG.md                      # Version history
+-- SECURITY.md                       # Security policy
+-- BREAKING_CHANGES.md               # Migration guide
```

---

## Component Architecture

### CLI Layer (`cli/`)

The CLI layer provides the user-facing command-line interface built on Click.

```python
# Entry point: gmail-assistant
@click.group()
def main():
    """Gmail Assistant - Backup, analyze, and manage your Gmail."""
    pass

# Subcommands
main.add_command(fetch)    # Email fetching
main.add_command(delete)   # Email deletion
main.add_command(analyze)  # Email analysis
main.add_command(auth)     # Authentication
main.add_command(config)   # Configuration
```

**Exit Codes**:
- `0`: Success
- `1`: General error
- `2`: Usage/argument error (Click default)
- `3`: Authentication error
- `4`: Network error
- `5`: Configuration error

### Core Layer (`core/`)

#### Authentication (`core/auth/`)

Three authentication tiers supporting different permission levels:

| Class | Scope | Use Case |
|-------|-------|----------|
| `ReadOnlyGmailAuth` | `gmail.readonly` | Fetching, reading emails |
| `GmailModifyAuth` | `gmail.modify` | Labeling, deletion |
| `FullGmailAuth` | `gmail.modify` + `gmail.compose` | All operations |

**Authentication Flow**:
```
User Request --> Rate Limiter Check --> Credential Manager
                                              |
                        +---------------------+---------------------+
                        |                     |                     |
                   Keyring Lookup        OAuth Flow           Token Refresh
                        |                     |                     |
                        v                     v                     v
                 Return Cached         Browser Auth          Refresh Token
                  Credentials           + Store                + Store
```

#### Fetch Subsystem (`core/fetch/`)

| Component | Purpose |
|-----------|---------|
| `GmailFetcher` | Main fetcher class with sync operations |
| `AsyncGmailFetcher` | Async fetcher for concurrent operations |
| `StreamingGmailFetcher` | Memory-efficient streaming |
| `IncrementalFetcher` | Delta sync support |
| `GmailBatchClient` | Batch API operations (100 msgs/call) |
| `CheckpointManager` | Resume capability after interruption |
| `DeadLetterQueue` | Failed operation tracking with retry |

**Fetch Data Flow**:
```
Query --> Search API --> Message IDs --> Batch Fetch --> Process --> Save
                              |              |              |
                              v              v              v
                         Checkpoint    Rate Limiter    Output Plugin
```

#### Processing Subsystem (`core/processing/`)

| Component | Purpose |
|-----------|---------|
| `EmailClassifier` | Rule-based email categorization |
| `EmailDataExtractor` | Metadata and content extraction |
| `EmailPlaintextProcessor` | Plain text processing |
| `EmailDatabaseImporter` | SQLite persistence |

#### AI Subsystem (`core/ai/`)

| Component | Purpose |
|-----------|---------|
| `AINewsletterDetector` | Pattern-based newsletter detection |
| `AINewsletterCleaner` | Automated newsletter management |
| `GmailAnalysisIntegration` | Analysis pipeline integration |

### Parser Layer (`parsers/`)

Multi-strategy email parsing with quality scoring:

```
Input (HTML/EML) --> Type Detection --> Strategy Selection --> Parse --> Quality Score
                          |                    |
                          v                    v
                    newsletter?          readability
                    notification?        trafilatura
                    marketing?           html2text
                    simple?              markdownify
```

### Analysis Layer (`analysis/`)

Modular analysis pipeline:

| Component | Purpose |
|-----------|---------|
| `DailyEmailAnalyzer` | Canonical entry point |
| `DataQualityAssessment` | Data validation |
| `HierarchicalClassifier` | Multi-level classification |
| `TemporalAnalyzer` | Time-based patterns |
| `SenderAnalyzer` | Sender pattern analysis |
| `ContentAnalyzer` | Content analysis |
| `InsightsGenerator` | Actionable insights |

### Utility Layer (`utils/`)

Cross-cutting utilities:

| Component | Purpose |
|-----------|---------|
| `CacheManager` | In-memory caching with TTL |
| `CircuitBreaker` | Fault tolerance pattern |
| `ErrorHandler` | Centralized error handling |
| `InputValidator` | Input sanitization |
| `MemoryTracker` | Memory usage monitoring |
| `SecureLogger` | PII-safe logging |
| `PIIRedactor` | PII pattern matching and redaction |
| `GmailRateLimiter` | Token bucket rate limiting |

---

## Data Flow

### Email Fetch Flow

```
1. CLI Command
   gmail-assistant fetch --query "is:unread" --max-emails 100

2. Configuration Loading
   AppConfig.load() --> Resolve credentials path, output dir, rate limits

3. Authentication
   ReadOnlyGmailAuth.authenticate() --> OAuth flow or cached token

4. Search Phase
   GmailFetcher.search_messages(query) --> List[message_id]

5. Fetch Phase (per message)
   GmailFetcher.get_message_details(id) --> Message data

6. Processing Phase
   extract_headers() --> Extract metadata
   get_message_body() --> Extract text/HTML

7. Output Phase
   create_eml_content() --> EML format
   create_markdown_content() --> Markdown format
   atomic_write() --> Save to disk

8. Result
   Return FetchResult(success, count, directory)
```

### Email Deletion Flow

```
1. CLI Command
   gmail-assistant delete --query "from:spam@example.com" --dry-run

2. Authentication (Modify scope)
   GmailModifyAuth.authenticate()

3. Discovery Phase
   get_email_count(query) --> Affected count

4. Confirmation
   User confirmation (unless --confirm flag)

5. Execution Phase
   If dry_run: Report only
   If use_trash: trash_emails()
   If permanent: delete_emails()

6. Result
   Return DeleteResult(deleted, failed, trashed)
```

### Analysis Flow

```
1. Input
   Email data (JSON/DataFrame)

2. Quality Assessment
   DataQualityAssessment.validate()

3. Classification
   HierarchicalClassifier.classify()

4. Analysis Pipeline
   TemporalAnalyzer --> Time patterns
   SenderAnalyzer --> Sender patterns
   ContentAnalyzer --> Content patterns

5. Insight Generation
   InsightsGenerator.generate()

6. Output
   Report (summary, detailed, or JSON)
```

---

## Module Dependencies

### Core Module Dependency Graph

```
                    +----------------+
                    |   cli/main.py  |
                    +-------+--------+
                            |
            +---------------+---------------+
            |               |               |
            v               v               v
    +-------+------+ +------+------+ +------+-------+
    | core/config  | | core/auth   | | core/fetch   |
    +-------+------+ +------+------+ +------+-------+
            |               |               |
            |       +-------+-------+       |
            |       |               |       |
            v       v               v       v
    +-------+-------+-------+ +-----+------+
    | core/exceptions       | | utils/*    |
    +-----------------------+ +------------+
```

### Import Hierarchy

```python
# Level 0: No internal imports
core.exceptions
core.constants

# Level 1: Imports Level 0
core.config              # imports exceptions
core.protocols           # imports typing only

# Level 2: Imports Level 0-1
core.auth.base           # imports exceptions, protocols
core.container           # imports protocols

# Level 3: Imports Level 0-2
core.fetch.gmail_assistant  # imports auth, config, utils
parsers.advanced_email_parser  # imports protocols

# Level 4: CLI layer
cli.main                 # imports all core modules
cli.commands.*           # imports specific core modules
```

### External Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| `click` | CLI framework | Yes |
| `google-api-python-client` | Gmail API | Yes |
| `google-auth` | OAuth authentication | Yes |
| `google-auth-oauthlib` | OAuth flow | Yes |
| `html2text` | HTML to text conversion | Yes |
| `tenacity` | Retry logic | Yes |
| `pandas` | Data analysis | Optional (analysis) |
| `rich` | Terminal UI | Optional (ui) |
| `beautifulsoup4` | HTML parsing | Optional (advanced-parsing) |
| `keyring` | Secure credential storage | Optional (security) |
| `aiohttp` | Async HTTP | Optional (async) |
| `pyarrow` | Parquet export | Optional (analysis) |

---

## Configuration Management

### Configuration Resolution Order

```
Priority (highest to lowest):
1. CLI arguments (--config, --credentials-path, etc.)
2. Environment variable: GMAIL_ASSISTANT_CONFIG
3. Project config: ./gmail-assistant.json (current directory)
4. User config: ~/.gmail-assistant/config.json
5. Built-in defaults
```

### Configuration Schema

```json
{
  "credentials_path": "~/.gmail-assistant/credentials.json",
  "token_path": "~/.gmail-assistant/token.json",
  "output_dir": "~/.gmail-assistant/backups",
  "max_emails": 1000,
  "rate_limit_per_second": 10.0,
  "log_level": "INFO"
}
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `GMAIL_ASSISTANT_CONFIG` | Path to config file |
| `GMAIL_ASSISTANT_CONFIG_DIR` | Config directory override |
| `GMAIL_ASSISTANT_DATA_DIR` | Data directory override |
| `GMAIL_ASSISTANT_BACKUP_DIR` | Backup directory override |
| `GMAIL_ASSISTANT_CREDENTIALS_DIR` | Credentials directory override |
| `GMAIL_ASSISTANT_CACHE_DIR` | Cache directory override |

### AppConfig Class

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

    @classmethod
    def load(cls, cli_config: Path | None = None,
             *, allow_repo_credentials: bool = False) -> "AppConfig":
        """Load configuration with validation and security checks."""
```

---

## Authentication Flow

### OAuth 2.0 Implementation

```
+----------------+     +------------------+     +----------------+
|  Application   |     |  Google OAuth    |     |  Gmail API     |
+-------+--------+     +--------+---------+     +-------+--------+
        |                       |                       |
        |  1. Check keyring     |                       |
        |  for cached token     |                       |
        |                       |                       |
        |  2. If expired/missing|                       |
        +---------------------->|                       |
        |  Request authorization|                       |
        |                       |                       |
        |  3. User grants access|                       |
        |<----------------------+                       |
        |  Return auth code     |                       |
        |                       |                       |
        |  4. Exchange code     |                       |
        +---------------------->|                       |
        |  for tokens           |                       |
        |                       |                       |
        |  5. Store in keyring  |                       |
        |                       |                       |
        |  6. API request       |                       |
        +---------------------------------------------->|
        |  with access token    |                       |
        |                       |                       |
        |  7. Response          |                       |
        |<----------------------------------------------+
```

### Authentication Classes

```python
# Base class with common functionality
class AuthenticationBase(ABC):
    def authenticate(self) -> bool
    def reset_authentication(self) -> bool
    def validate_scopes(self) -> bool
    def get_authentication_status(self) -> Dict[str, Any]

# Specialized implementations
class ReadOnlyGmailAuth(AuthenticationBase):
    # Scope: gmail.readonly

class GmailModifyAuth(AuthenticationBase):
    # Scope: gmail.modify

class FullGmailAuth(AuthenticationBase):
    # Scopes: gmail.readonly, gmail.modify, gmail.compose
```

### Rate Limiting on Auth

```python
# L-2 Security Fix: Auth attempt rate limiting
rate_limiter = get_auth_rate_limiter()
if not rate_limiter.check_rate_limit(credentials_file):
    remaining = rate_limiter.get_lockout_remaining(credentials_file)
    raise AuthError(f"Rate limited. Try again in {remaining}s")
```

---

## Design Patterns

### 1. Protocol-Driven Interfaces

Using `typing.Protocol` for structural subtyping:

```python
@runtime_checkable
class EmailFetcherProtocol(Protocol):
    def search_messages(self, query: str, max_results: int) -> List[str]: ...
    def get_message(self, message_id: str, format: str) -> Optional[Dict]: ...
    def download_emails(self, query: str, ...) -> FetchResult: ...
```

### 2. Dependency Injection Container

```python
container = ServiceContainer()

# Register services
container.register(CacheManager, CacheManager())
container.register_factory(GmailFetcher, lambda: GmailFetcher(creds))

# Resolve services
fetcher = container.resolve(GmailFetcher)
```

**Service Lifetimes**:
- `SINGLETON`: One instance for entire container
- `TRANSIENT`: New instance each time
- `SCOPED`: One instance per scope

### 3. Strategy Pattern (Parsers)

```python
class ParsingStrategy(ABC):
    @abstractmethod
    def parse(self, content: str) -> ParseResult: ...

class ReadabilityStrategy(ParsingStrategy): ...
class TrafilaturaStrategy(ParsingStrategy): ...
class Html2TextStrategy(ParsingStrategy): ...
class MarkdownifyStrategy(ParsingStrategy): ...
```

### 4. Factory Pattern (Authentication)

```python
class AuthenticationFactory:
    @staticmethod
    def create_auth(auth_type: str, credentials_file: str) -> AuthenticationBase:
        auth_classes = {
            'readonly': ReadOnlyGmailAuth,
            'modify': GmailModifyAuth,
            'full': FullGmailAuth
        }
        return auth_classes[auth_type](credentials_file)
```

### 5. Circuit Breaker Pattern

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int, recovery_timeout: float):
        self.state = CircuitState.CLOSED
        self.failure_count = 0

    def call(self, func: Callable) -> Any:
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError("Circuit is open")
        try:
            result = func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

### 6. Repository Pattern (M-9)

```python
@runtime_checkable
class EmailRepositoryProtocol(Protocol):
    def save(self, email: Dict[str, Any]) -> bool: ...
    def get(self, email_id: str) -> Optional[Dict[str, Any]]: ...
    def find(self, query: str, limit: int) -> List[Dict[str, Any]]: ...
    def delete(self, email_id: str) -> bool: ...
    def count(self, query: Optional[str]) -> int: ...
    def exists(self, email_id: str) -> bool: ...
```

### 7. Lazy Import Pattern

```python
# In core/__init__.py
def __getattr__(name):
    """Lazy import handler for backwards compatibility."""
    if name == 'GmailFetcher':
        from .fetch.gmail_assistant import GmailFetcher
        return GmailFetcher
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

---

## Security Architecture

### Credential Protection

```
Security Layers:
1. Default Storage: ~/.gmail-assistant/ (outside any repo)
2. Repo Detection: Blocks credentials inside git repos
3. Explicit Override: --allow-repo-credentials flag required
4. Keyring Storage: OS-level credential protection
```

### PII Redaction

```python
class PIIRedactor:
    """Redacts PII from logs and outputs."""

    PATTERNS = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'ip': r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        # ... more patterns
    }

    def redact(self, text: str) -> str:
        """Replace PII with [REDACTED_TYPE]."""
```

### Secure Logging

```python
class SecureLogger:
    """Logger that automatically redacts PII."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.redactor = PIIRedactor()

    def info(self, msg: str, *args):
        self.logger.info(self.redactor.redact(msg), *args)
```

### Input Validation

```python
class InputValidator:
    """Validates and sanitizes all user inputs."""

    def validate_gmail_query(self, query: str) -> str:
        """Validate Gmail search query syntax."""

    def validate_file_path(self, path: Path, must_exist: bool) -> Path:
        """Validate file path for security issues."""

    def validate_batch_size(self, size: int, max_allowed: int) -> int:
        """Validate batch size within limits."""
```

### API Security

```python
def _validate_api_response(self, response: Optional[Dict],
                          required_fields: List[str],
                          context: str = "") -> Dict:
    """
    Validate API response structure (M-3 security fix).
    Prevents injection attacks via malformed responses.
    """
    if response is None:
        raise ValueError(f"API returned null response {context}")
    if not isinstance(response, dict):
        raise ValueError(f"API returned non-dict: {type(response)}")
    # ... validation continues
```

---

## Extension Points

### 1. Output Format Plugins

Add new output formats by implementing `OutputPluginProtocol`:

```python
# In core/output/plugin_manager.py

@runtime_checkable
class OutputPluginProtocol(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def extension(self) -> str: ...
    def generate(self, email_data: Dict[str, Any]) -> str: ...
    def save(self, content: str, path: Path) -> bool: ...

# Example: JSON output plugin
class JSONOutputPlugin:
    name = "json"
    extension = ".json"

    def generate(self, email_data: Dict[str, Any]) -> str:
        return json.dumps(email_data, indent=2)
```

### 2. Organization Strategies

Add new file organization strategies:

```python
@runtime_checkable
class OrganizationPluginProtocol(Protocol):
    @property
    def name(self) -> str: ...
    def get_path(self, email_data: Dict, base_dir: Path) -> Path: ...

# Example: Organization by label
class LabelOrganization:
    name = "label"

    def get_path(self, email_data: Dict, base_dir: Path) -> Path:
        labels = email_data.get('labels', ['unlabeled'])
        return base_dir / labels[0] / self._make_filename(email_data)
```

### 3. Parsing Strategies

Add new HTML parsing strategies:

```python
# In parsers/advanced_email_parser.py

class NewParsingStrategy(ParsingStrategy):
    name = "new_parser"

    def parse(self, html_content: str, sender: str = "") -> ParseResult:
        # Implementation
        return ParseResult(
            success=True,
            markdown=converted_content,
            strategy=self.name,
            quality=0.85
        )

# Register with parser
parser.register_strategy(NewParsingStrategy())
```

### 4. Custom Validators

Add domain-specific validation:

```python
# In utils/input_validator.py

class CustomValidator(InputValidator):
    def validate_custom_field(self, value: Any) -> Any:
        # Custom validation logic
        return validated_value

# Register with container
container.register_type(ValidatorProtocol, CustomValidator)
```

### 5. Analysis Modules

Add new analysis capabilities:

```python
# In analysis/

class CustomAnalyzer:
    """Custom analysis module."""

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Analysis logic
        return results

# Register with DailyEmailAnalyzer
analyzer.register_analyzer("custom", CustomAnalyzer())
```

### 6. Storage Backends

Implement `EmailRepositoryProtocol` for new storage:

```python
class CloudStorageRepository:
    """Store emails in cloud storage."""

    def save(self, email: Dict[str, Any]) -> bool:
        # Upload to cloud
        pass

    def get(self, email_id: str) -> Optional[Dict[str, Any]]:
        # Download from cloud
        pass

# Register with container
container.register(EmailRepositoryProtocol, CloudStorageRepository())
```

---

## Testing Architecture

### Test Organization

```
tests/
+-- conftest.py          # Shared fixtures
+-- unit/                # Unit tests (no external deps)
|   +-- test_config.py
|   +-- test_validators.py
|   +-- test_utils.py
+-- integration/         # Integration tests (mocked APIs)
|   +-- test_gmail_api.py
|   +-- test_auth_flow.py
+-- security/            # Security-focused tests
|   +-- test_pii_redaction.py
|   +-- test_credential_safety.py
+-- fixtures/            # Test data
    +-- sample_emails/
    +-- config_samples/
```

### Test Markers

```python
# In pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (no external deps)",
    "integration: Integration tests (mocked external services)",
    "api: Tests requiring real Gmail API credentials",
    "slow: Tests taking >5 seconds",
]
```

### Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/ -m unit

# With coverage
pytest tests/ --cov=gmail_assistant --cov-report=html

# Skip slow tests
pytest tests/ -m "not slow"
```

### Test Fixtures

```python
# In conftest.py

@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service."""
    with patch('googleapiclient.discovery.build') as mock:
        yield mock

@pytest.fixture
def sample_email_data():
    """Sample email data for testing."""
    return {
        'id': 'test123',
        'threadId': 'thread123',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'test@example.com'},
                {'name': 'Subject', 'value': 'Test Email'},
            ]
        }
    }

@pytest.fixture
def temp_config_dir(tmp_path):
    """Temporary config directory."""
    config_dir = tmp_path / ".gmail-assistant"
    config_dir.mkdir()
    return config_dir
```

---

## Appendix: Quick Reference

### Import Patterns

```python
# Main package
from gmail_assistant import __version__

# Configuration
from gmail_assistant.core.config import AppConfig
from gmail_assistant.core.constants import SCOPES_READONLY

# Authentication
from gmail_assistant.core.auth.base import ReadOnlyGmailAuth

# Fetching
from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

# Exceptions
from gmail_assistant.core.exceptions import (
    GmailAssistantError,
    ConfigError,
    AuthError,
    NetworkError,
    APIError,
)

# Protocols
from gmail_assistant.core.protocols import (
    EmailFetcherProtocol,
    EmailParserProtocol,
)

# Utilities
from gmail_assistant.utils.input_validator import InputValidator
from gmail_assistant.utils.rate_limiter import GmailRateLimiter
```

### CLI Commands

```bash
# Authentication
gmail-assistant auth
gmail-assistant auth --status
gmail-assistant auth --revoke

# Configuration
gmail-assistant config --init
gmail-assistant config --show
gmail-assistant config --validate

# Fetching
gmail-assistant fetch --query "is:unread" --max-emails 1000
gmail-assistant fetch --query "from:news@" --format json --async

# Deletion
gmail-assistant delete --query "older_than:1y" --dry-run
gmail-assistant delete --query "from:spam@" --confirm --trash

# Analysis
gmail-assistant analyze --input-dir ./backups --report detailed
```

### Environment Setup

```bash
# Install
pip install -e ".[all]"

# Development
pip install -e ".[dev]"

# Create default config
gmail-assistant config --init

# Verify setup
gmail-assistant auth --status
```
