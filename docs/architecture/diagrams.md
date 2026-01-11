# Gmail Assistant Architecture Diagrams

**Document**: Architecture visualization for the Gmail Assistant project
**Generated**: 2026-01-09 22:00 UTC
**Purpose**: Visual representation of package structure, component relationships, data flow, authentication flow, and CLI command flow

---

## 1. Package Structure Diagram

Shows the actual module hierarchy in `src/gmail_assistant/`:

```mermaid
graph TB
    subgraph gmail_assistant["gmail_assistant (root)"]
        direction TB

        subgraph cli["📋 cli"]
            main["main.py<br/>(Click CLI)"]
            commands["commands/<br/>fetch.py, delete.py<br/>analyze.py, auth.py<br/>config_cmd.py"]
        end

        subgraph core["⚙️ core"]
            direction TB

            subgraph auth["auth/"]
                auth_base["base.py<br/>(AuthenticationBase)"]
                auth_cred["credential_manager.py<br/>(SecureCredentialManager)"]
                auth_rl["rate_limiter.py<br/>(AuthRateLimiter)"]
            end

            subgraph fetch["fetch/"]
                fetch_client["gmail_api_client.py<br/>(GmailAPIClient)"]
                fetch_asst["gmail_assistant.py<br/>(GmailFetcher)"]
                fetch_async["async_fetcher.py"]
                fetch_batch["batch_api.py"]
                fetch_checkpoint["checkpoint.py"]
                fetch_stream["streaming.py"]
                fetch_dlq["dead_letter_queue.py"]
                fetch_incr["incremental.py"]
            end

            subgraph processing["processing/"]
                proc_extract["extractor.py<br/>(EmailDataExtractor)"]
                proc_class["classifier.py"]
                proc_plain["plaintext.py"]
                proc_db["database.py"]
                proc_dbext["database_extensions.py"]
            end

            subgraph ai["ai/"]
                ai_clean["newsletter_cleaner.py<br/>(AINewsletterDetector)"]
                ai_analysis["analysis_integration.py"]
            end

            config["config.py<br/>(AppConfig)"]
            constants["constants.py"]
            exceptions["exceptions.py"]
            protocols["protocols.py<br/>(Protocol definitions)"]
            container["container.py<br/>(ServiceContainer)"]
        end

        subgraph parsers["🔄 parsers"]
            parser_adv["advanced_email_parser.py<br/>(EmailContentParser)"]
            parser_eml["gmail_eml_to_markdown_cleaner.py"]
            parser_robust["robust_eml_converter.py"]
        end

        subgraph analysis["📊 analysis"]
            anal_analyzer["email_analyzer.py"]
            anal_daily["daily_email_analyzer.py"]
            anal_converter["email_data_converter.py"]
            anal_setup["setup_email_analysis.py"]
        end

        subgraph deletion["🗑️ deletion"]
            del_deleter["deleter.py"]
            del_ui["ui.py"]
            del_setup["setup.py"]
        end

        subgraph utils["🛠️ utils"]
            util_cache["cache_manager.py<br/>(CacheManager)"]
            util_rate["rate_limiter.py<br/>(GmailRateLimiter)"]
            util_error["error_handler.py<br/>(ErrorHandler)"]
            util_memory["memory_manager.py<br/>(MemoryTracker)"]
            util_circuit["circuit_breaker.py<br/>(CircuitBreaker)"]
            util_validator["input_validator.py<br/>(InputValidator)"]
            util_secure["secure_logger.py, secure_file.py<br/>pii_redactor.py"]
            util_config["config_schema.py"]
        end
    end

    style cli fill:#e1f5ff
    style core fill:#f3e5f5
    style parsers fill:#e8f5e9
    style analysis fill:#fff3e0
    style deletion fill:#fce4ec
    style utils fill:#f1f8e9

---

## 2. Component Relationship Diagram

Shows how core components interact and their dependencies:

```mermaid
graph LR
    subgraph CLI["🖥️ CLI Layer"]
        main_cli["main.py"]
        cmd_fetch["fetch command"]
        cmd_delete["delete command"]
        cmd_analyze["analyze command"]
        cmd_auth["auth command"]
    end

    subgraph Auth["🔐 Authentication"]
        auth_factory["AuthenticationFactory"]
        auth_base["AuthenticationBase"]
        readonly["ReadOnlyGmailAuth"]
        modify["GmailModifyAuth"]
        full["FullGmailAuth"]
        cred_mgr["SecureCredentialManager"]
        auth_rl["AuthRateLimiter"]
    end

    subgraph Fetch["📥 Email Fetching"]
        gmail_fetcher["GmailFetcher"]
        gmail_client["GmailAPIClient"]
        batch_api["BatchAPIClient"]
        async_fetch["AsyncFetcher"]
        checkpoint["Checkpoint"]
        dlq["DeadLetterQueue"]
    end

    subgraph Parse["🔄 Content Parsing"]
        email_parser["EmailContentParser"]
        eml_cleaner["EMLMarkdownCleaner"]
        robust_conv["RobustEMLConverter"]
    end

    subgraph Process["⚙️ Processing"]
        extractor["EmailDataExtractor"]
        classifier["EmailClassifier"]
        plaintext["PlaintextExtractor"]
        database["DatabaseManager"]
    end

    subgraph AI["🧠 AI Operations"]
        newsletter["AINewsletterDetector"]
        analysis_int["AnalysisIntegration"]
    end

    subgraph Utils["🛠️ Utilities"]
        cache["CacheManager"]
        rate["GmailRateLimiter"]
        error["ErrorHandler"]
        memory["MemoryTracker"]
        circuit["CircuitBreaker"]
        validator["InputValidator"]
    end

    subgraph Container["📦 DI Container"]
        service_cont["ServiceContainer"]
    end

    main_cli --> cmd_fetch
    main_cli --> cmd_delete
    main_cli --> cmd_analyze
    main_cli --> cmd_auth

    cmd_fetch --> gmail_fetcher
    cmd_delete --> newsletter
    cmd_analyze --> extractor
    cmd_auth --> auth_factory

    auth_factory --> auth_base
    auth_base --> readonly
    auth_base --> modify
    auth_base --> full
    auth_base --> cred_mgr
    auth_base --> auth_rl

    gmail_fetcher --> auth_base
    gmail_fetcher --> memory
    gmail_fetcher --> email_parser

    gmail_client --> cred_mgr
    gmail_client --> newsletter

    batch_api --> gmail_client
    async_fetch --> batch_api
    checkpoint --> async_fetch
    dlq --> checkpoint

    email_parser --> eml_cleaner
    email_parser --> robust_conv

    extractor --> email_parser
    extractor --> database

    classifier --> plaintext
    plaintext --> validator

    newsletter --> email_parser
    analysis_int --> email_parser

    cache -.-> Utils
    rate -.-> Utils
    error -.-> Utils
    memory -.-> Utils
    circuit -.-> Utils
    validator -.-> Utils

    service_cont -.->|provides| Auth
    service_cont -.->|provides| Fetch
    service_cont -.->|provides| Utils

    style CLI fill:#e1f5ff
    style Auth fill:#f3e5f5
    style Fetch fill:#e8f5e9
    style Parse fill:#fff3e0
    style Process fill:#fce4ec
    style AI fill:#ede7f6
    style Utils fill:#f1f8e9
    style Container fill:#e0f2f1

---

## 3. Data Flow Diagram

Shows email fetch → parse → output pipeline:

```mermaid
graph TD
    Start["User Request<br/>(CLI Command)"]

    Config["Load AppConfig"]
    Auth["Authenticate<br/>(ReadOnlyGmailAuth)"]

    Query["Execute Gmail Query<br/>(search_messages)"]
    Fetch["Fetch Email IDs"]

    subgraph Fetching["📥 Email Fetching"]
        FetchBatch["Batch Fetch<br/>(100 emails/batch)"]
        MemTrack["Memory Tracking"]
        CheckPoint["Checkpoint State"]
    end

    subgraph Parsing["🔄 Content Parsing"]
        Extract["Extract Metadata<br/>From: To: Subject:"]
        Html2Md["Convert HTML→Markdown<br/>(Strategy selection)"]
        QScore["Quality Scoring"]
    end

    subgraph Processing["⚙️ Content Processing"]
        Classify["Classify Email<br/>(Newsletter/Notification/Marketing)"]
        Clean["Clean Content<br/>(Remove tracking/ads)"]
        Validate["Validate<br/>(InputValidator)"]
    end

    subgraph Output["📤 Output Generation"]
        Format["Apply Output Format<br/>(JSON/EML/MBOX)"]
        Organize["Organize by Date/Sender"]
        Write["Write to File System"]
    end

    Cache["Store in Cache<br/>(CacheManager)"]

    End["✓ Complete<br/>Display Summary"]

    Error["❌ Error Handling<br/>(ErrorHandler)"]

    Start --> Config
    Config --> Auth
    Auth -->|rate limited| Error
    Auth -->|success| Query

    Query --> Fetch
    Fetch --> FetchBatch
    FetchBatch --> MemTrack
    MemTrack --> CheckPoint
    CheckPoint --> Extract

    Extract --> Html2Md
    Html2Md --> QScore
    QScore --> Classify

    Classify --> Clean
    Clean --> Validate
    Validate -->|valid| Format
    Validate -->|invalid| Error

    Format --> Organize
    Organize --> Write
    Write --> Cache
    Cache --> End

    Error --> End

    style Start fill:#b3e5fc
    style Config fill:#c8e6c9
    style Auth fill:#f8bbd0
    style Fetching fill:#e8f5e9
    style Parsing fill:#fff3e0
    style Processing fill:#fce4ec
    style Output fill:#c5cae9
    style Cache fill:#e1f5fe
    style End fill:#c8e6c9
    style Error fill:#ffcdd2

---

## 4. Authentication Flow

OAuth 2.0 flow with rate limiting and secure credential management:

```mermaid
sequenceDiagram
    participant User as User
    participant CLI as CLI main.py
    participant AppConfig as AppConfig
    participant AuthFactory as AuthenticationFactory
    participant AuthBase as AuthenticationBase
    participant CredMgr as SecureCredentialManager
    participant AuthRL as AuthRateLimiter
    participant GmailAPI as Gmail OAuth API
    participant Keyring as OS Keyring

    User->>CLI: Execute --auth command
    CLI->>AppConfig: Load configuration
    AppConfig-->>CLI: config (credentials_path, etc)

    CLI->>AuthFactory: create_auth('readonly')
    AuthFactory->>AuthBase: new ReadOnlyGmailAuth()
    AuthBase->>CredMgr: __init__(credentials.json)
    AuthBase->>AuthRL: get_auth_rate_limiter()

    AuthBase->>AuthRL: check_rate_limit()
    AuthRL-->>AuthBase: rate limit OK?

    alt Rate Limited
        AuthBase-->>CLI: Fail - rate limited
        CLI-->>User: Error: Try again later
    else Proceed
        AuthBase->>CredMgr: authenticate()

        alt Token Exists in Keyring
            CredMgr->>Keyring: retrieve_token()
            Keyring-->>CredMgr: token
            CredMgr-->>AuthBase: authenticated
        else New Authentication
            CredMgr->>GmailAPI: Start OAuth flow
            GmailAPI-->>User: Open browser to authorize
            User->>GmailAPI: Grant permission
            GmailAPI-->>CredMgr: Return auth_code
            CredMgr->>GmailAPI: Exchange code for token
            GmailAPI-->>CredMgr: access_token, refresh_token
            CredMgr->>Keyring: store_token_secure()
            Keyring-->>CredMgr: ✓ Stored
            CredMgr-->>AuthBase: authenticated
        end

        AuthBase->>CredMgr: get_service()
        CredMgr-->>AuthBase: Gmail service object
        AuthBase->>CredMgr: get_user_info()
        CredMgr-->>AuthBase: {email, messages_total, ...}

        AuthRL->>AuthRL: record_attempt(success=true)
        AuthBase-->>CLI: ✓ Authenticated
        CLI-->>User: Success: Logged in as user@example.com
    end

---

## 5. CLI Command Flow

Detailed flow from entry point to command execution:

```mermaid
graph TD
    Start["CLI Invocation"]

    Main["@click.group()<br/>main()"]

    subgraph Options["Global Options"]
        OptConfig["--config/-c PATH"]
        OptAllow["--allow-repo-credentials"]
        OptVersion["--version"]
    end

    subgraph Commands["Command Selection"]
        CmdFetch["fetch<br/>-q/--query<br/>-m/--max-emails<br/>-o/--output-dir<br/>--format json|mbox|eml"]
        CmdDelete["delete<br/>-q/--query REQUIRED<br/>--dry-run<br/>--confirm"]
        CmdAnalyze["analyze<br/>-i/--input-dir<br/>-r/--report summary|detailed|json"]
        CmdAuth["auth<br/>(no options)"]
        CmdConfig["config<br/>--show<br/>--validate<br/>--init"]
    end

    subgraph FetchFlow["fetch command flow"]
        FetchLoad["AppConfig.load()"]
        FetchMerge["Merge CLI options<br/>with config defaults"]
        FetchValidate["@handle_errors decorator"]
        FetchExec["Print status<br/>(v2.1.0 deferred)"]
    end

    subgraph DeleteFlow["delete command flow"]
        DeleteLoad["AppConfig.load()"]
        DeleteValidate["@handle_errors decorator"]
        DeleteExec["Print status<br/>(v2.1.0 deferred)"]
    end

    subgraph AnalyzeFlow["analyze command flow"]
        AnalyzeLoad["AppConfig.load()"]
        AnalyzeMerge["Use input_dir or<br/>config.output_dir"]
        AnalyzeValidate["@handle_errors decorator"]
        AnalyzeExec["Print status<br/>(v2.1.0 deferred)"]
    end

    subgraph AuthFlow["auth command flow"]
        AuthLoad["AppConfig.load()"]
        AuthValidate["@handle_errors decorator"]
        AuthExec["Print credentials paths<br/>(v2.1.0 deferred)"]
    end

    subgraph ConfigFlow["config command flow"]
        ConfigInit["if --init:<br/>Create default config<br/>at AppConfig.default_dir()"]
        ConfigValidate["if --validate:<br/>Load and check config"]
        ConfigShow["if --show:<br/>Display all settings"]
    end

    subgraph ErrorHandling["Error Handler"]
        ConfigError["ConfigError → exit(5)"]
        AuthError["AuthError → exit(3)"]
        NetworkError["NetworkError → exit(4)"]
        GeneralError["GmailAssistantError → exit(1)"]
        UnexpectedError["Exception → exit(1)"]
    end

    Start --> Main
    Main --> Options
    Options --> Commands

    Commands --> CmdFetch
    Commands --> CmdDelete
    Commands --> CmdAnalyze
    Commands --> CmdAuth
    Commands --> CmdConfig

    CmdFetch --> FetchLoad --> FetchMerge --> FetchValidate --> FetchExec
    CmdDelete --> DeleteLoad --> DeleteValidate --> DeleteExec
    CmdAnalyze --> AnalyzeLoad --> AnalyzeMerge --> AnalyzeValidate --> AnalyzeExec
    CmdAuth --> AuthLoad --> AuthValidate --> AuthExec
    CmdConfig --> ConfigInit
    CmdConfig --> ConfigValidate
    CmdConfig --> ConfigShow

    FetchExec -.->|exception| ErrorHandling
    DeleteExec -.->|exception| ErrorHandling
    AnalyzeExec -.->|exception| ErrorHandling
    AuthExec -.->|exception| ErrorHandling

    ConfigError --> End["Exit with code"]
    AuthError --> End
    NetworkError --> End
    GeneralError --> End
    UnexpectedError --> End

    FetchExec -->|success| Success["Exit(0)"]
    DeleteExec -->|success| Success
    AnalyzeExec -->|success| Success
    AuthExec -->|success| Success

    style Start fill:#e1f5ff
    style Main fill:#b3e5fc
    style Options fill:#81d4fa
    style Commands fill:#4fc3f7
    style FetchFlow fill:#c8e6c9
    style DeleteFlow fill:#a5d6a7
    style AnalyzeFlow fill:#81c784
    style AuthFlow fill:#66bb6a
    style ConfigFlow fill:#4caf50
    style ErrorHandling fill:#ffcdd2
    style Success fill:#c8e6c9

---

## 6. Service Container & Dependency Injection

DI container pattern showing service registration and resolution:

```mermaid
graph LR
    subgraph Creation["Container Creation"]
        create_default["create_default_container()"]
        create_readonly["create_readonly_container()"]
        create_modify["create_modify_container()"]
        create_full["create_full_container()"]
    end

    subgraph DefaultServices["Default Services (Singleton)"]
        cache_svc["CacheManager"]
        rate_svc["GmailRateLimiter"]
        error_svc["ErrorHandler"]
        validator_svc["InputValidator"]
    end

    subgraph ReadOnlyServices["Read-Only Services"]
        auth_readonly["ReadOnlyGmailAuth"]
        fetcher["GmailFetcher"]
    end

    subgraph ModifyServices["Modify Services"]
        auth_modify["GmailModifyAuth"]
    end

    subgraph FullServices["Full Access Services"]
        auth_full["FullGmailAuth"]
        parser["EmailContentParser"]
    end

    subgraph Container["ServiceContainer"]
        services["_services: Dict"]
        register["register()"]
        register_factory["register_factory()"]
        register_type["register_type()"]
        resolve["resolve()"]
        try_resolve["try_resolve()"]
        create_scope["create_scope()"]
    end

    subgraph Resolution["Service Resolution"]
        check_local["Check local services"]
        check_parent["Check parent container"]
        create_inst["Create instance"]
        return_inst["Return instance"]
    end

    subgraph Lifetime["Service Lifetimes"]
        singleton["SINGLETON<br/>One instance"]
        transient["TRANSIENT<br/>New each time"]
        scoped["SCOPED<br/>Per scope"]
    end

    create_default --> DefaultServices
    create_readonly --> DefaultServices
    create_readonly --> ReadOnlyServices
    create_modify --> DefaultServices
    create_modify --> ModifyServices
    create_full --> DefaultServices
    create_full --> ReadOnlyServices
    create_full --> FullServices

    DefaultServices --> Container
    ReadOnlyServices --> Container
    ModifyServices --> Container
    FullServices --> Container

    register --> services
    register_factory --> services
    register_type --> services

    resolve --> check_local
    check_local --> check_parent
    check_parent --> create_inst
    create_inst --> return_inst

    try_resolve -->|fallback| return_inst

    create_scope --> Container

    services --> Lifetime

    style Creation fill:#e3f2fd
    style DefaultServices fill:#e8f5e9
    style ReadOnlyServices fill:#f3e5f5
    style ModifyServices fill:#fce4ec
    style FullServices fill:#ede7f6
    style Container fill:#fff9c4
    style Resolution fill:#ffccbc
    style Lifetime fill:#b2dfdb

---

## Component Descriptions

### CLI Layer (`cli/`)
- **main.py**: Click-based command group with error handling decorator
- **commands/**: Modular commands (fetch, delete, analyze, auth, config)
- **Error handling**: Maps exceptions to exit codes (ConfigError→5, AuthError→3, NetworkError→4)

### Authentication (`core/auth/`)
- **base.py**: Abstract `AuthenticationBase` with three implementations
  - `ReadOnlyGmailAuth`: Gmail read-only scope
  - `GmailModifyAuth`: Gmail modify scope (delete/label)
  - `FullGmailAuth`: All Gmail scopes
- **credential_manager.py**: Secure keyring-based token storage
- **rate_limiter.py**: Brute-force protection with lockout mechanism

### Email Fetching (`core/fetch/`)
- **gmail_assistant.py**: `GmailFetcher` - main fetching engine using `ReadOnlyGmailAuth`
- **gmail_api_client.py**: `GmailAPIClient` - direct API operations with batch processing
- **async_fetcher.py**: Async batch processing
- **batch_api.py**: Batch operation client
- **checkpoint.py**: State persistence for resume capability
- **streaming.py**: Streaming email processor for memory efficiency
- **dead_letter_queue.py**: Failed email handling and retry

### Content Processing (`core/processing/`)
- **extractor.py**: `EmailDataExtractor` - metadata extraction from markdown
- **classifier.py**: Email type classification
- **plaintext.py**: Plain text extraction
- **database.py**: Email database management

### Parsing (`parsers/`)
- **advanced_email_parser.py**: Multi-strategy HTML→Markdown with quality scoring
- **gmail_eml_to_markdown_cleaner.py**: EML to Markdown with YAML front matter
- **robust_eml_converter.py**: Robust email format conversion

### AI Operations (`core/ai/`)
- **newsletter_cleaner.py**: `AINewsletterDetector` - pattern-based AI newsletter identification
- **analysis_integration.py**: Integration with analysis pipeline

### Utilities (`utils/`)
- **cache_manager.py**: Email caching for performance
- **rate_limiter.py**: Global rate limiting for Gmail API
- **error_handler.py**: Centralized error handling with recovery
- **memory_manager.py**: Memory tracking and streaming processors
- **circuit_breaker.py**: Circuit breaker pattern implementation
- **input_validator.py**: Input validation with custom rules
- **secure_logger.py**: PII-redacting logger
- **secure_file.py**: Secure file operations

### Core Services (`core/`)
- **config.py**: `AppConfig` - configuration loading and validation
- **container.py**: `ServiceContainer` - DI container with factory functions
- **protocols.py**: Protocol definitions for loose coupling
- **constants.py**: Global constants (scopes, paths, etc)
- **exceptions.py**: Custom exception hierarchy

### Analysis (`analysis/`)
- **email_analyzer.py**: Email content analysis
- **daily_email_analyzer.py**: Time-series analysis
- **email_data_converter.py**: Data format conversion

### Deletion (`deletion/`)
- **deleter.py**: Email deletion with dry-run support
- **ui.py**: CLI UI for deletion confirmation
- **setup.py**: Setup wizard

---

## Key Architectural Patterns

### 1. **Authentication Factory Pattern**
```
User Request
    ↓
AuthenticationFactory.create_auth(auth_type)
    ↓
Returns appropriate auth class:
  - ReadOnlyGmailAuth (gmail.readonly scope)
  - GmailModifyAuth (gmail.modify scope)
  - FullGmailAuth (all scopes)
    ↓
Handles rate limiting & credential management
```

### 2. **Dependency Injection**
- `ServiceContainer` manages service lifecycle
- Factory functions: `create_default_container()`, `create_readonly_container()`, etc.
- Supports singleton, transient, and scoped lifetimes
- Thread-safe with RLock

### 3. **Error Handling Chain**
- Specific exceptions: `ConfigError`, `AuthError`, `NetworkError`, `GmailAssistantError`
- `@handle_errors` decorator maps to exit codes
- `ErrorHandler` provides centralized handling and recovery

### 4. **Streaming & Memory Optimization**
- `MemoryTracker` monitors usage
- `StreamingEmailProcessor` processes large batches
- Batch processing (100 emails per batch)
- Checkpoint system for resume capability

### 5. **Secure Credential Storage**
- OS keyring integration via `SecureCredentialManager`
- No plaintext token storage
- Automatic migration from legacy tokens

### 6. **Multi-Strategy Parsing**
- `EmailContentParser` with fallback strategies:
  1. Smart extraction (BeautifulSoup)
  2. Readability algorithm
  3. Trafilatura extraction
  4. HTML2Text conversion
  5. Markdownify conversion
- Quality scoring for best result

---

## Data Types & Schemas

### EmailData (core/ai/newsletter_cleaner.py)
```
{
  message_id: str,
  from_addr: str,
  to_addr: str,
  subject: str,
  date: str,
  body: str,
  is_ai_newsletter: bool
}
```

### AppConfig (core/config.py)
```
{
  credentials_path: Path,
  token_path: Path,
  output_dir: Path,
  max_emails: int,
  rate_limit_per_second: float,
  log_level: str
}
```

### Email Metadata (core/processing/extractor.py)
```
{
  date: str,
  from: str,
  to: str,
  subject: str,
  message_id: str,
  in_reply_to: Optional[str],
  content: str
}
```

---

## Import Dependencies Summary

| Module | Key Imports | Purpose |
|--------|-------------|---------|
| `cli/main.py` | click, AppConfig, exceptions | CLI command interface |
| `core/auth/base.py` | SecureCredentialManager, AuthRateLimiter | OAuth flow management |
| `core/fetch/gmail_assistant.py` | ReadOnlyGmailAuth, MemoryTracker | Email fetching |
| `core/fetch/gmail_api_client.py` | SecureCredentialManager, AINewsletterDetector | Direct API operations |
| `core/processing/extractor.py` | EmailDataExtractor, EmailParser | Email metadata extraction |
| `parsers/advanced_email_parser.py` | BeautifulSoup, html2text, markdownify | Content parsing |
| `core/container.py` | protocols | Service registration |

---

## Deployment Architecture Notes

1. **Stateless CLI**: All state management in AppConfig and local cache
2. **Secure by default**: Credentials in OS keyring, not filesystem
3. **Rate-limited**: Protects against brute-force auth and API abuse
4. **Extensible**: Protocol-based design allows component swapping
5. **Observable**: Secure logging with PII redaction
6. **Recoverable**: Checkpoint system enables resume from failures
