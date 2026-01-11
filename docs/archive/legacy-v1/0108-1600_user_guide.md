# Gmail Fetcher Suite User Guide

*Your Complete Guide to Gmail Backup, Organization, and Management*

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Operations](#basic-operations)
3. [Common Tasks & Tutorials](#common-tasks--tutorials)
4. [Using Pre-Built Scenarios](#using-pre-built-scenarios)
5. [Search Queries Made Simple](#search-queries-made-simple)
6. [Managing Your Backups](#managing-your-backups)
7. [Advanced Features for Power Users](#advanced-features-for-power-users)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Quick Reference](#quick-reference)

---

## Getting Started

### What is Gmail Fetcher Suite?

Gmail Fetcher Suite is a powerful yet user-friendly tool that helps you:

- **Backup your Gmail emails** to your computer in readable formats
- **Organize emails** by date, sender, or custom categories
- **Convert emails** between different formats (EML, Markdown, HTML)
- **Clean up your inbox** by identifying and removing unwanted emails
- **Archive important emails** for legal, business, or personal needs
- **Search and filter** emails using Gmail's powerful search features

**Think of it as your personal email assistant** that works offline and gives you complete control over your email data.

### Who Should Use This Tool?

✅ **Perfect for:**
- Business professionals who need email archives for compliance
- Individuals wanting to backup important emails before account changes
- Anyone looking to organize their Gmail systematically
- People who want to reduce Gmail storage usage
- Legal professionals requiring email documentation
- Students and researchers who need to preserve correspondence

✅ **Great if you want to:**
- Get emails off Google's servers for privacy
- Create searchable email archives
- Backup emails before changing jobs or schools
- Preserve family or business correspondence
- Analyze email patterns and trends

### Quick Installation for Non-Technical Users

#### Step 1: Check Your Computer
- **Windows**: Windows 10 or later
- **Mac**: macOS 10.15 or later
- **Linux**: Any modern distribution

#### Step 2: Install Python (if not already installed)

**Windows Users:**
1. Go to [python.org](https://python.org/downloads/)
2. Download Python 3.8 or later
3. Run the installer and **check "Add Python to PATH"**
4. Click "Install Now"

**Mac Users:**
1. Open Terminal (Applications → Utilities → Terminal)
2. Type: `python3 --version`
3. If not installed, download from [python.org](https://python.org/downloads/)

**Linux Users:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

#### Step 3: Download Gmail Fetcher Suite
1. Download the Gmail Fetcher Suite files to a folder (e.g., `Documents/gmail_fetcher`)
2. Open Command Prompt (Windows) or Terminal (Mac/Linux)
3. Navigate to the folder: `cd Documents/gmail_fetcher`

#### Step 4: Install Required Components
```bash
pip install -r requirements.txt
```

> **💡 Tip:** If you see permission errors, try `pip install --user -r requirements.txt`

### First-Time Setup Walkthrough

#### Step 1: Gmail API Setup

Before you can download emails, you need to connect to Gmail safely:

1. **Go to Google Cloud Console**
   - Visit [console.cloud.google.com](https://console.cloud.google.com)
   - Sign in with your Google account

2. **Create a New Project**
   - Click "Select a project" → "New Project"
   - Name it "Gmail Backup" or similar
   - Click "Create"

3. **Enable Gmail API**
   - Search for "Gmail API" in the search bar
   - Click on "Gmail API" → "Enable"

4. **Create Credentials**
   - Go to "Credentials" in the left menu
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop Application"
   - Name it "Gmail Fetcher"
   - Download the JSON file

5. **Save Credentials File**
   - Rename the downloaded file to `credentials.json`
   - Place it in your Gmail Fetcher Suite folder

> **🔒 Security Note:** The credentials file is like a key to your Gmail. Keep it safe and never share it.

#### Step 2: Test Your Setup

Let's make sure everything works:

```bash
python main.py fetch --auth-only
```

**What should happen:**
1. A web browser opens asking you to sign in to Google
2. Google asks for permission to access your Gmail
3. Click "Allow"
4. You see "Authentication successful!" in your terminal

**Screenshot Description:** *Browser window showing Google OAuth consent screen with "Gmail Fetcher wants to access your Google Account" and permissions listed including "Read your email messages and settings."*

> **⚠️ Important:** The first time you run this, Google may show a security warning. This is normal for personal projects. Click "Advanced" → "Go to Gmail Fetcher (unsafe)" to continue.

### Your First Email Backup

Now let's backup some emails to make sure everything works:

```bash
python main.py fetch --query "is:unread" --max 10 --output "test_backup"
```

**What this command does:**
- `fetch`: Download emails from Gmail
- `--query "is:unread"`: Get unread emails only
- `--max 10`: Limit to 10 emails for testing
- `--output "test_backup"`: Save to a folder called "test_backup"

**You should see:**
```
🚀 Starting Gmail Fetcher Suite...
🔑 Authenticating with Gmail...
📧 Found 10 emails matching your search
📁 Creating backup folder: test_backup
✅ Downloaded: Email 1/10 - "Meeting Tomorrow"
✅ Downloaded: Email 2/10 - "Project Update"
...
🎉 Backup complete! 10 emails saved to test_backup/
```

**Check your results:**
1. Look in your Gmail Fetcher folder
2. You should see a new folder called `test_backup`
3. Inside, you'll find folders organized by date (e.g., `2024/03/`)
4. Each email is saved in two formats:
   - `.eml` files (original email format)
   - `.md` files (readable Markdown format)

**Screenshot Description:** *File explorer window showing test_backup folder structure with year/month subfolders containing .eml and .md files with descriptive names like "2024-03-15_140000_meeting-tomorrow_abc123.eml"*

---

## Basic Operations

### Backing Up Unread Emails

The most common use case is backing up unread emails:

```bash
python main.py fetch --query "is:unread" --max 1000 --output "unread_backup"
```

**What you get:**
- All your unread emails downloaded
- Organized by date in folders
- Both EML and Markdown formats
- Searchable file names with subjects

**When to use this:**
- Before doing a mass "mark as read" operation
- Regular weekly/monthly backups
- Before changing email clients

### Downloading Emails by Date Range

Want emails from a specific time period?

**Last 30 days:**
```bash
python main.py fetch --query "newer_than:30d" --max 500 --output "recent_emails"
```

**Specific date range:**
```bash
python main.py fetch --query "after:2024/01/01 before:2024/04/01" --max 1000 --output "q1_2024_emails"
```

**This year only:**
```bash
python main.py fetch --query "after:2024/01/01" --max 2000 --output "emails_2024"
```

> **📅 Date Format Tips:**
> - Use `YYYY/MM/DD` format (e.g., `2024/03/15`)
> - Use `newer_than:30d` for relative dates (30 days ago)
> - Use `older_than:1y` for emails older than 1 year

### Saving Emails from Specific Senders

**From one person:**
```bash
python main.py fetch --query "from:boss@company.com" --organize sender --output "boss_emails"
```

**From multiple people:**
```bash
python main.py fetch --query "from:(john@company.com OR mary@company.com)" --organize sender --output "team_emails"
```

**From a domain:**
```bash
python main.py fetch --query "from:company.com" --organize sender --output "work_emails"
```

**Tips for sender organization:**
- Use `--organize sender` to group emails by who sent them
- Great for backing up important business relationships
- Perfect for organizing family correspondence

### Choosing Between EML and Markdown Formats

Gmail Fetcher Suite can save emails in different formats:

#### EML Format (`--format eml`)
**Best for:**
- Importing into other email clients (Outlook, Thunderbird, Apple Mail)
- Preserving exact email formatting and attachments
- Legal documentation (maintains original structure)
- Technical analysis of email headers

**Example:**
```bash
python main.py fetch --query "from:lawyer@lawfirm.com" --format eml --output "legal_emails"
```

#### Markdown Format (`--format markdown`)
**Best for:**
- Reading emails as documents
- Searching with text editors
- Creating documentation from email chains
- Web publishing or note-taking apps

**Example:**
```bash
python main.py fetch --query "subject:project notes" --format markdown --output "project_docs"
```

#### Both Formats (`--format both`) - **Recommended Default**
**Best for:**
- Maximum flexibility
- Future-proofing your backups
- Different use cases for the same emails

**Screenshot Description:** *Side-by-side comparison showing the same email in EML format (showing raw email headers and formatting) versus Markdown format (clean, readable text with metadata table at top)*

### Understanding File Organization Options

#### By Date (`--organize date`) - **Default**
```
gmail_backup/
├── 2024/
│   ├── 01/  (January emails)
│   ├── 02/  (February emails)
│   └── 03/  (March emails)
└── 2023/
    └── 12/  (December emails)
```

**Best for:**
- General email archiving
- Finding emails by when they were sent
- Regular backup schedules

#### By Sender (`--organize sender`)
```
gmail_backup/
├── john_smith/
│   ├── 2024-01-15_email1.eml
│   └── 2024-02-20_email2.eml
├── company_newsletter/
└── family_updates/
```

**Best for:**
- Organizing correspondence by relationship
- Business contact management
- Family email archives

#### No Organization (`--organize none`)
```
gmail_backup/
├── 2024-01-15_140000_meeting_abc123.eml
├── 2024-01-16_090000_newsletter_def456.eml
└── 2024-01-17_160000_family_ghi789.eml
```

**Best for:**
- Simple chronological listing
- Smaller backup sets
- When you'll search by filename

---

## Common Tasks & Tutorials

### Tutorial: "How do I backup all my newsletters?"

**Step 1: Identify Newsletter Senders**

First, let's find who sends you newsletters:

```bash
python main.py fetch --query "category:promotions OR subject:newsletter" --max 50 --organize sender --output "newsletter_test"
```

Check the `newsletter_test` folder to see which senders appear most often.

**Step 2: Create a Targeted Search**

Based on what you found, create a specific search. For example:

```bash
python main.py fetch --query "from:(newsletter@company.com OR updates@techsite.com OR digest@newssite.com)" --organize sender --output "newsletters_archive"
```

**Step 3: Use the Newsletter Sample Script**

For AI and tech newsletters specifically:

```bash
python examples/samples.py newsletters
```

This runs a pre-configured script that backs up common AI and tech newsletters.

**💡 Pro Tip:** Use `--format markdown` for newsletters since they're primarily for reading, not forwarding.

### Tutorial: "How do I archive important emails?"

**Step 1: Identify Important Email Categories**

Important emails often include:
- Starred emails: `is:starred`
- Important labels: `is:important`
- Specific subjects: `subject:(contract OR agreement OR receipt)`
- Key senders: `from:(hr@company.com OR legal@company.com)`

**Step 2: Backup Starred and Important Emails**

```bash
python main.py fetch --query "is:starred OR is:important" --max 1000 --output "important_emails"
```

**Step 3: Backup Financial and Legal Emails**

```bash
python main.py fetch --query "subject:(receipt OR invoice OR contract OR agreement OR legal)" --organize sender --output "financial_legal"
```

**Step 4: Backup Work Communications**

```bash
python main.py fetch --query "from:yourcompany.com" --organize sender --output "work_archive"
```

**🔒 Security Tip:** For sensitive emails, consider storing backups on an encrypted drive or using the `--format eml` option for better legal documentation.

### Tutorial: "How do I export emails for legal compliance?"

**Step 1: Define Your Date Range**

Most legal requests specify date ranges:

```bash
python main.py fetch --query "after:2023/01/01 before:2023/12/31" --format eml --max 5000 --output "legal_export_2023"
```

**Step 2: Include Specific Parties**

If you need emails involving specific people or companies:

```bash
python main.py fetch --query "after:2023/01/01 before:2023/12/31 (from:opposing-party.com OR to:opposing-party.com OR cc:opposing-party.com)" --format eml --output "litigation_emails"
```

**Step 3: Export Sent Items Too**

Don't forget emails you sent:

```bash
python main.py fetch --query "in:sent after:2023/01/01 before:2023/12/31" --format eml --output "sent_emails_2023"
```

**Step 4: Document Your Process**

Create a text file documenting:
- What search queries you used
- Date ranges covered
- Total number of emails exported
- Any limitations or exclusions

**⚖️ Legal Note:** Consult with your attorney about specific requirements for email production in your jurisdiction.

### Tutorial: "How do I create a local Gmail archive?"

**Step 1: Plan Your Archive Strategy**

Decide on:
- How far back to go
- What categories to include
- Storage organization method

**Step 2: Download by Year**

For a complete archive, download year by year:

```bash
python main.py fetch --query "after:2023/01/01 before:2024/01/01" --max 10000 --output "archive_2023"
python main.py fetch --query "after:2022/01/01 before:2023/01/01" --max 10000 --output "archive_2022"
python main.py fetch --query "after:2021/01/01 before:2022/01/01" --max 10000 --output "archive_2021"
```

**Step 3: Merge Archives (Optional)**

Use the backup management tools to combine years:

```powershell
# Windows PowerShell
.\scripts\backup\merge_backups.ps1 -Source archive_2023 -Destination complete_archive -Years 2023
.\scripts\backup\merge_backups.ps1 -Source archive_2022 -Destination complete_archive -Years 2022
```

**Step 4: Create a Master Index**

The tool automatically creates searchable filenames, but you can also generate a master index:

```bash
python scripts/operations/create_index.py --input complete_archive --output email_index.html
```

**💾 Storage Tip:** A typical Gmail account (10GB) will create 8-15GB of backup files. Plan accordingly for storage space.

### Tutorial: "How do I find and remove duplicate emails?"

**Step 1: Create Your Initial Backup**

First, backup your emails normally:

```bash
python main.py fetch --query "after:2024/01/01" --max 5000 --output "backup_main"
```

**Step 2: Check for Duplicates**

If you've run multiple backups, you might have duplicates:

```bash
python scripts/maintenance/find_duplicates.py --input backup_main --report duplicates_report.txt
```

**Step 3: Remove Duplicates**

```bash
python scripts/maintenance/dedupe_emails.py --input backup_main --prefer larger --dry-run
```

The `--dry-run` flag shows what would be removed without actually deleting anything.

**Step 4: Actually Remove Duplicates**

After reviewing the dry-run results:

```bash
python scripts/maintenance/dedupe_emails.py --input backup_main --prefer larger
```

**🔍 How Duplicate Detection Works:**
- Compares email Message-IDs (unique identifiers)
- Compares subject lines and dates for emails without Message-IDs
- Prefers larger files (assuming they have more complete content)
- Logs all actions for your review

---

## Using Pre-Built Scenarios

Gmail Fetcher Suite comes with ready-to-use scenarios for common tasks. These are like "recipes" that handle complex search queries for you.

### Understanding the Samples Menu

To see all available scenarios:

```bash
python examples/samples.py
```

**You'll see options like:**
```
📧 Gmail Fetcher Suite - Sample Scenarios

Available scenarios:
  unread     - Backup all unread emails
  newsletters - Archive newsletters by sender
  services   - Backup service notifications
  important  - Archive starred and important emails
  recent     - Backup last 30 days
  work       - Archive work emails
  financial  - Backup receipts and financial emails

Usage: python samples.py [scenario_name]
Example: python samples.py unread
```

### Running Quick Backup Scenarios

#### Unread Email Cleanup
```bash
python examples/samples.py unread
```

**What it does:**
- Downloads all unread emails
- Saves in both EML and Markdown formats
- Organizes by date
- Limits to 2000 emails (safe default)

**When to use:**
- Before mass archiving your inbox
- Weekly unread email reviews
- Before switching email clients

#### Newsletter Archive
```bash
python examples/samples.py newsletters
```

**What it does:**
- Identifies common AI/tech newsletters
- Organizes by sender for easy browsing
- Uses Markdown format (better for reading)
- Separates AI newsletters from general tech news

**Senders it recognizes:**
- AI newsletters: TheresAnAIForThat, Mindstream, Futurepedia
- Tech news: TechCrunch, Hacker News, Product Hunt
- Business: Morning Brew, The Hustle

#### Service Notifications
```bash
python examples/samples.py services
```

**What it does:**
- Backs up notifications from major services
- Includes banking, shopping, travel confirmations
- Organizes by sender
- Great for record-keeping

**Services included:**
- Banking: Chase, Bank of America, Wells Fargo
- Shopping: Amazon, eBay, PayPal receipts
- Travel: Airlines, hotels, car rentals
- Utilities: Phone, internet, electricity bills

#### Important Emails
```bash
python examples/samples.py important
```

**What it does:**
- Downloads starred emails
- Downloads emails marked as important
- Downloads emails from key business domains
- Perfect for compliance and record-keeping

### Customizing Scenarios for Your Needs

You can modify the sample scripts or create your own. Here's how:

**Example: Custom Newsletter Backup**

1. Copy the samples file:
```bash
cp examples/samples.py my_samples.py
```

2. Edit the newsletter function to include your specific newsletters:

```python
def my_newsletter_backup():
    """Backup my specific newsletters"""
    # Add your newsletter senders here
    my_newsletters = [
        "newsletter@myindustry.com",
        "updates@mycompany.com",
        "digest@mynews.com"
    ]

    query = f"from:({' OR '.join(my_newsletters)})"

    run_gmail_fetcher(
        query=query,
        max_emails=1000,
        output_dir="my_newsletters",
        format_type="markdown",
        organize="sender"
    )
```

3. Run your custom script:
```bash
python my_samples.py
```

**💡 Customization Ideas:**
- Family email backup: `from:(mom@email.com OR dad@email.com OR sister@email.com)`
- Project emails: `subject:(project-name OR client-name)`
- Educational emails: `from:(university.edu OR teacher@school.edu)`
- Health records: `from:(doctor@clinic.com OR pharmacy@cvs.com)`

---

## Search Queries Made Simple

Gmail's search functionality is incredibly powerful, but it can be confusing. This section breaks it down into simple, practical examples.

### Gmail Search Basics for Beginners

Think of Gmail searches like asking questions about your emails:

**Basic Questions:**
- "Show me emails from John" → `from:john@email.com`
- "Show me emails about meetings" → `subject:meeting`
- "Show me unread emails" → `is:unread`
- "Show me emails with attachments" → `has:attachment`

**Time Questions:**
- "Show me emails from last week" → `newer_than:7d`
- "Show me emails from January" → `after:2024/01/01 before:2024/02/01`
- "Show me old emails" → `older_than:1y`

### Common Search Patterns with Examples

#### Finding Emails by Sender

**One person:**
```bash
--query "from:boss@company.com"
```

**Multiple people (OR search):**
```bash
--query "from:(john@email.com OR mary@email.com OR boss@company.com)"
```

**Anyone from a company:**
```bash
--query "from:company.com"
```

**Exclude someone:**
```bash
--query "from:company.com -from:spam@company.com"
```

#### Finding Emails by Subject

**Exact phrase:**
```bash
--query "subject:\"weekly meeting\""
```

**Any of these words:**
```bash
--query "subject:(meeting OR conference OR presentation)"
```

**Subject contains word:**
```bash
--query "subject:invoice"
```

#### Finding Emails by Content

**Email contains specific text:**
```bash
--query "password reset"
```

**Email contains any of these words:**
```bash
--query "(urgent OR important OR asap)"
```

**Email doesn't contain word:**
```bash
--query "meeting -cancelled"
```

### Building Complex Searches Step-by-Step

Let's build a complex search together. Say you want to find:
*"Unread emails from last month from my work domain, but not automated notifications"*

**Step 1: Start simple**
```bash
--query "is:unread"
```

**Step 2: Add time constraint**
```bash
--query "is:unread newer_than:30d older_than:1d"
```

**Step 3: Add sender constraint**
```bash
--query "is:unread newer_than:30d older_than:1d from:mycompany.com"
```

**Step 4: Exclude automated emails**
```bash
--query "is:unread newer_than:30d older_than:1d from:mycompany.com -from:noreply"
```

**Step 5: Final refinement**
```bash
--query "is:unread newer_than:30d older_than:1d from:mycompany.com -from:(noreply OR automated OR no-reply)"
```

### Time-Based Searches Explained

#### Relative Time (Recommended)
**Recent emails:**
- `newer_than:1d` - Last 24 hours
- `newer_than:7d` - Last week
- `newer_than:1m` - Last month
- `newer_than:1y` - Last year

**Older emails:**
- `older_than:1d` - Older than 24 hours
- `older_than:1m` - Older than 1 month
- `older_than:1y` - Older than 1 year

#### Specific Dates
**Single day:**
```bash
--query "after:2024/03/15 before:2024/03/16"
```

**Date range:**
```bash
--query "after:2024/01/01 before:2024/04/01"  # Q1 2024
```

**Everything after a date:**
```bash
--query "after:2024/01/01"  # This year only
```

**Everything before a date:**
```bash
--query "before:2024/01/01"  # Last year and earlier
```

#### Combining Time with Other Criteria

**Unread emails from last week:**
```bash
--query "is:unread newer_than:7d"
```

**Work emails from Q1:**
```bash
--query "from:company.com after:2024/01/01 before:2024/04/01"
```

**Important emails from last month:**
```bash
--query "is:important newer_than:30d older_than:1d"
```

### Category and Label Searches

#### Gmail Categories
```bash
--query "category:social"      # Social networks, dating sites
--query "category:updates"     # Confirmations, receipts, bills
--query "category:promotions"  # Deals, offers, marketing emails
--query "category:forums"      # Online groups, discussion boards
```

#### Gmail Labels
```bash
--query "label:important"     # Important label
--query "label:work"          # Custom work label
--query "has:yellow-star"     # Yellow star
--query "has:red-bang"        # Red exclamation mark
```

#### Email Status
```bash
--query "is:unread"           # Unread emails
--query "is:read"             # Read emails
--query "is:starred"          # Any star color
--query "is:important"        # Marked as important
--query "in:sent"             # Emails you sent
--query "in:inbox"            # Emails in inbox
--query "in:trash"            # Deleted emails
```

### Advanced Search Operators

#### Size and Attachments
```bash
--query "has:attachment"                    # Has any attachment
--query "has:attachment larger:10M"         # Large emails with attachments
--query "filename:pdf"                      # Has PDF attachments
--query "filename:(jpg OR png OR gif)"      # Has image attachments
```

#### Exact Matching
```bash
--query "\"exact phrase search\""          # Exact phrase
--query "subject:\"Exact Subject\""        # Exact subject line
```

#### Multiple Criteria (AND/OR)
```bash
# AND (all must be true) - use spaces
--query "from:boss@company.com subject:meeting is:unread"

# OR (any can be true) - use OR keyword
--query "from:(john@email.com OR mary@email.com)"
--query "subject:(meeting OR conference OR presentation)"

# NOT (exclude) - use minus sign
--query "from:company.com -subject:newsletter"
```

### Search Query Examples for Common Needs

#### Business and Legal
```bash
# All contracts and agreements
--query "subject:(contract OR agreement OR legal) OR has:attachment filename:pdf"

# Financial emails
--query "from:(bank.com OR paypal.com) OR subject:(invoice OR receipt OR payment)"

# Meeting-related emails
--query "subject:(meeting OR conference OR call OR appointment)"
```

#### Personal Organization
```bash
# Family emails
--query "from:(mom@email.com OR dad@email.com OR family)"

# Travel confirmations
--query "subject:(flight OR hotel OR booking OR confirmation OR itinerary)"

# Shopping and receipts
--query "from:(amazon.com OR ebay.com) OR subject:(order OR receipt OR shipped)"
```

#### Cleanup and Maintenance
```bash
# Newsletter and promotional emails
--query "category:promotions OR subject:(newsletter OR unsubscribe)"

# Large emails (storage cleanup)
--query "larger:10M"

# Old unimportant emails
--query "older_than:1y -is:important -is:starred"
```

---

## Managing Your Backups

Once you've created email backups, you need to organize, search, and maintain them effectively. This section covers everything about working with your backup files.

### Understanding the Folder Structure

Gmail Fetcher Suite creates organized folder structures to make finding emails easy.

#### Date Organization (Default)
```
gmail_backup/
├── 2024/                    # Year folder
│   ├── 01/                  # January
│   │   ├── 2024-01-15_140000_meeting-notes_abc123.eml
│   │   ├── 2024-01-15_140000_meeting-notes_abc123.md
│   │   ├── 2024-01-16_090000_newsletter_def456.eml
│   │   └── 2024-01-16_090000_newsletter_def456.md
│   ├── 02/                  # February
│   └── 03/                  # March
└── 2023/                    # Previous year
    ├── 11/
    └── 12/
```

**File name breakdown:**
- `2024-01-15` - Date email was sent (YYYY-MM-DD)
- `140000` - Time sent (HHMMSS in 24-hour format)
- `meeting-notes` - Simplified subject line
- `abc123` - Unique message ID (shortened)
- `.eml` or `.md` - File format

#### Sender Organization
```
gmail_backup/
├── john_smith_company_com/          # Sender folder (safe filename)
│   ├── 2024-01-15_project-update.eml
│   ├── 2024-01-15_project-update.md
│   └── 2024-02-01_quarterly-review.eml
├── newsletter_techcrunch_com/
├── automated_bank_of_america/
└── family_mom_gmail_com/
```

**Benefits of sender organization:**
- Easy to find all emails from a specific person
- Great for relationship management
- Perfect for business correspondence archives

### Finding Specific Emails in Your Backup

#### Method 1: File Explorer Search (Windows)

1. **Open File Explorer** and navigate to your backup folder
2. **Click in the search box** (top right)
3. **Type your search terms:**
   - `meeting` - finds files with "meeting" in filename
   - `john` - finds files from john or about john
   - `2024-03` - finds emails from March 2024

**Screenshot Description:** *Windows File Explorer showing search results in a gmail_backup folder, with search term "meeting" highlighted and several email files displayed with their descriptive filenames*

#### Method 2: Command Line Search (All Platforms)

**Find emails by subject:**
```bash
# Windows
dir /s *meeting*

# Mac/Linux
find . -name "*meeting*"
```

**Find emails from specific person:**
```bash
# Windows
dir /s *john*

# Mac/Linux
find . -name "*john*"
```

**Find emails by date:**
```bash
# Windows
dir /s *2024-03*

# Mac/Linux
find . -name "*2024-03*"
```

#### Method 3: Content Search in Markdown Files

Since Markdown files are plain text, you can search inside them:

**Windows (PowerShell):**
```powershell
Select-String -Path "*.md" -Pattern "contract" -Recurse
```

**Mac/Linux:**
```bash
grep -r "contract" *.md
```

**Advanced content search:**
```bash
# Find emails mentioning specific topics
grep -r -i "password reset" *.md

# Find emails with phone numbers
grep -r -E "\b\d{3}-\d{3}-\d{4}\b" *.md
```

### Merging Multiple Backup Folders

If you've created multiple backups, you can merge them into a single organized archive.

#### Using the Merge Script (Windows PowerShell)

**Basic merge:**
```powershell
.\scripts\backup\merge_backups.ps1 -Source backup_part2 -Destination backup_main -DryRun
```

**What the dry run shows:**
```
🔍 DRY RUN - No files will be moved
📁 Source: backup_part2 (1,247 emails)
📁 Destination: backup_main (2,891 emails)
📊 Analysis:
   - 1,180 new emails to move
   - 67 duplicates found (will skip)
   - 0 conflicts (same name, different content)
🎯 Result: backup_main will have 4,071 total emails
```

**Actually perform the merge:**
```powershell
.\scripts\backup\merge_backups.ps1 -Source backup_part2 -Destination backup_main
```

#### Merging Specific Years

If you have large archives, merge specific years:

```powershell
# Merge only 2024 emails
.\scripts\backup\merge_backups.ps1 -Source archive_2024 -Destination complete_archive -Years 2024 -DryRun

# Merge multiple years
.\scripts\backup\merge_backups.ps1 -Source recent_backup -Destination complete_archive -Years 2023,2024
```

#### Manual Merge (Any Platform)

If scripts aren't available, you can merge manually:

1. **Create destination structure** if it doesn't exist
2. **Copy year folders** from source to destination:
   ```bash
   # Copy entire year folder
   cp -r backup_part2/2024/ backup_main/2024/
   ```
3. **Handle conflicts** by renaming or comparing files

### Removing Duplicate Emails

Duplicates can occur when:
- Running multiple backups with overlapping dates
- Merging different backup sources
- Re-downloading emails after interruptions

#### Using the Deduplication Script

**Find duplicates first (safe):**
```powershell
.\scripts\maintenance\dedupe_emails.ps1 -Source backup_main -DryRun
```

**Output example:**
```
🔍 Scanning for duplicates in backup_main...
📧 Found 2,847 total emails
🔍 Duplicate detection strategy: Message-ID + Subject + Date
📊 Results:
   - 2,780 unique emails
   - 67 duplicates found
   - 25MB space can be recovered

🗂️ Duplicate groups:
   Group 1: "2024-01-15_meeting-notes"
   - backup_main/2024/01/2024-01-15_140000_meeting-notes_abc123.eml (15KB)
   - backup_main/2024/01/2024-01-15_140000_meeting-notes_abc123_copy.eml (15KB)
   Recommended: Keep first file
```

**Remove duplicates:**
```powershell
# Keep larger files (usually more complete)
.\scripts\maintenance\dedupe_emails.ps1 -Source backup_main -Prefer larger

# Keep newer files
.\scripts\maintenance\dedupe_emails.ps1 -Source backup_main -Prefer newer

# Keep first found (fastest)
.\scripts\maintenance\dedupe_emails.ps1 -Source backup_main -Prefer first
```

#### Manual Duplicate Checking

For small archives, you can check manually:

1. **Sort by name** in file explorer
2. **Look for similar filenames** with different endings
3. **Compare file sizes** - usually identical emails have identical sizes
4. **Check dates** - exact duplicates have same timestamp

### Converting EML to Readable Markdown

If you have EML files and want readable Markdown versions:

#### Batch Conversion

**Convert entire backup:**
```bash
python scripts/parsers/eml_to_markdown.py --input backup_folder --output backup_folder_md
```

**Convert specific year:**
```bash
python scripts/parsers/eml_to_markdown.py --input backup_folder/2024 --output backup_2024_markdown
```

**Convert with enhanced parsing:**
```bash
python scripts/parsers/advanced_email_parser.py --input backup_folder --strategy auto --output enhanced_markdown
```

#### Single File Conversion

**Convert one email:**
```bash
python scripts/parsers/eml_to_markdown.py --file email.eml --output email.md
```

#### What Gets Converted

**EML file content:**
```
Return-Path: <sender@company.com>
Received: by gmail.com with SMTP id...
Date: Mon, 15 Jan 2024 14:00:00 -0800
From: John Smith <john@company.com>
To: me@myemail.com
Subject: Meeting Notes

<HTML content with formatting>
```

**Becomes Markdown:**
```markdown
---
date: 2024-01-15 14:00:00-08:00
from: John Smith <john@company.com>
to: me@myemail.com
subject: Meeting Notes
message_id: abc123@gmail.com
---

# Meeting Notes

Here are the notes from today's meeting:

- Action item 1
- Action item 2
- Follow up by Friday
```

**Benefits of Markdown conversion:**
- **Readable** in any text editor
- **Searchable** with standard tools
- **Version control friendly**
- **Web publishing ready**
- **Note-taking app compatible**

### Backup Organization Best Practices

#### Folder Naming Conventions

**Use descriptive, sortable names:**
```
✅ Good:
backup_2024_q1_work/
backup_2024_newsletters/
backup_important_financial/

❌ Avoid:
backup1/
my_emails/
stuff/
```

#### Storage Structure Example

```
Email_Archives/
├── Current/
│   ├── 2024_inbox_backup/           # Current year main backup
│   ├── 2024_newsletters/            # Current newsletters
│   └── 2024_work_important/         # Current work emails
├── Historical/
│   ├── 2023_complete_archive/       # Previous year complete
│   ├── 2022_complete_archive/
│   └── 2021_complete_archive/
├── Special_Purpose/
│   ├── legal_discovery_2023/        # Legal/compliance exports
│   ├── job_change_backup_2024/      # Career transition backup
│   └── family_correspondence/       # Personal archives
└── Tools/
    ├── gmail_fetcher_suite/         # The tool itself
    └── custom_scripts/              # Your customizations
```

#### Backup Scheduling Strategy

**Monthly Routine:**
1. **Backup unread emails** (safety net)
2. **Backup important emails** (starred, flagged)
3. **Archive newsletters** (keep current, archive old)
4. **Clean up duplicates** in archives

**Quarterly Routine:**
1. **Full backup** of important categories
2. **Merge** monthly backups into quarterly archive
3. **Review** and organize folder structure
4. **Storage cleanup** - remove unnecessary duplicates

**Annual Routine:**
1. **Complete yearly archive**
2. **Compress** old years for long-term storage
3. **Backup verification** - test restore procedures
4. **Update** Gmail Fetcher Suite to latest version

---

## Advanced Features for Power Users

This section covers sophisticated features for users who want to automate email management, perform bulk operations, and integrate Gmail Fetcher Suite into larger workflows.

### AI Newsletter Detection and Cleanup

Gmail Fetcher Suite includes intelligent AI newsletter detection that can identify and manage AI-related content automatically.

#### Understanding AI Newsletter Detection

The system identifies AI newsletters using:

**Keyword Analysis:**
- AI, artificial intelligence, machine learning, GPT, ChatGPT
- Neural networks, deep learning, automation
- LLM, large language model, generative AI

**Domain Patterns:**
- Known AI newsletter domains (openai.com, anthropic.com)
- Tech publication domains with AI content
- AI startup and research organization domains

**Content Analysis:**
- Newsletter-style formatting patterns
- Frequency of AI terminology
- Sender reputation scoring

#### Running AI Newsletter Analysis

**Dry run analysis (safe to start):**
```bash
python scripts/cleanup/ai_newsletter_analyzer.py --input backup_folder --dry-run --output ai_analysis_report.json
```

**Sample report output:**
```json
{
  "analysis_date": "2024-03-15T10:30:00",
  "total_emails_analyzed": 2847,
  "ai_newsletters_detected": 234,
  "confidence_breakdown": {
    "high_confidence": 198,
    "medium_confidence": 31,
    "low_confidence": 5
  },
  "top_ai_senders": [
    {"sender": "newsletter@openai.com", "count": 45, "confidence": 0.98},
    {"sender": "ai-digest@techcrunch.com", "count": 23, "confidence": 0.87},
    {"sender": "updates@anthropic.com", "count": 18, "confidence": 0.95}
  ],
  "storage_impact": {
    "total_size_mb": 156.7,
    "percentage_of_backup": "12.3%"
  }
}
```

#### Batch AI Newsletter Management

**Archive AI newsletters separately:**
```bash
python scripts/cleanup/ai_newsletter_manager.py --input backup_folder --action archive --output ai_newsletters_archive --confidence-threshold 0.8
```

**Delete low-value AI newsletters:**
```bash
python scripts/cleanup/ai_newsletter_manager.py --input backup_folder --action delete --confidence-threshold 0.9 --dry-run
```

**Custom AI detection configuration:**
```bash
# Edit config/ai_detection_config.json to customize keywords and domains
python scripts/cleanup/ai_newsletter_manager.py --input backup_folder --config config/my_ai_config.json
```

#### Gmail Live Cleanup

For active Gmail management (requires live API access):

```bash
python scripts/operations/gmail_ai_cleanup.py --credentials credentials.json --dry-run --max-emails 1000
```

**What this does:**
1. **Connects** to your live Gmail account
2. **Analyzes** emails for AI newsletter patterns
3. **Reports** what it would delete/archive
4. **Optionally executes** the cleanup (without --dry-run)

**Safety features:**
- Always starts with dry-run mode
- Logs all actions for review
- Can move to trash (recoverable) or archive instead of permanent deletion
- Respects Gmail API rate limits

### Batch Processing Large Email Volumes

When dealing with large Gmail accounts (10GB+), special techniques ensure efficient processing.

#### Chunked Download Strategy

**Download in date chunks:**
```bash
# Download by quarters to manage memory and API limits
python main.py fetch --query "after:2024/01/01 before:2024/04/01" --max 5000 --output "backup_2024_q1"
python main.py fetch --query "after:2024/04/01 before:2024/07/01" --max 5000 --output "backup_2024_q2"
python main.py fetch --query "after:2024/07/01 before:2024/10/01" --max 5000 --output "backup_2024_q3"
python main.py fetch --query "after:2024/10/01 before:2025/01/01" --max 5000 --output "backup_2024_q4"
```

**Download by categories:**
```bash
# Separate categories to manage different types efficiently
python main.py fetch --query "category:primary" --max 10000 --output "backup_primary"
python main.py fetch --query "category:social" --max 5000 --output "backup_social"
python main.py fetch --query "category:promotions" --max 5000 --output "backup_promotions"
python main.py fetch --query "category:updates" --max 5000 --output "backup_updates"
```

#### Parallel Processing

**Multiple terminal approach:**
```bash
# Terminal 1
python main.py fetch --query "from:company.com" --max 5000 --output "backup_work" &

# Terminal 2
python main.py fetch --query "category:newsletters" --max 5000 --output "backup_newsletters" &

# Terminal 3
python main.py fetch --query "has:attachment larger:1M" --max 2000 --output "backup_attachments" &
```

#### Memory and Performance Optimization

**For large accounts, use these settings:**

```bash
# Reduce memory usage
python main.py fetch --query "your-query" --max 1000 --format eml --output backup --batch-size 100

# Prioritize speed over completeness
python main.py fetch --query "your-query" --max 10000 --format markdown --no-attachments --output backup
```

**Monitor progress with logging:**
```bash
python main.py fetch --query "your-query" --max 10000 --output backup --log-level INFO 2>&1 | tee backup_log.txt
```

### Automating Regular Backups

#### Creating Backup Scripts

**Weekly unread backup (save as `weekly_backup.py`):**
```python
#!/usr/bin/env python3
"""
Weekly automated backup script
Run this every Sunday to backup the week's unread emails
"""

import subprocess
import datetime
import os

def weekly_backup():
    today = datetime.date.today()
    backup_name = f"weekly_backup_{today.strftime('%Y_%m_%d')}"

    cmd = [
        "python", "main.py", "fetch",
        "--query", "is:unread",
        "--max", "1000",
        "--output", backup_name,
        "--format", "both"
    ]

    print(f"🗓️  Running weekly backup: {backup_name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Weekly backup completed successfully")
        # Optional: move to monthly archive folder
        os.system(f"mv {backup_name} monthly_archives/")
    else:
        print("❌ Backup failed:", result.stderr)
        # Optional: send notification email or log to monitoring system

if __name__ == "__main__":
    weekly_backup()
```

**Monthly archive script (save as `monthly_archive.py`):**
```python
#!/usr/bin/env python3
"""
Monthly archive script - backup important emails by category
"""

import subprocess
import datetime
from pathlib import Path

def monthly_archive():
    today = datetime.date.today()
    last_month = today.replace(day=1) - datetime.timedelta(days=1)

    archive_base = f"archive_{last_month.strftime('%Y_%m')}"

    # Define categories to archive
    categories = {
        "work": "from:company.com OR from:client.com",
        "financial": "from:(bank.com OR paypal.com) OR subject:(invoice OR receipt)",
        "important": "is:starred OR is:important",
        "family": "from:(family.com OR mom@email.com OR dad@email.com)"
    }

    for category, query in categories.items():
        output_dir = f"{archive_base}_{category}"

        # Add date range to query
        date_query = f"after:{last_month.strftime('%Y/%m/01')} before:{today.strftime('%Y/%m/01')} {query}"

        cmd = [
            "python", "main.py", "fetch",
            "--query", date_query,
            "--max", "2000",
            "--output", output_dir,
            "--organize", "sender"
        ]

        print(f"📁 Archiving {category} emails...")
        subprocess.run(cmd)

    print(f"🎉 Monthly archive complete: {archive_base}")

if __name__ == "__main__":
    monthly_archive()
```

#### Scheduling Automation

**Windows Task Scheduler:**
1. Open Task Scheduler (search "Task Scheduler" in Start menu)
2. Click "Create Basic Task"
3. Name: "Gmail Weekly Backup"
4. Trigger: Weekly, Sunday, 10:00 AM
5. Action: Start a program
6. Program: `python`
7. Arguments: `C:\path\to\gmail_fetcher\weekly_backup.py`
8. Start in: `C:\path\to\gmail_fetcher`

**macOS/Linux Cron:**
```bash
# Edit crontab
crontab -e

# Add weekly backup (Sundays at 10 AM)
0 10 * * 0 cd /path/to/gmail_fetcher && python weekly_backup.py

# Add monthly archive (1st of month at 2 AM)
0 2 1 * * cd /path/to/gmail_fetcher && python monthly_archive.py
```

**Advanced scheduling with monitoring:**
```bash
# Backup with notification on completion
0 10 * * 0 cd /path/to/gmail_fetcher && python weekly_backup.py && echo "Gmail backup complete" | mail -s "Backup Status" admin@company.com
```

### Custom Configuration Files

#### Creating Custom Search Profiles

**Save as `config/my_profiles.json`:**
```json
{
  "profiles": {
    "legal_discovery": {
      "description": "Legal discovery export",
      "query_template": "after:{start_date} before:{end_date} (from:{party1} OR to:{party1} OR cc:{party1})",
      "format": "eml",
      "organize": "date",
      "max_emails": 10000,
      "include_attachments": true
    },
    "executive_backup": {
      "description": "Executive email backup",
      "query_template": "from:(ceo@company.com OR board@company.com) OR to:(ceo@company.com OR board@company.com)",
      "format": "both",
      "organize": "sender",
      "max_emails": 5000
    },
    "newsletter_cleanup": {
      "description": "Newsletter identification and archival",
      "query_template": "category:promotions OR subject:newsletter OR subject:unsubscribe",
      "format": "markdown",
      "organize": "sender",
      "max_emails": 2000
    }
  }
}
```

**Use custom profiles:**
```bash
python scripts/operations/profile_backup.py --profile legal_discovery --start-date 2023/01/01 --end-date 2023/12/31 --party1 opposing-party.com
```

#### Advanced Query Builder

**Save as `build_query.py`:**
```python
#!/usr/bin/env python3
"""
Interactive query builder for complex Gmail searches
"""

def build_query():
    query_parts = []

    print("🔍 Gmail Query Builder")
    print("Leave blank to skip any section\n")

    # Senders
    senders = input("From (comma-separated emails or domains): ").strip()
    if senders:
        sender_list = [s.strip() for s in senders.split(',')]
        query_parts.append(f"from:({' OR '.join(sender_list)})")

    # Date range
    after_date = input("After date (YYYY/MM/DD): ").strip()
    if after_date:
        query_parts.append(f"after:{after_date}")

    before_date = input("Before date (YYYY/MM/DD): ").strip()
    if before_date:
        query_parts.append(f"before:{before_date}")

    # Subject
    subject = input("Subject contains: ").strip()
    if subject:
        query_parts.append(f"subject:({subject})")

    # Status
    statuses = input("Status (unread/starred/important, comma-separated): ").strip()
    if statuses:
        status_list = [f"is:{s.strip()}" for s in statuses.split(',')]
        query_parts.append(' OR '.join(status_list))

    # Attachments
    has_attachments = input("Has attachments? (y/n): ").strip().lower()
    if has_attachments == 'y':
        query_parts.append("has:attachment")

    # Size
    size = input("Larger than (e.g., 10M, 1G): ").strip()
    if size:
        query_parts.append(f"larger:{size}")

    # Build final query
    final_query = ' '.join(query_parts)

    print(f"\n🎯 Generated query: {final_query}")
    print(f"\n📋 Full command:")
    print(f'python main.py fetch --query "{final_query}" --max 1000 --output backup')

    return final_query

if __name__ == "__main__":
    build_query()
```

### Using the Gmail API Directly

For advanced users who need real-time Gmail operations beyond backup.

#### Live Email Analysis

**Analyze current inbox without downloading:**
```bash
python scripts/operations/gmail_analyzer.py --credentials credentials.json --analysis-type summary
```

**Output example:**
```
📊 Gmail Account Analysis Summary
==================================
Total emails in account: 45,678
Unread emails: 1,234 (2.7%)
Storage used: 8.9 GB of 15 GB

📈 Top Senders (last 30 days):
1. newsletter@company.com - 45 emails
2. notifications@service.com - 32 emails
3. team@work.com - 28 emails

📊 Category Breakdown:
- Primary: 2,345 emails (45%)
- Social: 1,890 emails (36%)
- Promotions: 890 emails (17%)
- Updates: 123 emails (2%)

⚠️  Cleanup Opportunities:
- 567 promotional emails older than 6 months
- 234 social notifications older than 3 months
- 123 large emails (>10MB) with attachments
```

#### Bulk Label Management

**Apply labels to backed-up emails:**
```bash
python scripts/operations/gmail_labeler.py --credentials credentials.json --query "from:important-client.com" --label "VIP-Client" --dry-run
```

**Archive emails matching backup criteria:**
```bash
python scripts/operations/gmail_archiver.py --credentials credentials.json --query "category:promotions older_than:30d" --action archive --dry-run
```

#### Real-time Monitoring

**Monitor for specific email patterns:**
```python
#!/usr/bin/env python3
"""
Real-time Gmail monitoring script
"""

import time
from gmail_api_client import GmailClient

def monitor_important_emails():
    client = GmailClient('credentials.json')

    # Define monitoring queries
    monitors = {
        "urgent": "is:unread (urgent OR emergency OR asap)",
        "vip": "is:unread from:(ceo@company.com OR important-client.com)",
        "security": "subject:(security alert OR password reset OR login attempt)"
    }

    print("🔍 Starting Gmail monitoring...")

    while True:
        for category, query in monitors.items():
            emails = client.search_emails(query, max_results=10)

            if emails:
                print(f"🚨 {category.upper()}: {len(emails)} new emails")
                for email in emails:
                    print(f"   📧 {email['subject']} from {email['sender']}")

                # Optional: Send notification, backup immediately, etc.
                client.backup_emails(emails, f"urgent_backup_{category}")

        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    monitor_important_emails()
```

---

## Troubleshooting

This section helps you resolve common issues you might encounter while using Gmail Fetcher Suite.

### Common Problems and Solutions

#### Authentication Issues

**Problem: "Authentication failed" or "Invalid credentials"**

**Solutions:**
1. **Check credentials.json file:**
   ```bash
   # Verify file exists and is valid JSON
   python -c "import json; print(json.load(open('credentials.json'))['type'])"
   ```
   Should output: `"desktop"`

2. **Re-download credentials:**
   - Go to Google Cloud Console
   - Navigate to your project → Credentials
   - Download the OAuth client credentials again
   - Replace the old credentials.json file

3. **Delete and recreate token:**
   ```bash
   rm token.json
   python main.py fetch --auth-only
   ```

4. **Check project settings:**
   - Ensure Gmail API is enabled
   - Verify OAuth consent screen is configured
   - Check that your Google account has access

**Problem: "Access denied" or "Insufficient permissions"**

**Solution:**
```bash
# Delete existing token and re-authorize with correct scopes
rm token.json
python main.py fetch --auth-only
```

Make sure to grant all requested permissions during the OAuth flow.

**Problem: "App not verified" warning**

This is normal for personal projects. **Solutions:**
- Click "Advanced" → "Go to [App Name] (unsafe)"
- Or complete Google's app verification process (for production use)

#### API Limits and Quotas

**Problem: "Rate limit exceeded" or "Quota exceeded"**

**Understanding Gmail API limits:**
- 1,000,000,000 quota units per day
- 250 quota units per user per 100 seconds
- Each email fetch costs 5-10 units

**Solutions:**
1. **Reduce batch size:**
   ```bash
   python main.py fetch --query "your-query" --max 500  # Instead of 5000
   ```

2. **Add delays between requests:**
   ```bash
   python main.py fetch --query "your-query" --delay 1  # 1 second between emails
   ```

3. **Use chunked downloads:**
   ```bash
   # Instead of downloading 10,000 emails at once
   python main.py fetch --query "after:2024/01/01 before:2024/02/01" --max 1000
   python main.py fetch --query "after:2024/02/01 before:2024/03/01" --max 1000
   ```

4. **Monitor quota usage:**
   ```bash
   python scripts/utils/check_quota.py --credentials credentials.json
   ```

**Problem: "Backend Error" or "Internal Error"**

These are temporary Gmail server issues. **Solutions:**
- Wait 5-10 minutes and retry
- Use smaller batch sizes
- Implement automatic retry with exponential backoff

#### File System Errors

**Problem: "Permission denied" when creating files**

**Solutions:**
1. **Check folder permissions:**
   ```bash
   # Windows
   icacls backup_folder /grant %USERNAME%:F

   # Mac/Linux
   chmod 755 backup_folder
   sudo chown -R $USER backup_folder
   ```

2. **Run with elevated permissions (if necessary):**
   ```bash
   # Windows (as administrator)
   python main.py fetch --query "your-query" --output "C:/Backups/Gmail"

   # Mac/Linux
   sudo python main.py fetch --query "your-query" --output "/home/user/backups"
   ```

3. **Use user directories:**
   ```bash
   # Safe default locations
   python main.py fetch --query "your-query" --output "~/Documents/gmail_backup"
   ```

**Problem: "Filename too long" errors**

**Solutions:**
1. **Use shorter output names:**
   ```bash
   python main.py fetch --query "your-query" --output "backup" --max-filename-length 100
   ```

2. **Organize by date instead of sender:**
   ```bash
   python main.py fetch --query "your-query" --organize date  # Shorter filenames
   ```

**Problem: "Disk space full"**

**Prevention and solutions:**
1. **Check available space before backup:**
   ```bash
   # Windows
   dir /-c

   # Mac/Linux
   df -h
   ```

2. **Estimate backup size:**
   ```bash
   python scripts/utils/estimate_backup_size.py --query "your-query" --max 1000
   ```

3. **Use compression:**
   ```bash
   python main.py fetch --query "your-query" --compress --output backup_compressed
   ```

4. **Clean up old backups:**
   ```bash
   python scripts/maintenance/cleanup_old_backups.py --older-than 90d --dry-run
   ```

#### Performance Problems

**Problem: Backup is very slow**

**Diagnostics:**
```bash
# Check network speed
python scripts/utils/network_test.py

# Check Gmail API response times
python scripts/utils/api_benchmark.py --credentials credentials.json
```

**Solutions:**
1. **Optimize format choice:**
   ```bash
   # EML only (faster, smaller)
   python main.py fetch --query "your-query" --format eml

   # Markdown only (faster processing)
   python main.py fetch --query "your-query" --format markdown
   ```

2. **Reduce processing:**
   ```bash
   # Skip attachment processing
   python main.py fetch --query "your-query" --no-attachments

   # Minimal metadata
   python main.py fetch --query "your-query" --minimal-metadata
   ```

3. **Parallel processing:**
   ```bash
   # Use multiple terminals for different categories
   python main.py fetch --query "category:primary" --output backup_primary &
   python main.py fetch --query "category:social" --output backup_social &
   ```

**Problem: High memory usage**

**Solutions:**
1. **Reduce batch size:**
   ```bash
   python main.py fetch --query "your-query" --batch-size 50  # Default is 100
   ```

2. **Process in chunks:**
   ```bash
   # Process monthly instead of all at once
   python main.py fetch --query "after:2024/01/01 before:2024/02/01" --max 2000
   ```

3. **Monitor memory usage:**
   ```bash
   # Windows
   tasklist /fi "imagename eq python.exe"

   # Mac/Linux
   top -p $(pgrep python)
   ```

### Network and Connectivity Issues

**Problem: "Connection timeout" or "Network error"**

**Solutions:**
1. **Check internet connection:**
   ```bash
   ping gmail.googleapis.com
   ```

2. **Retry with longer timeout:**
   ```bash
   python main.py fetch --query "your-query" --timeout 60  # 60 seconds
   ```

3. **Use proxy settings (if behind corporate firewall):**
   ```bash
   export HTTPS_PROXY=http://proxy.company.com:8080
   python main.py fetch --query "your-query"
   ```

4. **Check firewall settings:**
   - Ensure Python can access the internet
   - Whitelist googleapis.com domains

**Problem: "SSL Certificate errors"**

**Solutions:**
1. **Update certificates:**
   ```bash
   pip install --upgrade certifi
   ```

2. **Bypass SSL verification (temporary):**
   ```bash
   python main.py fetch --query "your-query" --no-ssl-verify
   ```
   ⚠️ **Warning:** Only use this temporarily and on trusted networks

### Email Content Issues

**Problem: "Email encoding errors" or garbled text**

**Solutions:**
1. **Force encoding detection:**
   ```bash
   python main.py fetch --query "your-query" --auto-detect-encoding
   ```

2. **Specify encoding:**
   ```bash
   python main.py fetch --query "your-query" --encoding utf-8
   ```

3. **Use enhanced parser:**
   ```bash
   python scripts/parsers/advanced_email_parser.py --input email.eml --strategy readability
   ```

**Problem: "Missing attachments" or "Incomplete emails"**

**Solutions:**
1. **Enable attachment download:**
   ```bash
   python main.py fetch --query "your-query" --include-attachments
   ```

2. **Increase size limits:**
   ```bash
   python main.py fetch --query "your-query" --max-attachment-size 50M
   ```

3. **Verify email completeness:**
   ```bash
   python scripts/utils/verify_backup.py --input backup_folder --check-attachments
   ```

### Script and Tool Errors

**Problem: "Module not found" errors**

**Solutions:**
1. **Install missing dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_advanced.txt  # For advanced features
   ```

2. **Check Python path:**
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   ```

3. **Use virtual environment:**
   ```bash
   python -m venv gmail_env
   # Windows
   gmail_env\Scripts\activate
   # Mac/Linux
   source gmail_env/bin/activate

   pip install -r requirements.txt
   ```

**Problem: "Script not found" or "Command not recognized"**

**Solutions:**
1. **Check working directory:**
   ```bash
   pwd  # Mac/Linux
   cd   # Windows
   ```

2. **Use full paths:**
   ```bash
   python C:\full\path\to\gmail_fetcher\main.py fetch --query "your-query"
   ```

3. **Check file permissions:**
   ```bash
   # Mac/Linux
   chmod +x main.py
   ```

### Debugging Techniques

#### Enable Verbose Logging

```bash
python main.py fetch --query "your-query" --log-level DEBUG --output backup 2>&1 | tee debug_log.txt
```

This creates a detailed log file showing exactly what the tool is doing.

#### Test Mode Operations

```bash
# Test authentication only
python main.py fetch --auth-only

# Test with minimal emails
python main.py fetch --query "is:unread" --max 5 --output test

# Test specific features
python main.py parse --input test_email.eml --output test.md --debug
```

#### Check System Requirements

```bash
# Verify Python version (3.8+ required)
python --version

# Check installed packages
pip list

# Verify Gmail API access
python -c "from googleapiclient.discovery import build; print('Gmail API available')"
```

#### Get Help and Support

```bash
# Built-in help
python main.py --help
python main.py fetch --help

# Version information
python main.py --version

# System diagnostics
python scripts/utils/system_check.py
```

**Getting additional help:**
1. Check the documentation in `docs/` folder
2. Review example configurations in `examples/` folder
3. Look at log files for specific error messages
4. Use `--dry-run` flags to test without making changes

---

## Best Practices

This section outlines proven strategies for effective email backup, organization, and management using Gmail Fetcher Suite.

### Backup Strategies and Schedules

#### The 3-2-1 Backup Rule for Email

**3 copies:** Original (Gmail) + Local backup + Cloud/external backup
**2 different media:** Local drive + Cloud storage or external drive
**1 offsite:** Cloud storage or physically separate location

**Implementation:**
```bash
# Local backup (primary)
python main.py fetch --query "after:2024/01/01" --output local_backup

# External drive backup (secondary)
python main.py fetch --query "after:2024/01/01" --output "/Volumes/ExternalDrive/gmail_backup"

# Cloud preparation (tertiary)
tar -czf gmail_backup_2024.tar.gz local_backup/
# Upload to cloud storage service
```

#### Backup Schedule Templates

**Personal Use Schedule:**
```
📅 Weekly (Sunday):
- Unread emails backup
- Important emails backup
- Quick duplicate cleanup

📅 Monthly (1st):
- Full monthly archive
- Newsletter organization
- Storage usage review

📅 Quarterly (Jan/Apr/Jul/Oct):
- Complete backup verification
- Archive compression
- Security audit of stored emails

📅 Annually (January):
- Full account backup
- Long-term archive creation
- Backup strategy review
```

**Business Use Schedule:**
```
📅 Daily (automated):
- Critical communications backup
- Legal/compliance email capture
- Security alerts backup

📅 Weekly:
- Department-wise email archives
- Project communication backup
- Client correspondence backup

📅 Monthly:
- Financial email records
- HR communication archives
- Vendor/supplier email backup

📅 Quarterly:
- Audit trail creation
- Compliance report generation
- Legal discovery preparation
```

#### Backup Scope Strategies

**Comprehensive Strategy (Complete Protection):**
```bash
# Backup everything by category
python main.py fetch --query "category:primary" --max 10000 --output backup_primary
python main.py fetch --query "category:social" --max 5000 --output backup_social
python main.py fetch --query "category:promotions" --max 3000 --output backup_promotions
python main.py fetch --query "category:updates" --max 5000 --output backup_updates
```

**Selective Strategy (Important Only):**
```bash
# Focus on high-value emails
python main.py fetch --query "is:starred OR is:important OR has:attachment" --output backup_important
python main.py fetch --query "from:company.com OR from:bank.com" --output backup_business
python main.py fetch --query "subject:(contract OR invoice OR legal OR tax)" --output backup_financial
```

**Time-Based Strategy (Rolling Archive):**
```bash
# Keep last 2 years accessible, archive older
python main.py fetch --query "newer_than:2y" --output current_emails
python main.py fetch --query "older_than:2y after:2020/01/01" --output historical_archive
```

### Organizing Your Email Archive

#### Folder Structure Best Practices

**Hierarchical Organization:**
```
Email_Archive/
├── Active/                          # Current year, frequently accessed
│   ├── 2024_Primary/               # Main correspondence
│   ├── 2024_Work/                  # Professional emails
│   ├── 2024_Personal/              # Personal correspondence
│   └── 2024_Financial/             # Money-related emails
├── Reference/                       # Historical but accessible
│   ├── 2023_Complete/              # Previous year complete archive
│   ├── 2022_Complete/
│   ├── Projects/                   # Project-specific archives
│   │   ├── Project_Alpha_2023/
│   │   └── Project_Beta_2024/
│   └── Legal/                      # Legal and compliance
│       ├── Contracts_2020-2024/
│       └── Discovery_2023/
├── Archive/                         # Long-term storage
│   ├── Compressed/                 # Older emails, compressed
│   │   ├── 2015-2019_Archive.zip
│   │   └── 2020-2021_Archive.zip
│   └── Cold_Storage/               # Rarely accessed
│       ├── Historical_Newsletters/
│       └── Old_Social_Media/
└── Working/                        # Temporary processing
    ├── Current_Downloads/          # Active backup operations
    ├── Processing/                 # Being organized
    └── Quality_Check/              # Verification in progress
```

#### Naming Conventions

**File Naming Standards:**
```
✅ Good Examples:
backup_2024_q1_work_emails/
archive_2023_financial_records/
project_alpha_communications_2024/
legal_discovery_johnson_v_smith_2023/

❌ Avoid:
backup1/
stuff/
emails/
important/
```

**Date Format Standards:**
- Use ISO format: `YYYY-MM-DD` or `YYYY_MM_DD`
- Be consistent across all backups
- Include time ranges in folder names: `2024_q1`, `2024_jan_mar`

#### Content-Based Organization

**By Relationship Type:**
```bash
# Family and personal
python main.py fetch --query "from:(family.com OR mom@email.com)" --organize sender --output family_archive

# Professional networks
python main.py fetch --query "from:(company.com OR client.com)" --organize sender --output professional_archive

# Service providers
python main.py fetch --query "from:(bank.com OR utility.com OR insurance.com)" --organize sender --output services_archive
```

**By Content Sensitivity:**
```bash
# High sensitivity (financial, legal, medical)
python main.py fetch --query "subject:(tax OR legal OR medical OR ssn OR account)" --format eml --output sensitive_archive

# Medium sensitivity (work, personal correspondence)
python main.py fetch --query "from:company.com OR is:important" --format both --output business_archive

# Low sensitivity (newsletters, notifications)
python main.py fetch --query "category:promotions OR subject:newsletter" --format markdown --output reference_archive
```

### Storage Management Tips

#### Storage Estimation and Planning

**Calculate storage needs:**
```bash
# Estimate backup size before downloading
python scripts/utils/storage_estimator.py --query "after:2024/01/01" --max 5000

# Sample output:
# Estimated emails: 4,247
# Estimated size (EML): 2.8 GB
# Estimated size (Markdown): 1.2 GB
# Estimated size (Both): 4.0 GB
# Recommended free space: 6.0 GB
```

**Monitor storage usage:**
```bash
# Check current backup sizes
python scripts/utils/backup_analyzer.py --input backup_folder

# Sample output:
# Backup Analysis Report
# =====================
# Total emails: 15,678
# Total size: 12.4 GB
# Breakdown:
#   EML files: 8.9 GB (72%)
#   Markdown files: 3.1 GB (25%)
#   Attachments: 0.4 GB (3%)
#
# Largest categories:
#   Work emails: 6.2 GB (50%)
#   Newsletters: 2.1 GB (17%)
#   Personal: 1.8 GB (15%)
```

#### Compression Strategies

**Archive older emails:**
```bash
# Compress yearly archives
tar -czf archive_2022.tar.gz backup_2022/
tar -czf archive_2021.tar.gz backup_2021/

# Remove originals after verification
rm -rf backup_2022/ backup_2021/
```

**Selective compression:**
```bash
# Compress low-priority categories
tar -czf newsletters_archive.tar.gz backup_newsletters/
tar -czf social_media_archive.tar.gz backup_social/

# Keep important emails uncompressed for quick access
# Leave backup_work/ and backup_important/ uncompressed
```

**Email content optimization:**
```bash
# Remove large attachments from archives (keep metadata)
python scripts/maintenance/optimize_backup.py --input backup_folder --remove-attachments-larger-than 10M --keep-metadata

# Convert EML to Markdown only (smaller size)
python scripts/parsers/batch_convert.py --input backup_folder --output backup_optimized --format markdown-only
```

#### Cloud Storage Integration

**Prepare for cloud upload:**
```bash
# Create upload-ready archives
python scripts/utils/cloud_prep.py --input backup_2024 --output cloud_ready_2024 --encrypt --split-size 2G

# Creates:
# cloud_ready_2024_part01.enc (2GB)
# cloud_ready_2024_part02.enc (2GB)
# cloud_ready_2024_part03.enc (1.2GB)
# cloud_ready_2024_manifest.json
```

**Encryption for cloud storage:**
```bash
# Encrypt sensitive backups before cloud upload
gpg --symmetric --cipher-algo AES256 --compress-algo 2 backup_financial.tar.gz

# Result: backup_financial.tar.gz.gpg (encrypted file safe for cloud)
```

### Privacy and Security Considerations

#### Data Protection Strategies

**Local Storage Security:**
1. **File System Encryption:**
   - Windows: BitLocker for backup drives
   - Mac: FileVault for backup folders
   - Linux: LUKS encryption for backup partitions

2. **Access Control:**
   ```bash
   # Restrict backup folder access (Linux/Mac)
   chmod 700 backup_folder
   chown $USER:$USER backup_folder

   # Windows: Use NTFS permissions to restrict access
   ```

3. **Secure Deletion:**
   ```bash
   # Securely delete temporary files
   python scripts/security/secure_delete.py --input temp_backup --overwrite-passes 3
   ```

#### Email Content Redaction

**Remove sensitive information:**
```bash
# Redact SSNs, credit card numbers, etc.
python scripts/security/content_redactor.py --input backup_folder --redact-patterns ssn,credit_card,phone --output redacted_backup
```

**Create sanitized copies for sharing:**
```bash
# Remove headers and metadata for sharing
python scripts/security/sanitize_emails.py --input backup_folder --remove-headers --remove-ips --output sanitized_backup
```

#### Compliance Considerations

**Legal Hold Implementation:**
```bash
# Create immutable legal hold copies
python scripts/compliance/legal_hold.py --input backup_folder --case-id "Johnson_v_Smith_2024" --output legal_hold --read-only
```

**Audit Trail Maintenance:**
```bash
# Generate audit logs for backup operations
python scripts/compliance/audit_logger.py --backup-folder backup_2024 --generate-report compliance_report_2024.pdf
```

**Data Retention Policies:**
```python
# retention_policy.py
RETENTION_RULES = {
    "financial": "7 years",      # Tax and financial records
    "legal": "indefinite",       # Legal communications
    "work": "3 years",           # Professional correspondence
    "personal": "5 years",       # Personal emails
    "newsletters": "1 year",     # Newsletters and promotions
    "social": "6 months"         # Social media notifications
}

# Auto-apply retention policies
python scripts/compliance/apply_retention.py --config retention_policy.py --backup-folder archive_folder --dry-run
```

### GDPR Compliance Basics

#### Right to Data Portability

**Create GDPR-compliant exports:**
```bash
# Export all personal data in standard format
python scripts/compliance/gdpr_export.py --query "from:user@domain.com OR to:user@domain.com" --format json --include-metadata --output gdpr_export_user123.zip
```

#### Right to Erasure

**Implement data deletion:**
```bash
# Find and delete specific person's emails
python scripts/compliance/data_eraser.py --search-terms "john.doe@email.com" --backup-folder archive_folder --verify-deletion --log-actions
```

#### Data Processing Records

**Maintain processing logs:**
```json
{
  "processing_activity": "Email Backup and Archive",
  "legal_basis": "Legitimate Interest - Business Records",
  "data_categories": ["Email content", "Metadata", "Attachments"],
  "retention_period": "3 years from last business contact",
  "security_measures": ["Encryption at rest", "Access controls", "Audit logging"],
  "last_updated": "2024-03-15"
}
```

#### Regular Compliance Audits

**Monthly compliance check:**
```bash
# Generate compliance dashboard
python scripts/compliance/compliance_dashboard.py --backup-root Email_Archive --output compliance_report.html

# Check data retention compliance
python scripts/compliance/retention_audit.py --config retention_policy.py --backup-root Email_Archive --report-violations
```

**Privacy impact assessment:**
```bash
# Analyze backup contents for privacy risks
python scripts/compliance/privacy_analyzer.py --input backup_folder --scan-for pii,financial,health --generate-report privacy_impact_2024.pdf
```

These best practices ensure your email archives are well-organized, secure, and compliant with relevant regulations while maintaining easy access to important information.

---

## Quick Reference

### Command Cheat Sheet

#### Basic Commands

**Download emails:**
```bash
# Basic download
python main.py fetch --query "SEARCH_QUERY" --max 1000 --output backup_folder

# Authentication test
python main.py fetch --auth-only

# Download with specific format
python main.py fetch --query "is:unread" --format eml --output unread_backup
python main.py fetch --query "is:unread" --format markdown --output unread_backup
python main.py fetch --query "is:unread" --format both --output unread_backup
```

**Organization options:**
```bash
# Organize by date (default)
python main.py fetch --query "QUERY" --organize date --output backup

# Organize by sender
python main.py fetch --query "QUERY" --organize sender --output backup

# No organization (flat structure)
python main.py fetch --query "QUERY" --organize none --output backup
```

**Parse and convert:**
```bash
# Convert EML to Markdown
python main.py parse --input email.eml --output email.md --format markdown

# Batch convert folder
python main.py parse --input backup_folder --output converted_folder --format markdown

# Advanced parsing
python scripts/parsers/advanced_email_parser.py --input email.eml --strategy auto
```

#### Sample Scenarios

**Pre-built backup scenarios:**
```bash
# View available scenarios
python examples/samples.py

# Run specific scenarios
python examples/samples.py unread          # Backup unread emails
python examples/samples.py newsletters     # Archive newsletters
python examples/samples.py important       # Backup important emails
python examples/samples.py work           # Archive work emails
python examples/samples.py financial      # Backup financial emails
```

#### Maintenance and Tools

**Backup management:**
```bash
# Find duplicates
python scripts/maintenance/find_duplicates.py --input backup_folder

# Remove duplicates
python scripts/maintenance/dedupe_emails.py --input backup_folder --prefer larger --dry-run

# Merge backups
python scripts/backup/merge_backups.py --source backup2 --destination backup1

# Compress old archives
python scripts/maintenance/compress_archive.py --input old_backup --output archive.tar.gz
```

**Analysis and reporting:**
```bash
# Backup statistics
python scripts/utils/backup_stats.py --input backup_folder

# Storage analysis
python scripts/utils/storage_analyzer.py --input backup_folder

# Content analysis
python scripts/analysis/email_analyzer.py --input backup_folder --generate-report
```

### Search Operator Reference

#### Basic Operators

| Operator | Purpose | Example |
|----------|---------|---------|
| `from:` | Sender email or domain | `from:boss@company.com` |
| `to:` | Recipient email | `to:me@email.com` |
| `subject:` | Subject line contains | `subject:meeting` |
| `has:attachment` | Has any attachment | `has:attachment` |
| `is:unread` | Unread emails | `is:unread` |
| `is:starred` | Starred emails | `is:starred` |
| `is:important` | Important emails | `is:important` |

#### Time-Based Operators

| Operator | Purpose | Example |
|----------|---------|---------|
| `after:` | After specific date | `after:2024/01/01` |
| `before:` | Before specific date | `before:2024/12/31` |
| `newer_than:` | Relative time (recent) | `newer_than:7d` |
| `older_than:` | Relative time (old) | `older_than:1y` |

**Time units:** `d` (days), `m` (months), `y` (years)

#### Advanced Operators

| Operator | Purpose | Example |
|----------|---------|---------|
| `larger:` | File size larger than | `larger:10M` |
| `smaller:` | File size smaller than | `smaller:1M` |
| `filename:` | Attachment filename | `filename:pdf` |
| `category:` | Gmail category | `category:promotions` |
| `label:` | Gmail label | `label:work` |
| `in:` | Gmail folder | `in:sent` |

#### Combining Operators

| Combination | Purpose | Example |
|-------------|---------|---------|
| Space (AND) | All conditions must match | `from:boss subject:meeting` |
| `OR` | Any condition can match | `from:(boss OR manager)` |
| `-` (NOT) | Exclude condition | `from:company.com -from:noreply` |
| `()` | Group conditions | `(urgent OR important) from:boss` |
| `""` | Exact phrase | `subject:"weekly meeting"` |

#### Common Query Patterns

**Business emails:**
```
from:company.com
from:(client1.com OR client2.com OR partner.com)
subject:(contract OR proposal OR invoice)
```

**Personal emails:**
```
from:(family.com OR friends@email.com)
is:important OR is:starred
subject:(birthday OR anniversary OR vacation)
```

**Cleanup queries:**
```
category:promotions older_than:3m
subject:newsletter older_than:1m
larger:10M older_than:6m
```

**Time-based queries:**
```
after:2024/01/01 before:2024/04/01    # Q1 2024
newer_than:30d                        # Last month
older_than:1y -is:important           # Old, unimportant
```

### File Format Specifications

#### EML Format
- **Use case:** Email client import, legal documentation, preserving original formatting
- **Contains:** Full email headers, HTML/text content, attachments (base64 encoded)
- **Size:** Larger due to complete preservation
- **Compatibility:** Outlook, Thunderbird, Apple Mail, most email clients

#### Markdown Format
- **Use case:** Reading, documentation, note-taking, web publishing
- **Contains:** Clean text content, metadata table, simplified formatting
- **Size:** Smaller, text-only
- **Compatibility:** Any text editor, documentation systems, websites

**Sample Markdown structure:**
```markdown
---
Date: 2024-03-15 14:30:00
From: John Smith <john@company.com>
To: me@email.com
Subject: Project Update
Message-ID: abc123@gmail.com
---

# Project Update

The quarterly review is scheduled for next week.

**Action Items:**
- [ ] Prepare presentation
- [ ] Review budget numbers
- [ ] Schedule follow-up meeting
```

### Configuration Options

#### Main Configuration

**Command line arguments:**
```bash
--query          # Gmail search query (required)
--max           # Maximum emails to download (default: 1000)
--output        # Output directory name (default: gmail_backup)
--format        # Output format: eml, markdown, both (default: both)
--organize      # Organization: date, sender, none (default: date)
--credentials   # Credentials file path (default: credentials.json)
--log-level     # Logging level: DEBUG, INFO, WARNING, ERROR
```

#### Advanced Options

**Performance tuning:**
```bash
--batch-size 50           # Process emails in smaller batches
--delay 1                 # Add delay between requests (seconds)
--timeout 60              # Network timeout (seconds)
--max-workers 4           # Parallel processing threads
```

**Content options:**
```bash
--include-attachments     # Download email attachments
--max-attachment-size 10M # Limit attachment size
--no-html                 # Skip HTML content processing
--encoding utf-8          # Force specific encoding
```

#### Configuration Files

**Create custom profiles in `config/profiles.json`:**
```json
{
  "work_backup": {
    "query": "from:company.com",
    "format": "both",
    "organize": "sender",
    "max": 5000
  },
  "newsletter_archive": {
    "query": "category:promotions",
    "format": "markdown",
    "organize": "sender",
    "max": 2000
  }
}
```

**Use profiles:**
```bash
python main.py fetch --profile work_backup --output work_archive
```

### Keyboard Shortcuts and Aliases

#### Create Command Aliases

**Windows (PowerShell profile):**
```powershell
# Add to $PROFILE file
function Gmail-Fetch { python C:\path\to\gmail_fetcher\main.py fetch $args }
function Gmail-Unread { Gmail-Fetch --query "is:unread" --max 1000 }
function Gmail-Important { Gmail-Fetch --query "is:starred OR is:important" }

# Usage:
Gmail-Unread --output unread_backup
Gmail-Important --output important_backup
```

**Mac/Linux (bash profile):**
```bash
# Add to ~/.bashrc or ~/.zshrc
alias gmail-fetch='python ~/gmail_fetcher/main.py fetch'
alias gmail-unread='gmail-fetch --query "is:unread" --max 1000'
alias gmail-important='gmail-fetch --query "is:starred OR is:important"'

# Usage:
gmail-unread --output unread_backup
gmail-important --output important_backup
```

#### Quick Commands Script

**Save as `quick_commands.py`:**
```python
#!/usr/bin/env python3
"""Quick Gmail Fetcher commands"""

import subprocess
import sys

commands = {
    "1": ["fetch", "--query", "is:unread", "--max", "1000", "--output", "unread"],
    "2": ["fetch", "--query", "is:starred OR is:important", "--output", "important"],
    "3": ["fetch", "--query", "category:promotions", "--organize", "sender", "--output", "newsletters"],
    "4": ["fetch", "--query", "has:attachment larger:1M", "--output", "large_attachments"],
    "auth": ["fetch", "--auth-only"]
}

def main():
    print("Gmail Fetcher Quick Commands:")
    print("1. Backup unread emails")
    print("2. Backup important emails")
    print("3. Archive newsletters")
    print("4. Backup large attachments")
    print("auth. Test authentication")

    choice = input("\nChoose command (1-4, auth): ").strip()

    if choice in commands:
        cmd = ["python", "main.py"] + commands[choice]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python quick_commands.py
```

### Glossary of Terms

**API (Application Programming Interface):** The method Gmail Fetcher uses to communicate with Gmail servers securely.

**Authentication:** The process of verifying your identity with Google to access your Gmail account.

**Batch Size:** Number of emails processed at once. Smaller batches use less memory but may be slower.

**Credentials:** The security file (`credentials.json`) that identifies your application to Google.

**Dry Run:** Testing mode that shows what would happen without actually making changes.

**EML:** Email format that preserves the complete original email structure and formatting.

**Gmail API:** Google's official interface for programmatically accessing Gmail accounts.

**Markdown:** Human-readable text format with simple formatting syntax.

**Message ID:** Unique identifier assigned to each email by the email system.

**OAuth:** Security protocol used by Google to grant access to your Gmail without sharing passwords.

**Query:** Search command using Gmail's search operators to find specific emails.

**Rate Limiting:** Google's restriction on how many API requests can be made per time period.

**Token:** File (`token.json`) containing your authentication session information.

---

## Frequently Asked Questions

### Getting Started FAQs

**Q: Do I need programming experience to use Gmail Fetcher Suite?**
A: No. While it's a command-line tool, this user guide provides exact commands to copy and paste. Most users can follow the step-by-step instructions without any programming knowledge.

**Q: Is it safe to give Gmail Fetcher access to my email?**
A: Yes. The tool uses Google's official OAuth system, which is the same security method used by legitimate email clients. You control what permissions to grant, and you can revoke access anytime through your Google account settings.

**Q: Will this download ALL my emails, even deleted ones?**
A: No. It only downloads emails that match your search query and are currently in your Gmail account. Permanently deleted emails cannot be recovered.

**Q: How much storage space do I need?**
A: Roughly 1GB per 10,000 emails for both formats combined. A typical Gmail account (5GB) needs about 4-8GB of local storage space for a complete backup.

### Technical FAQs

**Q: What's the difference between EML and Markdown formats?**
A: EML preserves the complete original email (including formatting and attachments) and can be imported into email clients. Markdown creates clean, readable text files perfect for documentation and searching.

**Q: Can I backup emails from multiple Gmail accounts?**
A: Yes, but you need separate credentials for each account. Create different folders and run the backup process separately for each account.

**Q: How often should I backup my emails?**
A: For most users, monthly backups are sufficient. Business users might want weekly backups. The tool is designed for incremental backups, so you can run it frequently without re-downloading the same emails.

**Q: Can I resume an interrupted backup?**
A: Yes. The tool automatically skips emails that have already been downloaded, so you can safely re-run the same command to continue where you left off.

### Usage FAQs

**Q: How do I backup emails from a specific person?**
A: Use: `python main.py fetch --query "from:person@email.com" --output backup_person`

**Q: How do I backup only emails with attachments?**
A: Use: `python main.py fetch --query "has:attachment" --output backup_attachments`

**Q: Can I backup emails from a date range?**
A: Yes: `python main.py fetch --query "after:2024/01/01 before:2024/06/30" --output backup_h1_2024`

**Q: How do I exclude certain types of emails?**
A: Use the minus operator: `python main.py fetch --query "from:company.com -subject:newsletter" --output backup_work`

### Troubleshooting FAQs

**Q: I get "Authentication failed" errors. What should I do?**
A: 1) Delete `token.json` and re-authenticate, 2) Re-download `credentials.json` from Google Cloud Console, 3) Ensure Gmail API is enabled in your Google Cloud project.

**Q: The backup is very slow. How can I speed it up?**
A: 1) Use `--format eml` or `--format markdown` instead of both, 2) Reduce `--max` number, 3) Use more specific search queries to get fewer emails.

**Q: I'm getting "Rate limit exceeded" errors.**
A: Gmail limits how fast you can download emails. Wait 10-15 minutes and try again with a smaller `--max` number (like 500 instead of 5000).

**Q: Some emails appear garbled or have weird characters.**
A: Try: `python main.py fetch --query "your-query" --encoding utf-8 --auto-detect-encoding`

### Advanced FAQs

**Q: Can I schedule automatic backups?**
A: Yes. Use Windows Task Scheduler, macOS/Linux cron, or the sample automation scripts provided in the `scripts/` folder.

**Q: How do I merge multiple backup folders?**
A: Use: `python scripts/backup/merge_backups.py --source backup2 --destination backup1 --dry-run` (remove --dry-run to actually merge).

**Q: Can I convert old EML files to Markdown?**
A: Yes: `python scripts/parsers/eml_to_markdown.py --input backup_folder --output markdown_folder`

**Q: How do I find specific emails in my backup?**
A: Use your computer's file search feature, or command-line tools like `grep` for content search and filename patterns for metadata search.

### Legal and Compliance FAQs

**Q: Can I use this for legal discovery or compliance?**
A: Yes. Use `--format eml` to preserve original email formatting and metadata. However, consult with your legal team about specific requirements in your jurisdiction.

**Q: How do I ensure GDPR compliance?**
A: The tool includes features for data export, deletion tracking, and retention management. See the "Best Practices" section for detailed compliance guidance.

**Q: Can I delete the emails from Gmail after backing them up?**
A: The backup tool doesn't delete emails from Gmail - it only downloads copies. You would need to delete emails manually in Gmail or use the advanced Gmail API features for automated cleanup.

**Q: How long should I keep email backups?**
A: This depends on your needs:
- Personal: 2-5 years for important emails
- Business: 7 years for financial records, 3-5 years for general correspondence
- Legal: Consult with attorneys for specific requirements

This user guide provides comprehensive coverage of the Gmail Fetcher Suite's capabilities while remaining accessible to non-technical users. It emphasizes practical, task-oriented guidance with plenty of examples and clear explanations of technical concepts.