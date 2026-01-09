# Gmail Assistant

**A comprehensive Gmail management and backup solution with advanced email processing, AI-powered content analysis, and automated cleanup capabilities.**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Gmail API](https://img.shields.io/badge/Gmail%20API-v1-red.svg)](https://developers.google.com/gmail/api)
[![CI](https://github.com/user/gmail-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/user/gmail-assistant/actions)

> **v2.0.0 Breaking Changes**: This version introduces a new package structure and CLI.
> See [BREAKING_CHANGES.md](BREAKING_CHANGES.md) for migration guide.

## 🌟 Overview

Gmail Fetcher Suite is a powerful collection of tools designed to help you backup, analyze, and manage your Gmail emails efficiently. Whether you need to create archives, clean up AI newsletters, convert emails to readable formats, or analyze email content, this suite provides comprehensive solutions.

### Key Features

- 📥 **Email Backup & Archive**: Download emails in EML and Markdown formats
- 🤖 **AI Newsletter Detection**: Automatically identify and manage AI newsletters  
- 📝 **Advanced Content Parsing**: Convert HTML emails to clean Markdown with multiple strategies
- 🔄 **Backup Management**: Merge, deduplicate, and organize email backups
- ⚡ **Cross-Platform Scripts**: Windows batch files and PowerShell automation
- 🎯 **Gmail API Integration**: Direct inbox operations with real-time processing

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Gmail account with API access
- Google Cloud Console project (free)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gmail_assistant
   ```

2. **Install the package**
   ```bash
   # Standard installation
   pip install -e .

   # With development dependencies
   pip install -e ".[dev]"

   # With optional analysis features
   pip install -e ".[analysis,ui,advanced-parsing]"
   ```

3. **Set up Gmail API**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download as `credentials.json`

4. **Quick setup (Interactive)**
   ```bash
   # Windows
   quick_start.bat
   
   # PowerShell (Windows/Linux)
   .\quick_start.ps1
   ```

## 📁 Project Structure

```
gmail_assistant/
├── src/                          # Core source code
│   ├── gmail_assistant.py         # Main Gmail backup tool
│   ├── advanced_email_parser.py # Multi-strategy content parsing
│   ├── gmail_ai_newsletter_cleaner.py # AI newsletter detection
│   ├── gmail_api_client.py      # Gmail API integration
│   └── gmail_eml_to_markdown_cleaner.py # EML to Markdown converter
├── scripts/                      # Automation and utility scripts
│   ├── quick_start.bat          # Windows batch setup
│   ├── quick_start.ps1          # PowerShell setup  
│   ├── move_backup_years.ps1    # Backup folder merger
│   └── dedupe_merge.ps1         # Email deduplication
├── config/                       # Configuration files
│   ├── config.json              # AI detection patterns
│   └── gmail_assistant_config.json # Main fetcher settings
├── examples/                     # Example usage and samples
│   ├── samples.py               # Pre-built backup scenarios
│   └── example_usage.py         # AI cleaner demo
├── docs/                        # Documentation
│   ├── usage_deletion.md        # AI newsletter deletion guide
│   └── README2.md               # Additional documentation
├── requirements.txt             # Core dependencies
├── requirements_advanced.txt    # Advanced processing dependencies
└── README.md                    # This file
```

## 🛠️ Tools & Components

### Core Tools

#### 1. Gmail Fetcher (`gmail_assistant.py`)
The primary email backup tool with comprehensive search and organization capabilities.

```bash
# Download unread emails (new CLI)
gmail-assistant fetch --query "is:unread" --max-emails 1000

# Download by date range with organization
python src/gmail_assistant.py --query "after:2025/02/28 before:2025/04/01" --organize sender --format both

# Download AI newsletters specifically
python src/gmail_assistant.py --query "from:(deeplearning.ai OR theresanaiforthat.com)" --output ai_newsletters
```

**Features:**
- Gmail API integration with OAuth 2.0
- Multiple output formats (EML, Markdown, both)
- Organization by date or sender
- Advanced Gmail search query support
- Rate limiting and error handling

#### 2. Advanced Email Parser (`advanced_email_parser.py`)
Intelligent email content extraction with multiple parsing strategies.

```bash
# Parse HTML email with multiple strategies
python src/advanced_email_parser.py email_file.html
```

**Features:**
- Smart email type detection (newsletter, notification, marketing)
- Multiple parsing engines (readability, trafilatura, html2text, markdownify)
- Newsletter-specific extraction rules
- Quality scoring and automatic best-result selection
- Configurable content cleaning rules

#### 3. AI Newsletter Cleaner (`gmail_ai_newsletter_cleaner.py`)
Automated AI newsletter detection and management system.

```bash
# Analyze emails for AI newsletters (dry run)
python src/gmail_ai_newsletter_cleaner.py email_data.json

# Actually delete identified AI newsletters
python src/gmail_ai_newsletter_cleaner.py email_data.json --delete
```

**Features:**
- Pattern-based AI newsletter detection
- Configurable confidence scoring
- Dry-run mode with detailed logging
- Support for JSON/CSV email data
- Customizable detection rules

#### 4. Gmail API Client (`gmail_api_client.py`)
Direct Gmail operations for real-time email management.

```bash
# Fetch and analyze unread emails
python src/gmail_api_client.py --credentials credentials.json --max-emails 1000

# Actually delete AI newsletters from Gmail
python src/gmail_api_client.py --delete --max-emails 500
```

**Features:**
- Real-time Gmail inbox operations
- Batch email processing
- Trash vs permanent deletion options
- Comprehensive error handling
- Progress tracking and logging

#### 5. EML to Markdown Cleaner (`gmail_eml_to_markdown_cleaner.py`)
Professional email format converter with metadata preservation.

```bash
# Convert EML files to clean Markdown
python src/gmail_eml_to_markdown_cleaner.py --base backup_folder --year 2025
```

**Features:**
- EML to Markdown conversion with YAML front matter
- Attachment and inline image handling
- Content cleaning and formatting
- Metadata preservation
- Bulk processing capabilities

### Utility Scripts

#### Setup Scripts
- **`quick_start.bat`**: Windows batch file for interactive setup
- **`quick_start.ps1`**: PowerShell script for cross-platform setup

#### Backup Management
- **`move_backup_years.ps1`**: Merge backup folders by year with conflict resolution
- **`dedupe_merge.ps1`**: Deduplicate emails across backup folders using message IDs

#### Examples
- **`samples.py`**: Pre-built backup scenarios for common use cases
- **`example_usage.py`**: Demonstration of AI newsletter cleaner functionality

## 📋 Usage Scenarios

### 1. Basic Email Backup

```bash
# First-time authentication
python src/gmail_assistant.py --auth-only

# Backup all unread emails
python src/gmail_assistant.py --query "is:unread" --max 1000 --format both

# Organize by sender for easy browsing
python src/gmail_assistant.py --query "newer_than:6m" --organize sender --output recent_emails
```

### 2. AI Newsletter Management

```bash
# Step 1: Analyze existing emails for AI newsletters
python src/gmail_ai_newsletter_cleaner.py backup_emails.json

# Step 2: Review the generated log file
cat gmail_cleanup_*.txt

# Step 3: Delete AI newsletters if satisfied
python src/gmail_ai_newsletter_cleaner.py backup_emails.json --delete

# Alternative: Use Gmail API for direct deletion
python src/gmail_api_client.py --credentials credentials.json --delete
```

### 3. Professional Email Archive

```bash
# Step 1: Download emails in EML format
python src/gmail_assistant.py --query "important:true OR starred:true" --format eml --output important_archive

# Step 2: Convert to clean Markdown with metadata
python src/gmail_eml_to_markdown_cleaner.py --base important_archive --verbose

# Step 3: Apply advanced parsing for complex emails
python src/advanced_email_parser.py complex_newsletter.html
```

### 4. Bulk Cleanup Workflow

```bash
# Step 1: Backup everything first
python src/gmail_assistant.py --query "newer_than:2y" --max 5000 --output full_backup

# Step 2: Identify and backup AI newsletters separately
python src/gmail_assistant.py --query "subject:(AI OR newsletter OR digest)" --output newsletters --organize sender

# Step 3: Clean up AI newsletters from main inbox
python src/gmail_api_client.py --credentials credentials.json --delete --max-emails 2000

# Step 4: Merge and deduplicate backup folders
.\scripts\dedupe_merge.ps1 -Source newsletters -Destination full_backup -Years 2024,2025
```

### 5. Content Analysis Pipeline

```bash
# Step 1: Download specific content for analysis
python src/gmail_assistant.py --query "from:(research.ai OR papers.arxiv.org)" --format markdown --output research_emails

# Step 2: Apply advanced parsing for better content extraction
find research_emails -name "*.eml" -exec python src/advanced_email_parser.py {} \;

# Step 3: Convert to consistent format
python src/gmail_eml_to_markdown_cleaner.py --base research_emails --year 2025

# Step 4: Ready for AI analysis tools
# The clean markdown files are now ready for analysis with AI tools
```

## ⚙️ Configuration

### Gmail API Setup
1. **Google Cloud Console**: Create project and enable Gmail API
2. **OAuth Credentials**: Download `credentials.json` file
3. **Authentication**: Run with `--auth-only` flag first

### Configuration Files
The project uses two configuration files in the `config/` directory:

#### Gmail Fetcher Configuration (`config/gmail_assistant_config.json`)
Contains default settings and common queries:

```json
{
  "common_queries": {
    "unread_only": "is:unread",
    "newsletters": "from:(theresanaiforthat.com OR mindstream.news)",
    "ai_content": "subject:(AI OR artificial intelligence OR machine learning)"
  },
  "default_settings": {
    "max_emails": 500,
    "output_format": "both",
    "organize_by": "date"
  }
}
```

#### AI Newsletter Detection (`config/config.json`)
Edit `config/config.json` to customize AI detection:

```json
{
  "ai_keywords": ["artificial intelligence", "machine learning", "chatgpt"],
  "ai_newsletter_domains": ["deeplearning.ai", "openai.com"],
  "confidence_weights": {
    "ai_keywords_subject": 3,
    "known_domain": 4
  },
  "decision_threshold": {
    "minimum_confidence": 4,
    "minimum_reasons": 2
  }
}
```

### Advanced Parser Configuration
The advanced parser supports newsletter-specific rules:

```json
{
  "newsletter_patterns": {
    "theresanaiforthat.com": {
      "content_selectors": [".email-content", "#main-content"],
      "remove_selectors": [".unsubscribe", ".footer"],
      "preserve_images": true
    }
  }
}
```

## 🔍 Gmail Search Query Reference

### Time-Based Queries
- `after:2025/01/01` - After specific date
- `before:2025/04/01` - Before specific date  
- `newer_than:6m` - Last 6 months
- `older_than:1y` - Older than 1 year

### Content-Based Queries
- `subject:AI` - Subject contains "AI"
- `from:example.com` - From specific domain
- `to:me` - Sent to you
- `has:attachment` - Has attachments
- `is:unread` - Unread emails only
- `is:important` - Important emails
- `category:updates` - Update category
- `category:promotions` - Promotional emails

### Advanced Combinations
```bash
# Complex query examples
"is:unread AND subject:(AI OR newsletter) AND newer_than:3m"
"from:(noreply OR notifications) AND older_than:6m"
"has:attachment AND larger:5M AND older_than:1y"
```

## 📊 Output Formats

### EML Format
- Native email format preserving all headers and formatting
- Compatible with email clients (Thunderbird, Outlook, Apple Mail)
- Best for legal/compliance needs and complete data preservation

### Markdown Format
- Human-readable text format with metadata table
- Converts HTML to markdown automatically
- Great for searching, reading, and AI analysis
- Includes structured metadata (from, to, date, subject)

### Example Markdown Output
```markdown
---
source_file: backup/2025/03/email.eml
subject: "Weekly AI Newsletter"
from: ["AI Weekly <newsletter@aiweekly.co>"]
to: ["user@example.com"]
date: "2025-03-15T10:30:00+00:00"
message_id: "<12345@aiweekly.co>"
---

# Weekly AI Newsletter

This week in AI: breakthrough in transformer models...

## Key Highlights
- New GPT-4 capabilities
- Computer vision advances
- Industry updates

[Read more](https://example.com/article)
```

## 🛡️ Security & Privacy

### Data Handling
- **Read-only Gmail access**: Scripts only request read permissions
- **Local storage**: All data stored locally on your machine
- **No data transmission**: No email content sent to external services
- **Credential security**: Keep `credentials.json` and `token.json` private

### Best Practices
- Add credential files to `.gitignore`
- Use dry-run mode before any deletion operations
- Regularly backup your local email archives
- Review AI detection logs before confirming deletions

## 🔧 Troubleshooting

### Common Issues

**"credentials.json not found"**
- Download OAuth credentials from Google Cloud Console
- Ensure file is named exactly `credentials.json`

**"Authentication failed"**
- Delete `token.json` and re-run with `--auth-only`
- Verify Gmail API is enabled in Google Cloud Console

**"Too many requests"**
- Gmail API has rate limits
- Reduce `--max` parameter or add delays between requests

**"Unicode decode error"**
- Some emails have encoding issues
- The advanced parser handles most cases automatically

**"Permission denied" on PowerShell scripts**
- Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Performance Tips

1. **Start small**: Test with `--max 10` first
2. **Use specific queries**: More specific queries = faster downloads
3. **Regular backups**: Run weekly/monthly for ongoing backup
4. **Monitor file sizes**: Large attachments increase download time
5. **Use SSD storage**: Faster I/O for large backup operations

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements_advanced.txt

# Run tests
python -m pytest tests/

# Code formatting
black src/
flake8 src/
```

### Adding New Features
1. Follow existing code patterns and naming conventions
2. Add comprehensive error handling and logging
3. Include usage examples in docstrings
4. Test with various email types and edge cases

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gmail API** for email access capabilities
- **html2text** for HTML to Markdown conversion
- **BeautifulSoup** for HTML parsing and cleaning
- **readability** and **trafilatura** for content extraction
- Community contributors and testers

## 📞 Support

For questions, bug reports, or feature requests:
1. Check the troubleshooting section above
2. Review existing documentation in the `docs/` folder
3. Create an issue with detailed information about your use case

---

**Happy email management! 📧✨**