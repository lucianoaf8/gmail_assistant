# Gmail Fetcher Suite - Comprehensive Project Documentation

**Document Version**: 1.0
**Created**: 2026-01-08 19:32
**Project Version**: 2.0.0
**Author**: Technical Documentation System

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Feature Inventory](#feature-inventory)
4. [Configuration Reference](#configuration-reference)
5. [CLI Reference](#cli-reference)
6. [API Reference](#api-reference)
7. [Workflow Guides](#workflow-guides)
8. [Integration Patterns](#integration-patterns)
9. [Development Guidelines](#development-guidelines)
10. [Troubleshooting](#troubleshooting)

---

## Executive Summary

### Project Overview

The Gmail Fetcher Suite is a professional Python toolkit for comprehensive Gmail email management, backup, and analysis. It provides enterprise-grade capabilities for:

- **Email Backup**: Download and archive emails in EML and Markdown formats
- **Email Analysis**: Pattern recognition, classification, and insights generation
- **Email Management**: Bulk deletion with safety controls and rate limiting
- **Format Conversion**: Advanced HTML-to-Markdown parsing with multiple strategies

### Key Capabilities

| Capability | Description |
|------------|-------------|
| Gmail API Integration | OAuth 2.0 authentication with read-only and modify scopes |
| Multi-Format Export | EML (native), Markdown (readable), JSON (structured) |
| Intelligent Organization | By date, sender, or flat structure |
| Advanced Parsing | 5 parsing strategies with quality scoring |
| Safe Deletion | Dry-run mode, confirmation gates, rate limiting |
| Email Classification | Automatic categorization (Financial, Notifications, Marketing, etc.) |
| Dependency Injection | Protocol-based architecture with service containers |

### Technology Stack

- **Language**: Python 3.10+
- **Core Dependencies**: google-api-python-client, google-auth, html2text, pandas
- **UI Framework**: Rich (terminal UI with progress bars)
- **Data Processing**: pandas, pyarrow (Parquet support)
- **Optional**: beautifulsoup4, markdownify, readability-lxml, trafilatura

---

## Architecture Overview

### System Architecture Diagram

```
                    +------------------+
                    |     main.py      |
                    |  (Orchestrator)  |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         |                   |                   |
+--------v--------+ +--------v--------+ +--------v--------+
|   CLI Module    | |   Handlers      | |   Analysis      |
| src/cli/*.py    | | src/handlers/*  | | src/analysis/*  |
+-----------------+ +-----------------+ +-----------------+
         |                   |                   |
         +-------------------+-------------------+
                             |
              +-------------+-------------+
              |                           |
    +---------v---------+      +----------v----------+
    |   Core Module     |      |   Parsers Module    |
    |  src/core/*.py    |      |  src/parsers/*.py   |
    +-------------------+      +---------------------+
    | - gmail_assistant   |      | - advanced_parser   |
    | - gmail_api_client|      | - eml_to_markdown   |
    | - credential_mgr  |      | - robust_converter  |
    | - protocols       |      +---------------------+
    | - container (DI)  |
    +-------------------+
              |
    +---------v---------+
    |   Utils Module    |
    |  src/utils/*.py   |
    +-------------------+
    | - rate_limiter    |
    | - cache_manager   |
    | - error_handler   |
    | - memory_manager  |
    | - input_validator |
    +-------------------+
```

### Core Components

#### 1. Core Module (`src/core/`)

| Component | Purpose |
|-----------|---------|
| `gmail_assistant.py` | Main GmailFetcher class for downloading emails |
| `gmail_api_client.py` | Gmail API integration for live operations |
| `gmail_ai_newsletter_cleaner.py` | AI newsletter detection and cleanup |
| `auth_base.py` | OAuth 2.0 authentication handlers |
| `credential_manager.py` | Secure credential storage and management |
| `protocols.py` | Protocol definitions for structural subtyping |
| `container.py` | Dependency injection container |
| `constants.py` | Centralized configuration constants |
| `streaming_fetcher.py` | Memory-efficient streaming fetcher |
| `incremental_fetcher.py` | Incremental backup support |

#### 2. Parsers Module (`src/parsers/`)

| Component | Purpose |
|-----------|---------|
| `advanced_email_parser.py` | Multi-strategy HTML-to-Markdown conversion |
| `gmail_eml_to_markdown_cleaner.py` | EML file to clean Markdown converter |
| `robust_eml_converter.py` | Robust EML parsing with fallbacks |

#### 3. Analysis Module (`src/analysis/`)

| Component | Purpose |
|-----------|---------|
| `email_analyzer.py` | Core analysis engine |
| `daily_email_analysis.py` | Daily analysis pipeline |
| `daily_email_analyzer.py` | Analysis workflow orchestration |
| `email_data_converter.py` | Email data format conversion |
| `setup_email_analysis.py` | Analysis environment setup |

#### 4. Deletion Module (`src/deletion/`)

| Component | Purpose |
|-----------|---------|
| `deleter.py` | GmailDeleter class with batch operations |
| `ui.py` | Rich terminal UI for deletion operations |
| `setup.py` | Module initialization |

#### 5. Utilities Module (`src/utils/`)

| Component | Purpose |
|-----------|---------|
| `rate_limiter.py` | Gmail API rate limiting with exponential backoff |
| `cache_manager.py` | In-memory and disk caching |
| `error_handler.py` | Centralized error handling |
| `memory_manager.py` | Memory tracking and streaming processors |
| `input_validator.py` | Input validation and sanitization |
| `audit_logger.py` | Audit logging for operations |

#### 6. Plugin System (`src/plugins/`)

| Plugin Type | Available Plugins |
|-------------|-------------------|
| Output | `eml.py`, `markdown.py`, `json_output.py` |
| Organization | `by_date.py`, `by_sender.py`, `none.py` |
| Filters | (Extensible) |

### Protocol-Based Architecture

The project uses Python's `typing.Protocol` for structural subtyping, enabling:

- **Duck typing with type safety**
- **Easier testing with mock objects**
- **Clear API contracts**
- **Decoupled components**

Key protocols defined in `src/core/protocols.py`:

```python
# Authentication
CredentialProviderProtocol
GmailClientProtocol

# Operations
EmailFetcherProtocol
StreamingFetcherProtocol
EmailDeleterProtocol

# Parsing
EmailParserProtocol
MarkdownConverterProtocol

# Output
OutputPluginProtocol
OrganizationPluginProtocol

# Infrastructure
CacheProtocol
RateLimiterProtocol
ServiceContainerProtocol
ValidatorProtocol
ErrorHandlerProtocol
```

### Dependency Injection Container

The `ServiceContainer` class provides lightweight dependency injection:

```python
from src.core.container import create_default_container, create_readonly_container

# Create container with default services
container = create_default_container()

# Create container for read-only operations
container = create_readonly_container(credentials_file="credentials.json")

# Register and resolve services
container.register(CacheManager, cache_instance)
cache = container.resolve(CacheManager)
```

---

## Feature Inventory

### Email Fetching

| Feature | Description | Status |
|---------|-------------|--------|
| Query-based search | Full Gmail search syntax support | Active |
| Pagination handling | Automatic multi-page result processing | Active |
| Format selection | EML, Markdown, or both | Active |
| Organization strategies | By date, sender, or flat | Active |
| Skip/limit support | Process specific ranges | Active |
| Auth-only mode | Test authentication without downloading | Active |
| Count-only mode | Count matching emails without download | Active |
| Streaming fetch | Memory-efficient large-scale operations | Active |
| Incremental backup | Only fetch new emails since last backup | Active |

### Email Parsing

| Feature | Description | Status |
|---------|-------------|--------|
| Smart strategy | Auto-detects email type and selects parser | Active |
| Readability parsing | Content extraction using readability-lxml | Optional |
| Trafilatura parsing | Advanced content extraction | Optional |
| HTML2Text parsing | Standard HTML-to-Markdown conversion | Active |
| Markdownify parsing | Alternative Markdown conversion | Active |
| Quality scoring | 0.0-1.0 quality assessment for each parse | Active |
| Newsletter detection | Specialized newsletter content extraction | Active |
| Tracking removal | Removes UTM and tracking parameters | Active |
| URL fixing | Corrects relative and broken URLs | Active |

### Email Deletion

| Feature | Description | Status |
|---------|-------------|--------|
| Dry-run mode | Preview deletions without executing | Active |
| Batch deletion | Efficient batch API calls (up to 1000) | Active |
| Query-based deletion | Delete by Gmail search query | Active |
| Preset queries | Predefined deletion patterns | Active |
| Confirmation gates | Multiple confirmation steps for safety | Active |
| Rate limiting | Respects Gmail API quotas | Active |
| Progress tracking | Rich UI with progress bars | Active |
| Parquet input | Delete based on analysis results | Active |
| Fallback handling | Individual delete on batch failure | Active |

### Email Analysis

| Feature | Description | Status |
|---------|-------------|--------|
| Classification | Financial, Notifications, Marketing, Social, etc. | Active |
| Temporal patterns | Hour/day/month distribution analysis | Active |
| Sender analysis | Top senders, domain analysis | Active |
| Content analysis | Subject patterns, keyword extraction | Active |
| Quality metrics | Data completeness scoring | Active |
| Insights generation | Actionable recommendations | Active |
| Parquet output | Efficient columnar storage | Active |
| Date filtering | Analyze specific date ranges | Active |

### Predefined Scenarios

| Scenario | Query | Purpose |
|----------|-------|---------|
| `unread` | `is:unread` | Backup all unread emails |
| `newsletters` | Newsletter domains | Archive newsletters by sender |
| `services` | Service domains | Backup service notifications |
| `important` | `is:important OR is:starred` | Backup important emails |
| `large` | `larger:10M` | Backup large emails |
| `timeperiod` | Date ranges | Backup specific time periods |
| `ai` | AI keywords | Collect AI-related content |
| `comprehensive` | Monthly batches | Complete backup strategy |
| `cleanup` | Categories | Prepare for inbox cleanup |

---

## Configuration Reference

### OAuth Scopes

| Scope | Constant | Permission Level |
|-------|----------|------------------|
| Read-only | `SCOPES_READONLY` | Fetch and read emails |
| Modify | `SCOPES_MODIFY` | Read, label, and delete emails |
| Full | `SCOPES_FULL` | All operations including sending |

### API Rate Limits

| Setting | Default | Conservative |
|---------|---------|--------------|
| Requests per second | 10.0 | 8.0 |
| Batch size | 100 | 100 |
| Max emails default | 1000 | 1000 |

### Path Configuration

| Path | Default Location |
|------|------------------|
| Project root | `PROJECT_ROOT` |
| Config directory | `config/` |
| Data directory | `data/` |
| Backup directory | `backups/` |
| Cache directory | `~/.gmail_assistant_cache` |

### Classification Rules

The analysis engine uses keyword and pattern-based classification:

| Category | Priority | Example Keywords |
|----------|----------|------------------|
| Financial | 1 | payment, invoice, bill, bank |
| Notifications | 2 | alert, reminder, backup, status |
| Transportation | 3 | ride, trip, uber, taxi |
| Marketing/News | 4 | newsletter, unsubscribe, offer |
| Social | 5 | friend, follow, like, comment |

### Parser Configuration

```json
{
  "strategies": ["smart", "readability", "trafilatura", "html2text", "markdownify"],
  "newsletter_patterns": {
    "domain.com": {
      "content_selectors": [".email-content"],
      "remove_selectors": [".unsubscribe", ".footer"],
      "preserve_images": true
    }
  },
  "cleaning_rules": {
    "remove_tags": ["script", "style", "meta"],
    "preserve_attributes": ["href", "src", "alt"],
    "remove_tracking": true
  },
  "formatting": {
    "max_line_length": 80,
    "add_section_breaks": true
  }
}
```

---

## CLI Reference

### Main Entry Point

```bash
python main.py <command> [options]
```

### Commands Overview

| Command | Description |
|---------|-------------|
| `fetch` | Download emails from Gmail |
| `parse` | Parse and convert email formats |
| `tools` | Utilities and maintenance tools |
| `samples` | Run predefined sample scenarios |
| `analyze` | Analyze email patterns and generate insights |
| `delete` | Delete emails from Gmail |
| `config` | Configuration management |

### Fetch Command

```bash
python main.py fetch --query <query> [options]

Options:
  --query, -q     Gmail search query (required)
  --max, -m       Maximum emails to fetch (default: 1000)
  --output, -o    Output directory (default: gmail_backup)
  --format, -f    Output format: eml|markdown|both (default: both)
  --organize      Organization: date|sender|none (default: date)
  --auth-only     Test authentication only
```

**Examples:**

```bash
# Download unread emails
python main.py fetch --query "is:unread" --max 500

# Download by date range
python main.py fetch --query "after:2025/01/01 before:2025/02/01" --format markdown

# Download from specific sender
python main.py fetch --query "from:example.com" --organize sender
```

### Parse Command

```bash
python main.py parse --input <path> [options]

Options:
  --input         Input directory or file (required)
  --format        Output format: markdown|eml (default: markdown)
  --strategy      Parser strategy: auto|readability|trafilatura|html2text
  --clean         Apply cleaning rules
```

### Delete Command

```bash
python main.py delete <action> [options]

Actions:
  unread          Clean unread emails
  query           Delete by custom query
  preset          Use predefined deletion patterns

Common Options:
  --dry-run       Show what would be deleted (default: True)
  --execute       Actually perform deletion
  --force         Skip confirmation prompts
  --max-delete    Maximum number of emails to delete

Presets:
  old             older_than:1y
  large           larger:10M
  newsletters     is:unread (newsletter OR unsubscribe)
  notifications   is:unread (notification OR alert)
```

**Examples:**

```bash
# Dry run for unread emails
python main.py delete unread --dry-run

# Delete old emails with confirmation
python main.py delete preset old --execute

# Delete by custom query
python main.py delete query --query "from:spam.com older_than:30d" --execute
```

### Analyze Command

```bash
python main.py analyze [options]

Options:
  --input         Email backup directory
  --output        Analysis output file
  --date          Specific date to analyze (YYYY-MM-DD)
  --yesterday     Analyze yesterday's emails
  --days          Number of days to analyze (default: 1)
  --config        Analysis configuration file
  --format        Input format: parquet|auto
```

**Examples:**

```bash
# Analyze yesterday's emails
python main.py analyze --yesterday

# Analyze last 7 days
python main.py analyze --days 7

# Analyze specific date
python main.py analyze --date 2025-01-15
```

### Samples Command

```bash
python main.py samples <scenario> [options]

Scenarios:
  unread          Backup all unread emails
  newsletters     Archive newsletters by sender
  services        Backup service notifications
  important       Backup starred and important emails
  list            List all available scenarios

Options:
  --max           Maximum emails for scenario (default: 1000)
```

### Config Command

```bash
python main.py config [options]

Options:
  --show          Show current configuration
  --setup         Setup initial configuration
```

### Global Options

```bash
python main.py [command] [options]

Global Options:
  -v, --verbose    Enable verbose output
  --debug          Enable debug logging
  --credentials    Path to OAuth credentials file
  --version        Show version number
```

---

## API Reference

### GmailFetcher Class

```python
from src.core.gmail_assistant import GmailFetcher

class GmailFetcher:
    def __init__(self, credentials_file: str = 'credentials.json'):
        """Initialize fetcher with credentials file path."""

    def authenticate(self) -> bool:
        """Authenticate with Gmail API. Returns True on success."""

    def get_profile(self) -> Optional[Dict]:
        """Get Gmail profile info (email, message count, thread count)."""

    def search_messages(self, query: str = '', max_results: int = 100) -> List[str]:
        """Search for messages matching query. Returns list of message IDs."""

    def get_message_details(self, message_id: str) -> Optional[Dict]:
        """Get full message details by ID."""

    def download_emails(
        self,
        query: str = '',
        max_emails: int = 100,
        output_dir: str = 'gmail_backup',
        format_type: str = 'both',
        organize_by: str = 'date',
        skip: int = 0
    ):
        """Download emails matching query to local files."""
```

### GmailDeleter Class

```python
from src.deletion.deleter import GmailDeleter

class GmailDeleter:
    def __init__(self, credentials_file: str = 'credentials.json'):
        """Initialize deleter with credentials and rate limiting."""

    def get_email_count(self, query: str = '') -> int:
        """Get total count of emails matching query."""

    def list_emails(self, query: str = '', max_results: int = None) -> List[str]:
        """List email IDs matching query with pagination."""

    def delete_emails_batch(
        self,
        message_ids: List[str],
        batch_size: int = 100
    ) -> Dict[str, int]:
        """Delete emails in batches. Returns {'deleted': n, 'failed': n}."""

    def delete_by_query(
        self,
        query: str,
        dry_run: bool = True,
        max_delete: int = None
    ) -> Dict[str, int]:
        """Delete emails matching query with safety checks."""
```

### EmailContentParser Class

```python
from src.parsers.advanced_email_parser import EmailContentParser

class EmailContentParser:
    def __init__(self, config_file: Optional[str] = None):
        """Initialize parser with optional config file."""

    def detect_email_type(self, html_content: str, sender: str = "") -> str:
        """Detect email type: newsletter|notification|marketing|simple."""

    def clean_html(self, html_content: str, sender: str = "") -> str:
        """Clean and prepare HTML for conversion."""

    def parse_email_content(
        self,
        html_content: str,
        plain_text: str = "",
        sender: str = "",
        subject: str = ""
    ) -> Dict[str, Union[str, float]]:
        """
        Parse email content using multiple strategies.
        Returns:
            {
                'markdown': str,
                'strategy': str,
                'quality': float,
                'metadata': dict
            }
        """
```

### EmailAnalysisEngine Class

```python
from src.analysis.email_analyzer import EmailAnalysisEngine

class EmailAnalysisEngine:
    def __init__(self, config: Dict[str, Any]):
        """Initialize analysis engine with configuration."""

    def analyze_data_quality(self, df: pd.DataFrame) -> Dict:
        """Assess data quality and completeness."""

    def classify_emails(self, df: pd.DataFrame) -> pd.DataFrame:
        """Classify emails into categories."""

    def analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze time-based patterns."""

    def analyze_senders(self, df: pd.DataFrame) -> Dict:
        """Analyze sender patterns and domains."""

    def analyze_content(self, df: pd.DataFrame) -> Dict:
        """Analyze content patterns and keywords."""

    def generate_insights(self, analysis_results: Dict) -> Dict:
        """Generate actionable insights from analysis."""
```

### ServiceContainer Class

```python
from src.core.container import ServiceContainer

class ServiceContainer:
    def register(
        self,
        service_type: Type[T],
        instance: T,
        lifetime: str = ServiceLifetime.SINGLETON
    ) -> 'ServiceContainer':
        """Register a service instance."""

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[[], T],
        lifetime: str = ServiceLifetime.SINGLETON
    ) -> 'ServiceContainer':
        """Register a factory function for a service."""

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service by type."""

    def create_scope(self) -> 'ServiceContainer':
        """Create a new scoped container."""
```

---

## Workflow Guides

### Workflow 1: Complete Email Backup

**Objective**: Create a full backup of unread emails with organization.

```bash
# Step 1: Test authentication
python main.py fetch --query "is:unread" --auth-only

# Step 2: Count emails to backup
python main.py fetch --query "is:unread" --count-only

# Step 3: Perform backup
python main.py fetch --query "is:unread" --max 5000 --output backup_unread --format both --organize date

# Step 4: Verify backup
ls -la backup_unread/
```

### Workflow 2: Newsletter Archival

**Objective**: Archive and organize newsletters for offline reading.

```bash
# Step 1: Run newsletter scenario
python main.py samples newsletters --max 2000

# Step 2: Alternative - manual query
python main.py fetch \
  --query "from:(substack.com OR newsletter@) OR subject:newsletter" \
  --format markdown \
  --organize sender \
  --output newsletters_archive
```

### Workflow 3: Inbox Cleanup

**Objective**: Safely delete old, large, or promotional emails.

```bash
# Step 1: Analyze current state
python main.py analyze --days 30

# Step 2: Dry run for old emails
python main.py delete preset old --dry-run

# Step 3: Dry run for large emails
python main.py delete preset large --dry-run

# Step 4: Execute deletion (requires confirmation)
python main.py delete preset old --execute
```

### Workflow 4: Daily Email Analysis

**Objective**: Generate daily insights from email patterns.

```bash
# Option 1: Using main.py
python main.py analyze --yesterday --output reports/daily_analysis.json

# Option 2: Using quick analysis script
python scripts/quick_analysis.py yesterday

# Option 3: Analyze last 7 days
python scripts/quick_analysis.py last7days
```

### Workflow 5: Email Format Conversion

**Objective**: Convert downloaded EML files to clean Markdown.

```bash
# Step 1: Parse single file
python main.py parse --input email_file.eml --format markdown

# Step 2: Parse directory
python main.py parse --input backup_folder/ --format markdown --clean
```

### Workflow 6: AI Newsletter Detection

**Objective**: Identify and optionally remove AI-related newsletters.

```bash
# Step 1: Export email data
python main.py fetch --query "is:unread" --format both --output ai_check

# Step 2: Run AI detection (dry run)
python main.py tools ai-cleanup --input email_data.json

# Step 3: Execute cleanup (with confirmation)
python main.py tools ai-cleanup --input email_data.json --delete --threshold 0.8
```

---

## Integration Patterns

### Pattern 1: Custom Email Processor

```python
from src.core.gmail_assistant import GmailFetcher
from src.parsers.advanced_email_parser import EmailContentParser

def process_emails_custom(query: str, processor_func):
    """Custom email processing pipeline."""
    fetcher = GmailFetcher()
    parser = EmailContentParser()

    if not fetcher.authenticate():
        raise RuntimeError("Authentication failed")

    message_ids = fetcher.search_messages(query, max_results=100)

    for msg_id in message_ids:
        message = fetcher.get_message_details(msg_id)
        if message:
            # Extract content
            headers = fetcher.extract_headers(message['payload'].get('headers', []))
            plain_text, html_body = fetcher.get_message_body(message['payload'])

            # Parse to Markdown
            result = parser.parse_email_content(
                html_content=html_body,
                plain_text=plain_text,
                sender=headers.get('from', ''),
                subject=headers.get('subject', '')
            )

            # Custom processing
            processor_func(message, result)
```

### Pattern 2: Extending the Plugin System

```python
from src.core.protocols import OutputPluginProtocol
from pathlib import Path

class JSONOutputPlugin:
    """Custom JSON output plugin."""

    @property
    def name(self) -> str:
        return "json"

    @property
    def extension(self) -> str:
        return ".json"

    def generate(self, email_data: dict) -> str:
        import json
        return json.dumps(email_data, indent=2)

    def save(self, content: str, path: Path) -> bool:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
```

### Pattern 3: Analysis Pipeline Integration

```python
from src.analysis.email_analyzer import EmailAnalysisEngine
import pandas as pd

def run_custom_analysis(data_file: str, custom_rules: dict):
    """Run analysis with custom classification rules."""
    config = {
        'quality_thresholds': {'min_completeness': 95},
        'log_file': 'logs/custom_analysis.log'
    }

    engine = EmailAnalysisEngine(config)

    # Load data
    df = pd.read_parquet(data_file)

    # Run standard pipeline
    quality = engine.analyze_data_quality(df)
    if not quality['quality_passed']:
        raise ValueError(f"Quality issues: {quality['quality_issues']}")

    df_classified = engine.classify_emails(df)

    # Apply custom rules
    for category, rules in custom_rules.items():
        mask = df_classified['subject'].str.contains(
            '|'.join(rules['keywords']), case=False, na=False
        )
        df_classified.loc[mask, 'category'] = category

    return engine.generate_insights({'classification': df_classified})
```

### Pattern 4: Rate-Limited Batch Operations

```python
from src.utils.rate_limiter import GmailRateLimiter

def batch_operation_with_rate_limiting(operation_func, items, batch_size=100):
    """Execute batch operations with rate limiting."""
    rate_limiter = GmailRateLimiter(
        requests_per_second=8.0,
        max_retries=5,
        base_delay=1.0
    )

    results = {'success': 0, 'failed': 0}

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        # Wait for rate limit
        rate_limiter.wait_if_needed(quota_cost=50)

        try:
            operation_func(batch)
            results['success'] += len(batch)
        except Exception as e:
            results['failed'] += len(batch)
            print(f"Batch failed: {e}")

    return results
```

---

## Development Guidelines

### Project Structure Rules

Following `config/0922-0238_project_governance.json`:

1. **No files in root directory** - Organize in appropriate folders
2. **Source code**: `src/` (organized by feature: `core/`, `parsers/`, `analysis/`, etc.)
3. **Tests**: `tests/` (ALL test-related scripts)
4. **Documentation**: `docs/` with timestamped naming
5. **Configuration**: `config/`
6. **Utilities**: `scripts/`
7. **Examples**: `examples/`

### Documentation Naming Convention

All documentation files must use timestamped format:

```
<mmdd-hhmm_name.extension>

Examples:
  0922-0238_implementation_plan.md
  0922-1430_api_design.json
```

**Exceptions**: `README.md`, `CLAUDE.md`, `LICENSE`, `CHANGELOG.md`

### Code Quality Standards

1. **Type hints**: Use Python type annotations throughout
2. **Protocols**: Implement protocols for dependency injection
3. **Logging**: Use logging module, not print statements
4. **Error handling**: Log before raising or passing exceptions
5. **Validation**: Validate inputs using `InputValidator`
6. **Rate limiting**: Use `GmailRateLimiter` for API operations
7. **Caching**: Use `CacheManager` for repeated operations

### Testing Requirements

1. Place all tests in `tests/` directory
2. Name test files: `test_*.py` or `*_test.py`
3. Run tests: `python tests/run_tests.py`
4. Coverage configuration: `tests/coverage.ini`

### Security Considerations

1. **Never commit credentials** - Use `.gitignore` for `credentials.json`, `token.json`
2. **Use JSON serialization** - Avoid pickle for security
3. **Validate all inputs** - Use `InputValidator` class
4. **Rate limiting** - Protect against quota exhaustion
5. **Confirmation gates** - Require explicit confirmation for destructive operations

---

## Troubleshooting

### Common Issues

#### Authentication Failures

```
Problem: "Authentication failed" or token refresh errors
Solution:
1. Delete token.json
2. Run: python main.py fetch --query "test" --auth-only
3. Complete OAuth flow in browser
```

#### Rate Limit Errors

```
Problem: HTTP 429 or "Rate limit exceeded"
Solution:
1. Wait 1-5 minutes before retrying
2. Reduce requests_per_second in rate limiter
3. Use --max with lower values
```

#### Parsing Failures

```
Problem: "All parsing strategies failed"
Solution:
1. Check if email has HTML content
2. Try different strategy: --strategy html2text
3. Check parser logs for specific errors
```

#### Memory Issues

```
Problem: Out of memory with large backups
Solution:
1. Use --max to limit batch size
2. Enable streaming mode for large operations
3. Process in date ranges using --skip
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
python main.py --debug <command> [options]
```

### Log Files

| Log Location | Purpose |
|--------------|---------|
| `logs/email_analysis.log` | Analysis operations |
| `logs/deletion_*.log` | Deletion operations |
| `src/core/email_classifier.log` | Classification logs |

### Getting Help

```bash
# General help
python main.py --help

# Command-specific help
python main.py fetch --help
python main.py delete --help
python main.py analyze --help
```

---

## Appendices

### A. Gmail Query Syntax Reference

| Operator | Example | Description |
|----------|---------|-------------|
| `is:` | `is:unread` | Status flags |
| `from:` | `from:example.com` | Sender filter |
| `to:` | `to:me` | Recipient filter |
| `subject:` | `subject:"meeting"` | Subject contains |
| `after:` | `after:2025/01/01` | Date after |
| `before:` | `before:2025/02/01` | Date before |
| `older_than:` | `older_than:1y` | Relative age |
| `newer_than:` | `newer_than:6m` | Relative freshness |
| `larger:` | `larger:10M` | Size filter |
| `has:` | `has:attachment` | Content flags |
| `category:` | `category:promotions` | Gmail categories |
| `label:` | `label:important` | Label filter |

### B. Output Format Specifications

#### EML Format
- Native email format preserving all headers
- Compatible with email clients
- Preserves attachments and MIME structure

#### Markdown Format
- Human-readable with metadata table
- YAML front matter support
- HTML-to-Markdown conversion
- Suitable for documentation and archival

### C. API Quota Information

| Operation | Quota Cost |
|-----------|------------|
| messages.list | 5 units |
| messages.get | 5 units |
| messages.delete | 10 units |
| messages.batchDelete | 50 units |
| messages.trash | 5 units |

**Daily Quota**: 1,000,000,000 units
**Per-User Per-Second**: 250 units

---

**Document End**

*For updates to this documentation, please follow the project governance rules for timestamped naming.*
