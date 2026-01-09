# Gmail Fetcher Suite - Comprehensive Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Core Components](#core-components)
5. [Configuration](#configuration)
6. [Usage Guide](#usage-guide)
7. [Advanced Processing Tools](#advanced-processing-tools)
8. [Utility Scripts](#utility-scripts)
9. [API Reference](#api-reference)
10. [Workflows & Examples](#workflows--examples)
11. [Troubleshooting](#troubleshooting)
12. [Development Guide](#development-guide)

---

## Overview

**Gmail Fetcher Suite** is a comprehensive Python-based email management and backup system designed for downloading, processing, and organizing Gmail emails. It provides professional-grade tools for email backup, content extraction, format conversion, and intelligent cleanup operations.

### Key Features

- **Gmail API Integration**: Secure OAuth 2.0 authentication with Gmail API
- **Multi-Format Support**: Export emails as EML, Markdown, or both formats
- **Intelligent Organization**: Organize emails by date, sender, or custom patterns
- **Advanced Content Processing**: Multiple parsing strategies for clean HTML-to-Markdown conversion
- **AI Newsletter Detection**: Automated identification and cleanup of AI/tech newsletters
- **Batch Operations**: Efficient processing of large email volumes
- **Cross-Platform Compatibility**: Windows, Linux, and macOS support
- **Flexible Configuration**: JSON-based configuration system
- **Professional Tools**: Comprehensive utility scripts for backup management

### Use Cases

- **Email Backup & Archive**: Create comprehensive backups before account cleanup
- **Newsletter Management**: Organize and analyze newsletter subscriptions
- **Content Analysis**: Extract and analyze email content for research
- **Migration Support**: Convert email formats for different systems
- **Automated Cleanup**: Intelligent deletion of unwanted emails
- **Service Notification Backup**: Preserve important service communications

---

## Architecture

### Project Structure

```
gmail_fetcher/
├── main.py                          # Main orchestrator and CLI entry point
├── src/                             # Core application modules
│   ├── core/                        # Primary business logic
│   │   ├── gmail_fetcher.py         # Main Gmail API client and fetcher
│   │   ├── gmail_api_client.py      # Live Gmail API operations
│   │   ├── gmail_ai_newsletter_cleaner.py  # AI newsletter detection
│   │   ├── email_data_extractor.py  # Email metadata extraction
│   │   ├── email_database_importer.py # Database import utilities
│   │   ├── email_plaintext_processor.py # Text processing tools
│   │   └── email_classifier.py      # Email classification system
│   ├── parsers/                     # Content processing modules
│   │   ├── advanced_email_parser.py # Multi-strategy HTML parsing
│   │   └── gmail_eml_to_markdown_cleaner.py # EML to Markdown converter
│   ├── utils/                       # Utility modules
│   │   ├── gmail_organizer.py       # Email organization tools
│   │   ├── comprehensive_email_processor.py # Batch processing
│   │   └── ultimate_email_processor.py # Advanced workflows
│   └── cleanup/                     # Cleanup and maintenance tools
│       ├── cleanup_markdown.py      # Markdown file cleanup
│       ├── markdown_post_fixer.py   # Post-processing fixes
│       ├── markdown_post_fixer_stage2.py # Advanced fixes
│       └── regenerate_markdown_from_eml.py # Format regeneration
├── examples/                        # Sample scripts and usage examples
│   ├── samples.py                   # Predefined backup scenarios
│   └── example_usage.py             # Demonstration scripts
├── scripts/                         # Automation and management scripts
│   ├── setup/                       # Installation and setup scripts
│   │   ├── quick_start.ps1          # PowerShell quick setup
│   │   ├── quick_start.bat          # Batch quick setup
│   │   └── setup_and_test.bat       # Installation verification
│   ├── backup/                      # Backup management scripts
│   │   ├── move_backup_years.ps1    # Year-based backup merging
│   │   ├── dedupe_merge.ps1         # Deduplication and merging
│   │   └── dedupe_in_place.ps1      # In-place deduplication
│   └── operations/                  # Operational scripts
│       ├── quick_test.ps1           # Quick testing
│       ├── run_comprehensive.ps1    # Comprehensive operations
│       └── run_comprehensive.bat    # Batch operations
├── config/                          # Configuration files
│   ├── app/                         # Application configurations
│   │   ├── gmail_fetcher_config.json # Main fetcher settings
│   │   └── config.json              # AI detection settings
│   └── security/                    # Authentication files
│       ├── credentials.json         # Gmail API credentials
│       └── token.json              # OAuth tokens
└── requirements.txt                 # Python dependencies
```

### Core Design Principles

1. **Modular Architecture**: Clear separation of concerns with specialized modules
2. **Configuration-Driven**: JSON-based configuration for all settings
3. **Error Resilience**: Comprehensive error handling and recovery mechanisms
4. **Performance Optimization**: Batch processing and efficient API usage
5. **Security First**: OAuth 2.0 authentication and secure credential management
6. **Cross-Platform Support**: Compatible with Windows, Linux, and macOS

---

## Installation & Setup

### Prerequisites

- **Python 3.8+**: Required for all operations
- **Gmail API Access**: Google Cloud Console project with Gmail API enabled
- **Internet Connection**: Required for Gmail API operations

### Quick Installation

#### Option 1: Automated Setup (Recommended)

**Windows PowerShell:**
```powershell
cd scripts/setup
.\quick_start.ps1
```

**Windows Batch:**
```cmd
cd scripts\setup
quick_start.bat
```

#### Option 2: Manual Installation

1. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Gmail API Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download credentials as `config/security/credentials.json`

3. **Test Authentication:**
   ```bash
   python main.py fetch --auth-only
   ```

### Dependencies

#### Core Dependencies (requirements.txt)
```
google-api-python-client==2.108.0    # Gmail API client
google-auth-httplib2==0.1.1          # HTTP authentication
google-auth-oauthlib==1.1.0          # OAuth 2.0 flow
google-auth==2.23.4                  # Authentication library
html2text==2024.2.26                 # HTML to text conversion
```

#### Advanced Processing Dependencies (Optional)
```
beautifulsoup4>=4.12.0               # HTML parsing
markdownify>=0.11.6                  # HTML to Markdown conversion
readability-lxml>=0.8.1              # Content extraction (optional)
trafilatura>=1.6.0                   # Advanced content extraction (optional)
python-frontmatter>=1.0.0            # YAML front matter handling
chardet>=5.2.0                       # Character encoding detection
mdformat>=0.7.16                     # Markdown formatting
html5lib>=1.1                        # HTML5 parser
```

---

## Core Components

### 1. Gmail Fetcher (`src/core/gmail_fetcher.py`)

**Primary email fetching and backup functionality.**

#### Key Classes and Methods

```python
class GmailFetcher:
    """Main Gmail API client for email fetching and backup operations"""

    def __init__(self, credentials_file: str = 'credentials.json',
                 token_file: str = 'token.json')

    def authenticate(self) -> bool
    """Authenticate with Gmail API using OAuth 2.0"""

    def get_profile(self) -> Dict
    """Get Gmail profile information"""

    def search_messages(self, query: str = '', max_results: int = 100) -> List[str]
    """Search for messages matching Gmail query syntax"""

    def get_message_details(self, message_id: str) -> Optional[Dict]
    """Retrieve full message details including headers and content"""

    def download_emails(self, query: str = '', max_emails: int = 100,
                       output_dir: str = 'gmail_backup',
                       format_type: str = 'both',
                       organize_by: str = 'date',
                       skip: int = 0)
    """Download emails and save in specified format"""
```

#### Supported Gmail Query Operators

- **Time-based**: `after:2025/01/01`, `before:2025/04/01`, `newer_than:6m`, `older_than:1y`
- **Content-based**: `subject:AI`, `from:example.com`, `has:attachment`, `filename:pdf`
- **Status-based**: `is:unread`, `is:important`, `is:starred`, `is:sent`
- **Category-based**: `category:updates`, `category:promotions`, `category:social`
- **Size-based**: `larger:10M`, `smaller:1M`
- **Boolean**: `AND`, `OR`, `NOT`, `()` for grouping

### 2. Gmail API Client (`src/core/gmail_api_client.py`)

**Live Gmail operations for real-time email management.**

#### Key Features
- **Real-time email fetching** with batch processing
- **Email deletion** (permanent or trash)
- **AI newsletter detection** integration
- **Progress tracking** and error handling

```python
class GmailAPIClient:
    """Gmail API client for actual email operations"""

    def fetch_unread_emails(self, max_results: int = 2938) -> List[EmailData]
    def delete_emails(self, email_ids: List[str]) -> Dict[str, int]
    def trash_emails(self, email_ids: List[str]) -> Dict[str, int]
```

### 3. AI Newsletter Detector (`src/core/gmail_ai_newsletter_cleaner.py`)

**Intelligent detection and cleanup of AI/tech newsletters.**

#### Detection Strategies
- **Keyword Matching**: AI-related terms in subject and sender
- **Domain Recognition**: Known AI newsletter domains
- **Pattern Analysis**: Newsletter-specific subject patterns
- **Content Analysis**: Unsubscribe links and automated sender detection

```python
class AINewsletterDetector:
    """Detects AI newsletters using multiple pattern matching strategies"""

    def is_ai_newsletter(self, email: EmailData) -> Dict
    """Analyze email and return detection results with confidence score"""

    def analyze_batch(self, emails: List[EmailData]) -> List[Dict]
    """Batch analysis of multiple emails for efficiency"""
```

#### Confidence Scoring System
```json
{
  "confidence_weights": {
    "ai_keywords_subject": 3,
    "ai_keywords_sender": 2,
    "known_domain": 4,
    "newsletter_pattern": 2,
    "unsubscribe_link": 1,
    "automated_sender": 1
  },
  "decision_threshold": {
    "minimum_confidence": 4,
    "minimum_reasons": 2
  }
}
```

---

## Configuration

### 1. Main Fetcher Configuration (`config/app/gmail_fetcher_config.json`)

```json
{
  "common_queries": {
    "march_2025": "after:2025/02/28 before:2025/04/01",
    "unread_only": "is:unread",
    "newsletters": "from:(theresanaiforthat.com OR mindstream.news OR futurepedia.io)",
    "ai_content": "subject:(AI OR artificial intelligence OR machine learning)",
    "service_notifications": "from:(namecheap.com OR pythonanywhere.com OR zoho.com)",
    "last_6_months": "newer_than:6m",
    "large_emails": "larger:10M"
  },
  "default_settings": {
    "max_emails": 500,
    "output_format": "both",
    "organize_by": "date",
    "output_directory": "gmail_backup"
  },
  "cleanup_suggestions": {
    "auto_delete_queries": [
      "category:promotions older_than:3m",
      "from:noreply older_than:6m"
    ],
    "auto_archive_queries": [
      "category:updates older_than:1m"
    ]
  }
}
```

### 2. AI Detection Configuration (`config/app/config.json`)

**Comprehensive AI newsletter detection settings:**

- **AI Keywords**: 38+ relevant terms (artificial intelligence, machine learning, ChatGPT, etc.)
- **Newsletter Domains**: 25+ known AI/tech newsletter domains
- **Pattern Matching**: Regular expressions for newsletter identification
- **Confidence Scoring**: Weighted scoring system for accurate detection

---

## Usage Guide

### Main CLI Interface (`main.py`)

The main orchestrator provides a unified interface for all operations:

```bash
python main.py --help
```

#### Command Structure
```
main.py <command> [options]

Commands:
  fetch     Download emails from Gmail
  parse     Parse and convert email formats
  tools     Utilities and maintenance tools
  samples   Run predefined sample scenarios
  config    Configuration management
```

### 1. Email Fetching

#### Basic Operations
```bash
# Download unread emails
python main.py fetch --query "is:unread" --max 1000

# Download by date range
python main.py fetch --query "after:2025/02/28 before:2025/04/01" --max 500

# Download with specific organization
python main.py fetch --query "is:unread" --organize sender --format markdown
```

#### Advanced Queries
```bash
# AI content analysis
python main.py fetch --query "subject:(AI OR artificial intelligence) AND newer_than:6m" --max 1000

# Large emails with attachments
python main.py fetch --query "larger:10M has:attachment" --max 200

# Service notifications
python main.py fetch --query "from:(github.com OR stackoverflow.com)" --max 500
```

### 2. Content Processing

#### EML to Markdown Conversion
```bash
# Convert single file
python main.py parse --input email.eml --format markdown

# Convert entire directory
python main.py parse --input backup_folder --format markdown --clean
```

#### Advanced Processing Strategies
```bash
# Use specific parsing strategy
python main.py parse --input backup_folder --strategy readability

# Apply cleaning rules
python main.py parse --input backup_folder --clean
```

### 3. Tools and Utilities

#### Cleanup Operations
```bash
# Markdown cleanup
python main.py tools cleanup --target backup_folder --type markdown

# AI newsletter detection and cleanup
python main.py tools ai-cleanup --input email_data.json --threshold 0.7

# Actually delete AI newsletters
python main.py tools ai-cleanup --input email_data.json --delete
```

### 4. Sample Scenarios

#### Predefined Backup Scenarios
```bash
# List available scenarios
python main.py samples list

# Run specific scenarios
python main.py samples unread
python main.py samples newsletters
python main.py samples services
python main.py samples important
```

---

## Advanced Processing Tools

### 1. Advanced Email Parser (`src/parsers/advanced_email_parser.py`)

**Multi-strategy HTML-to-Markdown conversion with intelligent content extraction.**

#### Features
- **Multiple Parsing Strategies**: Smart, readability, trafilatura, html2text, markdownify
- **Newsletter Detection**: Specialized handling for newsletter content
- **Quality Scoring**: Automatic selection of best parsing result
- **Link Preservation**: Maintains link integrity and formatting
- **Image Handling**: Processes inline images and attachments

#### Parsing Strategies
1. **Smart Strategy**: Intelligent content detection and extraction
2. **Readability**: Mozilla Readability algorithm for clean content
3. **Trafilatura**: Advanced web content extraction
4. **HTML2Text**: Traditional HTML-to-text conversion
5. **Markdownify**: Direct HTML-to-Markdown conversion

### 2. EML to Markdown Cleaner (`src/parsers/gmail_eml_to_markdown_cleaner.py`)

**Professional EML file processing with YAML front matter and consistent formatting.**

#### Features
- **YAML Front Matter**: Structured metadata preservation
- **Encoding Detection**: Automatic character encoding handling
- **CID Image Processing**: Inline image extraction and handling
- **Attachment Management**: Separate attachment extraction
- **Consistent Formatting**: Standardized Markdown output

#### Output Format
```markdown
---
subject: "Email Subject"
from: "sender@example.com"
to: "recipient@example.com"
date: "2025-03-31T12:00:00Z"
message_id: "12345@gmail.com"
thread_id: "67890"
labels: ["INBOX", "UNREAD"]
---

# Email Content

Clean, formatted email content in Markdown...
```

---

## Utility Scripts

### 1. PowerShell Backup Management

#### Move Backup Years (`scripts/backup/move_backup_years.ps1`)
```powershell
# Merge backup folders by year
.\move_backup_years.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -DryRun

# Actually perform the merge
.\move_backup_years.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025
```

**Features:**
- Year-based folder merging
- Duplicate detection and handling
- Conflict resolution with automatic renaming
- Dry-run mode for safe previewing
- Progress tracking and logging

#### Deduplicate and Merge (`scripts/backup/dedupe_merge.ps1`)
```powershell
# Deduplicate emails across backup folders
.\dedupe_merge.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -Prefer larger -DryRun
```

**Features:**
- Content-based deduplication
- Size-based conflict resolution
- Cross-folder duplicate detection
- Configurable preferences
- Detailed operation logs

### 2. Quick Setup Scripts

#### PowerShell Setup (`scripts/setup/quick_start.ps1`)
- Automated dependency installation
- Python environment verification
- Gmail API credential setup
- Authentication testing
- Interactive menu system

#### Batch Setup (`scripts/setup/quick_start.bat`)
- Windows batch alternative
- Cross-version compatibility
- Error handling and recovery
- User-friendly interface

---

## API Reference

### Core Classes

#### GmailFetcher Class

```python
class GmailFetcher:
    """Main Gmail API client for email operations"""

    # Initialization
    def __init__(self, credentials_file: str = 'credentials.json',
                 token_file: str = 'token.json')

    # Authentication
    def authenticate(self) -> bool
    """Returns: True if authentication successful, False otherwise"""

    def get_profile(self) -> Dict
    """Returns: {'email': str, 'total_messages': int, 'total_threads': int}"""

    # Message Operations
    def search_messages(self, query: str = '', max_results: int = 100) -> List[str]
    """
    Args:
        query: Gmail search query string
        max_results: Maximum number of message IDs to return
    Returns: List of Gmail message IDs
    """

    def get_message_details(self, message_id: str) -> Optional[Dict]
    """
    Args:
        message_id: Gmail message ID
    Returns: Full message data including headers and content
    """

    # Content Processing
    def create_eml_content(self, message_data: Dict) -> str
    """Convert Gmail message data to EML format"""

    def create_markdown_content(self, message_data: Dict) -> str
    """Convert Gmail message data to Markdown format"""

    # File Operations
    def download_emails(self, query: str = '', max_emails: int = 100,
                       output_dir: str = 'gmail_backup',
                       format_type: str = 'both',
                       organize_by: str = 'date',
                       skip: int = 0)
    """
    Main email download function

    Args:
        query: Gmail search query
        max_emails: Maximum emails to download
        output_dir: Output directory path
        format_type: 'eml', 'markdown', or 'both'
        organize_by: 'date', 'sender', or 'none'
        skip: Number of messages to skip
    """
```

#### AINewsletterDetector Class

```python
class AINewsletterDetector:
    """AI newsletter detection and analysis"""

    def __init__(self, config_path: str = '../config/config.json')

    def is_ai_newsletter(self, email: EmailData) -> Dict
    """
    Analyze single email for AI newsletter characteristics

    Args:
        email: EmailData object with email information

    Returns:
        {
            'is_ai_newsletter': bool,
            'confidence': float,
            'reasons': List[str],
            'analysis_details': Dict
        }
    """

    def analyze_batch(self, emails: List[EmailData]) -> List[Dict]
    """Batch analysis for multiple emails"""
```

#### EmailData Class

```python
@dataclass
class EmailData:
    """Structure for email data"""
    id: str                    # Gmail message ID
    subject: str              # Email subject line
    sender: str               # From address
    date: str                 # Date string
    labels: List[str] = None  # Gmail labels
    thread_id: str = None     # Gmail thread ID
    body_snippet: str = ""    # Content snippet
```

### Command Line Arguments

#### Main CLI Arguments
```bash
python main.py <command> [options]

Global Options:
  -h, --help     Show help message

Fetch Command Options:
  --query QUERY        Gmail search query (required)
  --max MAX           Maximum emails to fetch (default: 1000)
  --output OUTPUT     Output directory (default: gmail_backup)
  --format FORMAT     Output format: eml|markdown|both (default: both)
  --organize ORG      Organization: date|sender|none (default: date)
  --auth-only         Test authentication only

Parse Command Options:
  --input INPUT       Input directory or file (required)
  --format FORMAT     Output format: markdown|eml (default: markdown)
  --strategy STRATEGY Parsing strategy: auto|readability|trafilatura|html2text
  --clean            Apply cleaning rules

Tools Command Options:
  cleanup --target TARGET --type TYPE
  ai-cleanup --input INPUT [--delete] [--threshold THRESHOLD]

Samples Command Options:
  scenario            Scenario name or 'list' to show available scenarios
  --max MAX          Maximum emails for scenario (default: 1000)
```

---

## Workflows & Examples

### 1. Complete Email Backup Workflow

```bash
# Step 1: Test authentication
python main.py fetch --auth-only

# Step 2: Download unread emails for review
python main.py fetch --query "is:unread" --max 2000 --output backup_unread

# Step 3: Download important emails
python main.py fetch --query "is:important OR is:starred" --max 500 --output backup_important

# Step 4: Download large emails with attachments
python main.py fetch --query "larger:10M" --max 200 --format eml --output backup_large

# Step 5: Convert EML files to clean Markdown
python main.py parse --input backup_unread --format markdown --clean
```

### 2. AI Newsletter Management Workflow

```bash
# Step 1: Download recent emails for analysis
python main.py fetch --query "newer_than:3m" --max 3000 --output recent_emails

# Step 2: Analyze for AI newsletters (dry run)
python main.py tools ai-cleanup --input recent_emails --threshold 0.7

# Step 3: Actually delete AI newsletters
python main.py tools ai-cleanup --input recent_emails --delete
```

### 3. Newsletter Organization Workflow

```bash
# Step 1: Download newsletters organized by sender
python main.py fetch --query "subject:newsletter OR from:substack.com" --organize sender --output newsletters

# Step 2: Parse for better readability
python main.py parse --input newsletters --format markdown --strategy readability

# Step 3: Clean up formatting
python main.py tools cleanup --target newsletters --type markdown
```

### 4. Service Notification Backup

```bash
# Backup important service notifications
python main.py fetch --query "from:(github.com OR namecheap.com OR pythonanywhere.com)" --format eml --organize sender --output service_notifications
```

### 5. Content Analysis Workflow

```bash
# Download AI-related content for analysis
python main.py fetch --query "subject:(AI OR artificial intelligence OR machine learning) AND newer_than:1y" --format markdown --output ai_content_analysis

# Process with advanced parsing
python main.py parse --input ai_content_analysis --strategy trafilatura --clean
```

### 6. Using Sample Scenarios

```bash
# List all available scenarios
python main.py samples list

# Run comprehensive newsletter backup
python main.py samples newsletters --max 2000

# Run unread email backup
python main.py samples unread --max 1500

# Run service notifications backup
python main.py samples services --max 1000
```

### 7. Backup Management with PowerShell

```powershell
# Merge backup folders by year
.\scripts\backup\move_backup_years.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -DryRun

# Deduplicate across backups
.\scripts\backup\dedupe_merge.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -Prefer larger
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Authentication Problems

**Issue**: `❌ Error: credentials.json not found!`
**Solution**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Download as `config/security/credentials.json`

**Issue**: `Invalid credentials` or token expired
**Solution**:
```bash
# Delete existing token and re-authenticate
rm config/security/token.json
python main.py fetch --auth-only
```

#### 2. Download Issues

**Issue**: `❌ Error: Rate limit exceeded`
**Solution**:
- Reduce `--max` parameter
- Add delays between requests
- Use batch processing approach

**Issue**: `Base64 decode error`
**Solution**:
- This is usually handled automatically
- Check email content for corruption
- Try re-downloading the specific message

#### 3. Processing Issues

**Issue**: `HTML conversion failed`
**Solution**:
```bash
# Use different parsing strategy
python main.py parse --input email.eml --strategy html2text

# Install optional dependencies
pip install readability-lxml trafilatura
```

**Issue**: `Encoding detection failed`
**Solution**:
```bash
# Install chardet for better encoding detection
pip install chardet
```

#### 4. File Organization Issues

**Issue**: Filename too long or invalid characters
**Solution**: The system automatically sanitizes filenames, but if issues persist:
```python
# Manual filename sanitization in code
filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
```

#### 5. PowerShell Script Issues

**Issue**: `Execution policy` errors
**Solution**:
```powershell
# Temporarily allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Issue**: Path not found errors
**Solution**:
- Use absolute paths
- Ensure all directories exist
- Check Windows path separators

### Performance Optimization

#### Large Volume Processing
```bash
# Process in smaller batches
python main.py fetch --query "is:unread" --max 500 --skip 0
python main.py fetch --query "is:unread" --max 500 --skip 500
python main.py fetch --query "is:unread" --max 500 --skip 1000
```

#### Memory Management
- Use EML format for large emails with attachments
- Process directories in batches
- Clear output directories periodically

#### API Rate Limiting
- Gmail API has quota limits
- Implement delays for large operations
- Use batch requests where possible

---

## Development Guide

### Code Structure

#### Adding New Features

1. **Core Functionality**: Add to `src/core/`
2. **Processing Tools**: Add to `src/parsers/` or `src/utils/`
3. **Cleanup Tools**: Add to `src/cleanup/`
4. **CLI Integration**: Update `main.py` command handlers

#### Configuration Extension

1. **Update JSON files** in `config/app/`
2. **Add validation** in relevant classes
3. **Update documentation**

#### Testing

```bash
# Test authentication
python main.py fetch --auth-only

# Test with small dataset
python main.py fetch --query "is:unread" --max 5 --output test_backup

# Test parsing
python main.py parse --input test_backup --format markdown
```

### Contributing Guidelines

1. **Code Style**: Follow PEP 8 for Python code
2. **Documentation**: Update relevant documentation files
3. **Error Handling**: Implement comprehensive error handling
4. **Testing**: Test with various email types and edge cases
5. **Logging**: Use appropriate logging levels
6. **Security**: Never commit credentials or tokens

### Extension Points

#### Custom Parsers
```python
class CustomEmailParser(EmailContentParser):
    def parse_custom_format(self, content: str) -> str:
        # Custom parsing logic
        return processed_content
```

#### Custom Detectors
```python
class CustomNewsletterDetector(AINewsletterDetector):
    def detect_custom_pattern(self, email: EmailData) -> bool:
        # Custom detection logic
        return is_match
```

#### Custom Organization
```python
def custom_organization(message_data: Dict) -> str:
    # Custom folder structure logic
    return folder_path
```

---

This comprehensive documentation covers all aspects of the Gmail Fetcher Suite, from basic usage to advanced development scenarios. The system is designed to be flexible, extensible, and professional-grade for serious email management needs.