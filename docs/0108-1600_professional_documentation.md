# Gmail Fetcher Suite - Professional Documentation

**Version:** 2.0
**Last Updated:** September 2025
**Platform:** Cross-platform (Windows, Linux, macOS)
**License:** MIT

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [System Components](#system-components)
4. [Installation & Setup](#installation--setup)
5. [Core Functionality](#core-functionality)
6. [Advanced Features](#advanced-features)
7. [Configuration Management](#configuration-management)
8. [Automation & Scripts](#automation--scripts)
9. [API Integration](#api-integration)
10. [Troubleshooting](#troubleshooting)
11. [Performance Considerations](#performance-considerations)
12. [Security Best Practices](#security-best-practices)
13. [Development Guide](#development-guide)
14. [Use Cases & Workflows](#use-cases--workflows)

---

## Executive Summary

The Gmail Fetcher Suite is a comprehensive email management and backup solution designed for professionals, researchers, and organizations who need sophisticated Gmail operations beyond the standard web interface. The suite provides advanced email backup, intelligent content parsing, AI-powered newsletter management, and automated cleanup workflows.

### Key Value Propositions

- **Professional Email Archiving**: Download emails in standardized formats (EML, Markdown) with complete metadata preservation
- **Intelligent Content Processing**: Multi-strategy HTML to Markdown conversion with newsletter-specific optimization
- **AI-Powered Management**: Automated detection and management of AI newsletters and marketing content
- **Cross-Platform Automation**: Windows batch files, PowerShell scripts, and Python tools for seamless integration
- **Enterprise-Ready**: Configurable, scalable, and suitable for both individual and organizational use

### Target Users

- **Email Administrators**: Managing large-scale email operations and compliance
- **Researchers**: Archiving and analyzing email communications for studies
- **Content Managers**: Converting email newsletters to readable documentation
- **IT Professionals**: Automating email backup and cleanup workflows
- **Privacy-Conscious Users**: Maintaining local email archives independent of cloud services

---

## Architecture Overview

The Gmail Fetcher Suite follows a modular, layered architecture designed for extensibility, reliability, and performance.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   main.py       │    │   samples.py    │    │  Quick Start │ │
│  │  (Coordinator)  │    │  (Scenarios)    │    │   Scripts    │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CORE SERVICES LAYER                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ GmailFetcher    │    │ AINewsletterDet │    │ EmailParser  │ │
│  │ (Gmail API)     │    │ (AI Detection)  │    │ (Multi-Strat)│ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ Email Content   │    │ Markdown Clean  │    │ Backup Tools │ │
│  │ Processor       │    │ & Converter     │    │ & Utilities  │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA ACCESS LAYER                           │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ Gmail API       │    │ File System     │    │ Configuration│ │
│  │ Integration     │    │ Operations      │    │ Management   │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Architectural Principles

1. **Separation of Concerns**: Each component has a single, well-defined responsibility
2. **Modular Design**: Components can be used independently or in combination
3. **Error Resilience**: Comprehensive error handling and graceful degradation
4. **Configuration-Driven**: Behavior controlled through JSON configuration files
5. **Cross-Platform Compatibility**: Works on Windows, Linux, and macOS
6. **Performance Optimization**: Efficient Gmail API usage with rate limiting awareness

---

## System Components

### Core Components

#### 1. Gmail Fetcher (`src/core/gmail_fetcher.py`)
**Purpose**: Primary email backup and download engine
**Key Features**:
- Gmail API authentication with OAuth 2.0
- Advanced search query support (all Gmail operators)
- Multi-format output (EML, Markdown, both)
- Flexible organization (by date, sender, or flat structure)
- Pagination handling for large result sets
- Comprehensive metadata preservation

**Technical Details**:
- **Authentication**: OAuth 2.0 with token refresh
- **API Scope**: `gmail.readonly` (read-only access)
- **Rate Limiting**: Built-in respect for Gmail API quotas
- **Output Formats**: RFC-compliant EML, clean Markdown with metadata tables
- **File Organization**: Year/month hierarchy or sender-based grouping

#### 2. Advanced Email Parser (`src/parsers/advanced_email_parser.py`)
**Purpose**: Intelligent HTML-to-Markdown conversion with multiple strategies
**Key Features**:
- Multi-strategy parsing (readability, trafilatura, html2text, markdownify)
- Newsletter-specific content extraction rules
- Quality scoring and automatic best-result selection
- Smart email type detection (newsletter, notification, marketing, simple)

**Parsing Strategies**:
```python
STRATEGIES = {
    'readability': 'Extract main content using readability algorithm',
    'trafilatura': 'Advanced content extraction with NLP techniques',
    'html2text': 'Standard HTML to text conversion',
    'markdownify': 'Direct HTML to Markdown transformation',
    'smart': 'Dynamic strategy selection based on content analysis'
}
```

#### 3. AI Newsletter Cleaner (`src/core/gmail_ai_newsletter_cleaner.py`)
**Purpose**: Pattern-based detection and management of AI newsletters
**Key Features**:
- Configurable AI keyword detection
- Domain-based newsletter identification
- Confidence scoring with adjustable thresholds
- Dry-run mode with detailed logging
- Batch processing with progress tracking

**Detection Patterns**:
- **Keywords**: AI, artificial intelligence, machine learning, LLM, GPT, etc.
- **Domains**: Known AI newsletter publishers and platforms
- **Subject Patterns**: Newsletter-specific subject line formats
- **Unsubscribe Patterns**: Newsletter footer detection

#### 4. EML to Markdown Converter (`src/parsers/gmail_eml_to_markdown_cleaner.py`)
**Purpose**: Professional conversion of EML files to clean Markdown with front matter
**Key Features**:
- YAML front matter with complete email metadata
- Attachment handling and CID reference processing
- Configurable content cleaning and formatting rules
- Batch processing with mirror directory structure
- Character encoding detection and handling

### Utility Components

#### 5. Gmail API Client (`src/core/gmail_api_client.py`)
**Purpose**: Live Gmail API integration for real-time operations
**Key Features**:
- Real-time email fetching and analysis
- Batch operations for efficient processing
- Trash vs permanent deletion options
- Full API authentication and error handling

#### 6. Comprehensive Email Processor (`src/utils/comprehensive_email_processor.py`)
**Purpose**: 4-layer architecture for maximum quality email processing
**Architecture**:
1. **SafeMetadataExtractor**: Robust YAML serialization handling
2. **IntelligentContentAnalyzer**: Dynamic strategy selection
3. **QualityDrivenProcessor**: Multi-attempt with validation
4. **ProfessionalOutputGenerator**: Consistent formatting with error recovery

#### 7. Email Classifier (`src/core/email_classifier.py`)
**Purpose**: Intelligent email categorization and analysis
**Categories**:
- Newsletters and subscriptions
- Service notifications
- Personal communications
- Marketing and promotional
- AI and technology content

---

## Installation & Setup

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, Linux (Ubuntu 18.04+), macOS 10.15+
- **Memory**: Minimum 4GB RAM (8GB recommended for large operations)
- **Storage**: 1GB+ free space for software and email backups
- **Network**: Stable internet connection for Gmail API access

### Core Installation

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd gmail_fetcher
   ```

2. **Install Core Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Advanced Processing Dependencies (Optional)**
   ```bash
   pip install -r docs/legacy/requirements_advanced.txt
   ```

### Gmail API Setup

1. **Google Cloud Console Setup**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing project
   - Enable Gmail API in the API Library
   - Navigate to "Credentials" section

2. **OAuth 2.0 Configuration**
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Select "Desktop Application" as application type
   - Download credentials as `credentials.json`
   - Place file in project root directory

3. **Security Configuration**
   ```bash
   # Create secure config structure
   mkdir -p config/security
   mv credentials.json config/security/
   ```

### Quick Setup Scripts

#### Windows Batch Setup
```batch
# Run interactive setup
scripts\setup\quick_start.bat
```

#### PowerShell Setup (Cross-platform)
```powershell
# Run comprehensive setup
.\scripts\setup\quick_start.ps1
```

### Verification

```bash
# Test authentication
python main.py fetch --auth-only

# Expected output:
# ✅ Authentication successful!
#    Email: your.email@gmail.com
#    Total messages: 15,432
```

---

## Core Functionality

### Email Fetching Operations

#### Basic Fetch Commands

```bash
# Download unread emails
python main.py fetch --query "is:unread" --max 1000

# Download by date range
python main.py fetch --query "after:2025/01/01 before:2025/04/01" --max 500

# Download with specific organization
python main.py fetch --query "is:unread" --organize sender --format markdown
```

#### Advanced Search Queries

The system supports all Gmail search operators:

```bash
# Time-based searches
--query "after:2025/01/01"                    # After specific date
--query "before:2025/04/01"                   # Before specific date
--query "newer_than:6m"                       # Last 6 months
--query "older_than:1y"                       # Older than 1 year

# Content searches
--query "subject:AI"                          # Subject contains "AI"
--query "from:newsletter@example.com"         # From specific sender
--query "has:attachment"                      # Has attachments
--query "larger:10M"                          # Larger than 10MB

# Status searches
--query "is:unread"                           # Unread emails
--query "is:important"                        # Important emails
--query "is:starred"                          # Starred emails

# Category searches
--query "category:updates"                    # Update notifications
--query "category:promotions"                 # Promotional emails
--query "category:social"                     # Social notifications

# Complex combinations
--query "from:ai-newsletter.com after:2025/01/01 is:unread"
```

#### Output Formats

##### EML Format
- **Standard**: RFC-compliant email format
- **Compatibility**: Works with all email clients
- **Metadata**: Complete header preservation
- **Content**: Multipart MIME with HTML and plain text

##### Markdown Format
- **Structure**: Metadata table + converted content
- **Front Matter**: YAML headers with email details
- **Content**: Clean Markdown with preserved formatting
- **Links**: Functional hyperlinks maintained

##### Both Formats
- **Efficiency**: Single API call, dual output
- **Flexibility**: Choose format based on use case
- **Consistency**: Identical metadata across formats

#### File Organization Patterns

##### Date Organization (Default)
```
gmail_backup/
├── 2025/
│   ├── 01/
│   │   ├── 2025-01-15_120000_subject_messageid.eml
│   │   └── 2025-01-15_120000_subject_messageid.md
│   ├── 02/
│   └── 03/
├── 2024/
│   ├── 11/
│   └── 12/
```

##### Sender Organization
```
gmail_backup/
├── john.doe/
│   ├── 2025-01-15_120000_project_update_abc123.eml
│   └── 2025-01-15_120000_project_update_abc123.md
├── newsletter.site/
├── support.service/
```

##### Flat Organization
```
gmail_backup/
├── 2025-01-15_120000_subject1_id1.eml
├── 2025-01-15_120000_subject1_id1.md
├── 2025-01-16_143000_subject2_id2.eml
└── 2025-01-16_143000_subject2_id2.md
```

### Content Processing Operations

#### Advanced Parsing

```bash
# Parse single HTML file
python main.py parse --input email.html --format markdown --strategy auto

# Convert EML directory to Markdown
python main.py parse --input backup_folder --format markdown --clean

# Apply specific parsing strategy
python main.py parse --input newsletter.html --strategy readability
```

#### EML to Markdown Conversion

```bash
# Convert single EML file
python src/parsers/gmail_eml_to_markdown_cleaner.py --file email.eml

# Convert entire backup directory
python src/parsers/gmail_eml_to_markdown_cleaner.py --base backup_folder --year 2025

# Batch conversion with cleaning
python src/parsers/gmail_eml_to_markdown_cleaner.py --base backup_folder --clean
```

### Sample Scenarios

#### Pre-built Workflows

```bash
# List available scenarios
python main.py samples list

# Run specific scenarios
python main.py samples unread      # Backup all unread emails
python main.py samples newsletters # Backup newsletters by sender
python main.py samples services    # Backup service notifications
python main.py samples important   # Backup important emails
```

#### Custom Scenario Development

```python
# Create custom scenario in examples/samples.py
def scenario_custom():
    """Custom backup scenario"""
    run_gmail_fetcher(
        query="your-custom-query",
        max_emails=1000,
        output_dir="custom_backup",
        format_type="both",
        organize="date"
    )
```

---

## Advanced Features

### AI Newsletter Management

#### Detection Configuration

The AI newsletter detection system uses configurable patterns stored in `config/app/config.json`:

```json
{
  "ai_keywords": [
    "artificial intelligence", "AI", "machine learning", "ML",
    "deep learning", "neural network", "LLM", "GPT", "ChatGPT",
    "OpenAI", "Anthropic", "Claude", "automation", "AI tools"
  ],
  "ai_newsletter_domains": [
    "theresanaiforthat.com", "mindstream.news", "futurepedia.io",
    "newsletter.futurepedia.io", "aibreakfast.com", "deeplearning.ai"
  ],
  "confidence_weights": {
    "keyword_in_subject": 0.4,
    "keyword_in_body": 0.2,
    "domain_match": 0.6,
    "newsletter_pattern": 0.3,
    "unsubscribe_link": 0.2
  },
  "decision_threshold": {
    "delete": 0.8,
    "flag": 0.6
  }
}
```

#### AI Cleanup Operations

```bash
# Dry run analysis (recommended first step)
python main.py tools ai-cleanup --input email_data.json

# Actual deletion with custom threshold
python main.py tools ai-cleanup --input email_data.json --delete --threshold 0.8

# Live Gmail integration
python src/core/gmail_api_client.py --credentials config/security/credentials.json --max-emails 1000 --dry-run
```

#### Detection Quality Metrics

The system provides detailed metrics for detection accuracy:

- **Precision**: Percentage of correctly identified AI newsletters
- **Recall**: Percentage of AI newsletters successfully detected
- **F1 Score**: Harmonic mean of precision and recall
- **Confidence Distribution**: Histogram of confidence scores
- **False Positive Rate**: Incorrectly flagged emails

### Multi-Strategy Content Parsing

#### Parsing Strategy Selection

```python
PARSING_STRATEGIES = {
    'auto': {
        'description': 'Automatically select best strategy based on content analysis',
        'use_case': 'Default for mixed content types'
    },
    'readability': {
        'description': 'Extract main content using readability algorithm',
        'use_case': 'News articles, blog posts, long-form content'
    },
    'trafilatura': {
        'description': 'Advanced content extraction with NLP techniques',
        'use_case': 'Complex layouts, embedded content'
    },
    'html2text': {
        'description': 'Standard HTML to text conversion',
        'use_case': 'Simple emails, plain formatting'
    },
    'markdownify': {
        'description': 'Direct HTML to Markdown transformation',
        'use_case': 'Preserve complex formatting, tables, lists'
    }
}
```

#### Quality Assessment

Each parsing strategy is evaluated on multiple criteria:

- **Content Completeness**: Percentage of original content preserved
- **Formatting Quality**: Markdown syntax correctness
- **Link Preservation**: Functional hyperlinks maintained
- **Media Handling**: Images and embedded content processing
- **Performance**: Processing time and resource usage

### Backup Management Tools

#### PowerShell Automation Scripts

##### Backup Folder Merging
```powershell
# Merge backup folders by year
.\scripts\backup\move_backup_years.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -DryRun

# Execute merge
.\scripts\backup\move_backup_years.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025
```

##### Email Deduplication
```powershell
# Deduplicate with size preference
.\scripts\backup\dedupe_merge.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -Prefer larger -DryRun

# Deduplicate with date preference
.\scripts\backup\dedupe_merge.ps1 -Source backup_part2 -Destination backup_main -Years 2024,2025 -Prefer newer
```

#### Maintenance Operations

```bash
# Cleanup and reorganization
python main.py tools cleanup --target backup_folder --type all

# Markdown formatting standardization
python main.py tools cleanup --target backup_folder --type markdown

# Duplicate detection and removal
python main.py tools cleanup --target backup_folder --type duplicates
```

---

## Configuration Management

### Configuration File Structure

```
config/
├── app/
│   ├── gmail_fetcher_config.json    # Main fetcher settings
│   └── config.json                  # AI detection patterns
├── security/
│   ├── credentials.json             # OAuth credentials (user-provided)
│   └── token.json                   # Generated auth tokens
└── organizer_config.json            # File organization rules
```

### Main Fetcher Configuration

**File**: `config/app/gmail_fetcher_config.json`

```json
{
  "common_queries": {
    "march_2025": "after:2025/02/28 before:2025/04/01",
    "unread_only": "is:unread",
    "newsletters": "from:(theresanaiforthat.com OR mindstream.news OR futurepedia.io)",
    "ai_content": "subject:(AI OR artificial intelligence OR machine learning OR ML OR LLM)",
    "service_notifications": "from:(namecheap.com OR pythonanywhere.com OR zoho.com)",
    "last_6_months": "newer_than:6m",
    "large_emails": "larger:10M",
    "with_attachments": "has:attachment"
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
      "from:noreply older_than:6m",
      "subject:newsletter older_than:6m"
    ],
    "auto_archive_queries": [
      "category:updates older_than:1m",
      "from:(github.com OR stackoverflow.com) older_than:3m"
    ]
  }
}
```

### AI Detection Configuration

**File**: `config/app/config.json`

```json
{
  "ai_keywords": [
    "artificial intelligence", "AI", "machine learning", "ML",
    "deep learning", "neural network", "LLM", "GPT", "ChatGPT",
    "OpenAI", "Anthropic", "Claude", "automation", "AI tools",
    "generative AI", "foundation model", "transformer", "BERT"
  ],
  "ai_newsletter_domains": [
    "theresanaiforthat.com", "mindstream.news", "futurepedia.io",
    "newsletter.futurepedia.io", "aibreakfast.com", "deeplearning.ai",
    "import-ai.com", "thebatch.ai", "artificialintelligence-news.com"
  ],
  "newsletter_patterns": [
    "weekly roundup", "daily digest", "newsletter", "update",
    "briefing", "summary", "recap", "highlights"
  ],
  "unsubscribe_patterns": [
    "unsubscribe", "opt out", "manage preferences",
    "update subscription", "email preferences"
  ],
  "confidence_weights": {
    "keyword_in_subject": 0.4,
    "keyword_in_body": 0.2,
    "domain_match": 0.6,
    "newsletter_pattern": 0.3,
    "unsubscribe_link": 0.2
  },
  "decision_threshold": {
    "delete": 0.8,
    "flag": 0.6,
    "review": 0.4
  }
}
```

### Configuration Management Commands

```bash
# Show current configuration
python main.py config --show

# Initialize default configuration
python main.py config --setup

# Validate configuration files
python main.py config --validate
```

---

## Automation & Scripts

### Cross-Platform Scripts

#### Windows Batch Files

##### Quick Start (`scripts/setup/quick_start.bat`)
```batch
@echo off
echo Gmail Fetcher - Quick Setup and Run
echo ===================================

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Install dependencies
if exist requirements.txt (
    echo Installing Python dependencies...
    pip install -r requirements.txt
) else (
    echo WARNING: requirements.txt not found
)

REM Check credentials
if not exist credentials.json (
    echo ERROR: credentials.json not found!
    echo Please follow setup instructions to configure Gmail API
    pause
    exit /b 1
)

REM Run authentication test
python src/gmail_fetcher.py --auth-only
```

##### Comprehensive Run (`scripts/operations/run_comprehensive.bat`)
```batch
@echo off
setlocal

echo Running Comprehensive Gmail Backup Suite
echo ==========================================

REM Backup unread emails
echo [1/4] Backing up unread emails...
python src/gmail_fetcher.py --query "is:unread" --max 1000 --output backup_unread

REM Backup newsletters
echo [2/4] Backing up newsletters...
python src/gmail_fetcher.py --query "from:(newsletter OR digest)" --max 500 --output backup_newsletters --organize sender

REM AI newsletter analysis
echo [3/4] Analyzing AI newsletters...
python src/gmail_ai_newsletter_cleaner.py backup_unread/email_data.json

REM Convert to clean markdown
echo [4/4] Converting to clean markdown...
python src/gmail_eml_to_markdown_cleaner.py --base backup_unread --year 2025

echo Comprehensive backup completed!
pause
```

#### PowerShell Scripts

##### Advanced Setup (`scripts/setup/quick_start.ps1`)
```powershell
#!/usr/bin/env pwsh

Write-Host "Gmail Fetcher - Advanced Setup" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Function to test command availability
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Check Python installation
if (Test-Command python) {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    exit 1
}

# Check pip and install dependencies
if (Test-Path "requirements.txt") {
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Blue
    try {
        pip install -r requirements.txt
        Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error installing dependencies: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Advanced dependency installation
if (Test-Path "docs/legacy/requirements_advanced.txt") {
    $response = Read-Host "Install advanced processing dependencies? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        pip install -r docs/legacy/requirements_advanced.txt
        Write-Host "✅ Advanced dependencies installed" -ForegroundColor Green
    }
}

# Configuration validation
Write-Host "🔧 Validating configuration..." -ForegroundColor Blue

if (-not (Test-Path "config/security/credentials.json")) {
    Write-Host "❌ Missing credentials.json" -ForegroundColor Red
    Write-Host "Setup Instructions:" -ForegroundColor Yellow
    Write-Host "1. Visit https://console.cloud.google.com/"
    Write-Host "2. Create project and enable Gmail API"
    Write-Host "3. Create OAuth 2.0 credentials"
    Write-Host "4. Save as config/security/credentials.json"
    exit 1
}

# Test authentication
Write-Host "🔐 Testing Gmail API authentication..." -ForegroundColor Blue
python main.py fetch --auth-only

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Setup completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  python main.py samples list        # View available scenarios"
    Write-Host "  python main.py fetch --help        # View fetch options"
    Write-Host "  python main.py samples unread      # Backup unread emails"
} else {
    Write-Host "❌ Authentication failed. Please check your setup." -ForegroundColor Red
    exit 1
}
```

##### Backup Management (`scripts/backup/move_backup_years.ps1`)
```powershell
#!/usr/bin/env pwsh

param(
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$Destination,
    [Parameter(Mandatory=$true)][string[]]$Years,
    [switch]$DryRun
)

Write-Host "Backup Folder Merger" -ForegroundColor Cyan
Write-Host "Source: $Source" -ForegroundColor Yellow
Write-Host "Destination: $Destination" -ForegroundColor Yellow
Write-Host "Years: $($Years -join ', ')" -ForegroundColor Yellow
Write-Host "Mode: $(if ($DryRun) { 'DRY RUN' } else { 'EXECUTE' })" -ForegroundColor $(if ($DryRun) { 'Green' } else { 'Red' })

foreach ($year in $Years) {
    $sourcePath = Join-Path $Source $year
    $destPath = Join-Path $Destination $year

    if (Test-Path $sourcePath) {
        Write-Host "Processing year $year..." -ForegroundColor Blue

        $files = Get-ChildItem -Path $sourcePath -Recurse -File
        Write-Host "  Found $($files.Count) files" -ForegroundColor Gray

        if (-not $DryRun) {
            if (-not (Test-Path $destPath)) {
                New-Item -ItemType Directory -Path $destPath -Force | Out-Null
            }

            Copy-Item -Path "$sourcePath\*" -Destination $destPath -Recurse -Force
            Write-Host "  ✅ Copied to destination" -ForegroundColor Green
        } else {
            Write-Host "  📋 Would copy to $destPath" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠️  Year $year not found in source" -ForegroundColor Yellow
    }
}

Write-Host "Backup merge $(if ($DryRun) { 'analysis' } else { 'operation' }) completed!" -ForegroundColor Green
```

### Automation Workflows

#### Scheduled Backup Workflow

**Windows Task Scheduler Configuration**:
```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-01-01T02:00:00</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-File "C:\path\to\gmail_fetcher\scripts\operations\daily_backup.ps1"</Arguments>
    </Exec>
  </Actions>
</Task>
```

**Linux Cron Configuration**:
```bash
# Daily backup at 2 AM
0 2 * * * /usr/bin/python3 /path/to/gmail_fetcher/main.py samples unread

# Weekly newsletter backup on Sundays at 3 AM
0 3 * * 0 /usr/bin/python3 /path/to/gmail_fetcher/main.py samples newsletters

# Monthly AI cleanup on first day of month at 4 AM
0 4 1 * * /usr/bin/python3 /path/to/gmail_fetcher/main.py tools ai-cleanup --input /path/to/data.json --delete
```

---

## API Integration

### Gmail API Implementation

#### Authentication Flow

```python
class GmailAuthenticator:
    """Handle Gmail API authentication with OAuth 2.0"""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, credentials_file: str, token_file: str):
        self.credentials_file = credentials_file
        self.token_file = token_file

    def authenticate(self) -> bool:
        """Authenticate with Gmail API"""
        creds = None

        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        return True
```

#### API Rate Limiting

The Gmail API has the following quotas:
- **Quota Units per Day**: 1,000,000,000
- **Quota Units per 100 seconds per user**: 250,000,000
- **Quota Units per 100 seconds**: 1,000,000,000

**Rate Limiting Implementation**:
```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests = []

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests
                        if now - req_time < timedelta(minutes=1)]

        if len(self.requests) >= self.max_requests:
            sleep_time = 60 - (now - self.requests[0]).total_seconds()
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.requests.append(now)
```

#### Message Processing Pipeline

```python
class MessageProcessor:
    """Process Gmail messages with error handling and retries"""

    def __init__(self, service, rate_limiter):
        self.service = service
        self.rate_limiter = rate_limiter

    def get_message_batch(self, message_ids: List[str]) -> List[Dict]:
        """Efficiently fetch multiple messages"""
        results = []

        for message_id in message_ids:
            self.rate_limiter.wait_if_needed()

            try:
                message = self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()
                results.append(message)

            except HttpError as error:
                if error.resp.status == 429:  # Rate limit exceeded
                    time.sleep(60)  # Wait 1 minute
                    continue
                elif error.resp.status == 404:  # Message not found
                    logger.warning(f"Message {message_id} not found")
                    continue
                else:
                    logger.error(f"Error fetching message {message_id}: {error}")
                    continue

        return results
```

### Error Handling Strategies

#### Network Resilience

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class ResilientGmailClient:
    """Gmail client with comprehensive error handling"""

    def __init__(self):
        self.setup_retry_strategy()

    def setup_retry_strategy(self):
        """Configure retry strategy for network requests"""
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["GET", "POST"],
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
```

#### Data Integrity Validation

```python
class DataValidator:
    """Validate downloaded email data integrity"""

    @staticmethod
    def validate_eml_structure(eml_content: str) -> bool:
        """Validate EML file structure"""
        try:
            msg = email.message_from_string(eml_content)

            # Check required headers
            required_headers = ['Message-ID', 'Date', 'From']
            for header in required_headers:
                if header not in msg:
                    return False

            # Validate date format
            date_str = msg.get('Date')
            if date_str:
                parsedate_to_datetime(date_str)

            return True

        except Exception as e:
            logger.error(f"EML validation failed: {e}")
            return False

    @staticmethod
    def validate_markdown_structure(md_content: str) -> bool:
        """Validate Markdown file structure"""
        lines = md_content.split('\n')

        # Check for metadata table
        has_metadata = any('|' in line for line in lines[:20])

        # Check for content section
        has_content = len(lines) > 20

        return has_metadata and has_content
```

---

## Troubleshooting

### Common Issues and Solutions

#### Authentication Problems

**Issue**: "Error: credentials.json not found"
```
❌ Error: credentials.json not found!
📋 Setup Instructions:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download as 'credentials.json'
```

**Solution**:
1. Verify file exists: `ls -la credentials.json`
2. Check file permissions: `chmod 644 credentials.json`
3. Validate JSON syntax: `python -m json.tool credentials.json`
4. Ensure proper OAuth scope configuration

**Issue**: "Token has been expired or revoked"
```
❌ Error: Token has been expired or revoked
google.auth.exceptions.RefreshError: ('invalid_grant: Token has been expired or revoked.')
```

**Solution**:
```bash
# Remove expired token
rm token.json

# Re-authenticate
python main.py fetch --auth-only
```

#### Gmail API Quota Issues

**Issue**: "Quota exceeded for quota metric 'Requests' and limit 'Requests per 100 seconds'"

**Solution**:
```python
# Implement exponential backoff
import time
import random

def exponential_backoff(attempt: int) -> float:
    """Calculate backoff time with jitter"""
    base_delay = 2 ** attempt
    jitter = random.uniform(0.5, 1.5)
    return min(base_delay * jitter, 300)  # Max 5 minutes

# Usage in API calls
for attempt in range(5):
    try:
        result = api_call()
        break
    except QuotaExceeded:
        delay = exponential_backoff(attempt)
        time.sleep(delay)
```

#### File System Issues

**Issue**: "PermissionError: [Errno 13] Permission denied"

**Solution**:
```bash
# Windows: Run as administrator or change directory permissions
icacls "C:\path\to\gmail_fetcher" /grant Users:F

# Linux/macOS: Fix ownership and permissions
sudo chown -R $USER:$USER /path/to/gmail_fetcher
chmod -R 755 /path/to/gmail_fetcher
```

**Issue**: "FileNotFoundError: No such file or directory"

**Solution**:
```bash
# Verify working directory
pwd

# Check required files exist
ls -la requirements.txt
ls -la config/security/credentials.json

# Create missing directories
mkdir -p config/security
mkdir -p logs
mkdir -p backup
```

#### Content Processing Issues

**Issue**: "UnicodeDecodeError: 'utf-8' codec can't decode byte"

**Solution**:
```python
import chardet

def safe_decode(byte_content: bytes) -> str:
    """Safely decode bytes with encoding detection"""
    try:
        # Try UTF-8 first
        return byte_content.decode('utf-8')
    except UnicodeDecodeError:
        # Detect encoding
        detected = chardet.detect(byte_content)
        encoding = detected.get('encoding', 'utf-8')

        try:
            return byte_content.decode(encoding)
        except UnicodeDecodeError:
            # Fallback with error handling
            return byte_content.decode('utf-8', errors='replace')
```

**Issue**: "HTML parsing failed: lxml not found"

**Solution**:
```bash
# Install parsing dependencies
pip install lxml beautifulsoup4 html5lib

# Or use alternative parser
pip install html-parser
```

### Diagnostic Tools

#### System Health Check

```bash
# Create health check script
cat > health_check.py << 'EOF'
#!/usr/bin/env python3
"""Gmail Fetcher System Health Check"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False

def check_dependencies():
    """Check required dependencies"""
    required = [
        'google-api-python-client',
        'google-auth-oauthlib',
        'html2text'
    ]

    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)

    return len(missing) == 0

def check_configuration():
    """Check configuration files"""
    config_files = [
        'config/security/credentials.json',
        'config/app/gmail_fetcher_config.json'
    ]

    all_present = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file}")

            # Validate JSON syntax
            try:
                with open(config_file, 'r') as f:
                    json.load(f)
                print(f"✅ {config_file} (valid JSON)")
            except json.JSONDecodeError as e:
                print(f"❌ {config_file} (invalid JSON): {e}")
                all_present = False
        else:
            print(f"❌ {config_file} (missing)")
            all_present = False

    return all_present

def main():
    print("Gmail Fetcher System Health Check")
    print("=" * 40)

    python_ok = check_python_version()
    deps_ok = check_dependencies()
    config_ok = check_configuration()

    print("\nSummary:")
    if python_ok and deps_ok and config_ok:
        print("✅ System is ready")
        return 0
    else:
        print("❌ System has issues - see above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

# Run health check
python health_check.py
```

#### Log Analysis

```bash
# Create log analysis script
cat > analyze_logs.py << 'EOF'
#!/usr/bin/env python3
"""Analyze Gmail Fetcher logs for common issues"""

import re
import sys
from collections import Counter
from pathlib import Path

def analyze_log_file(log_path: Path):
    """Analyze single log file"""
    if not log_path.exists():
        print(f"Log file not found: {log_path}")
        return

    with open(log_path, 'r') as f:
        content = f.read()

    # Extract error patterns
    error_patterns = {
        'Authentication': r'auth.*error|credential.*error|token.*error',
        'Rate Limiting': r'quota.*exceeded|rate.*limit|429',
        'Network': r'connection.*error|timeout|network.*error',
        'File System': r'permission.*denied|no such file|disk.*full',
        'API Errors': r'api.*error|http.*error|[45]\d\d'
    }

    print(f"\nAnalyzing: {log_path}")
    print("-" * 40)

    for category, pattern in error_patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            print(f"{category}: {len(matches)} occurrences")

    # Count status messages
    success_count = len(re.findall(r'✅|success', content, re.IGNORECASE))
    error_count = len(re.findall(r'❌|error|fail', content, re.IGNORECASE))

    print(f"\nSummary:")
    print(f"  Success messages: {success_count}")
    print(f"  Error messages: {error_count}")
    print(f"  Success rate: {success_count/(success_count+error_count)*100:.1f}%")

def main():
    log_dir = Path("logs")

    if not log_dir.exists():
        print("No logs directory found")
        return

    log_files = list(log_dir.glob("*.log"))

    if not log_files:
        print("No log files found")
        return

    for log_file in sorted(log_files):
        analyze_log_file(log_file)

if __name__ == "__main__":
    main()
EOF

# Run log analysis
python analyze_logs.py
```

---

## Performance Considerations

### Gmail API Optimization

#### Batch Processing

```python
class BatchProcessor:
    """Optimize Gmail API calls with batching"""

    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size

    def process_messages_in_batches(self, message_ids: List[str]) -> List[Dict]:
        """Process messages in optimized batches"""
        results = []

        for i in range(0, len(message_ids), self.batch_size):
            batch = message_ids[i:i + self.batch_size]

            # Use batch request to get multiple messages efficiently
            batch_request = self.service.new_batch_http_request()

            for msg_id in batch:
                batch_request.add(
                    self.service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='metadata',
                        metadataHeaders=['Date', 'From', 'Subject']
                    ),
                    callback=self._batch_callback
                )

            batch_request.execute()

        return results
```

#### Memory Management

```python
import gc
import psutil
from typing import Generator

class MemoryEfficientProcessor:
    """Process large email sets with controlled memory usage"""

    def __init__(self, memory_limit_mb: int = 1024):
        self.memory_limit = memory_limit_mb * 1024 * 1024  # Convert to bytes

    def process_large_dataset(self, message_ids: List[str]) -> Generator[Dict, None, None]:
        """Process messages with memory monitoring"""
        processed_count = 0

        for message_id in message_ids:
            # Check memory usage
            memory_usage = psutil.Process().memory_info().rss

            if memory_usage > self.memory_limit:
                # Force garbage collection
                gc.collect()

                # If still over limit, pause processing
                if psutil.Process().memory_info().rss > self.memory_limit:
                    logger.warning(f"Memory usage high: {memory_usage / 1024 / 1024:.1f}MB")
                    time.sleep(1)

            # Process message
            message_data = self.get_message_details(message_id)

            if message_data:
                yield message_data
                processed_count += 1

                # Periodic progress report
                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} messages")
```

#### Concurrent Processing

```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import threading

class ConcurrentEmailProcessor:
    """Process emails concurrently while respecting rate limits"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.rate_limiter = threading.Semaphore(max_workers)

    async def process_message_async(self, session: aiohttp.ClientSession, message_id: str) -> Dict:
        """Process single message asynchronously"""
        with self.rate_limiter:
            # Simulate API call with proper delay
            await asyncio.sleep(0.1)  # Rate limiting

            # Actual processing would happen here
            return await self.fetch_message_data(session, message_id)

    async def process_messages_concurrent(self, message_ids: List[str]) -> List[Dict]:
        """Process multiple messages concurrently"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.process_message_async(session, msg_id)
                for msg_id in message_ids
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            valid_results = [r for r in results if not isinstance(r, Exception)]

            return valid_results
```

### File I/O Optimization

#### Streaming File Processing

```python
import mmap
from pathlib import Path

class StreamingFileProcessor:
    """Process large files efficiently using streaming"""

    def process_large_eml_file(self, file_path: Path) -> Generator[email.message.EmailMessage, None, None]:
        """Process large EML files without loading into memory"""
        with open(file_path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                # Process file in chunks
                chunk_size = 1024 * 1024  # 1MB chunks

                for i in range(0, len(mmapped_file), chunk_size):
                    chunk = mmapped_file[i:i + chunk_size]

                    try:
                        # Parse email from chunk
                        msg = email.message_from_bytes(chunk)
                        yield msg
                    except Exception as e:
                        logger.warning(f"Failed to parse chunk at offset {i}: {e}")
                        continue
```

#### Efficient Directory Operations

```python
import os
from concurrent.futures import ProcessPoolExecutor

class ParallelDirectoryProcessor:
    """Process directory trees in parallel"""

    def __init__(self, max_processes: int = None):
        self.max_processes = max_processes or os.cpu_count()

    def process_directory_parallel(self, base_dir: Path, file_pattern: str = "*.eml") -> List[Path]:
        """Process directory tree with parallel workers"""

        # Find all matching files
        all_files = list(base_dir.rglob(file_pattern))

        # Split into chunks for parallel processing
        chunk_size = max(1, len(all_files) // self.max_processes)
        file_chunks = [all_files[i:i + chunk_size] for i in range(0, len(all_files), chunk_size)]

        processed_files = []

        with ProcessPoolExecutor(max_workers=self.max_processes) as executor:
            futures = [
                executor.submit(self.process_file_chunk, chunk)
                for chunk in file_chunks
            ]

            for future in futures:
                try:
                    chunk_results = future.result(timeout=300)  # 5 minute timeout
                    processed_files.extend(chunk_results)
                except Exception as e:
                    logger.error(f"Chunk processing failed: {e}")

        return processed_files

    def process_file_chunk(self, files: List[Path]) -> List[Path]:
        """Process a chunk of files in a separate process"""
        processed = []

        for file_path in files:
            try:
                # Process individual file
                self.process_single_file(file_path)
                processed.append(file_path)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")

        return processed
```

### Performance Monitoring

#### Metrics Collection

```python
import time
import statistics
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class PerformanceMetrics:
    operation: str
    duration: float
    memory_usage: int
    items_processed: int
    success_rate: float

class PerformanceMonitor:
    """Monitor and collect performance metrics"""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []

    @contextmanager
    def measure_operation(self, operation_name: str):
        """Context manager to measure operation performance"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss

            duration = end_time - start_time
            memory_delta = end_memory - start_memory

            logger.info(f"{operation_name} completed in {duration:.2f}s, memory delta: {memory_delta / 1024 / 1024:.1f}MB")

    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        if not self.metrics:
            return "No performance data available"

        # Group metrics by operation
        by_operation = {}
        for metric in self.metrics:
            if metric.operation not in by_operation:
                by_operation[metric.operation] = []
            by_operation[metric.operation].append(metric)

        report_lines = ["Performance Report", "=" * 50]

        for operation, operation_metrics in by_operation.items():
            durations = [m.duration for m in operation_metrics]

            report_lines.extend([
                f"\n{operation}:",
                f"  Executions: {len(operation_metrics)}",
                f"  Avg Duration: {statistics.mean(durations):.2f}s",
                f"  Min Duration: {min(durations):.2f}s",
                f"  Max Duration: {max(durations):.2f}s",
                f"  Std Deviation: {statistics.stdev(durations) if len(durations) > 1 else 0:.2f}s"
            ])

        return "\n".join(report_lines)
```

---

## Security Best Practices

### Credential Management

#### Secure Storage

```python
import os
import json
import keyring
from cryptography.fernet import Fernet

class SecureCredentialManager:
    """Manage credentials securely using system keyring"""

    def __init__(self, service_name: str = "gmail_fetcher"):
        self.service_name = service_name
        self.encryption_key = self._get_or_create_encryption_key()

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key from system keyring"""
        key = keyring.get_password(self.service_name, "encryption_key")

        if not key:
            # Generate new key
            key = Fernet.generate_key().decode()
            keyring.set_password(self.service_name, "encryption_key", key)

        return key.encode()

    def store_credentials(self, credentials_data: Dict) -> None:
        """Store credentials securely"""
        # Encrypt credentials
        fernet = Fernet(self.encryption_key)
        encrypted_data = fernet.encrypt(json.dumps(credentials_data).encode())

        # Store in system keyring
        keyring.set_password(
            self.service_name,
            "oauth_credentials",
            encrypted_data.decode()
        )

    def retrieve_credentials(self) -> Dict:
        """Retrieve and decrypt credentials"""
        encrypted_data = keyring.get_password(self.service_name, "oauth_credentials")

        if not encrypted_data:
            raise ValueError("No stored credentials found")

        # Decrypt credentials
        fernet = Fernet(self.encryption_key)
        decrypted_data = fernet.decrypt(encrypted_data.encode())

        return json.loads(decrypted_data.decode())
```

#### File Permission Management

```python
import os
import stat
from pathlib import Path

class SecureFileManager:
    """Manage file permissions for sensitive data"""

    @staticmethod
    def secure_file_permissions(file_path: Path) -> None:
        """Set secure permissions on sensitive files"""
        # Owner read/write only (600)
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)

    @staticmethod
    def create_secure_directory(dir_path: Path) -> None:
        """Create directory with secure permissions"""
        dir_path.mkdir(parents=True, exist_ok=True)

        # Owner read/write/execute only (700)
        os.chmod(dir_path, stat.S_IRWXU)

    @staticmethod
    def validate_file_permissions(file_path: Path) -> bool:
        """Validate that file has secure permissions"""
        file_stat = file_path.stat()

        # Check that only owner has permissions
        permissions = stat.filemode(file_stat.st_mode)

        # Should be -rw------- (600)
        expected_permissions = ['-rw-------', '-r--------']

        return permissions in expected_permissions
```

### Data Privacy

#### Email Content Sanitization

```python
import re
from typing import Set

class EmailSanitizer:
    """Sanitize email content to remove sensitive information"""

    def __init__(self):
        # Patterns for sensitive data
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }

    def sanitize_content(self, content: str, preserve_domains: Set[str] = None) -> str:
        """Sanitize email content while preserving specified domains"""
        sanitized = content

        for pattern_name, pattern in self.patterns.items():
            if pattern_name == 'email' and preserve_domains:
                # Only sanitize emails not in preserve list
                sanitized = self._sanitize_emails_selective(sanitized, preserve_domains)
            else:
                # Replace with generic placeholder
                placeholder = f"[{pattern_name.upper()}_REDACTED]"
                sanitized = re.sub(pattern, placeholder, sanitized)

        return sanitized

    def _sanitize_emails_selective(self, content: str, preserve_domains: Set[str]) -> str:
        """Sanitize emails but preserve specified domains"""
        def email_replacer(match):
            email = match.group(0)
            domain = email.split('@')[1] if '@' in email else ''

            if domain in preserve_domains:
                return email  # Keep original
            else:
                return '[EMAIL_REDACTED]'

        return re.sub(self.patterns['email'], email_replacer, content)
```

#### Audit Logging

```python
import logging
import json
from datetime import datetime
from pathlib import Path

class SecurityAuditLogger:
    """Log security-relevant events for audit purposes"""

    def __init__(self, log_file: Path = Path("logs/security_audit.log")):
        self.log_file = log_file
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup secure audit logger"""
        logger = logging.getLogger("security_audit")
        logger.setLevel(logging.INFO)

        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # File handler with secure permissions
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)

        # JSON formatter for structured logging
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        # Secure log file permissions
        os.chmod(self.log_file, stat.S_IRUSR | stat.S_IWUSR)

        return logger

    def log_authentication_event(self, event_type: str, user_info: Dict, success: bool) -> None:
        """Log authentication events"""
        event = {
            "event_type": "authentication",
            "sub_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "user_email": user_info.get("email", "unknown"),
            "success": success,
            "source_ip": self._get_source_ip()
        }

        self.logger.info(json.dumps(event))

    def log_data_access_event(self, operation: str, resource: str, count: int) -> None:
        """Log data access events"""
        event = {
            "event_type": "data_access",
            "operation": operation,
            "resource": resource,
            "count": count,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.logger.info(json.dumps(event))

    def _get_source_ip(self) -> str:
        """Get source IP address if available"""
        # In a desktop application, this might not be applicable
        return "localhost"
```

### Compliance Considerations

#### GDPR Compliance

```python
from datetime import datetime, timedelta
from typing import Dict, List

class GDPRComplianceManager:
    """Manage GDPR compliance for email data"""

    def __init__(self):
        self.retention_periods = {
            'personal_emails': timedelta(days=2555),  # 7 years
            'business_emails': timedelta(days=2555),  # 7 years
            'marketing_emails': timedelta(days=1095), # 3 years
            'system_notifications': timedelta(days=365) # 1 year
        }

    def classify_email_for_retention(self, email_data: Dict) -> str:
        """Classify email for retention policy"""
        subject = email_data.get('subject', '').lower()
        sender = email_data.get('from', '').lower()

        # Classification logic
        if any(word in subject for word in ['unsubscribe', 'marketing', 'promotion']):
            return 'marketing_emails'
        elif any(word in sender for word in ['noreply', 'no-reply', 'system', 'notification']):
            return 'system_notifications'
        elif '@' in sender and not any(domain in sender for domain in ['gmail.com', 'yahoo.com', 'hotmail.com']):
            return 'business_emails'
        else:
            return 'personal_emails'

    def should_retain_email(self, email_data: Dict, current_date: datetime = None) -> bool:
        """Determine if email should be retained based on GDPR"""
        if current_date is None:
            current_date = datetime.now()

        email_date = datetime.fromisoformat(email_data.get('date', current_date.isoformat()))
        email_category = self.classify_email_for_retention(email_data)

        retention_period = self.retention_periods.get(email_category, timedelta(days=365))
        expiry_date = email_date + retention_period

        return current_date <= expiry_date

    def generate_retention_report(self, email_dataset: List[Dict]) -> Dict:
        """Generate GDPR retention compliance report"""
        current_date = datetime.now()

        categories = {}
        total_emails = len(email_dataset)
        retained_emails = 0

        for email_data in email_dataset:
            category = self.classify_email_for_retention(email_data)

            if category not in categories:
                categories[category] = {'total': 0, 'retained': 0, 'expired': 0}

            categories[category]['total'] += 1

            if self.should_retain_email(email_data, current_date):
                categories[category]['retained'] += 1
                retained_emails += 1
            else:
                categories[category]['expired'] += 1

        return {
            'report_date': current_date.isoformat(),
            'total_emails': total_emails,
            'retained_emails': retained_emails,
            'expired_emails': total_emails - retained_emails,
            'retention_rate': retained_emails / total_emails if total_emails > 0 else 0,
            'categories': categories
        }
```

---

## Development Guide

### Project Structure

```
gmail_fetcher/
├── src/                              # Source code
│   ├── core/                         # Core functionality
│   │   ├── __init__.py
│   │   ├── gmail_fetcher.py          # Main fetcher class
│   │   ├── gmail_api_client.py       # API integration
│   │   ├── gmail_ai_newsletter_cleaner.py  # AI detection
│   │   ├── email_classifier.py       # Email categorization
│   │   ├── email_database_importer.py # Database operations
│   │   ├── email_data_extractor.py   # Data extraction
│   │   └── email_plaintext_processor.py # Text processing
│   ├── parsers/                      # Content parsing
│   │   ├── __init__.py
│   │   ├── advanced_email_parser.py  # Multi-strategy parsing
│   │   └── gmail_eml_to_markdown_cleaner.py # EML conversion
│   ├── utils/                        # Utilities
│   │   ├── comprehensive_email_processor.py # Complete processor
│   │   └── gmail_organizer.py        # File organization
│   └── cleanup/                      # Maintenance tools
│       ├── cleanup_markdown.py       # Markdown cleanup
│       ├── markdown_post_fixer.py    # Post-processing
│       ├── markdown_post_fixer_stage2.py # Advanced fixes
│       └── regenerate_markdown_from_eml.py # Regeneration
├── scripts/                          # Automation scripts
│   ├── setup/                        # Setup and installation
│   │   ├── quick_start.bat           # Windows setup
│   │   ├── quick_start.ps1           # PowerShell setup
│   │   └── setup_and_test.bat        # Test setup
│   ├── operations/                   # Operational scripts
│   │   ├── quick_test.ps1            # Quick testing
│   │   ├── run_comprehensive.bat     # Full operation
│   │   └── run_comprehensive.ps1     # PowerShell operation
│   ├── backup/                       # Backup management
│   │   ├── dedupe_in_place.ps1       # In-place deduplication
│   │   ├── dedupe_merge.ps1          # Merge with deduplication
│   │   └── move_backup_years.ps1     # Year-based organization
│   └── maintenance/                  # Maintenance scripts
├── config/                           # Configuration
│   ├── app/                          # Application config
│   │   ├── gmail_fetcher_config.json # Main settings
│   │   └── config.json               # AI detection config
│   ├── security/                     # Security files
│   │   ├── credentials.json          # OAuth credentials (user)
│   │   └── token.json                # Generated tokens
│   └── organizer_config.json         # Organization rules
├── examples/                         # Examples and samples
│   ├── samples.py                    # Sample scenarios
│   └── example_usage.py              # Usage examples
├── docs/                             # Documentation
│   ├── legacy/                       # Legacy documentation
│   │   └── requirements_advanced.txt # Advanced dependencies
│   ├── AI_Summarization_Implementation_Plan.md
│   ├── AI_Summarizer_Design.md
│   ├── email_classification_report.md
│   ├── email_report_workflow.md
│   └── project_documentation_hub.md
├── logs/                             # Log files
├── backup/                           # Default backup location
├── main.py                           # Main orchestrator
├── requirements.txt                  # Core dependencies
├── README.md                         # Project readme
├── CLAUDE.md                         # Claude instructions
└── PROFESSIONAL_DOCUMENTATION.md    # This document
```

### Development Environment Setup

#### Prerequisites

```bash
# Create virtual environment
python -m venv gmail_fetcher_env

# Activate environment
# Windows:
gmail_fetcher_env\Scripts\activate
# Linux/macOS:
source gmail_fetcher_env/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -r docs/legacy/requirements_advanced.txt

# Install development tools
pip install pytest pytest-cov black flake8 mypy
```

#### Development Tools Configuration

**pytest configuration** (`pytest.ini`):
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --strict-markers
markers =
    integration: Integration tests requiring Gmail API
    unit: Unit tests that can run offline
    slow: Tests that take longer than 5 seconds
```

**Black configuration** (`pyproject.toml`):
```toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.mypy_cache
  | \.pytest_cache
  | \.venv
  | _build
  | backup
  | logs
)/
'''
```

**MyPy configuration** (`mypy.ini`):
```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-google.*]
ignore_missing_imports = True

[mypy-html2text.*]
ignore_missing_imports = True
```

### Testing Framework

#### Unit Tests

```python
# tests/test_gmail_fetcher.py
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.core.gmail_fetcher import GmailFetcher

class TestGmailFetcher:
    """Unit tests for GmailFetcher class"""

    @pytest.fixture
    def mock_service(self):
        """Mock Gmail service for testing"""
        service = Mock()
        service.users.return_value.getProfile.return_value.execute.return_value = {
            'emailAddress': 'test@example.com',
            'messagesTotal': 1000,
            'threadsTotal': 500
        }
        return service

    @pytest.fixture
    def fetcher(self, tmp_path):
        """Create GmailFetcher instance for testing"""
        credentials_file = tmp_path / "credentials.json"
        credentials_file.write_text(json.dumps({
            "client_id": "test_client_id",
            "client_secret": "test_client_secret"
        }))

        return GmailFetcher(
            credentials_file=str(credentials_file),
            token_file=str(tmp_path / "token.json")
        )

    def test_sanitize_filename(self, fetcher):
        """Test filename sanitization"""
        test_cases = [
            ("normal_filename", "normal_filename"),
            ("file<>name", "file__name"),
            ("file:with|chars", "file_with_chars"),
            ("a" * 250, "a" * 200)  # Length truncation
        ]

        for input_name, expected in test_cases:
            result = fetcher.sanitize_filename(input_name)
            assert result == expected

    def test_decode_base64(self, fetcher):
        """Test base64 decoding with padding"""
        # Test normal base64
        data = "SGVsbG8gV29ybGQ="  # "Hello World"
        result = fetcher.decode_base64(data)
        assert result == "Hello World"

        # Test URL-safe base64 without padding
        data = "SGVsbG8gV29ybGQ"  # Missing padding
        result = fetcher.decode_base64(data)
        assert result == "Hello World"

    @patch('src.core.gmail_fetcher.build')
    def test_authentication_success(self, mock_build, fetcher, mock_service):
        """Test successful authentication"""
        mock_build.return_value = mock_service

        with patch('src.core.gmail_fetcher.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value.valid = True

            result = fetcher.authenticate()
            assert result is True
            assert fetcher.service == mock_service

    def test_get_profile(self, fetcher, mock_service):
        """Test profile retrieval"""
        fetcher.service = mock_service

        profile = fetcher.get_profile()

        assert profile['email'] == 'test@example.com'
        assert profile['total_messages'] == 1000
        assert profile['total_threads'] == 500
```

#### Integration Tests

```python
# tests/test_integration.py
import pytest
import os
from pathlib import Path
from src.core.gmail_fetcher import GmailFetcher

@pytest.mark.integration
class TestGmailIntegration:
    """Integration tests requiring actual Gmail API access"""

    @pytest.fixture(scope="class")
    def real_fetcher(self):
        """Create real GmailFetcher for integration testing"""
        credentials_path = "config/security/credentials.json"

        if not Path(credentials_path).exists():
            pytest.skip("Integration tests require real Gmail credentials")

        return GmailFetcher(credentials_file=credentials_path)

    def test_authentication_real(self, real_fetcher):
        """Test authentication with real Gmail API"""
        result = real_fetcher.authenticate()
        assert result is True
        assert real_fetcher.service is not None

    def test_profile_retrieval_real(self, real_fetcher):
        """Test profile retrieval with real Gmail API"""
        real_fetcher.authenticate()
        profile = real_fetcher.get_profile()

        assert 'email' in profile
        assert 'total_messages' in profile
        assert isinstance(profile['total_messages'], int)

    @pytest.mark.slow
    def test_search_messages_real(self, real_fetcher):
        """Test message search with real Gmail API"""
        real_fetcher.authenticate()

        # Search for a small number of messages
        message_ids = real_fetcher.search_messages("is:unread", max_results=5)

        assert isinstance(message_ids, list)
        assert len(message_ids) <= 5
```

#### Performance Tests

```python
# tests/test_performance.py
import pytest
import time
from src.core.gmail_fetcher import GmailFetcher

@pytest.mark.slow
class TestPerformance:
    """Performance tests for critical operations"""

    def test_filename_sanitization_performance(self):
        """Test filename sanitization performance"""
        fetcher = GmailFetcher()

        # Test with 1000 filenames
        test_filenames = [f"test_file_{i}_with_special_chars<>:|?*" for i in range(1000)]

        start_time = time.time()

        for filename in test_filenames:
            fetcher.sanitize_filename(filename)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in under 1 second
        assert duration < 1.0

        # Performance metric
        rate = len(test_filenames) / duration
        print(f"Sanitization rate: {rate:.0f} filenames/second")

    def test_base64_decode_performance(self):
        """Test base64 decoding performance"""
        fetcher = GmailFetcher()

        # Create test data
        test_data = ["SGVsbG8gV29ybGQ=" for _ in range(1000)]

        start_time = time.time()

        for data in test_data:
            fetcher.decode_base64(data)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in under 0.5 seconds
        assert duration < 0.5
```

### Code Quality Standards

#### Style Guidelines

1. **PEP 8 Compliance**: All code must follow PEP 8 style guidelines
2. **Type Hints**: Use type hints for all function parameters and return values
3. **Docstrings**: Google-style docstrings for all classes and functions
4. **Error Handling**: Comprehensive exception handling with specific error types
5. **Logging**: Structured logging with appropriate levels

#### Example Code Standards

```python
from typing import Optional, List, Dict, Union
import logging

logger = logging.getLogger(__name__)

class EmailProcessor:
    """
    Process email content with various strategies.

    This class provides methods for parsing and converting email content
    from various formats to standardized outputs.

    Attributes:
        config (Dict): Configuration settings for processing
        logger (logging.Logger): Logger instance for this class

    Example:
        processor = EmailProcessor(config={'strategy': 'auto'})
        result = processor.process_email(email_data)
    """

    def __init__(self, config: Optional[Dict] = None) -> None:
        """
        Initialize EmailProcessor with configuration.

        Args:
            config: Optional configuration dictionary with processing settings

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config or {}
        self.logger = logger.getChild(self.__class__.__name__)

        if not self._validate_config():
            raise ValueError("Invalid configuration provided")

    def process_email(
        self,
        email_data: Dict,
        strategy: Optional[str] = None
    ) -> Union[str, None]:
        """
        Process email data using specified strategy.

        Args:
            email_data: Dictionary containing email content and metadata
            strategy: Optional strategy override for processing

        Returns:
            Processed email content as string, or None if processing failed

        Raises:
            ProcessingError: If email processing fails
            ValueError: If email_data format is invalid

        Example:
            email_data = {'subject': 'Test', 'body': '<p>Hello</p>'}
            result = processor.process_email(email_data, strategy='markdown')
        """
        try:
            self.logger.info(f"Processing email with strategy: {strategy}")

            # Validate input
            if not isinstance(email_data, dict):
                raise ValueError("email_data must be a dictionary")

            if 'body' not in email_data:
                raise ValueError("email_data must contain 'body' field")

            # Process email
            strategy = strategy or self.config.get('default_strategy', 'auto')
            result = self._apply_strategy(email_data, strategy)

            self.logger.info("Email processing completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Email processing failed: {str(e)}")
            raise ProcessingError(f"Failed to process email: {str(e)}") from e

    def _validate_config(self) -> bool:
        """
        Validate configuration settings.

        Returns:
            True if configuration is valid, False otherwise
        """
        # Implementation details...
        return True

    def _apply_strategy(self, email_data: Dict, strategy: str) -> str:
        """
        Apply processing strategy to email data.

        Args:
            email_data: Email content and metadata
            strategy: Processing strategy to apply

        Returns:
            Processed content
        """
        # Implementation details...
        return "processed_content"

class ProcessingError(Exception):
    """Custom exception for email processing errors."""
    pass
```

### Contributing Guidelines

#### Pull Request Process

1. **Fork Repository**: Create personal fork of the main repository
2. **Feature Branch**: Create feature branch from main (`git checkout -b feature/description`)
3. **Code Changes**: Implement changes following style guidelines
4. **Tests**: Add comprehensive tests for new functionality
5. **Documentation**: Update documentation for any API changes
6. **Quality Checks**: Run all quality checks locally
7. **Pull Request**: Submit PR with clear description and tests

#### Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.8

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: requirements-txt-fixer
EOF

# Install hooks
pre-commit install
```

#### Code Review Checklist

- [ ] **Functionality**: Code works as intended and meets requirements
- [ ] **Tests**: Comprehensive test coverage with unit and integration tests
- [ ] **Documentation**: Updated documentation and docstrings
- [ ] **Style**: Follows PEP 8 and project style guidelines
- [ ] **Type Safety**: Proper type hints throughout
- [ ] **Error Handling**: Robust error handling with specific exceptions
- [ ] **Performance**: No obvious performance issues
- [ ] **Security**: No security vulnerabilities introduced
- [ ] **Compatibility**: Works on all supported platforms

---

## Use Cases & Workflows

### Professional Email Management

#### Legal Compliance Archiving

**Scenario**: Law firm needs to archive client communications for compliance

```bash
# Archive all client emails by sender organization
python main.py fetch \
  --query "from:client-domain.com OR to:client-domain.com" \
  --organize sender \
  --format both \
  --output legal_archive_2025

# Convert to searchable markdown for review
python main.py parse \
  --input legal_archive_2025 \
  --format markdown \
  --clean

# Generate compliance report
python src/utils/compliance_reporter.py \
  --input legal_archive_2025 \
  --type gdpr \
  --output compliance_report.json
```

#### IT Support Email Analysis

**Scenario**: IT department analyzing support ticket patterns

```bash
# Collect support emails from last 6 months
python main.py fetch \
  --query "from:support@company.com OR subject:ticket newer_than:6m" \
  --max 5000 \
  --organize date \
  --output support_analysis

# Apply AI classification
python src/core/email_classifier.py \
  --input support_analysis \
  --categories "bug,feature_request,user_error,system_issue" \
  --output support_classification.json

# Generate analytics report
python src/utils/email_analytics.py \
  --input support_classification.json \
  --report support_trends.html
```

### Research and Academic Use

#### Communication Pattern Analysis

**Scenario**: Researcher studying email communication patterns

```bash
# Download organizational communications
python main.py fetch \
  --query "from:university.edu OR to:university.edu" \
  --max 10000 \
  --organize sender \
  --format markdown \
  --output research_corpus

# Apply content analysis
python src/parsers/advanced_email_parser.py \
  --input research_corpus \
  --strategy readability \
  --extract-entities \
  --output analysis_results.json

# Generate research dataset
python src/utils/research_dataset_generator.py \
  --input analysis_results.json \
  --anonymize \
  --format csv \
  --output research_dataset.csv
```

#### Newsletter Content Analysis

**Scenario**: Content researcher analyzing newsletter evolution

```bash
# Collect newsletters from specific sources
python main.py samples newsletters --max 2000

# Apply advanced parsing for content extraction
python src/parsers/advanced_email_parser.py \
  --input newsletters_ai \
  --strategy trafilatura \
  --extract-topics \
  --sentiment-analysis

# Generate trend analysis
python src/utils/newsletter_trend_analyzer.py \
  --input newsletters_ai \
  --output newsletter_trends.html
```

### Personal Productivity

#### Email Inbox Zero Workflow

**Scenario**: Professional implementing inbox zero methodology

```bash
# 1. Backup current state
python main.py samples unread

# 2. Identify and cleanup newsletters
python main.py tools ai-cleanup \
  --input backup_unread/email_data.json \
  --threshold 0.7

# 3. Organize important emails
python main.py fetch \
  --query "is:important OR is:starred" \
  --organize sender \
  --output important_archive

# 4. Process notifications separately
python main.py fetch \
  --query "category:updates OR category:social" \
  --organize date \
  --output notifications_archive

# 5. Clean up processed emails (dry run first)
python src/core/gmail_api_client.py \
  --batch-delete \
  --query "category:promotions older_than:3m" \
  --dry-run
```

#### Digital Minimalism Email Audit

**Scenario**: Individual conducting digital minimalism audit

```bash
# Download complete email history
python main.py fetch \
  --query "after:2020/01/01" \
  --max 50000 \
  --organize date \
  --output complete_archive

# Analyze subscription patterns
python src/core/email_classifier.py \
  --input complete_archive \
  --focus subscriptions \
  --generate-unsubscribe-list

# Identify high-volume senders
python src/utils/email_analytics.py \
  --input complete_archive \
  --analyze sender_volume \
  --threshold 50 \
  --output high_volume_senders.csv

# Create deletion plan
python src/utils/cleanup_planner.py \
  --input complete_archive \
  --strategy conservative \
  --output cleanup_plan.json
```

### Business Intelligence

#### Customer Communication Analysis

**Scenario**: Business analyzing customer email interactions

```bash
# Collect customer communications
python main.py fetch \
  --query "from:customers.com OR subject:support OR subject:inquiry" \
  --max 10000 \
  --organize sender \
  --output customer_communications

# Apply sentiment analysis
python src/utils/sentiment_analyzer.py \
  --input customer_communications \
  --model vader \
  --output sentiment_analysis.json

# Generate customer insights
python src/utils/customer_insights.py \
  --input sentiment_analysis.json \
  --metrics "satisfaction,response_time,issue_resolution" \
  --output customer_insights.html
```

#### Competitive Intelligence

**Scenario**: Marketing team monitoring competitor newsletters

```bash
# Collect competitor newsletters
python main.py fetch \
  --query "from:competitor1.com OR from:competitor2.com OR from:competitor3.com" \
  --organize sender \
  --format markdown \
  --output competitor_intelligence

# Extract key topics and announcements
python src/parsers/advanced_email_parser.py \
  --input competitor_intelligence \
  --extract-announcements \
  --extract-product-mentions \
  --output competitive_analysis.json

# Generate intelligence report
python src/utils/competitive_intelligence.py \
  --input competitive_analysis.json \
  --trends monthly \
  --output intelligence_report.html
```

### Advanced Automation Workflows

#### Multi-Account Management

**Scenario**: Managing multiple Gmail accounts with unified workflow

```python
# multi_account_manager.py
import asyncio
from pathlib import Path
from src.core.gmail_fetcher import GmailFetcher

class MultiAccountManager:
    """Manage multiple Gmail accounts with unified operations"""

    def __init__(self, accounts_config: Dict):
        self.accounts = accounts_config
        self.results = {}

    async def process_all_accounts(self, query: str, max_emails: int):
        """Process query across all configured accounts"""
        tasks = []

        for account_name, config in self.accounts.items():
            task = self.process_single_account(account_name, config, query, max_emails)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for account_name, result in zip(self.accounts.keys(), results):
            self.results[account_name] = result

    async def process_single_account(self, account_name: str, config: Dict, query: str, max_emails: int):
        """Process single account asynchronously"""
        fetcher = GmailFetcher(
            credentials_file=config['credentials_path'],
            token_file=config['token_path']
        )

        output_dir = f"multi_account_backup/{account_name}"

        try:
            fetcher.authenticate()
            fetcher.download_emails(
                query=query,
                max_emails=max_emails,
                output_dir=output_dir,
                format_type="both",
                organize_by="date"
            )
            return {"status": "success", "output_dir": output_dir}

        except Exception as e:
            return {"status": "error", "error": str(e)}

# Usage
accounts_config = {
    "work": {
        "credentials_path": "config/work_credentials.json",
        "token_path": "config/work_token.json"
    },
    "personal": {
        "credentials_path": "config/personal_credentials.json",
        "token_path": "config/personal_token.json"
    }
}

manager = MultiAccountManager(accounts_config)
asyncio.run(manager.process_all_accounts("is:unread", 1000))
```

#### Scheduled Maintenance Workflow

**Scenario**: Automated daily maintenance and cleanup

```bash
#!/bin/bash
# daily_maintenance.sh

echo "Starting daily Gmail maintenance workflow"

# 1. Backup recent emails
python main.py fetch \
  --query "newer_than:1d" \
  --max 500 \
  --output daily_backup_$(date +%Y%m%d)

# 2. AI newsletter cleanup
python main.py tools ai-cleanup \
  --input daily_backup_$(date +%Y%m%d)/email_data.json \
  --delete \
  --threshold 0.8

# 3. Update markdown archives
python main.py parse \
  --input daily_backup_$(date +%Y%m%d) \
  --format markdown \
  --clean

# 4. Merge with main archive
./scripts/backup/dedupe_merge.ps1 \
  -Source daily_backup_$(date +%Y%m%d) \
  -Destination main_archive \
  -Prefer newer

# 5. Cleanup old temporary backups
find . -name "daily_backup_*" -type d -mtime +7 -exec rm -rf {} \;

# 6. Generate daily report
python src/utils/daily_report_generator.py \
  --date $(date +%Y-%m-%d) \
  --output reports/daily_report_$(date +%Y%m%d).html

echo "Daily maintenance workflow completed"
```

### Custom Integration Examples

#### Slack Integration

```python
# slack_email_integration.py
import requests
import json
from src.core.gmail_fetcher import GmailFetcher

class SlackEmailNotifier:
    """Send email summaries to Slack"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_daily_summary(self, email_stats: Dict):
        """Send daily email summary to Slack"""
        message = {
            "text": "📧 Daily Email Summary",
            "attachments": [
                {
                    "color": "good",
                    "fields": [
                        {
                            "title": "New Emails",
                            "value": str(email_stats['new_emails']),
                            "short": True
                        },
                        {
                            "title": "AI Newsletters Cleaned",
                            "value": str(email_stats['ai_newsletters_cleaned']),
                            "short": True
                        },
                        {
                            "title": "Important Emails",
                            "value": str(email_stats['important_emails']),
                            "short": True
                        }
                    ]
                }
            ]
        }

        response = requests.post(self.webhook_url, json=message)
        return response.status_code == 200

# Usage
notifier = SlackEmailNotifier("https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
notifier.send_daily_summary({
    'new_emails': 45,
    'ai_newsletters_cleaned': 12,
    'important_emails': 3
})
```

#### Database Integration

```python
# database_email_integration.py
import sqlite3
import json
from datetime import datetime
from src.core.gmail_fetcher import GmailFetcher

class EmailDatabaseManager:
    """Manage email data in SQLite database"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                thread_id TEXT,
                subject TEXT,
                sender TEXT,
                recipient TEXT,
                date_sent DATETIME,
                date_processed DATETIME,
                content_type TEXT,
                has_attachments BOOLEAN,
                file_path TEXT,
                classification TEXT,
                sentiment_score REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_metrics (
                date DATE PRIMARY KEY,
                total_emails INTEGER,
                processed_emails INTEGER,
                ai_newsletters INTEGER,
                important_emails INTEGER,
                processing_time_seconds REAL
            )
        ''')

        conn.commit()
        conn.close()

    def store_email_batch(self, emails_data: List[Dict]):
        """Store batch of emails in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for email_data in emails_data:
            cursor.execute('''
                INSERT OR REPLACE INTO emails
                (id, thread_id, subject, sender, recipient, date_sent,
                 date_processed, content_type, has_attachments, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_data['id'],
                email_data.get('thread_id'),
                email_data.get('subject'),
                email_data.get('from'),
                email_data.get('to'),
                email_data.get('date'),
                datetime.now(),
                email_data.get('content_type', 'unknown'),
                email_data.get('has_attachments', False),
                email_data.get('file_path')
            ))

        conn.commit()
        conn.close()
```

---

This comprehensive documentation covers all aspects of the Gmail Fetcher Suite, from basic installation to advanced development workflows. The suite provides a powerful, extensible platform for Gmail management that can be adapted to various professional, research, and personal use cases.

For additional support or questions, refer to the troubleshooting section or consult the project's issue tracker for community assistance.