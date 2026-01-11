# Gmail Assistant CLI Reference

Complete command-line interface documentation for gmail-assistant version 2.0.0.

**Version**: 2.0.0
**Status**: Production
**Last Updated**: 2026-01-09

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Entry Point](#entry-point)
3. [Global Options](#global-options)
4. [Commands](#commands)
5. [Exit Codes](#exit-codes)
6. [Configuration Resolution](#configuration-resolution)
7. [Examples](#examples)

---

## Quick Reference

```bash
# Authenticate with Gmail
gmail-assistant auth

# Fetch emails with query
gmail-assistant fetch --query "is:unread" --max-emails 100

# Delete emails (dry-run safe)
gmail-assistant delete --query "subject:test" --dry-run

# Analyze fetched emails
gmail-assistant analyze --input-dir ./backups --report summary

# Manage configuration
gmail-assistant config --init
gmail-assistant config --show
gmail-assistant config --validate
```

---

## Entry Point

**Module**: `gmail_assistant.cli.main:main`
**Package Script**: `gmail-assistant`
**Pyproject.toml Reference**:
```toml
[project.scripts]
gmail-assistant = "gmail_assistant.cli.main:main"
```

### Overview

The `main` command establishes a Click command group with global options and context management. All subcommands inherit these global options.

```python
@click.group()
@click.version_option(version=__version__, prog_name="gmail-assistant")
@click.option(...)
@click.pass_context
def main(ctx: click.Context, config: Path | None, allow_repo_credentials: bool) -> None:
    """Gmail Assistant - Backup, analyze, and manage your Gmail."""
```

---

## Global Options

These options apply to ALL subcommands and must appear BEFORE the subcommand name.

### --config / -c

**Type**: File path
**Required**: No
**Default**: None (uses resolution order)
**Exists Check**: Yes (file must exist)

Path to configuration file. If provided, overrides all other config resolution sources.

```bash
gmail-assistant --config /path/to/config.json fetch --query "is:unread"
```

### --allow-repo-credentials

**Type**: Boolean flag
**Required**: No
**Default**: False

Allow credentials to be stored inside a git repository. By default, credentials inside git repos trigger an error for security. This flag suppresses that check and allows credentials anywhere.

```bash
gmail-assistant --allow-repo-credentials fetch --query "is:unread"
```

### --version / -v

**Type**: Boolean flag
**Required**: No
**Default**: False

Display version information and exit.

```bash
gmail-assistant --version
# Output: gmail-assistant, version 2.0.0
```

---

## Commands

### auth

**Purpose**: Authenticate with Gmail API
**Status**: Stub implementation (v2.1.0 functional)

#### Usage

```bash
gmail-assistant auth
```

#### Behavior

- Loads configuration using global config resolution
- Validates credentials path and token path from config
- Initiates OAuth flow
- **Current Implementation**: Info message; actual OAuth deferred to v2.1.0

#### Options

None (uses global options only)

#### Example

```bash
gmail-assistant --config ~/.gmail-assistant/config.json auth
```

#### Related

- `config --init` - Create default configuration first
- [Configuration Resolution](#configuration-resolution)

---

### fetch

**Purpose**: Fetch emails from Gmail
**Status**: Stub implementation (v2.1.0 functional)

#### Usage

```bash
gmail-assistant fetch [OPTIONS]
```

#### Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--query` | `-q` | String | No | "" | Gmail search query |
| `--max-emails` | `-m` | Integer | No | None | Maximum emails to fetch (uses config default if omitted) |
| `--output-dir` | `-o` | Path | No | None | Output directory (uses config default if omitted) |
| `--format` | None | Choice | No | "json" | Output format: json, mbox, eml |

#### Parameters Detail

##### --query / -q

Gmail search query string. Supports all Gmail search operators:
- `is:unread` - Unread emails
- `from:example.com` - Emails from domain
- `subject:AI` - Emails with keyword in subject
- `after:2025/01/01` - Date ranges
- Combined: `is:unread after:2025/01/01`

If empty string or omitted, fetches all emails.

##### --max-emails / -m

Maximum number of emails to fetch. Overrides configuration file value if provided.

**Valid Range**: Integers (no explicit limit enforced at CLI level)
**Config Validation**: 1-50000 (enforced in AppConfig)

If not provided, uses:
1. Config file value (from `max_emails`)
2. Built-in default: 1000

##### --output-dir / -o

Directory where fetched emails are saved. Overrides configuration file value.

Path must be valid (created if not exists). Supports both absolute and relative paths.

If not provided, uses:
1. Config file value (from `output_dir`)
2. Built-in default: `~/.gmail-assistant/backups`

##### --format

Output format choice:

| Format | Description |
|--------|-------------|
| `json` | JSON serialized emails |
| `mbox` | MBOX format (mailbox) |
| `eml` | EML format (individual email files) |

#### Example

```bash
# Fetch unread emails (up to 1000)
gmail-assistant fetch --query "is:unread"

# Fetch with explicit limits
gmail-assistant fetch \
  --query "after:2025/01/01 before:2025/02/01" \
  --max-emails 500 \
  --output-dir ./january_backup \
  --format eml

# Using config, with query override
gmail-assistant --config config.json fetch --query "subject:important"
```

#### Behavior

1. Load configuration (respecting global --config option)
2. Determine effective parameters (CLI > config > defaults)
3. Log operation parameters
4. Execute fetch (deferred to v2.1.0)

#### Related

- [Configuration Reference](0109-1600_CONFIGURATION_REFERENCE.md)
- `analyze` - Analyze fetched emails

---

### delete

**Purpose**: Delete emails matching query
**Status**: Stub implementation (v2.1.0 functional)
**Safety**: Supports dry-run and confirmation prompts

#### Usage

```bash
gmail-assistant delete [OPTIONS]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--query` | String | Yes | N/A | Gmail search query |
| `--dry-run` | Boolean | No | False | Show what would delete without deleting |
| `--confirm` | Boolean | No | False | Skip confirmation prompt |

#### Parameters Detail

##### --query

**Required**: Yes

Gmail search query identifying emails to delete. Uses same syntax as fetch command.

**Warning**: This PERMANENTLY deletes emails from Gmail. They cannot be recovered (unless moved to trash first).

#### --dry-run

**Type**: Flag
**Default**: False

Preview which emails would be deleted without actually deleting them. Recommended to always use this first.

```bash
# Preview deletion
gmail-assistant delete --query "from:newsletter@example.com" --dry-run

# Actually delete after reviewing
gmail-assistant delete --query "from:newsletter@example.com"
```

#### --confirm

**Type**: Flag
**Default**: False

Skip the confirmation prompt. Combined with --dry-run=False, this allows destructive operations without prompting (use with caution).

#### Example

```bash
# Safe: preview what would be deleted
gmail-assistant delete \
  --query "subject:newsletter older_than:6m" \
  --dry-run

# Destructive: delete after confirming prompt
gmail-assistant delete \
  --query "category:promotions older_than:1y"

# Destructive without prompt (dangerous!)
gmail-assistant delete \
  --query "from:test@example.com" \
  --confirm
```

#### Behavior

1. Load configuration
2. Parse delete query
3. Log operation details
4. Execute delete (deferred to v2.1.0)

#### Related

- Gmail search query syntax documentation
- `fetch` - Fetch instead of delete

---

### analyze

**Purpose**: Analyze fetched emails
**Status**: Stub implementation (v2.1.0 functional)

#### Usage

```bash
gmail-assistant analyze [OPTIONS]
```

#### Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--input-dir` | `-i` | Path | No | None | Directory with fetched emails (uses config output_dir if omitted) |
| `--report` | `-r` | Choice | No | "summary" | Report type: summary, detailed, json |

#### Parameters Detail

##### --input-dir / -i

Directory containing email files to analyze. Must exist if provided.

If not provided, uses `config.output_dir`.

##### --report / -r

Report generation format:

| Type | Description |
|------|-------------|
| `summary` | High-level statistics and counts |
| `detailed` | Detailed analysis with breakdowns |
| `json` | Structured JSON output |

#### Example

```bash
# Analyze with defaults (from config)
gmail-assistant analyze

# Analyze specific directory
gmail-assistant analyze --input-dir ./backups --report detailed

# Generate JSON report
gmail-assistant analyze --input-dir ./march_backup --report json
```

#### Behavior

1. Load configuration
2. Resolve input directory
3. Log analysis parameters
4. Execute analysis (deferred to v2.1.0)

#### Related

- `fetch` - Fetch emails to analyze

---

### config

**Purpose**: Manage application configuration
**Status**: Functional (display, init, validate)

#### Usage

```bash
gmail-assistant config [OPTIONS]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--show` | Boolean | No | False | Display current configuration |
| `--validate` | Boolean | No | False | Validate configuration file |
| `--init` | Boolean | No | False | Create default configuration |

#### Behavior

##### --show

Display all configuration values from loaded config file (or defaults).

**Output Format**:
```
credentials_path: /home/user/.gmail-assistant/credentials.json
token_path: /home/user/.gmail-assistant/token.json
output_dir: /home/user/.gmail-assistant/backups
max_emails: 1000
rate_limit_per_second: 10.0
log_level: INFO
```

**Exit Code**: 0 (success)

#### --validate

Validate configuration file syntax and values.

**Success Output**:
```
Configuration valid.
```

**Failure Output**:
```
Configuration invalid: [error message]
```

**Exit Code**: 0 (valid) or 5 (invalid)

#### --init

Create default configuration file in user home directory.

**Target Location**: `~/.gmail-assistant/config.json`

**Contents**:
```json
{
  "credentials_path": "/home/user/.gmail-assistant/credentials.json",
  "token_path": "/home/user/.gmail-assistant/token.json",
  "output_dir": "/home/user/.gmail-assistant/backups",
  "max_emails": 1000,
  "rate_limit_per_second": 10.0,
  "log_level": "INFO"
}
```

**Behavior**:
- Creates `~/.gmail-assistant/` directory if missing
- Fails if config.json already exists (exit code 5)
- Creates file with write permissions for user only

#### Example

```bash
# Initialize default config
gmail-assistant config --init

# Verify it was created
gmail-assistant config --show

# Validate it
gmail-assistant config --validate

# View from custom location
gmail-assistant --config /etc/gmail-assistant/config.json config --show
```

#### Related

- [Configuration Reference](0109-1600_CONFIGURATION_REFERENCE.md)

---

## Exit Codes

All commands follow this exit code scheme:

| Exit Code | Meaning | Typical Causes |
|-----------|---------|----------------|
| 0 | Success | Operation completed successfully |
| 1 | General Error | Unexpected exceptions, API errors |
| 2 | Usage Error | Invalid arguments, Click-level errors |
| 3 | Authentication Error | OAuth failure, credential issues, missing credentials.json |
| 4 | Network Error | Connection failures, timeout, Gmail API unreachable |
| 5 | Configuration Error | Invalid config file, missing required keys, validation failures |

### Exit Code Implementation

```python
# Error hierarchy mapping:
ConfigError           → exit 5
AuthError             → exit 3
NetworkError          → exit 4
GmailAssistantError   → exit 1
Unexpected Exception  → exit 1
ClickException        → Handled by Click (usually 2)
```

---

## Configuration Resolution

Configuration is resolved using this priority order (highest to lowest):

1. **CLI Argument**: `--config /path/to/config.json`
2. **Environment Variable**: `gmail_assistant_CONFIG=/path/to/config.json`
3. **Project Config**: `./gmail-assistant.json` (current directory)
4. **User Config**: `~/.gmail-assistant/config.json`
5. **Built-in Defaults**: Secure defaults in user home directory

### Resolution Details

#### Priority 1: CLI Argument

```bash
gmail-assistant --config /etc/gmail-assistant/config.json fetch
```

- Must point to existing file
- Overrides all other sources
- Path is resolved to absolute path

#### Priority 2: Environment Variable

```bash
export gmail_assistant_CONFIG=/custom/config.json
gmail-assistant fetch
```

- Must point to existing file
- Overridden by CLI argument

#### Priority 3: Project Config

File: `gmail-assistant.json` in current working directory

```bash
cd /my/project
gmail-assistant fetch  # Uses ./gmail-assistant.json if exists
```

- Useful for per-project configuration
- Overridden by environment variable or CLI argument

#### Priority 4: User Config

File: `~/.gmail-assistant/config.json`

- Per-user configuration
- Persistent across sessions
- Created by `config --init` command

#### Priority 5: Built-in Defaults

If no config file found:
- credentials_path: `~/.gmail-assistant/credentials.json`
- token_path: `~/.gmail-assistant/token.json`
- output_dir: `~/.gmail-assistant/backups`
- max_emails: 1000
- rate_limit_per_second: 10.0
- log_level: INFO

### Security Considerations

#### Repo Credential Protection

If config is in a git repository, credentials path checking:
- Detects if credentials are inside git repo (using `git rev-parse --show-toplevel`)
- Requires `--allow-repo-credentials` flag to allow repo-local credentials
- Otherwise fails with ConfigError

Credentials should be in `~/.gmail-assistant/` (outside any repo).

#### Git Detection

- If git not installed or not in PATH: Warning logged, checks skipped
- If git available: Checks enforce credential location safety
- Timeout protection: 5-second timeout on git command

---

## Examples

### Basic Workflow

```bash
# 1. Initialize configuration
gmail-assistant config --init

# 2. Display configuration
gmail-assistant config --show

# 3. Authenticate
gmail-assistant auth

# 4. Fetch unread emails
gmail-assistant fetch --query "is:unread" --max-emails 500

# 5. Analyze
gmail-assistant analyze --report summary
```

### Advanced Queries

```bash
# Time-based
gmail-assistant fetch --query "after:2025/01/01 before:2025/02/01"

# Subject keywords
gmail-assistant fetch --query "subject:(AI OR machine learning)"

# From domain
gmail-assistant fetch --query "from:news@example.com"

# Combined
gmail-assistant fetch --query 'is:unread from:work.com after:2025/01/01'

# With attachments
gmail-assistant fetch --query "has:attachment larger:5M"
```

### Deletion Workflows

```bash
# 1. Preview what would be deleted
gmail-assistant delete --query "from:newsletter@example.com" --dry-run

# 2. Review the output carefully

# 3. Actually delete
gmail-assistant delete --query "from:newsletter@example.com"

# 4. Delete old promotions
gmail-assistant delete --query "category:promotions older_than:6m"
```

### Configuration Management

```bash
# Use custom config
gmail-assistant --config ~/.work/config.json fetch --query "is:unread"

# Override via environment
export gmail_assistant_CONFIG=/etc/gmail-assistant/config.json
gmail-assistant config --show

# Per-project config
cd ~/project
echo '{"output_dir": "./backups"}' > gmail-assistant.json
gmail-assistant fetch --query "is:unread"
```

### Error Handling

```bash
# Auth error (exit 3)
gmail-assistant auth  # credentials.json not found

# Config error (exit 5)
gmail-assistant --config /nonexistent/config.json fetch

# Network error (exit 4)
gmail-assistant fetch  # Gmail API unreachable

# Success (exit 0)
gmail-assistant fetch --query "is:unread"
```

---

## See Also

- [Configuration Reference](0109-1600_CONFIGURATION_REFERENCE.md) - Detailed config file schema
- [Public API Reference](0109-1700_PUBLIC_API_REFERENCE.md) - Python API for programmatic use
- [Constants Reference](0109-1800_CONSTANTS_REFERENCE.md) - Built-in constants and scopes

