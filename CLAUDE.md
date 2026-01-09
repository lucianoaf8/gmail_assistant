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
- **Quick Reference**: `docs/0922-0238_governance_quick_reference.md`
- **Enforcement**: These rules are mandatory and override any default behaviors

## Project Overview

Gmail Fetcher is a Python tool for downloading and backing up Gmail emails as EML or Markdown files with organization and search capabilities. The tool uses the Gmail API to authenticate and fetch emails based on search queries.

## Core Architecture

### Main Components

- **`gmail_assistant.py`**: Main application with `GmailFetcher` class containing all core functionality
  - Authentication with Google OAuth 2.0
  - Email search using Gmail API queries
  - Email content extraction (plain text and HTML)
  - File creation in EML and Markdown formats
  - Organization by date or sender

- **`samples.py`**: Pre-built scenarios for common use cases
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

- **`advanced_email_parser.py`**: Multi-strategy email content parsing with intelligent HTML to Markdown conversion
  - Smart email type detection (newsletter, notification, marketing, simple)
  - Multiple parsing strategies (readability, trafilatura, html2text, markdownify)
  - Newsletter-specific content extraction rules
  - Quality scoring and automatic best-result selection

- **`gmail_eml_to_markdown_cleaner.py`**: Professional EML to Markdown converter with front matter
  - Converts .eml files to clean, consistent Markdown format
  - Extracts and preserves email metadata in YAML front matter
  - Handles attachments and inline images (CID references)
  - Configurable content cleaning and formatting rules

- **`gmail_ai_newsletter_cleaner.py`**: AI newsletter identification and deletion system
  - Pattern-based detection of AI newsletters using keywords and domains
  - Configurable confidence scoring and thresholds
  - Dry-run mode with detailed logging for safety
  - Support for JSON/CSV email data formats

- **`gmail_api_client.py`**: Live Gmail API integration for direct inbox operations
  - Real-time email fetching and analysis
  - Batch operations for efficient processing
  - Trash vs permanent deletion options
  - Full API authentication and error handling

### Utility Scripts

- **`example_usage.py`**: Demonstration script with sample data generation
- **`move_backup_years.ps1`**: PowerShell script for merging backup folders by year
- **`dedupe_merge.ps1`**: PowerShell script for deduplicating emails across backup folders
- **`quick_start.bat`** & **`quick_start.ps1`**: Cross-platform setup and run scripts

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

### Quick Start Scripts
```bash
# Windows batch script with interactive menu
quick_start.bat

# PowerShell script with interactive menu (Windows/Linux)
.\quick_start.ps1
```

### Sample Scenarios
```bash
# List all available scenarios
python samples.py

# Run specific backup scenarios
python samples.py unread
python samples.py newsletters
python samples.py services
python samples.py important
```

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

### Backup Management
```powershell
# Merge backup folders by year (PowerShell)
.\move_backup_years.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -DryRun

# Deduplicate emails across backup folders
.\dedupe_merge.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -Prefer larger -DryRun
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

### Testing
Run authentication test:
```bash
python gmail_assistant.py --auth-only
```

This validates the OAuth setup and displays account information without downloading emails.

## Advanced Workflows

### AI Newsletter Management
1. **Export email data** from Gmail or use existing backup
2. **Analyze newsletters** with `gmail_ai_newsletter_cleaner.py` (dry-run first)
3. **Review detection log** to verify accuracy
4. **Delete AI newsletters** using `--delete` flag or `gmail_api_client.py`

### Professional Email Archive Creation
1. **Download emails** using standard `gmail_assistant.py` 
2. **Convert to clean Markdown** with `gmail_eml_to_markdown_cleaner.py`
3. **Apply advanced parsing** using `advanced_email_parser.py` for complex content
4. **Organize and deduplicate** using PowerShell management scripts

### Multi-Backup Management
1. **Create separate backups** for different time periods or criteria
2. **Merge backups** using `move_backup_years.ps1` 
3. **Deduplicate emails** using `dedupe_merge.ps1` with conflict resolution
4. **Clean and format** using EML to Markdown converter for consistency

### Content Analysis Pipeline
1. **Fetch emails** with specific queries (AI content, newsletters, etc.)
2. **Parse with multiple strategies** using `advanced_email_parser.py`
3. **Convert to structured format** with metadata preservation
4. **Analyze patterns** for automated classification and management