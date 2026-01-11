# Gmail Fetcher - Email Backup Tool

Download and backup Gmail emails as EML or Markdown files with full organization and search capabilities.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Google API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Gmail API**:
   - Search for "Gmail API" in the API Library
   - Click "Enable"
4. Create OAuth 2.0 Credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the JSON file as `credentials.json`
   - Place it in the same folder as `gmail_fetcher.py`

### 3. First Run (Authentication)
```bash
python gmail_fetcher.py --auth-only
```
This will open a browser for Gmail authorization and save your token.

## 📧 Usage Examples

### Basic Commands

**Download all unread emails:**
```bash
python gmail_fetcher.py --query "is:unread" --max 1000
```

**Download March 2025 emails:**
```bash
python gmail_fetcher.py --query "after:2025/02/28 before:2025/04/01" --max 500
```

**Download only AI newsletters:**
```bash
python gmail_fetcher.py --query "from:(theresanaiforthat.com OR mindstream.news OR futurepedia.io)" --max 200
```

**Download last 6 months, organize by sender:**
```bash
python gmail_fetcher.py --query "newer_than:6m" --organize sender --max 1000
```

### Output Formats

**EML only (native email format):**
```bash
python gmail_fetcher.py --format eml --query "is:unread"
```

**Markdown only (readable format):**
```bash
python gmail_fetcher.py --format markdown --query "is:unread"
```

**Both formats (default):**
```bash
python gmail_fetcher.py --format both --query "is:unread"
```

## 🗂️ Organization Options

**By Date (default):**
```
gmail_backup/
├── 2025/
│   ├── 03/
│   │   ├── 2025-03-31_120000_email1.eml
│   │   └── 2025-03-31_120000_email1.md
│   └── 04/
```

**By Sender:**
```
gmail_backup/
├── theresanaiforthat/
│   ├── 2025-03-31_120000_email1.eml
│   └── 2025-03-31_120000_email1.md
├── mindstream/
```

**No Organization:**
```
gmail_backup/
├── 2025-03-31_120000_email1.eml
├── 2025-03-31_120000_email1.md
├── 2025-03-30_150000_email2.eml
```

## 🔍 Advanced Search Queries

### Time-based
- `after:2025/01/01` - After specific date
- `before:2025/04/01` - Before specific date
- `newer_than:6m` - Last 6 months
- `older_than:1y` - Older than 1 year

### Content-based
- `subject:AI` - Subject contains "AI"
- `from:example.com` - From specific domain
- `to:me` - Sent to you
- `has:attachment` - Has attachments
- `is:unread` - Unread emails only
- `is:important` - Important emails
- `category:updates` - Update category
- `category:promotions` - Promotional emails

### Size-based
- `larger:10M` - Larger than 10MB
- `smaller:1M` - Smaller than 1MB

### Combine Queries
```bash
# Unread AI newsletters from last 3 months
python gmail_fetcher.py --query "is:unread AND subject:(AI OR newsletter) AND newer_than:3m"

# Large emails with attachments
python gmail_fetcher.py --query "has:attachment AND larger:5M"

# Service notifications to archive
python gmail_fetcher.py --query "from:(noreply OR notifications) AND older_than:6m"
```

## 🧹 Inbox Cleanup Strategy

### 1. Backup Everything First
```bash
# Backup last 2 years
python gmail_fetcher.py --query "newer_than:2y" --max 5000 --output "full_backup"
```

### 2. Backup by Category
```bash
# AI/Tech newsletters
python gmail_fetcher.py --query "from:(theresanaiforthat.com OR mindstream.news OR futurepedia.io)" --output "newsletters" --organize sender

# Service notifications
python gmail_fetcher.py --query "from:(namecheap.com OR pythonanywhere.com OR zoho.com)" --output "services" --organize sender

# Important emails
python gmail_fetcher.py --query "is:important OR is:starred" --output "important"
```

### 3. Use Gmail Web Interface for Cleanup
After backing up, use these searches in Gmail web to bulk delete/archive:

**Delete old promotions:**
```
category:promotions older_than:3m
```

**Archive old updates:**
```
category:updates older_than:1m
```

**Archive old service emails:**
```
from:(noreply OR notifications) older_than:6m
```

## 📁 File Formats

### EML Format
- Native email format
- Can be opened in email clients (Thunderbird, Outlook, Apple Mail)
- Preserves all original formatting and headers
- Best for legal/compliance needs

### Markdown Format
- Human-readable text format
- Includes metadata table
- Converts HTML to markdown
- Great for searching and reading
- Can be processed by text analysis tools

## ⚙️ Configuration

Edit `config.json` to customize:
- Default queries
- Output settings
- Cleanup suggestions

## 🔒 Security Notes

- `credentials.json` - Contains your Google API keys (don't share)
- `token.json` - Contains your access token (don't share)
- Add both files to `.gitignore` if using version control
- The script only requests **read-only** access to Gmail

## 🐛 Troubleshooting

**"credentials.json not found":**
- Download OAuth credentials from Google Cloud Console
- Rename to exactly `credentials.json`

**"Authentication failed":**
- Delete `token.json` and re-run with `--auth-only`
- Check that Gmail API is enabled in Google Cloud Console

**"Too many requests":**
- Gmail API has rate limits
- Reduce `--max` parameter or add delays

**"Unicode decode error":**
- Some emails have encoding issues
- The script handles most cases automatically

## 💡 Pro Tips

1. **Start small**: Test with `--max 10` first
2. **Use specific queries**: More specific = faster downloads
3. **Regular backups**: Run weekly/monthly for ongoing backup
4. **Check file sizes**: Large attachments increase download time
5. **Organize by date**: Better for chronological analysis
6. **Use markdown**: Better for AI analysis and summarization

## 📊 Integration Ideas

### With AI Analysis
```bash
# Download newsletters for AI summarization
python gmail_fetcher.py --query "subject:newsletter" --format markdown --organize sender

# Then use Claude/ChatGPT to analyze the markdown files
```

### With Search Tools
```bash
# Create searchable archive
python gmail_fetcher.py --query "newer_than:1y" --format both
# Use tools like grep, ripgrep, or ElasticSearch on the output
```

### Automated Workflows
```bash
# Weekly backup script
python gmail_fetcher.py --query "newer_than:1w" --output "weekly_$(date +%Y%m%d)"
```
