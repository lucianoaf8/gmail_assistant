# Gmail Assistant - Architecture Overview

**Version**: 2.0.0
**Document Date**: 2026-01-09
**Python Requirements**: >=3.10
**Status**: Production (CLI v2.0, Core modules stable)

---

## Executive Summary

Gmail Assistant is a Python-based email management suite that provides backup, analysis, and manipulation capabilities for Gmail accounts via the Gmail API. The system employs a modular architecture with clear separation of concerns, protocol-driven interfaces, and comprehensive security controls.

**Core Capabilities**:
- OAuth 2.0 authenticated Gmail API access with three permission tiers (readonly, modify, full)
- Email fetching with multiple output formats (EML, Markdown, JSON)
- Advanced HTML-to-Markdown parsing with strategy pattern
- AI-powered email classification and newsletter detection
- Dependency injection container for service management
- Comprehensive error handling and recovery mechanisms
- Rate limiting and quota management
- Security features including PII redaction and credential management

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Package Structure](#package-structure)
3. [Core Design Patterns](#core-design-patterns)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Security Architecture](#security-architecture)
6. [Configuration Management](#configuration-management)
7. [Dependency Graph](#dependency-graph)
8. [Extension Points](#extension-points)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer (Click)                       │
│  Entry Point: gmail-assistant command                        │
│  Commands: fetch, delete, analyze, auth, config              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Core Module Layer                          │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Auth      │  │   Fetch     │  │    AI       │         │
│  │ SubPackage  │  │ SubPackage  │  │ SubPackage  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐                           │
│  │ Processing  │  │   Config    │                           │
│  │ SubPackage  │  │   Manager   │                           │
│  └─────────────┘  └─────────────┘                           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Utility & Support Layer                         │
├──────────────────────────────────────────────────────────────┤
│  Error Handler | Rate Limiter | Cache Manager               │
│  Input Validator | Memory Manager | Circuit Breaker         │
│  Secure Logger | PII Redactor | Secure File Handler         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   External Services                          │
├──────────────────────────────────────────────────────────────┤
│  Gmail API | System Keyring | File System                   │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Architectural Principles

**Separation of Concerns**: Each package has a single, well-defined responsibility:
- `core.auth`: Authentication and credential management
- `core.fetch`: Email retrieval operations
- `core.processing`: Email content processing and transformation
- `core.ai`: AI-powered classification and analysis
- `utils`: Cross-cutting utility functions
- `parsers`: Format conversion and content extraction
- `cli`: User interface and command handling

**Protocol-Driven Design**: Interfaces defined using `typing.Protocol` for structural subtyping:
- `GmailClientProtocol`: Gmail API client operations
- `EmailFetcherProtocol`: Email fetching operations
- `EmailParserProtocol`: Content parsing operations
- `RateLimiterProtocol`: Rate limiting behavior
- `CacheProtocol`: Caching strategies

**Dependency Injection**: `ServiceContainer` class provides:
- Constructor injection for dependencies
- Singleton, transient, and scoped lifetimes
- Factory-based service registration
- Thread-safe service resolution

---

## 2. Package Structure

### 2.1 Source Tree Organization

```
src/gmail_assistant/
├── __init__.py                    # Package entry point, version info
├── __main__.py                    # Python -m gmail_assistant support
│
├── cli/                           # Command-line interface
│   ├── main.py                    # Click-based CLI (entry point)
│   └── commands/                  # Individual command modules
│       ├── fetch.py               # Email fetching command
│       ├── delete.py              # Email deletion command
│       ├── analyze.py             # Email analysis command
│       ├── auth.py                # Authentication command
│       └── config_cmd.py          # Configuration command
│
├── core/                          # Core business logic
│   ├── __init__.py                # Lazy import handler
│   ├── config.py                  # Configuration loader
│   ├── config_schemas.py          # Configuration validation schemas
│   ├── constants.py               # System-wide constants
│   ├── container.py               # Dependency injection container
│   ├── exceptions.py              # Exception hierarchy
│   ├── protocols.py               # Protocol definitions (interfaces)
│   ├── schemas.py                 # Pydantic data models
│   │
│   ├── auth/                      # Authentication subsystem
│   │   ├── base.py                # Base authentication classes
│   │   ├── credential_manager.py  # Secure credential storage
│   │   └── rate_limiter.py        # Auth rate limiting
│   │
│   ├── fetch/                     # Email fetching subsystem
│   │   ├── gmail_assistant.py     # Main fetcher implementation
│   │   ├── gmail_api_client.py    # Gmail API wrapper
│   │   ├── async_fetcher.py       # Async email fetching
│   │   ├── streaming.py           # Streaming fetcher
│   │   ├── incremental.py         # Incremental sync
│   │   ├── batch_api.py           # Batch API operations
│   │   ├── checkpoint.py          # Progress checkpointing
│   │   └── dead_letter_queue.py   # Failed operation handling
│   │
│   ├── processing/                # Email processing subsystem
│   │   ├── classifier.py          # Email classification
│   │   ├── extractor.py           # Data extraction
│   │   ├── plaintext.py           # Plain text processing
│   │   ├── database.py            # Database import/export
│   │   └── database_extensions.py # Advanced DB operations
│   │
│   └── ai/                        # AI-powered features
│       ├── newsletter_cleaner.py  # AI newsletter detection
│       └── analysis_integration.py # AI analysis integration
│
├── parsers/                       # Format conversion
│   ├── advanced_email_parser.py   # Multi-strategy HTML parser
│   ├── gmail_eml_to_markdown_cleaner.py  # EML to Markdown
│   └── robust_eml_converter.py    # Robust EML conversion
│
├── utils/                         # Utility modules
│   ├── cache_manager.py           # Caching strategies
│   ├── circuit_breaker.py         # Circuit breaker pattern
│   ├── error_handler.py           # Error classification & recovery
│   ├── input_validator.py         # Input validation
│   ├── memory_manager.py          # Memory optimization
│   ├── rate_limiter.py            # API rate limiting
│   ├── secure_file.py             # Secure file operations
│   ├── secure_logger.py           # PII-safe logging
│   └── pii_redactor.py            # PII detection & redaction
│
├── analysis/                      # Email analysis tools
│   ├── email_analyzer.py          # Email analysis engine
│   ├── daily_email_analyzer.py    # Daily analysis
│   ├── email_data_converter.py    # Format conversion
│   └── setup_email_analysis.py    # Analysis setup
│
└── deletion/                      # Email deletion tools
    ├── deleter.py                 # Email deletion engine
    ├── setup.py                   # Deletion setup
    └── ui.py                      # Deletion UI helpers
```

### 2.2 Package Dependencies

**Core Dependencies** (always required):
- `click>=8.1.0`: CLI framework
- `google-api-python-client>=2.140.0`: Gmail API client
- `google-auth>=2.27.0`: OAuth authentication
- `google-auth-oauthlib>=1.2.0`: OAuth flow
- `html2text>=2024.2.26`: HTML to text conversion
- `tenacity>=8.2.0`: Retry mechanisms

**Optional Feature Groups**:
```toml
[analysis]          # pandas, numpy, pyarrow
[ui]                # rich, tqdm
[advanced-parsing]  # beautifulsoup4, markdownify, lxml
[content-extraction] # readability-lxml, trafilatura
[async]             # aiohttp, asyncio-throttle, psutil
[security]          # keyring, regex
[network]           # requests, urllib3
```

---

## 3. Core Design Patterns

### 3.1 Protocol Pattern (Structural Typing)

**Purpose**: Define interfaces without inheritance, enabling duck typing with type safety.

**Implementation** (`core/protocols.py`):
```python
@runtime_checkable
class EmailFetcherProtocol(Protocol):
    def search_messages(self, query: str, max_results: int = 100) -> List[str]: ...
    def get_message(self, message_id: str, format: str = "full") -> Optional[Dict]: ...
    def download_emails(self, query: str, ...) -> FetchResult: ...
```

**Usage**: Any class implementing these methods satisfies the protocol without explicit inheritance.

### 3.2 Dependency Injection Pattern

**Purpose**: Decouple service creation from usage, enabling testability and configuration flexibility.

**Implementation** (`core/container.py`):
```python
class ServiceContainer:
    def register(self, service_type: Type[T], instance: T,
                 lifetime: str = ServiceLifetime.SINGLETON) -> 'ServiceContainer'
    def register_factory(self, service_type: Type[T],
                        factory: Callable[[], T]) -> 'ServiceContainer'
    def resolve(self, service_type: Type[T]) -> T
```

**Service Lifetimes**:
- `SINGLETON`: One instance per container (default for utilities)
- `TRANSIENT`: New instance each resolution (validators, builders)
- `SCOPED`: One instance per scope (database connections)

**Factory Functions**:
- `create_default_container()`: Core utilities only
- `create_readonly_container()`: Read-only Gmail operations
- `create_modify_container()`: Modify/delete operations
- `create_full_container()`: All features enabled

### 3.3 Strategy Pattern

**Purpose**: Select parsing algorithm at runtime based on content characteristics.

**Implementation** (`parsers/advanced_email_parser.py`):
```python
class EmailContentParser:
    strategies = ["smart", "readability", "trafilatura", "html2text", "markdownify"]

    def parse(self, html_content: str, sender: str = "") -> ParseResult:
        email_type = self.detect_email_type(html_content, sender)
        # Select strategy based on email_type
        for strategy in self.get_strategies_for_type(email_type):
            result = self.apply_strategy(strategy, html_content)
            if result.quality > threshold:
                return result
```

### 3.4 Template Method Pattern

**Purpose**: Define authentication workflow skeleton while allowing subclass customization.

**Implementation** (`core/auth/base.py`):
```python
class AuthenticationBase(ABC):
    def authenticate(self) -> bool:
        # Template method with fixed workflow
        if self.is_authenticated:
            return True
        if not self._check_rate_limit():
            return False
        success = self.credential_manager.authenticate()
        if success:
            self._fetch_user_info()
        return success

    @abstractmethod
    def get_required_scopes(self) -> List[str]:
        # Hook for subclass customization
        pass

class ReadOnlyGmailAuth(AuthenticationBase):
    def get_required_scopes(self) -> List[str]:
        return ['https://www.googleapis.com/auth/gmail.readonly']
```

### 3.5 Factory Pattern

**Purpose**: Create appropriate authentication instances based on required permissions.

**Implementation** (`core/auth/base.py`):
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

### 3.6 Circuit Breaker Pattern

**Purpose**: Prevent cascading failures by failing fast when downstream services are unavailable.

**Implementation** (`utils/circuit_breaker.py`):
- States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
- Threshold-based state transitions
- Automatic recovery attempts after timeout

---

## 4. Data Flow Architecture

### 4.1 Email Fetching Flow

```
User Input (CLI)
    │
    ├─→ AppConfig.load()              # Configuration resolution
    │
    ├─→ AuthenticationBase.authenticate()  # OAuth flow
    │       │
    │       ├─→ SecureCredentialManager.authenticate()
    │       ├─→ Keyring storage check
    │       └─→ OAuth browser flow (if needed)
    │
    ├─→ GmailFetcher.download_emails()
    │       │
    │       ├─→ search_messages(query)   # Get message IDs
    │       │       └─→ Gmail API: users.messages.list()
    │       │
    │       ├─→ get_message_details(id)  # For each message
    │       │       ├─→ Gmail API: users.messages.get()
    │       │       ├─→ API response validation (M-3 security)
    │       │       └─→ Extract headers, body, attachments
    │       │
    │       ├─→ _create_output_file()     # Format conversion
    │       │       ├─→ EML format: email.message_from_string()
    │       │       └─→ Markdown: AdvancedEmailParser.parse()
    │       │
    │       └─→ FetchResult(success, count, errors)
    │
    └─→ Output files written to configured directory
```

### 4.2 Authentication Flow

```
authenticate() called
    │
    ├─→ AuthRateLimiter.check_rate_limit()  # L-2 security
    │       └─→ Block if >5 failures in 15 min
    │
    ├─→ SecureCredentialManager.authenticate()
    │       │
    │       ├─→ Check keyring for existing token
    │       │       └─→ keyring.get_password(service, username)
    │       │
    │       ├─→ Validate token expiry
    │       │
    │       ├─→ If expired: refresh token
    │       │       └─→ credentials.refresh(Request())
    │       │
    │       └─→ If no token: OAuth flow
    │               ├─→ Read credentials.json (client ID/secret)
    │               ├─→ InstalledAppFlow.from_client_secrets_file()
    │               ├─→ Launch local server (port 8080)
    │               ├─→ Open browser for user consent
    │               ├─→ Receive authorization code
    │               ├─→ Exchange for access/refresh tokens
    │               └─→ Store in keyring (L-1 security)
    │
    ├─→ Build Gmail API service
    │       └─→ build('gmail', 'v1', credentials=creds)
    │
    ├─→ Fetch user profile
    │       └─→ service.users().getProfile(userId='me')
    │
    └─→ Return success/failure + record attempt
```

### 4.3 Email Parsing Flow

```
HTML Email Content
    │
    ├─→ EmailContentParser.parse()
    │       │
    │       ├─→ detect_email_type(html, sender)
    │       │       ├─→ Newsletter: multi-column, tracking pixels
    │       │       ├─→ Notification: simple layout, no-reply sender
    │       │       ├─→ Marketing: many images, tables
    │       │       └─→ Simple: plain HTML, minimal styling
    │       │
    │       ├─→ clean_html(html)
    │       │       ├─→ Remove script/style/meta tags
    │       │       ├─→ Strip tracking parameters from URLs
    │       │       ├─→ Remove invisible elements
    │       │       └─→ Normalize whitespace
    │       │
    │       ├─→ Try strategies in order until quality threshold met:
    │       │       │
    │       │       ├─→ 1. Smart Strategy (sender-specific rules)
    │       │       │       └─→ Apply newsletter_patterns[sender_domain]
    │       │       │
    │       │       ├─→ 2. Readability Strategy (if available)
    │       │       │       ├─→ Document(html).summary()
    │       │       │       └─→ Extract main content, remove boilerplate
    │       │       │
    │       │       ├─→ 3. Trafilatura Strategy (if available)
    │       │       │       ├─→ trafilatura.extract(html)
    │       │       │       └─→ News/article optimized extraction
    │       │       │
    │       │       ├─→ 4. HTML2Text Strategy
    │       │       │       └─→ html2text.handle(html)
    │       │       │
    │       │       └─→ 5. Markdownify Strategy
    │       │               └─→ markdownify.markdownify(html)
    │       │
    │       ├─→ score_quality(result)
    │       │       ├─→ Content length (too short/long = penalty)
    │       │       ├─→ Markdown structure (headings, lists)
    │       │       ├─→ Link density
    │       │       └─→ Special character ratio
    │       │
    │       └─→ Return ParseResult with best strategy
    │
    └─→ Markdown output with metadata
```

### 4.4 Configuration Resolution Flow

```
AppConfig.load(cli_config, allow_repo_credentials)
    │
    ├─→ Priority 1: CLI argument
    │       └─→ --config /path/to/config.json
    │
    ├─→ Priority 2: Environment variable
    │       └─→ $GMAIL_ASSISTANT_CONFIG
    │
    ├─→ Priority 3: Project config
    │       └─→ ./gmail-assistant.json (current directory)
    │
    ├─→ Priority 4: User config
    │       └─→ ~/.gmail-assistant/config.json
    │
    ├─→ Priority 5: Built-in defaults
    │       ├─→ credentials_path: ~/.gmail-assistant/credentials.json
    │       ├─→ token_path: ~/.gmail-assistant/token.json
    │       ├─→ output_dir: ~/.gmail-assistant/backups
    │       ├─→ max_emails: 1000
    │       ├─→ rate_limit_per_second: 10.0
    │       └─→ log_level: INFO
    │
    ├─→ Validate configuration
    │       ├─→ Check required keys only (strict validation)
    │       ├─→ Type validation (int, float, str, Path)
    │       ├─→ Range validation (max_emails: 1-50000)
    │       └─→ Path expansion (~/. and relative paths)
    │
    ├─→ Security checks
    │       ├─→ Find git repository root (if applicable)
    │       ├─→ Check if credentials inside repo
    │       └─→ Warn or error based on allow_repo_credentials
    │
    └─→ Return immutable AppConfig dataclass
```

---

## 5. Security Architecture

### 5.1 Authentication Security

**OAuth 2.0 Flow**:
- Client credentials stored in `credentials.json` (not committed to git)
- Access tokens stored in system keyring (not filesystem)
- Refresh tokens used for long-term authentication
- Automatic token refresh before expiry

**Rate Limiting** (L-2 Security Fix):
- Maximum 5 authentication attempts per 15 minutes
- Exponential backoff after failures
- Lockout period prevents brute force
- Implementation: `core/auth/rate_limiter.py`

**Credential Storage** (L-1 Security Fix):
- Tokens stored in OS keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- Never stored in plaintext files
- Automatic migration from legacy token.json to keyring
- Implementation: `core/auth/credential_manager.py`

### 5.2 Input Validation

**API Response Validation** (M-3 Security Fix):
```python
def _validate_api_response(self, response: Optional[Dict],
                           required_fields: List[str]) -> Dict:
    # Validates Gmail API responses have expected structure
    # Prevents null pointer exceptions and malformed data processing
    # Required fields: ['id', 'threadId', 'payload']
```

**Gmail Query Validation**:
- Validates search query syntax before API call
- Prevents injection attacks via query parameters
- Implementation: `utils/input_validator.py`

**Path Validation**:
- All paths validated and expanded before use
- Prevents directory traversal attacks
- Checks for repository-relative credential storage

### 5.3 Data Protection

**PII Redaction**:
- Email addresses, phone numbers, SSNs automatically detected
- Configurable redaction patterns
- Applied to logs and error messages
- Implementation: `utils/pii_redactor.py`

**Secure Logging**:
- Automatic PII redaction in log output
- Sensitive data (tokens, passwords) never logged
- Structured logging with severity levels
- Implementation: `utils/secure_logger.py`

**Secure File Operations**:
- Atomic file writes (write to temp, then rename)
- Permission checks before file operations
- Safe cleanup of temporary files
- Implementation: `utils/secure_file.py`

### 5.4 Error Handling Security

**Error Classification**:
```python
class ErrorCategory(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    API_QUOTA = "api_quota"
    RATE_LIMIT = "rate_limit"
    # ... other categories
```

**Secure Error Messages**:
- Technical details separated from user messages
- Sensitive information excluded from user-facing errors
- Detailed logging with PII redaction
- Implementation: `utils/error_handler.py`

---

## 6. Configuration Management

### 6.1 Configuration Schema

**File Format**: JSON
**Default Location**: `~/.gmail-assistant/config.json`

**Schema**:
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

**Validation Rules**:
- `credentials_path`: Must exist, must be file
- `token_path`: Parent directory must exist
- `output_dir`: Created if doesn't exist
- `max_emails`: Integer, 1-50000
- `rate_limit_per_second`: Float, 0.1-100.0
- `log_level`: One of DEBUG, INFO, WARNING, ERROR, CRITICAL

### 6.2 Environment Variable Overrides

**Path Overrides** (L-1 Security Enhancement):
```bash
export GMAIL_ASSISTANT_CONFIG_DIR=/custom/config
export GMAIL_ASSISTANT_DATA_DIR=/custom/data
export GMAIL_ASSISTANT_BACKUP_DIR=/custom/backups
export GMAIL_ASSISTANT_CREDENTIALS_DIR=/custom/credentials
export GMAIL_ASSISTANT_CACHE_DIR=/custom/cache
```

**Configuration File Override**:
```bash
export GMAIL_ASSISTANT_CONFIG=/path/to/config.json
```

### 6.3 Constants Management

**Implementation**: `core/constants.py`

**Categories**:
- Application metadata (name, version)
- OAuth scopes (readonly, modify, full)
- Default paths (config, data, backup, credentials)
- API rate limits (requests per second, batch sizes)
- Output formats (EML, Markdown, JSON)
- Logging configuration

**Usage**:
```python
from gmail_assistant.core.constants import (
    SCOPES_READONLY,
    DEFAULT_MAX_EMAILS,
    DEFAULT_CREDENTIALS_PATH
)
```

---

## 7. Dependency Graph

### 7.1 Core Module Dependencies

```
cli/main.py
    ├─→ core/config.py
    ├─→ core/exceptions.py
    └─→ cli/commands/*
            ├─→ core/auth/base.py
            ├─→ core/fetch/gmail_assistant.py
            └─→ core/ai/newsletter_cleaner.py

core/auth/base.py
    ├─→ core/auth/credential_manager.py
    ├─→ core/auth/rate_limiter.py
    ├─→ core/exceptions.py
    └─→ utils/error_handler.py

core/fetch/gmail_assistant.py
    ├─→ core/auth/base.py
    ├─→ core/constants.py
    ├─→ utils/memory_manager.py
    └─→ parsers/advanced_email_parser.py

parsers/advanced_email_parser.py
    ├─→ utils/input_validator.py
    ├─→ beautifulsoup4 (external)
    ├─→ html2text (external)
    ├─→ markdownify (external)
    ├─→ readability (optional external)
    └─→ trafilatura (optional external)
```

### 7.2 External Dependencies

**Google APIs**:
- `google-api-python-client`: Gmail API service
- `google-auth`: Credential management
- `google-auth-oauthlib`: OAuth flow
- `google-auth-httplib2`: HTTP transport

**Parsing**:
- `html2text`: HTML to Markdown conversion
- `beautifulsoup4`: HTML parsing and cleaning
- `markdownify`: Alternative HTML to Markdown
- `readability-lxml`: Content extraction (optional)
- `trafilatura`: News article extraction (optional)

**Data Handling**:
- `pandas`: Data analysis (optional)
- `numpy`: Numerical operations (optional)
- `pyarrow`: Parquet format (optional)

**CLI & UI**:
- `click`: Command-line interface
- `rich`: Rich terminal output (optional)
- `tqdm`: Progress bars (optional)

**Security**:
- `keyring`: Secure credential storage
- `regex`: ReDoS-safe regex (timeout support)

---

## 8. Extension Points

### 8.1 Adding New Authentication Scopes

**Steps**:
1. Define new scope in `core/constants.py`:
   ```python
   SCOPES_CUSTOM = ['https://www.googleapis.com/auth/gmail.custom']
   ```

2. Create new authentication class in `core/auth/base.py`:
   ```python
   class CustomGmailAuth(AuthenticationBase):
       def get_required_scopes(self) -> List[str]:
           return SCOPES_CUSTOM
   ```

3. Register in `AuthenticationFactory.create_auth()`:
   ```python
   auth_classes['custom'] = CustomGmailAuth
   ```

### 8.2 Adding New Parsing Strategies

**Steps**:
1. Implement strategy method in `parsers/advanced_email_parser.py`:
   ```python
   def parse_custom_strategy(self, html: str) -> Tuple[str, float]:
       # Return (markdown, quality_score)
       pass
   ```

2. Add strategy to configuration:
   ```python
   "strategies": ["smart", "custom", "readability", ...]
   ```

3. Register strategy in `apply_strategy()`:
   ```python
   elif strategy == "custom":
       return self.parse_custom_strategy(html)
   ```

### 8.3 Adding New CLI Commands

**Steps**:
1. Create command module in `cli/commands/`:
   ```python
   @click.command()
   @click.option("--option", help="Description")
   @click.pass_context
   @handle_errors
   def mycommand(ctx: click.Context, option: str) -> None:
       """Command description."""
       pass
   ```

2. Register in `cli/main.py`:
   ```python
   from cli.commands.mycommand import mycommand
   main.add_command(mycommand)
   ```

### 8.4 Adding New Protocols

**Steps**:
1. Define protocol in `core/protocols.py`:
   ```python
   @runtime_checkable
   class MyProtocol(Protocol):
       def my_method(self, arg: str) -> bool: ...
   ```

2. Implement in concrete class:
   ```python
   class MyImplementation:
       def my_method(self, arg: str) -> bool:
           # Implementation
           return True
   ```

3. No inheritance required - structural typing validates automatically.

### 8.5 Adding New Service Container Registrations

**Steps**:
1. Create factory function in `core/container.py`:
   ```python
   def create_custom_container() -> ServiceContainer:
       container = create_default_container()
       container.register(MyService, MyService())
       return container
   ```

2. Use in application:
   ```python
   container = create_custom_container()
   service = container.resolve(MyService)
   ```

---

## Appendix A: Version History

**2.0.0** (Current):
- Complete CLI rewrite using Click framework
- Pydantic data models for email representation
- Protocol-based architecture for extensibility
- Comprehensive security enhancements (L-1, L-2, M-3 fixes)
- Dependency injection container
- Advanced parsing strategies

**1.x** (Legacy):
- Argparse-based CLI
- Direct Gmail API integration
- Basic EML and Markdown export

---

## Appendix B: File Naming Conventions

**Documentation**: `MMDD-HHMM_description.md`
**Configuration**: `config_name.json`
**Source Code**: `snake_case.py`
**Test Files**: `test_module_name.py`
**Scripts**: `script_name.{bat,ps1,sh}`

---

## Appendix C: Exit Codes

| Code | Meaning | Exception Type |
|------|---------|---------------|
| 0 | Success | None |
| 1 | General error | GmailAssistantError, Exception |
| 2 | Usage error | Click validation |
| 3 | Authentication error | AuthError |
| 4 | Network error | NetworkError |
| 5 | Configuration error | ConfigError |

---

**End of Architecture Overview**
