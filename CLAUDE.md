# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL PROJECT GOVERNANCE RULES

**These rules MUST be followed at all times and override any default behaviors:**

### 1. Resource Discovery Protocol
- **ALWAYS check for existing resources before creating new files or functions**
- Use `Glob`, `Grep`, or `Read` tools to search for similar functionality
- Check relevant directories (`src/`, `tests/`, `docs/`, `scripts/`) for existing patterns
- If similar functionality exists, extend or modify existing code rather than duplicate

### 2. File Organization Requirements
- **NO files in root directory** - every file must be organized in appropriate folders
- **Project Structure**:
  - Source code: `src/` (organized by feature: `core/`, `parsers/`, `analysis/`, etc.)
  - Tests: `tests/` (ALL test-related scripts and files)
  - Documentation: `docs/`
  - Configuration: `config/`
  - Utilities: `scripts/` or `tools/`
  - Examples: `examples/`
  - Data/Logs: `data/`, `logs/`, `backups/`

### 3. Test File Placement
- **ALL test-related scripts must be inside the `tests/` folder**
- No exceptions: unit tests, integration tests, test data, test utilities
- Follow naming pattern: `test_*.py` for test files
- Test documentation goes in `tests/docs/` if needed

### 4. Documentation Naming Convention
- **ALL documentation files (docs, txt, md, json, etc.) must use timestamped naming**
- **Format**: `<mmdd-hhmm_name.extension>`
- **Examples**:
  - `0922-0238_implementation_plan.md` (NOT `implementation_plan.md`)
  - `0922-1430_api_design.json` (NOT `api_design.json`)
  - `0922-0945_test_results.txt` (NOT `test_results.txt`)
- This applies to ALL documentation created in `docs/`, `tests/docs/`, or any subdirectory

### 5. Validation Checklist
Before creating any file, Claude must:
- [ ] Search for existing similar functionality
- [ ] Identify the correct directory based on file purpose
- [ ] Apply timestamped naming for documentation files
- [ ] Verify placement follows project structure rules
- [ ] Confirm no files are being created in root directory

### 6. Governance Resources
- **Detailed Rules**: `config/0922-0238_project_governance.json`
- **Quick Reference**: `docs/reference/governance-quick-reference.md`
- **Enforcement**: These rules are mandatory and override any default behaviors

## Project Overview

Gmail Assistant is a Python tool for downloading, backing up, analyzing, and managing Gmail emails. The tool uses the Gmail API for authentication and email operations.

## Implementation Status (v2.0.0)

**Current Version**: 2.0.0

The v2.0.0 release restructured the project with a new Click-based CLI and src-layout package structure.

| Feature | Status | Notes |
|---------|--------|-------|
| Package structure | ✅ Complete | `src/gmail_assistant/` layout |
| CLI framework | ✅ Complete | Click-based with subcommands |
| CLI `fetch` command | ⚠️ Stub | Functional implementation v2.1.0 |
| CLI `delete` command | ⚠️ Stub | Functional implementation v2.1.0 |
| CLI `analyze` command | ⚠️ Stub | Functional implementation v2.1.0 |
| CLI `auth` command | ⚠️ Stub | Functional implementation v2.1.0 |
| CLI `config` command | ✅ Partial | `--init`, `--show`, `--validate` work |
| Core `GmailFetcher` class | ✅ Complete | Direct usage available |
| Parsers | ✅ Complete | Direct module usage available |
| Configuration | ✅ Complete | `~/.gmail-assistant/` defaults |

For full functionality before v2.1.0, use direct module imports:
```python
from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher
from gmail_assistant.core.config import AppConfig
```

## Core Architecture

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

### Configuration Files

- **`config/gmail_assistant_config.json`**: Main fetcher configuration
  - Predefined search queries (newsletters, AI content, services)
  - Default output settings (max emails, format, organization)
  - Cleanup suggestions for Gmail management

- **`config/config.json`**: AI newsletter detection configuration
  - AI keywords and newsletter domain patterns
  - Confidence scoring weights and decision thresholds
  - Pattern matching rules for newsletter identification

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

### Utility Scripts

- **`examples/example_usage.py`**: Demonstration script with sample data generation
- **`examples/samples.py`**: Pre-built backup scenarios for common use cases
- **`scripts/backup/move_backup_years.ps1`**: PowerShell script for merging backup folders by year
- **`scripts/backup/dedupe_merge.ps1`**: PowerShell script for deduplicating emails across backup folders
- **`scripts/setup/quick_start.bat`** & **`scripts/setup/quick_start.ps1`**: Cross-platform setup and run scripts

## Essential Commands

### Setup and Authentication
```bash
# Install package (editable mode recommended)
pip install -e .

# Install with all optional dependencies
pip install -e ".[all]"

# Install with development dependencies
pip install -e ".[dev]"

# First-time authentication
gmail-assistant auth
```

### Basic Operations (v2.0.0 CLI)

**Note**: The following CLI commands are stub implementations in v2.0.0. Functional implementations are planned for v2.1.0.

```bash
# Fetch unread emails
gmail-assistant fetch --query "is:unread" --max-emails 1000

# Fetch by date range
gmail-assistant fetch --query "after:2025/02/28 before:2025/04/01" --max-emails 500

# Fetch with specific format
gmail-assistant fetch --query "is:unread" --format json --output-dir ./backups

# Delete emails (dry run first)
gmail-assistant delete --query "from:spam@example.com" --dry-run

# Manage configuration
gmail-assistant config --show
gmail-assistant config --init
gmail-assistant config --validate
```

### Direct Module Usage (Immediately Functional)

For immediate functionality before v2.1.0 CLI completion:

```python
from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

fetcher = GmailFetcher('credentials.json')
fetcher.authenticate()
print(fetcher.get_profile())
```

### Quick Start Scripts
```bash
# Windows batch script with interactive menu
scripts\setup\quick_start.bat

# PowerShell script with interactive menu (Windows/Linux)
.\scripts\setup\quick_start.ps1
```

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

### Backup Management
```powershell
# Merge backup folders by year (PowerShell)
.\scripts\backup\move_backup_years.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -DryRun

# Deduplicate emails across backup folders
.\scripts\backup\dedupe_merge.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -Prefer larger -DryRun
```

## Key Configuration

### Command Line Arguments
- `--query`: Gmail search query (supports all Gmail search operators)
- `--max`: Maximum number of emails to download
- `--output`: Output directory name
- `--format`: Output format (`eml`, `markdown`, or `both`)
- `--organize`: File organization (`date`, `sender`, or `none`)

### Gmail API Setup Requirements
- Google Cloud Console project with Gmail API enabled
- OAuth 2.0 credentials saved as `credentials.json`
- First run generates `token.json` for subsequent authentications

## File Organization Patterns

### By Date (default)
```
gmail_backup/
├── 2025/
│   ├── 03/
│   │   ├── 2025-03-31_120000_subject_messageid.eml
│   │   └── 2025-03-31_120000_subject_messageid.md
```

### By Sender
```
gmail_backup/
├── sender_name/
│   ├── 2025-03-31_120000_subject_messageid.eml
│   └── 2025-03-31_120000_subject_messageid.md
```

## Output Formats

- **EML**: Native email format preserving all headers and formatting, compatible with email clients
- **Markdown**: Human-readable format with metadata table and HTML-to-markdown conversion

## Common Query Patterns

The tool supports all Gmail search operators:
- Time: `after:2025/01/01`, `before:2025/04/01`, `newer_than:6m`
- Content: `subject:AI`, `from:example.com`, `has:attachment`
- Status: `is:unread`, `is:important`, `is:starred`
- Categories: `category:updates`, `category:promotions`
- Size: `larger:10M`, `smaller:1M`

## Development Notes

### Error Handling
- Base64 decoding with padding correction for Gmail API responses
- Unicode handling for email content with encoding issues
- Gmail API rate limiting awareness
- Filename sanitization for filesystem compatibility

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

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=gmail_assistant --cov-report=html

# Run linting
ruff check src/

# Run type checking
mypy src/gmail_assistant
```

## Advanced Workflows

### AI Newsletter Management
1. **Export email data** from Gmail or use existing backup
2. **Analyze newsletters** with `python -m gmail_assistant.core.ai.newsletter_cleaner` (dry-run first)
3. **Review detection log** to verify accuracy
4. **Delete AI newsletters** using `--delete` flag

### Professional Email Archive Creation
1. **Download emails** using `GmailFetcher` class directly
2. **Convert to clean Markdown** with `python -m gmail_assistant.parsers.gmail_eml_to_markdown_cleaner`
3. **Apply advanced parsing** using `python -m gmail_assistant.parsers.advanced_email_parser` for complex content
4. **Organize and deduplicate** using PowerShell management scripts in `scripts/backup/`

### Multi-Backup Management
1. **Create separate backups** for different time periods or criteria
2. **Merge backups** using `scripts/backup/move_backup_years.ps1`
3. **Deduplicate emails** using `scripts/backup/dedupe_merge.ps1` with conflict resolution
4. **Clean and format** using EML to Markdown converter for consistency

### Content Analysis Pipeline
1. **Fetch emails** with specific queries using `GmailFetcher` class
2. **Parse with multiple strategies** using `advanced_email_parser` module
3. **Convert to structured format** with metadata preservation
4. **Analyze patterns** for automated classification and management

## Technical Reference

For comprehensive documentation, see:
- `docs/README.md` - Documentation index
- `docs/architecture/overview.md` - System architecture
- `docs/architecture/component-deep-dive.md` - Component details
- `docs/user-guide/cli-reference.md` - CLI command reference
- `docs/api/public-api-reference.md` - Public API reference
- `docs/architecture/diagrams.md` - Architecture diagrams