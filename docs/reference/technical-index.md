# Gmail Assistant Technical Reference Index

Complete technical documentation index for gmail-assistant v2.0.0 - The definitive reference for all APIs, configurations, and command-line interfaces.

**Version**: 2.0.0
**Last Updated**: 2026-01-09
**Status**: Production

---

## Overview

This index provides navigation to comprehensive technical reference documentation covering:
- Command-line interface (CLI) usage and options
- Configuration file schemas and validation rules
- Python public API for programmatic access
- Constants and environment variable overrides
- Data models and protocol specifications

---

## Quick Navigation

### For Command-Line Users
Start here if you're using gmail-assistant from the terminal.

1. **[CLI Reference](0109-1500_CLI_REFERENCE.md)** - Complete CLI documentation
   - All commands and options
   - Exit codes and error handling
   - Configuration resolution order
   - Usage examples for common tasks

### For Configuration Management
Start here to understand configuration files and settings.

1. **[Configuration Reference](0109-1600_CONFIGURATION_REFERENCE.md)** - All config file schemas
   - Main AppConfig parameters
   - AI newsletter cleaner configuration
   - Email organization patterns
   - Analysis pipeline settings
   - Validation rules and security

### For Python Development
Start here to integrate gmail-assistant into your Python code.

1. **[Public API Reference](0109-1700_PUBLIC_API_REFERENCE.md)** - Python API documentation
   - Core classes (AppConfig, GmailFetcher, etc.)
   - Data models (Email, EmailParticipant, etc.)
   - Protocol specifications for interfaces
   - Exception hierarchy and error handling
   - Code examples and best practices

### For System Administrators
Start here to configure and deploy gmail-assistant.

1. **[Constants Reference](0109-1800_CONSTANTS_REFERENCE.md)** - All hardcoded values
   - Application metadata
   - OAuth scopes and credentials
   - Directory paths and defaults
   - Rate limiting and API limits
   - Environment variable overrides

---

## Document Overview

### 0109-1500_CLI_REFERENCE.md

**Purpose**: Complete command-line interface documentation

**Covers**:
- Entry point and global options
- All commands: `auth`, `fetch`, `delete`, `analyze`, `config`
- Options for each command with valid ranges and defaults
- Exit codes (0, 1, 2, 3, 4, 5) and their meanings
- Configuration resolution order (5 levels of priority)
- Gmail search query syntax and examples
- Dry-run and safety features for destructive operations

**Key Sections**:
- Global options: `--config`, `--allow-repo-credentials`, `--version`
- Command details with parameters and validation
- Exit code mapping for error handling
- Configuration resolution with examples
- Practical workflows and advanced queries

**Use When**:
- Running commands from terminal
- Understanding CLI options
- Debugging command execution
- Automating with shell scripts

---

### 0109-1600_CONFIGURATION_REFERENCE.md

**Purpose**: Complete configuration file schema documentation

**Covers**:
- Main configuration (AppConfig) with all parameters
- AI newsletter cleaner configuration
- Email organization patterns and classifications
- Email analysis pipeline settings
- Deletion pattern configurations
- Gmail query presets and defaults
- Configuration file loading and resolution
- Validation rules and type checking
- Security considerations and repo credential protection
- Environment variable overrides for all paths

**Key Sections**:
- AppConfig parameters: credentials_path, token_path, output_dir, max_emails, rate_limit_per_second, log_level
- Parameter ranges and validation
- Path resolution (relative to config file, not CWD)
- Complete example configurations
- Security validation (repo detection, credential location)
- AI keyword lists (38 keywords, 27 domains, 18 patterns)
- Email classification thresholds

**Use When**:
- Creating or modifying config files
- Understanding parameter validation
- Implementing custom configurations
- Troubleshooting configuration errors
- Setting up production deployments

---

### 0109-1700_PUBLIC_API_REFERENCE.md

**Purpose**: Complete Python API documentation for programmatic use

**Covers**:
- Core classes: AppConfig, GmailFetcher, GmailAPIClient
- Data models: Email, EmailParticipant, EmailMetadata, FetchResult, DeleteResult, ParseResult
- Protocol interfaces for type hints and dependency injection
- Exception hierarchy and error handling
- Configuration loading and access APIs
- Constants module overview
- Code examples and best practices
- Type hint patterns and protocols

**Key Sections**:
- Quick start example code
- AppConfig loading, validation, resolution order
- GmailFetcher methods: authenticate(), search_messages(), get_message_details(), get_profile()
- Email model with from_gmail_message() factory and properties
- Protocols: GmailClientProtocol, EmailFetcherProtocol, EmailDeleterProtocol, EmailParserProtocol
- Exception classes: ConfigError, AuthError, NetworkError, APIError
- Best practices for configuration, error handling, type hints

**Use When**:
- Writing Python code using gmail-assistant
- Understanding class methods and their signatures
- Implementing protocol-based designs
- Handling exceptions properly
- Working with Email models and data structures

---

### 0109-1800_CONSTANTS_REFERENCE.md

**Purpose**: Complete reference of all constants and hardcoded values

**Covers**:
- Application metadata: APP_NAME, APP_VERSION
- OAuth scope constants and scope lists
- Default path constants with environment overrides
- Rate limiting constants: DEFAULT_RATE_LIMIT, MAX_RATE_LIMIT, CONSERVATIVE_REQUESTS_PER_SECOND
- API limits: BATCH_SIZE, MAX_EMAILS_LIMIT, DEFAULT_MAX_EMAILS
- Output format options: SUPPORTED_OUTPUT_FORMATS, DEFAULT_OUTPUT_FORMAT
- Organization types: SUPPORTED_ORGANIZATION_TYPES, DEFAULT_ORGANIZATION
- Keyring configuration: KEYRING_SERVICE, KEYRING_USERNAME
- Logging configuration: DEFAULT_LOG_FORMAT, DEFAULT_LOG_LEVEL
- Environment variable override mechanism

**Key Sections**:
- Each constant with type, value, purpose, and usage examples
- Environment variable overrides (5 path overrides)
- Scope lists and security principles
- Complete import example showing all constants
- Keyring storage details (Linux, macOS, Windows)
- Log format explanation and example output

**Use When**:
- Understanding default behaviors
- Configuring rate limits and batch sizes
- Overriding paths via environment variables
- Reviewing supported output formats and organizations
- Understanding keyring credential storage

---

## Cross-Reference Guide

### Finding Information

#### "How do I use the CLI?"
→ [CLI Reference](0109-1500_CLI_REFERENCE.md)
- See [Commands section](0109-1500_CLI_REFERENCE.md#commands) for all commands
- See [Examples section](0109-1500_CLI_REFERENCE.md#examples) for practical usage

#### "What configuration options are available?"
→ [Configuration Reference](0109-1600_CONFIGURATION_REFERENCE.md)
- See [AppConfig section](0109-1600_CONFIGURATION_REFERENCE.md#appconfig-main-configuration) for main config
- See [Parameters Detail section](0109-1600_CONFIGURATION_REFERENCE.md#parameters) for each parameter

#### "How do I use this in Python code?"
→ [Public API Reference](0109-1700_PUBLIC_API_REFERENCE.md)
- See [Core Classes section](0109-1700_PUBLIC_API_REFERENCE.md#core-classes) for available classes
- See [Quick Start section](0109-1700_PUBLIC_API_REFERENCE.md#quick-start) for example code

#### "What are all the default values?"
→ [Constants Reference](0109-1800_CONSTANTS_REFERENCE.md)
- See individual sections for each constant category
- See [Environment Variable Overrides section](0109-1800_CONSTANTS_REFERENCE.md#environment-variable-overrides) for customization

#### "How do I authenticate?"
→ [Public API Reference](0109-1700_PUBLIC_API_REFERENCE.md#authenticate)
→ [CLI Reference](0109-1500_CLI_REFERENCE.md#auth) `auth` command

#### "What does ConfigError mean?"
→ [CLI Reference](0109-1500_CLI_REFERENCE.md#exit-codes) Exit Code 5
→ [Public API Reference](0109-1700_PUBLIC_API_REFERENCE.md#configerror)

#### "How do I configure rate limiting?"
→ [Configuration Reference](0109-1600_CONFIGURATION_REFERENCE.md#rate_limit_per_second)
→ [Constants Reference](0109-1800_CONSTANTS_REFERENCE.md#rate-limiting)

#### "What's the maximum number of emails?"
→ [Constants Reference](0109-1800_CONSTANTS_REFERENCE.md#max_emails_limit)
→ [Configuration Reference](0109-1600_CONFIGURATION_REFERENCE.md#max_emails)

---

## Common Tasks Reference

### Task: Fetch Unread Emails

**Via CLI**:
```bash
gmail-assistant fetch --query "is:unread" --max-emails 100
```
→ See [CLI Reference - fetch command](0109-1500_CLI_REFERENCE.md#fetch)

**Via Python**:
```python
from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

fetcher = GmailFetcher('credentials.json')
fetcher.authenticate()
ids = fetcher.search_messages("is:unread", max_results=100)
```
→ See [Public API Reference - GmailFetcher](0109-1700_PUBLIC_API_REFERENCE.md#gmailtransactionfetcher)

---

### Task: Initialize Configuration

**Via CLI**:
```bash
gmail-assistant config --init
gmail-assistant config --show
```
→ See [CLI Reference - config command](0109-1500_CLI_REFERENCE.md#config)

**Manually**:
Create `~/.gmail-assistant/config.json`:
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
→ See [Configuration Reference - AppConfig](0109-1600_CONFIGURATION_REFERENCE.md#appconfig-main-configuration)

---

### Task: Load Configuration in Python

```python
from gmail_assistant.core.config import AppConfig

# Automatic resolution order
config = AppConfig.load()

# Specific file
from pathlib import Path
config = AppConfig.load(Path("/etc/gmail-assistant/config.json"))

# Access fields
print(config.max_emails)
print(config.rate_limit_per_second)
```
→ See [Public API Reference - AppConfig.load()](0109-1700_PUBLIC_API_REFERENCE.md#load)

---

### Task: Handle Errors Properly

```python
from gmail_assistant.core.exceptions import ConfigError, AuthError, NetworkError

try:
    config = AppConfig.load()
except ConfigError as e:
    # Configuration problem (exit code 5)
    handle_config_error(e)
except AuthError as e:
    # Authentication failure (exit code 3)
    handle_auth_error(e)
except NetworkError as e:
    # Network connectivity (exit code 4)
    handle_network_error(e)
```
→ See [Public API Reference - Exception Hierarchy](0109-1700_PUBLIC_API_REFERENCE.md#exception-hierarchy)
→ See [CLI Reference - Exit Codes](0109-1500_CLI_REFERENCE.md#exit-codes)

---

### Task: Safe Email Deletion

**Via CLI** (always preview first):
```bash
# Preview what would be deleted
gmail-assistant delete --query "from:newsletter@example.com" --dry-run

# Actually delete after review
gmail-assistant delete --query "from:newsletter@example.com"
```
→ See [CLI Reference - delete command](0109-1500_CLI_REFERENCE.md#delete)

---

### Task: Override Configuration Paths

**Via Environment Variables**:
```bash
export GMAIL_ASSISTANT_CONFIG_DIR=/etc/gmail-assistant
export GMAIL_ASSISTANT_BACKUP_DIR=/mnt/external/backups
export GMAIL_ASSISTANT_CREDENTIALS_DIR=/root/.secure/gmail

gmail-assistant fetch
```
→ See [Constants Reference - Environment Variable Overrides](0109-1800_CONSTANTS_REFERENCE.md#environment-variable-overrides)

---

### Task: Understand Configuration Resolution

Priority order (highest to lowest):
1. CLI argument: `--config /path/to/config.json`
2. Environment: `gmail_assistant_CONFIG=/path/to/config.json`
3. Project: `./gmail-assistant.json`
4. User: `~/.gmail-assistant/config.json`
5. Defaults: All in `~/.gmail-assistant/`

→ See [Configuration Reference - Configuration Resolution](0109-1600_CONFIGURATION_REFERENCE.md#configuration-resolution)
→ See [CLI Reference - Configuration Resolution](0109-1500_CLI_REFERENCE.md#configuration-resolution)

---

## API Specifications

### Gmail Search Query Syntax

Supported operators for `--query` / `search_messages()`:

| Operator | Example | Purpose |
|----------|---------|---------|
| `is:unread` | `is:unread` | Unread emails |
| `is:starred` | `is:starred` | Starred emails |
| `from:` | `from:example.com` | From sender/domain |
| `subject:` | `subject:AI` | Keywords in subject |
| `after:` | `after:2025/01/01` | After date |
| `before:` | `before:2025/02/01` | Before date |
| `has:attachment` | `has:attachment` | Has attachments |
| `larger:` | `larger:10M` | Larger than size |

→ See [CLI Reference - Examples](0109-1500_CLI_REFERENCE.md#examples)

---

### Output Formats

Supported formats for `--format`:

| Format | Extension | Purpose |
|--------|-----------|---------|
| `eml` | `.eml` | Email message format (RFC 5322) |
| `markdown` | `.md` | Human-readable markdown |
| `json` | `.json` | JSON serialization |
| `both` | `.eml`, `.md` | Both EML and Markdown |

→ See [Constants Reference - SUPPORTED_OUTPUT_FORMATS](0109-1800_CONSTANTS_REFERENCE.md#supported_output_formats)

---

### File Organization Types

Supported organization for `--organize`:

| Type | Structure | Example |
|------|-----------|---------|
| `date` | `{year}/{month}/{day}/` | `2025/01/15/email.eml` |
| `sender` | `{domain}/` | `example.com/email.eml` |
| `none` | Flat directory | `email.eml` |

→ See [Constants Reference - SUPPORTED_ORGANIZATION_TYPES](0109-1800_CONSTANTS_REFERENCE.md#supported_organization_types)

---

## Parameter Validation Reference

### max_emails

**Type**: Integer
**Valid Range**: 1 - 50000
**Default**: 1000
**Validation Error**: ConfigError (exit code 5)

```python
if not 1 <= max_emails <= 50000:
    raise ConfigError(f"max_emails must be 1-50000, got {max_emails}")
```

### rate_limit_per_second

**Type**: Float
**Valid Range**: 0.1 - 100.0
**Default**: 10.0
**Conservative**: 8.0
**Maximum**: 100.0

```python
if not 0.1 <= rate_limit_per_second <= 100:
    raise ConfigError(f"rate_limit_per_second must be 0.1-100, got {rate_limit_per_second}")
```

### log_level

**Type**: String (uppercase)
**Valid Values**: DEBUG, INFO, WARNING, ERROR, CRITICAL
**Default**: INFO

```python
if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    raise ConfigError(f"log_level must be one of {{'DEBUG', 'INFO', ...}}")
```

---

## Security Reference

### Credential Storage

**Modern (Secure)**: OS Keyring
- Linux: `~/.local/share/keyring/` or secret-service
- macOS: Keychain
- Windows: Credential Manager
- Service: `gmail_assistant`
- Username: `oauth_credentials`

**Legacy (Deprecated)**: Plaintext `token.json`
- Security risk if in version control
- Still supported for backward compatibility
- Automatic migration notice on startup

→ See [Constants Reference - Keyring Configuration](0109-1800_CONSTANTS_REFERENCE.md#keyring-configuration)

### Credentials in Git Repository

**Protection**: Automatic detection via `git rev-parse --show-toplevel`

**Behavior**:
- Default: Prevents credentials inside git repos
- Override: `--allow-repo-credentials` flag (not recommended)
- Fallback: If git not in PATH, checks skipped (warning logged)

→ See [Configuration Reference - Security Validation](0109-1600_CONFIGURATION_REFERENCE.md#security-validation)
→ See [CLI Reference - allow-repo-credentials](0109-1500_CLI_REFERENCE.md#--allow-repo-credentials)

---

## Support Matrix

| Feature | CLI | Python API | Config File |
|---------|-----|-----------|-------------|
| Fetch emails | ✓ | ✓ | ✓ |
| Delete emails | ✓ (stub) | ✓ | ✓ |
| Analyze emails | ✓ (stub) | ✓ | ✓ |
| Custom queries | ✓ | ✓ | ✓ |
| Rate limiting | ✓ | ✓ | ✓ |
| Auth setup | ✓ (stub) | ✓ | ✓ |
| Config management | ✓ | ✓ | ✓ |

---

## Version Information

**Current Version**: 2.0.0
**Python Support**: 3.10, 3.11, 3.12, 3.13
**Status**: Production
**Stability**: Stable API, some features deferred to v2.1.0

### Deferred Features (v2.1.0)

- Functional `fetch` implementation
- Functional `delete` implementation
- Functional `analyze` implementation
- Functional `auth` implementation
- Email sending functionality

---

## Document Maintenance

**Last Updated**: 2026-01-09
**Reviewed**: 2026-01-09
**Next Review**: Quarterly or as needed
**Maintainer**: Gmail Assistant Development Team

### Document Quality Checklist

- [x] All CLI commands documented with parameters
- [x] All configuration parameters with validation rules
- [x] All public APIs with signatures and examples
- [x] All constants with environment overrides
- [x] Exit codes and error handling
- [x] Security considerations documented
- [x] Cross-references between documents
- [x] Code examples for common tasks
- [x] Parameter validation rules
- [x] Configuration resolution order

---

## See Also

- **README.md** - Project overview and quick start
- **CHANGELOG.md** - Version history and changes
- **LICENSE** - MIT License
- **GitHub Issues** - Bug reports and feature requests

