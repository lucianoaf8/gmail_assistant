# Gmail Bulk Deletion Guide

Complete toolkit for safely cleaning your Gmail inbox using the Gmail API.

## ⚠️ SAFETY FIRST

**IMPORTANT**: These tools permanently delete emails. Always run with `--dry-run` first to see what would be deleted.

**Backup Strategy**: Consider downloading emails using Google Takeout or the gmail_fetcher.py before mass deletion.

## 🚀 Quick Start (Clean Unread Inbox)

For cleaning your unread inbox for a fresh start:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Validate setup and connection
python gmail_setup_integrated.py

# 3. Test what would be deleted (DRY RUN)
python clean_unread_inbox.py --dry-run

# 4. Actually delete all unread emails
python clean_unread_inbox.py

# 5. Keep recent emails (last 7 days) but delete older unread
python clean_unread_inbox.py --keep-recent 7
```

## 📋 Setup Requirements

### 1. Gmail API Credentials
- `credentials.json` - Download from Google Cloud Console
- Gmail API enabled with scopes:
  - `https://www.googleapis.com/auth/gmail.readonly` (for fetching)
  - `https://www.googleapis.com/auth/gmail.modify` (for deletion)

### 2. Dependencies
```bash
pip install -r requirements.txt
```

### 3. Authentication
First run will open browser for OAuth consent (creates `token.json` for future use).

## 🛠️ Available Tools

### 1. `gmail_setup_integrated.py` - Complete Setup & Validation
**Start here**: Validates dependencies, credentials, and connection.

```bash
# Complete setup validation and analysis
python gmail_setup_integrated.py

# Setup validation only
python gmail_setup_integrated.py --setup-only

# Analysis only (skip setup checks)
python gmail_setup_integrated.py --analysis-only

# Show safety checklist
python gmail_setup_integrated.py --safety-checklist
```

### 2. `clean_unread_inbox.py` - Focused Unread Cleaner
**Best for fresh start**: Clean unread emails with safety features.

```bash
# See what would be deleted
python clean_unread_inbox.py --dry-run

# Delete all unread emails
python clean_unread_inbox.py

# Keep emails from last 3 days
python clean_unread_inbox.py --keep-recent 3
```

### 3. `fresh_start.py` - One-Click Complete Cleanup
**High risk**: Deletes ALL unread emails with triple confirmation.

```bash
# WARNING: This deletes ALL unread emails
python fresh_start.py
```

### 4. `gmail_deleter.py` - Advanced Bulk Deleter
**For complex scenarios**: Custom queries, category-specific deletion.

```bash
# Interactive mode
python gmail_deleter.py

# Preset options
python gmail_deleter.py --preset unread --dry-run
python gmail_deleter.py --preset old --dry-run        # Older than 1 year
python gmail_deleter.py --preset large --dry-run      # Larger than 10MB

# Custom queries
python gmail_deleter.py --query "from:newsletters@example.com" --dry-run
python gmail_deleter.py --query "is:unread older_than:30d" --dry-run

# Delete based on parquet analysis
python gmail_deleter.py --parquet data.parquet --dry-run
```

### 5. `setup_gmail_deletion.py` - Legacy Setup (Deletion Only)
**Alternative setup**: Validates deletion-specific setup only.

## 📊 Deletion Strategies

### Strategy 1: Fresh Start (Complete Cleanup)
```bash
# Complete unread cleanup (safest approach)
python clean_unread_inbox.py --dry-run      # Test first
python clean_unread_inbox.py                # Execute

# One-click complete cleanup (high risk)
python fresh_start.py                       # Triple confirmation required
```

### Strategy 2: Conservative Cleanup
```bash
# Keep recent emails, delete older ones
python clean_unread_inbox.py --keep-recent 7 --dry-run
python clean_unread_inbox.py --keep-recent 7

# Keep very recent, delete moderately old
python clean_unread_inbox.py --keep-recent 3 --dry-run
python clean_unread_inbox.py --keep-recent 3
```

### Strategy 3: Category-Based Cleanup
```bash
# Delete financial emails
python gmail_deleter.py --query "is:unread (payment OR invoice OR bill OR receipt)" --dry-run

# Delete notifications
python gmail_deleter.py --query "is:unread (notification OR alert OR backup)" --dry-run

# Delete marketing emails
python gmail_deleter.py --query "is:unread (unsubscribe OR newsletter)" --dry-run

# Delete social emails
python gmail_deleter.py --query "is:unread (social OR friend OR follow)" --dry-run
```

### Strategy 4: Time-Based Cleanup
```bash
# Delete unread emails older than 30 days
python gmail_deleter.py --query "is:unread older_than:30d" --dry-run

# Delete unread emails older than 90 days
python gmail_deleter.py --query "is:unread older_than:90d" --dry-run

# Delete emails older than 1 year (read and unread)
python gmail_deleter.py --query "older_than:1y" --dry-run
```

### Strategy 5: Size-Based Cleanup
```bash
# Delete large emails
python gmail_deleter.py --query "larger:10M" --dry-run
python gmail_deleter.py --query "larger:5M older_than:6m" --dry-run

# Delete medium-large emails
python gmail_deleter.py --query "is:unread larger:1M" --dry-run
```

## 🎯 Gmail Search Query Reference

### Common Filters
- `is:unread` - Unread emails
- `is:read` - Read emails
- `is:starred` - Starred emails
- `is:important` - Important emails
- `from:sender@domain.com` - From specific sender
- `to:recipient@domain.com` - To specific recipient
- `subject:keyword` - Subject contains keyword
- `older_than:1y` - Older than 1 year (also: 1m, 1d, 1w)
- `newer_than:1w` - Newer than 1 week
- `larger:10M` - Larger than 10MB (also: 1K, 1G)
- `smaller:1M` - Smaller than 1MB
- `has:attachment` - Has attachments
- `-has:attachment` - No attachments

### Combining Filters
```bash
# Unread emails older than 30 days from newsletters
"is:unread older_than:30d (newsletter OR unsubscribe)"

# Large emails older than 6 months
"larger:5M older_than:6m"

# Financial emails from last year
"(payment OR invoice OR bill) older_than:1y"

# Unread notifications and alerts
"is:unread (notification OR alert OR backup OR report)"
```

## 🔒 Safety Features

### Multi-Layer Protection
1. **Dry Run Mode**: Always test with `--dry-run` first
2. **Interactive Confirmations**: Multiple confirmation steps for large deletions
3. **Case-Sensitive Confirmations**: Requires exact text matching ("DELETE", "FRESH START")
4. **Batch Processing**: Efficient API usage with rate limiting
5. **Progress Tracking**: Real-time status with progress bars
6. **Error Handling**: Failed deletions reported separately
7. **Count Warnings**: Alerts for large deletion operations (>1000 emails)

### Built-in Safeguards
- Rate limiting (0.1s between batches)
- Batch fallback (individual deletion if batch fails)
- Keyboard interrupt support (Ctrl+C)
- Recovery information displayed
- Maximum batch sizes enforced

### Best Practices Workflow
```bash
# 1. Setup validation
python gmail_setup_integrated.py

# 2. Backup important emails first
python gmail_fetcher.py --query "is:starred OR is:important" --max 1000

# 3. Always dry run first
python clean_unread_inbox.py --dry-run

# 4. Test with small batches if unsure
python gmail_deleter.py --query "is:unread" --max-delete 10 --dry-run

# 5. Keep recent emails initially
python clean_unread_inbox.py --keep-recent 7

# 6. Monitor deletion results
# Check output for deleted/failed counts
```

## 🚨 Emergency Procedures

### If Something Goes Wrong
1. **Stop the process**: Ctrl+C to interrupt
2. **Check Gmail Trash**: Deleted emails may be recoverable for 30 days
3. **Restore from Trash**: Use Gmail web interface to recover
4. **Rate Limits**: If you hit API limits, wait and retry
5. **Review logs**: Check console output for failure details

### Recovery Options
- **Gmail Trash**: Deleted emails stay in Trash for 30 days
- **Google Takeout**: If you created a backup beforehand
- **Email Client Sync**: If you sync with Outlook/Apple Mail
- **Backup Files**: If you used gmail_fetcher.py to backup first

## ⚡ Complete Example Workflow

### For Fresh Start with Safety
```bash
# Step 1: Complete setup and analysis
python gmail_setup_integrated.py

# Step 2: Review safety checklist
python gmail_setup_integrated.py --safety-checklist

# Step 3: Backup important emails (optional but recommended)
python gmail_fetcher.py --query "is:starred OR is:important" --max 1000

# Step 4: See current state and test deletion
python clean_unread_inbox.py --dry-run

# Step 5: Execute deletion (choose one approach)

# Option A: Complete fresh start
python clean_unread_inbox.py

# Option B: Conservative (keep recent)
python clean_unread_inbox.py --keep-recent 7

# Option C: One-click total cleanup (high risk)
python fresh_start.py
```

### Expected Output Example
```
🧹 Gmail Unread Inbox Cleaner
========================================
Target: ALL unread emails

Current unread count: 2,783

📊 Unread email breakdown:
   Financial: 1,076 emails
   Notifications: 630 emails
   Marketing: 724 emails
   Social: 353 emails
   Large emails: 89 emails

🎯 Target for deletion: 2,783 emails

⚠️  CONFIRMATION REQUIRED
About to permanently delete 2,783 unread emails

Type 'DELETE' to confirm (case sensitive): DELETE

🗑️  Starting deletion of 2,783 emails...
Deleting 2783 emails in batches of 100
Deleting batches: 100%|████████████| 28/28 [02:15<00:00,  4.83s/it]

✅ Cleanup complete!
   Deleted: 2,783 emails
   Failed: 0 emails
   Remaining unread: 0

🎉 Fresh start achieved! Deleted 2,783 unread emails.
```

## 🔧 Troubleshooting

### Common Issues
1. **Authentication Error**: Re-run setup to refresh token
2. **Rate Limits**: Built-in delays handle this automatically
3. **Large Deletions**: Use `--max-delete` to limit batch size
4. **Query Errors**: Test queries in Gmail web interface first
5. **Missing Dependencies**: Run `pip install -r requirements.txt`
6. **Scope Issues**: Delete token.json and re-authenticate

### Performance Tips
- Batch deletion is more efficient than individual
- Rate limiting prevents API quota issues
- Progress bars show real-time status
- Use --max-delete for testing large operations
- Stable internet connection recommended

### Integration with Gmail Fetcher
```bash
# Backup before deletion
python gmail_fetcher.py --query "is:unread" --max 1000 --output pre_deletion_backup

# Delete after backup
python clean_unread_inbox.py

# Backup specific categories before targeted deletion
python gmail_fetcher.py --query "is:unread (payment OR invoice)" --output financial_backup
python gmail_deleter.py --query "is:unread (payment OR invoice)" --dry-run
```

---

**Ready to start fresh? Always begin with setup validation and dry-run testing!**

For complete project documentation, see the main project CLAUDE.md file.