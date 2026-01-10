# CLAUDE.md Update Recommendations

**Generated**: 2026-01-09 23:10
**Reference**: `docs/0109-2310_documentation_audit_report.md`
**Priority**: P0 (Critical)

---

## Summary of Required Changes

CLAUDE.md requires significant updates to reflect the v2.0.0 restructuring. This document provides specific, actionable changes with before/after examples.

---

## Change 1: Update Core Architecture - Main Components

**Location**: Lines 60-74

**CURRENT (OUTDATED)**:
```markdown
### Main Components

- **`gmail_assistant.py`**: Main application with `GmailFetcher` class containing all core functionality
  - Authentication with Google OAuth 2.0
  - Email search using Gmail API queries
  - Email content extraction (plain text and HTML)
  - File creation in EML and Markdown formats
  - Organization by date or sender

- **`samples.py`**: Pre-built scenarios for common use cases
```

**RECOMMENDED**:
```markdown
### Main Components

- **`src/gmail_assistant/cli/main.py`**: Click-based CLI entry point with subcommands
  - `fetch`: Download emails from Gmail
  - `delete`: Delete emails matching query
  - `analyze`: Analyze fetched emails
  - `auth`: Authenticate with Gmail API
  - `config`: Manage configuration
  - **Note**: CLI commands are stub implementations; functional logic deferred to v2.1.0

- **`src/gmail_assistant/core/fetch/gmail_assistant.py`**: Core `GmailFetcher` class
  - Authentication with Google OAuth 2.0 via `ReadOnlyGmailAuth`
  - Email search using Gmail API queries
  - Email content extraction (plain text and HTML)
  - File creation in EML and Markdown formats
  - Organization by date or sender
  - Memory management and streaming support

- **`examples/samples.py`**: Pre-built scenarios for common use cases
  - Unread email backup
  - Newsletter archiving by sender
  - Service notification backup
  - Time-based backups
  - AI content analysis
```

**JUSTIFICATION**: Reflects actual package structure and clarifies CLI status.

---

## Change 2: Update Advanced Processing Tools Section

**Location**: Lines 88-112

**CURRENT (OUTDATED)**:
```markdown
### Advanced Processing Tools

- **`advanced_email_parser.py`**: Multi-strategy email content parsing
- **`gmail_eml_to_markdown_cleaner.py`**: Professional EML to Markdown converter
- **`gmail_ai_newsletter_cleaner.py`**: AI newsletter identification and deletion system
- **`gmail_api_client.py`**: Live Gmail API integration
```

**RECOMMENDED**:
```markdown
### Advanced Processing Tools

- **`src/gmail_assistant/parsers/advanced_email_parser.py`**: Multi-strategy email content parsing with intelligent HTML to Markdown conversion
  - Smart email type detection (newsletter, notification, marketing, simple)
  - Multiple parsing strategies (readability, trafilatura, html2text, markdownify)
  - Newsletter-specific content extraction rules
  - Quality scoring and automatic best-result selection

- **`src/gmail_assistant/parsers/gmail_eml_to_markdown_cleaner.py`**: Professional EML to Markdown converter with front matter
  - Converts .eml files to clean, consistent Markdown format
  - Extracts and preserves email metadata in YAML front matter
  - Handles attachments and inline images (CID references)
  - Configurable content cleaning and formatting rules

- **`src/gmail_assistant/core/ai/newsletter_cleaner.py`**: AI newsletter identification and deletion system
  - Pattern-based detection of AI newsletters using keywords and domains
  - Configurable confidence scoring and thresholds
  - Dry-run mode with detailed logging for safety
  - Support for JSON/CSV email data formats

- **`src/gmail_assistant/core/fetch/gmail_api_client.py`**: Live Gmail API integration for direct inbox operations
  - Real-time email fetching and analysis
  - Batch operations for efficient processing
  - Trash vs permanent deletion options
  - Full API authentication and error handling
```

**JUSTIFICATION**: Corrects all file paths to actual locations.

---

## Change 3: Update Utility Scripts Section

**Location**: Lines 114-119

**CURRENT (OUTDATED)**:
```markdown
### Utility Scripts

- **`example_usage.py`**: Demonstration script with sample data generation
- **`move_backup_years.ps1`**: PowerShell script for merging backup folders by year
- **`dedupe_merge.ps1`**: PowerShell script for deduplicating emails across backup folders
- **`quick_start.bat`** & **`quick_start.ps1`**: Cross-platform setup and run scripts
```

**RECOMMENDED**:
```markdown
### Utility Scripts

- **`examples/example_usage.py`**: Demonstration script with sample data generation
- **`examples/samples.py`**: Pre-built backup scenarios for common use cases
- **`scripts/backup/move_backup_years.ps1`**: PowerShell script for merging backup folders by year
- **`scripts/backup/dedupe_merge.ps1`**: PowerShell script for deduplicating emails across backup folders
- **`scripts/setup/quick_start.bat`** & **`scripts/setup/quick_start.ps1`**: Cross-platform setup and run scripts
```

**JUSTIFICATION**: Corrects all script paths to actual locations.

---

## Change 4: Update Essential Commands Section

**Location**: Lines 121-142

**CURRENT (OUTDATED)**:
```markdown
## Essential Commands

### Setup and Authentication
```bash
# Install dependencies
pip install -r requirements.txt

# First-time authentication (opens browser)
python gmail_assistant.py --auth-only
```

### Basic Operations
```bash
# Download unread emails
python gmail_assistant.py --query "is:unread" --max 1000

# Download by date range
python gmail_assistant.py --query "after:2025/02/28 before:2025/04/01" --max 500

# Download with specific organization
python gmail_assistant.py --query "is:unread" --organize sender --format markdown
```
```

**RECOMMENDED**:
```markdown
## Essential Commands

### Setup and Authentication
```bash
# Install package (editable mode recommended)
pip install -e .

# Install with all optional dependencies
pip install -e ".[all]"

# Install with development dependencies
pip install -e ".[dev]"

# First-time authentication (opens browser)
gmail-assistant auth
```

### Basic Operations (v2.0.0 CLI)

**Note**: The following commands use the new Click-based CLI. Functional implementations are deferred to v2.1.0; current commands display informational messages.

```bash
# Fetch unread emails
gmail-assistant fetch --query "is:unread" --max-emails 1000

# Fetch by date range
gmail-assistant fetch --query "after:2025/02/28 before:2025/04/01" --max-emails 500

# Fetch with specific format
gmail-assistant fetch --query "is:unread" --format json --output-dir ./backups

# Delete emails (dry run first)
gmail-assistant delete --query "from:spam@example.com" --dry-run

# Analyze fetched emails
gmail-assistant analyze --input-dir ./backups --report summary

# Manage configuration
gmail-assistant config --show
gmail-assistant config --init
gmail-assistant config --validate
```

### Legacy Operations (Direct Module Usage)

For immediate functionality before v2.1.0 CLI completion, use direct module execution:

```bash
# Using the core GmailFetcher class directly
python -c "
from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher
fetcher = GmailFetcher()
fetcher.authenticate()
print(fetcher.get_profile())
"
```
```

**JUSTIFICATION**: Updates to v2.0.0 CLI, clarifies implementation status, provides workaround.

---

## Change 5: Update Quick Start Scripts Section

**Location**: Lines 145-151

**CURRENT (OUTDATED)**:
```markdown
### Quick Start Scripts
```bash
# Windows batch script with interactive menu
quick_start.bat

# PowerShell script with interactive menu (Windows/Linux)
.\quick_start.ps1
```
```

**RECOMMENDED**:
```markdown
### Quick Start Scripts
```bash
# Windows batch script with interactive menu
scripts\setup\quick_start.bat

# PowerShell script with interactive menu (Windows/Linux)
.\scripts\setup\quick_start.ps1
```
```

**JUSTIFICATION**: Corrects script paths.

---

## Change 6: Update Sample Scenarios Section

**Location**: Lines 153-163

**CURRENT (OUTDATED)**:
```markdown
### Sample Scenarios
```bash
# List all available scenarios
python samples.py

# Run specific backup scenarios
python samples.py unread
python samples.py newsletters
```
```

**RECOMMENDED**:
```markdown
### Sample Scenarios
```bash
# List all available scenarios
python examples/samples.py

# Run specific backup scenarios
python examples/samples.py unread
python examples/samples.py newsletters
python examples/samples.py services
python examples/samples.py important
```
```

**JUSTIFICATION**: Corrects path to examples directory.

---

## Change 7: Update Advanced Email Processing Section

**Location**: Lines 165-181

**CURRENT (OUTDATED)**:
```markdown
### Advanced Email Processing
```bash
# Advanced HTML to Markdown parsing
python advanced_email_parser.py email_file.html

# Convert EML files to clean Markdown with front matter
python gmail_eml_to_markdown_cleaner.py --base backup_folder --year 2025

# AI newsletter detection and cleanup (dry run)
python gmail_ai_newsletter_cleaner.py email_data.json

# Actually delete AI newsletters
python gmail_ai_newsletter_cleaner.py email_data.json --delete

# Live Gmail API operations
python gmail_api_client.py --credentials credentials.json --max-emails 1000 --dry-run
```
```

**RECOMMENDED**:
```markdown
### Advanced Email Processing
```bash
# Advanced HTML to Markdown parsing
python -m gmail_assistant.parsers.advanced_email_parser email_file.html

# Convert EML files to clean Markdown with front matter
python -m gmail_assistant.parsers.gmail_eml_to_markdown_cleaner --base backup_folder --year 2025

# AI newsletter detection and cleanup (dry run)
python -m gmail_assistant.core.ai.newsletter_cleaner email_data.json

# Actually delete AI newsletters
python -m gmail_assistant.core.ai.newsletter_cleaner email_data.json --delete

# Live Gmail API operations
python -m gmail_assistant.core.fetch.gmail_api_client --credentials credentials.json --max-emails 1000 --dry-run
```

**Note**: Ensure you have run `pip install -e .` first to make the package importable.
```

**JUSTIFICATION**: Uses module invocation pattern for package structure.

---

## Change 8: Update Backup Management Section

**Location**: Lines 183-190

**CURRENT (OUTDATED)**:
```markdown
### Backup Management
```powershell
# Merge backup folders by year (PowerShell)
.\move_backup_years.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -DryRun

# Deduplicate emails across backup folders
.\dedupe_merge.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -Prefer larger -DryRun
```
```

**RECOMMENDED**:
```markdown
### Backup Management
```powershell
# Merge backup folders by year (PowerShell)
.\scripts\backup\move_backup_years.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -DryRun

# Deduplicate emails across backup folders
.\scripts\backup\dedupe_merge.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -Prefer larger -DryRun
```
```

**JUSTIFICATION**: Corrects script paths.

---

## Change 9: Update Dependencies Section

**Location**: Lines 247-261

**CURRENT (OUTDATED)**:
```markdown
### Dependencies

#### Core Dependencies (requirements.txt)
- `google-api-python-client`: Gmail API interaction
- `google-auth-*`: OAuth 2.0 authentication flow
- `html2text`: HTML to Markdown conversion

#### Advanced Processing Dependencies (requirements_advanced.txt)
- `beautifulsoup4`: HTML parsing and cleaning
- `markdownify`: Alternative HTML to Markdown conversion
- `readability-lxml`: Content extraction from HTML (optional)
- `trafilatura`: Advanced content extraction (optional)
- `python-frontmatter`: YAML front matter handling
- `chardet`: Character encoding detection
- `mdformat`: Markdown formatting and normalization
```

**RECOMMENDED**:
```markdown
### Dependencies

Dependencies are managed via `pyproject.toml` with optional dependency groups.

#### Core Dependencies (always installed)
- `click`: CLI framework
- `google-api-python-client`: Gmail API interaction
- `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`: OAuth 2.0 authentication
- `html2text`: HTML to Markdown conversion
- `tenacity`: Retry logic and resilience

#### Optional Dependency Groups (install with `pip install -e ".[group]"`)

| Group | Dependencies | Purpose |
|-------|-------------|---------|
| `analysis` | pandas, numpy, pyarrow | Data analysis |
| `ui` | rich, tqdm | Progress display |
| `advanced-parsing` | beautifulsoup4, markdownify, lxml, python-frontmatter | HTML parsing |
| `content-extraction` | readability-lxml, trafilatura | Content extraction |
| `async` | aiohttp, asyncio-throttle, psutil | Async operations |
| `security` | keyring, regex | Credential storage |
| `network` | requests, urllib3 | HTTP client |
| `all` | All optional dependencies | Full functionality |
| `dev` | pytest, pytest-cov, ruff, mypy, build | Development |

**Installation Examples**:
```bash
pip install -e .                          # Core only
pip install -e ".[all]"                   # All features
pip install -e ".[dev]"                   # Development
pip install -e ".[advanced-parsing,ui]"   # Specific groups
```
```

**JUSTIFICATION**: Reflects actual dependency management via pyproject.toml.

---

## Change 10: Add Implementation Status Notice

**Location**: Add after line 54 (before Core Architecture)

**ADD NEW SECTION**:
```markdown
## Implementation Status (v2.0.0)

**Current Version**: 2.0.0

The v2.0.0 release restructured the project with a new Click-based CLI. The following is the implementation status:

| Feature | Status | Notes |
|---------|--------|-------|
| Package structure | Complete | `src/gmail_assistant/` layout |
| CLI framework | Complete | Click-based with subcommands |
| CLI `fetch` command | **Stub** | Functional implementation v2.1.0 |
| CLI `delete` command | **Stub** | Functional implementation v2.1.0 |
| CLI `analyze` command | **Stub** | Functional implementation v2.1.0 |
| CLI `auth` command | **Stub** | Functional implementation v2.1.0 |
| CLI `config` command | Partial | `--init`, `--show`, `--validate` work |
| Core `GmailFetcher` class | Complete | Direct usage available |
| Parsers | Complete | Direct module usage available |
| Exception hierarchy | Complete | Centralized in `core/exceptions.py` |
| Configuration | Complete | `~/.gmail-assistant/` defaults |

For full functionality before v2.1.0, use direct module imports:
```python
from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher
from gmail_assistant.core.config import AppConfig
```
```

**JUSTIFICATION**: Clearly communicates what is functional vs. planned.

---

## Summary of Line-by-Line Changes

| Section | Line Range | Change Type | Priority |
|---------|------------|-------------|----------|
| Add Implementation Status | After 54 | ADD NEW | P0 |
| Main Components | 60-74 | REWRITE | P0 |
| Advanced Processing Tools | 88-112 | REWRITE | P0 |
| Utility Scripts | 114-119 | UPDATE PATHS | P1 |
| Essential Commands | 121-142 | REWRITE | P0 |
| Quick Start Scripts | 145-151 | UPDATE PATHS | P1 |
| Sample Scenarios | 153-163 | UPDATE PATHS | P1 |
| Advanced Email Processing | 165-181 | REWRITE | P0 |
| Backup Management | 183-190 | UPDATE PATHS | P1 |
| Dependencies | 247-261 | REWRITE | P0 |

---

## Verification Checklist

After applying changes, verify:

- [ ] All file paths reference actual existing files
- [ ] CLI commands use `gmail-assistant` entry point
- [ ] Implementation status is clearly documented
- [ ] Dependency groups match pyproject.toml
- [ ] Script paths include `scripts/` subdirectory
- [ ] No references to `requirements_advanced.txt`
