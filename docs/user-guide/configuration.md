# Gmail Assistant Configuration Reference

Complete reference for all configuration files used by gmail-assistant v2.0.0.

**Version**: 2.0.0
**Status**: Production
**Last Updated**: 2026-01-09

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [AppConfig (Main Configuration)](#appconfig-main-configuration)
3. [AI Newsletter Cleaner Config](#ai-newsletter-cleaner-config)
4. [Email Organization Config](#email-organization-config)
5. [Analysis Config](#analysis-config)
6. [Deletion Patterns Config](#deletion-patterns-config)
7. [Gmail Assistant Presets](#gmail-assistant-presets)
8. [Configuration Loading](#configuration-loading)
9. [Validation Rules](#validation-rules)
10. [Environment Variables](#environment-variables)

---

## Quick Reference

### File Locations

```
User Config:          ~/.gmail-assistant/config.json
Project Config:       ./gmail-assistant.json (CWD)
AI Patterns:          config/config.json
Organization:        config/organizer_config.json
Analysis:            config/analysis.json
Deletion Patterns:    config/deletion.json
Email Presets:       config/gmail_assistant_config.json
```

### Minimal Config

```json
{
  "credentials_path": "~/.gmail-assistant/credentials.json",
  "token_path": "~/.gmail-assistant/token.json",
  "output_dir": "~/.gmail-assistant/backups"
}
```

---

## AppConfig (Main Configuration)

**File**: `~/.gmail-assistant/config.json` or via CLI `--config`
**Module**: `gmail_assistant.core.config:AppConfig`
**Format**: JSON
**Required**: No (uses secure defaults if missing)

### Schema

```json
{
  "credentials_path": "string",
  "token_path": "string",
  "output_dir": "string",
  "max_emails": "integer (optional)",
  "rate_limit_per_second": "number (optional)",
  "log_level": "string (optional)"
}
```

### Parameters

#### credentials_path

**Type**: String (file path)
**Required**: No
**Default**: `~/.gmail-assistant/credentials.json`
**Security**: Must be outside git repository (enforced unless `--allow-repo-credentials`)

OAuth credentials file from Google Cloud Console. Contains client ID and secret.

**Path Resolution**:
- Relative paths resolved relative to config file location
- Absolute paths used as-is
- `~` expands to user home directory

**Example**:
```json
{
  "credentials_path": "~/.gmail-assistant/credentials.json"
}
```

#### token_path

**Type**: String (file path)
**Required**: No
**Default**: `~/.gmail-assistant/token.json`
**Security**: Must be outside git repository (enforced unless `--allow-repo-credentials`)
**Deprecated**: Now uses OS keyring for secure storage

OAuth access token generated after first authentication. Deprecated in favor of keyring storage.

**Path Resolution**:
- Same as credentials_path
- Relative to config file parent directory

**Note**: Credentials are now stored in OS keyring. This path is maintained for backward compatibility with legacy plaintext tokens.

**Example**:
```json
{
  "token_path": "~/.gmail-assistant/token.json"
}
```

#### output_dir

**Type**: String (directory path)
**Required**: No
**Default**: `~/.gmail-assistant/backups`

Directory where downloaded emails are saved. Created if missing.

**Path Resolution**:
- Relative paths resolved relative to config file location
- Absolute paths used as-is
- Directory created if doesn't exist

**Example**:
```json
{
  "output_dir": "./backups"
}
```

#### max_emails

**Type**: Integer
**Required**: No
**Default**: 1000
**Valid Range**: 1 - 50000

Maximum number of emails to fetch in a single operation. Can be overridden by CLI `--max-emails`.

**Validation**:
```python
if not 1 <= max_emails <= 50000:
    raise ConfigError(f"max_emails must be 1-50000, got {max_emails}")
```

**Example**:
```json
{
  "max_emails": 5000
}
```

#### rate_limit_per_second

**Type**: Float (decimal number)
**Required**: No
**Default**: 10.0 (conservative: 8.0)
**Valid Range**: 0.1 - 100.0
**Unit**: Requests per second

Rate limit for Gmail API calls. Lower values are safer but slower.

**Validation**:
```python
if not 0.1 <= rate_limit_per_second <= 100:
    raise ConfigError(f"rate_limit_per_second must be 0.1-100, got {rate_limit_per_second}")
```

**Recommended Values**:
- Conservative: 8.0 (safe, slower)
- Default: 10.0 (balanced)
- Aggressive: 25.0 (faster, may hit rate limits)
- Very Aggressive: 50.0+ (dangerous, use only for testing)

**Example**:
```json
{
  "rate_limit_per_second": 8.0
}
```

#### log_level

**Type**: String (uppercase)
**Required**: No
**Default**: "INFO"
**Valid Values**: DEBUG, INFO, WARNING, ERROR, CRITICAL

Logging verbosity level.

**Validation**:
```python
if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    raise ConfigError(f"log_level must be one of {{'DEBUG', 'INFO', ...}}")
```

**Levels**:
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages for potential issues
- ERROR: Error messages for failures
- CRITICAL: Critical messages for severe failures

**Example**:
```json
{
  "log_level": "DEBUG"
}
```

### Complete Example

```json
{
  "credentials_path": "~/.gmail-assistant/credentials.json",
  "token_path": "~/.gmail-assistant/token.json",
  "output_dir": "~/.gmail-assistant/backups",
  "max_emails": 5000,
  "rate_limit_per_second": 8.0,
  "log_level": "INFO"
}
```

### Security Validation

AppConfig enforces security checks on paths:

1. **Repo Detection**: Uses `git rev-parse --show-toplevel` to detect git repository
2. **Credential Location**: Checks if credentials_path or token_path are inside repo
3. **Enforcement**:
   - Fails if inside repo (unless `--allow-repo-credentials` flag)
   - Logs warning if flag used
4. **Git Unavailable**: If git not in PATH, checks are skipped (warning logged)

```python
# If git unavailable:
logger.warning(
    "git not found in PATH; repo-safety checks disabled. "
    "Credentials may be placed anywhere without warning."
)
```

---

## AI Newsletter Cleaner Config

**File**: `config/config.json`
**Module**: `gmail_assistant.core.ai.newsletter_cleaner`
**Format**: JSON
**Purpose**: AI newsletter detection and classification

### Schema Overview

```json
{
  "ai_keywords": ["list of keywords"],
  "ai_newsletter_domains": ["list of domains"],
  "newsletter_patterns": ["list of regex patterns"],
  "unsubscribe_patterns": ["list of patterns"],
  "confidence_weights": {"key": weight},
  "decision_threshold": {
    "minimum_confidence": number,
    "minimum_reasons": number
  }
}
```

### Parameters

#### ai_keywords

**Type**: Array of strings
**Purpose**: Keywords indicating AI newsletter content

Contains 38 keywords for AI-related content detection.

**Sample Keywords**:
```json
"ai_keywords": [
  "artificial intelligence",
  "machine learning",
  "deep learning",
  "neural network",
  "chatgpt",
  "claude",
  "llm",
  "gen ai",
  "langchain",
  "hugging face"
]
```

#### ai_newsletter_domains

**Type**: Array of strings
**Purpose**: Known AI newsletter and research domains

Contains 27 domain patterns for newsletter source detection.

**Sample Domains**:
```json
"ai_newsletter_domains": [
  "deeplearning.ai",
  "openai.com",
  "anthropic.com",
  "huggingface.co",
  "thesequence.substack.com",
  "techcrunch.com",
  "medium.com",
  "substack.com"
]
```

#### newsletter_patterns

**Type**: Array of strings (regex patterns)
**Purpose**: Regex patterns matching newsletter naming conventions

Contains 18 regex patterns for newsletter identification.

**Sample Patterns**:
```json
"newsletter_patterns": [
  "weekly.*ai",
  "ai.*weekly",
  "daily.*ai",
  "ai.*daily",
  "newsletter.*ai",
  "digest.*ai",
  "roundup.*ai"
]
```

#### unsubscribe_patterns

**Type**: Array of strings (regex patterns)
**Purpose**: Patterns indicating automated newsletter emails

Contains 7 patterns for identifying automated communications.

**Sample Patterns**:
```json
"unsubscribe_patterns": [
  "unsubscribe",
  "opt.?out",
  "manage.*subscription",
  "email.*preference",
  "stop.*receiving"
]
```

#### confidence_weights

**Type**: Object with string keys and numeric values
**Purpose**: Weighting system for confidence scoring

Each keyword/pattern match contributes weight towards confidence score.

**Valid Keys**:
- `ai_keywords_subject`: Weight for keywords in email subject
- `ai_keywords_sender`: Weight for keywords in sender/domain
- `known_domain`: Weight for known AI newsletter domain
- `newsletter_pattern`: Weight for newsletter naming pattern
- `unsubscribe_link`: Weight for unsubscribe pattern present
- `automated_sender`: Weight for automated sender indicators

**Example Values**:
```json
"confidence_weights": {
  "ai_keywords_subject": 3,
  "ai_keywords_sender": 2,
  "known_domain": 4,
  "newsletter_pattern": 2,
  "unsubscribe_link": 1,
  "automated_sender": 1
}
```

#### decision_threshold

**Type**: Object with integer values
**Purpose**: Thresholds for classification decision

Determines when cumulative confidence is sufficient for classification.

**Parameters**:

##### minimum_confidence

**Type**: Integer
**Default**: 4
**Purpose**: Minimum cumulative confidence score for classification

Example: With weights above, a known domain (4) alone meets threshold.

##### minimum_reasons

**Type**: Integer
**Default**: 2
**Purpose**: Minimum number of matching patterns/keywords

Ensures multiple signals before classification (reduces false positives).

**Example Configuration**:
```json
"decision_threshold": {
  "minimum_confidence": 4,
  "minimum_reasons": 2
}
```

**This means**: Classify as AI newsletter only if:
- Confidence score >= 4 AND
- At least 2 different patterns matched

### Complete Example

See `config/config.json` (38 keywords, 27 domains, 18 patterns)

---

## Email Organization Config

**File**: `config/organizer_config.json`
**Format**: JSON
**Purpose**: Patterns for email classification and priority

### Schema Overview

```json
{
  "work_patterns": {
    "keywords": [],
    "domains": [],
    "senders": []
  },
  "urgent_patterns": {
    "keywords": [],
    "personal_domains": []
  },
  "financial_alert_patterns": {
    "keywords": [],
    "domains": []
  },
  "legal_gov_patterns": {
    "keywords": [],
    "domains": []
  },
  "tax_patterns": {
    "keywords": [],
    "file_types": []
  },
  "delete_patterns": {
    "promotional": [],
    "social_media": [],
    "newsletters": [],
    "confirmations": [],
    "travel": [],
    "shopping": [],
    "entertainment": [],
    "health_fitness": []
  },
  "confidence_thresholds": {
    "work_email": 3,
    "urgent_personal": 4,
    "financial_alert": 4,
    "legal_gov": 3,
    "tax_document": 4
  }
}
```

### Parameters

#### work_patterns

**Purpose**: Identify work-related emails

**Keywords**: 25 work-related keywords
- urgent, asap, deadline, meeting, call, review, approval
- action required, please respond, need feedback
- project, client, proposal, budget, contract

**Domains**: 9 work domain patterns
- company.com, corp.com, enterprise.com, office.com

**Senders**: 10 work sender patterns
- boss@, manager@, hr@, client@, team@

#### urgent_patterns

**Purpose**: Identify urgent personal emails

**Keywords**: 14 emergency-related keywords
- emergency, urgent, critical, immediate, hospital, accident
- police, doctor, medical, 911, help, crisis, family emergency

**Domains**: 7 personal email domains
- gmail.com, yahoo.com, outlook.com, icloud.com

#### financial_alert_patterns

**Purpose**: Identify financial/security alerts

**Keywords**: 21 financial alert keywords
- fraud alert, suspicious activity, security alert, unauthorized
- payment due, overdue, account locked, identity theft
- password reset, security breach, compromised

**Domains**: 19 financial institution domains
- chase.com, wellsfargo.com, bankofamerica.com, paypal.com
- capitalone.com, amex.com, stripe.com, square.com

#### legal_gov_patterns

**Purpose**: Identify legal/government emails

**Keywords**: 21 legal/government keywords
- court, legal, lawsuit, subpoena, jury duty, irs, tax
- government, federal, state, license, permit, violation
- summons, warrant, legal notice, compliance, audit

**Domains**: 12 government domain patterns
- .gov, irs.gov, dmv., court., state., city.
- attorney, lawyer, legal

#### tax_patterns

**Purpose**: Identify tax-related documents

**Keywords**: 14 tax keywords
- tax, w-2, w2, 1099, tax document, tax form, tax return
- refund, irs, tax preparation, tax season, deduction

**File Types**: 6 tax document indicators
- .pdf, tax document, w-2, 1099

#### delete_patterns

**Purpose**: Identify deletable email categories

**Categories**:
- promotional: 13 keywords (sale, discount, offer, coupon, % off, black friday)
- social_media: 20 keywords (facebook, twitter, instagram, notification, like)
- newsletters: 15 keywords (newsletter, weekly, daily, digest, roundup, update)
- confirmations: 14 keywords (confirmation, receipt, order, shipping, invoice)
- travel: 11 keywords (flight, hotel, booking, airline, uber, lyft, airbnb)
- shopping: 14 keywords (amazon, ebay, etsy, shipped, return, refund)
- entertainment: 11 keywords (netflix, spotify, hulu, movie, concert, gaming)
- health_fitness: 9 keywords (fitbit, apple health, workout, calories, wellness)

#### confidence_thresholds

**Purpose**: Classification threshold scores

**Thresholds**:
```json
"confidence_thresholds": {
  "work_email": 3,
  "urgent_personal": 4,
  "financial_alert": 4,
  "legal_gov": 3,
  "tax_document": 4
}
```

---

## Analysis Config

**File**: `config/analysis.json`
**Format**: JSON
**Purpose**: Email analysis pipeline configuration

### Key Parameters

#### quality_thresholds

```json
"quality_thresholds": {
  "min_completeness": 95.0,
  "max_null_rate": 5.0,
  "max_duplicate_rate": 0.1,
  "min_date_coverage": 0.95,
  "min_classification_confidence": 0.8
}
```

- min_completeness: Minimum data completeness percentage
- max_null_rate: Maximum acceptable null/missing data rate
- max_duplicate_rate: Maximum acceptable duplicate rate
- min_date_coverage: Minimum temporal coverage
- min_classification_confidence: Minimum classification confidence

#### classification_config

```json
"classification_config": {
  "confidence_threshold": 0.7,
  "enable_custom_categories": true,
  "fallback_category": "Other",
  "case_sensitive": false,
  "use_content_analysis": true,
  "use_sender_patterns": true
}
```

#### automation_detection

```json
"automation_detection": {
  "indicators": ["noreply", "no-reply", "notification", "alert", "service"],
  "domain_patterns": ["amazonaws.com", "sendgrid.", "mailgun.", "mailchimp."],
  "confidence_threshold": 0.8
}
```

#### temporal_analysis

```json
"temporal_analysis": {
  "peak_detection_threshold": 2.0,
  "rolling_window_days": 7,
  "seasonal_analysis_enabled": true,
  "time_zone": "UTC",
  "business_hours": {
    "start": 9,
    "end": 17,
    "timezone": "UTC"
  }
}
```

#### performance_config

```json
"performance_config": {
  "batch_size": 1000,
  "parallel_processing": false,
  "memory_limit_gb": 8,
  "cache_enabled": true
}
```

#### alert_thresholds

```json
"alert_thresholds": {
  "volume_spike_multiplier": 3.0,
  "new_sender_threshold": 50,
  "quality_degradation_threshold": 0.9,
  "classification_confidence_min": 0.8,
  "processing_time_max_minutes": 30
}
```

#### scheduling

```json
"scheduling": {
  "execution_time": "06:00",
  "timezone": "UTC",
  "retry_attempts": 3,
  "retry_delay_minutes": 15,
  "skip_weekends": false,
  "skip_holidays": false
}
```

---

## Deletion Patterns Config

**File**: `config/deletion.json`
**Format**: JSON
**Purpose**: Safe deletion pattern matching (duplicate of organizer_config patterns)

Uses same structure as `organizer_config.json` for deletion patterns.

---

## Gmail Assistant Presets

**File**: `config/gmail_assistant_config.json`
**Format**: JSON
**Purpose**: Pre-defined queries and settings for common tasks

### Parameters

#### common_queries

**Type**: Object with string values
**Purpose**: Pre-defined Gmail search queries

**Example Queries**:
```json
"common_queries": {
  "march_2025": "after:2025/02/28 before:2025/04/01",
  "unread_only": "is:unread",
  "newsletters": "from:(theresanaiforthat.com OR mindstream.news OR futurepedia.io)",
  "ai_content": "subject:(AI OR artificial intelligence OR machine learning)",
  "service_notifications": "from:(namecheap.com OR pythonanywhere.com OR zoho.com)",
  "last_6_months": "newer_than:6m",
  "last_year": "newer_than:1y",
  "large_emails": "larger:10M",
  "with_attachments": "has:attachment"
}
```

**Usage**:
```bash
# Reference named query
gmail-assistant fetch --query "is:unread"
```

#### default_settings

**Type**: Object
**Purpose**: Default behavior for fetch operations

```json
"default_settings": {
  "max_emails": 500,
  "output_format": "both",
  "organize_by": "date",
  "output_directory": "gmail_backup"
}
```

**Parameters**:
- max_emails: Default email limit
- output_format: "eml", "markdown", or "both"
- organize_by: "date", "sender", or "none"
- output_directory: Default output folder

#### cleanup_suggestions

**Type**: Object with arrays
**Purpose**: Recommended deletion queries

```json
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
```

---

## Configuration Loading

### AppConfig Loading Process

```python
@classmethod
def load(
    cls,
    cli_config: Path | None = None,
    *,
    allow_repo_credentials: bool = False,
) -> "AppConfig":
    """Load config following resolution order."""
```

### Resolution Order

1. CLI argument `--config` → validate exists → load
2. Environment variable `gmail_assistant_CONFIG` → validate exists → load
3. Project config `./gmail-assistant.json` → if exists → load
4. User config `~/.gmail-assistant/config.json` → if exists → load
5. Use secure defaults → all in `~/.gmail-assistant/`

### Path Resolution

Relative paths in config files are resolved relative to **config file directory**, not current working directory:

```python
def resolve_path(key: str, default: Path) -> Path:
    if key not in data:
        return default
    p = Path(data[key])
    if not p.is_absolute():
        p = (config_dir / p).resolve()  # Relative to config file
    return p
```

### Example

If config at `/etc/gmail-assistant/config.json` contains:
```json
{
  "output_dir": "./backups"
}
```

Output directory resolves to: `/etc/gmail-assistant/backups`

---

## Validation Rules

### Schema Validation

Unknown keys are rejected:
```python
unknown_keys = set(data.keys()) - _ALLOWED_KEYS
if unknown_keys:
    raise ConfigError(f"Unknown config keys: {sorted(unknown_keys)}")
```

**Allowed Keys**:
- credentials_path
- token_path
- output_dir
- max_emails
- rate_limit_per_second
- log_level

### Type Validation

```python
# max_emails must be integer (not bool)
if not isinstance(val, int) or isinstance(val, bool):
    raise ConfigError(f"max_emails must be integer, got {type(val).__name__}")

# rate_limit_per_second must be float/int (not bool)
if isinstance(val, bool) or not isinstance(val, (int, float)):
    raise ConfigError(f"rate_limit_per_second must be number, got {type(val).__name__}")

# log_level must be string
if not isinstance(val, str):
    raise ConfigError(f"log_level must be string, got {type(val).__name__}")
```

### Range Validation

```python
if not 1 <= max_emails <= 50000:
    raise ConfigError(f"max_emails must be 1-50000, got {max_emails}")

if not 0.1 <= rate_limit_per_second <= 100:
    raise ConfigError(f"rate_limit_per_second must be 0.1-100, got {rate_limit_per_second}")

if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    raise ConfigError(f"log_level must be one of {{'DEBUG', 'INFO', ...}}")
```

---

## Environment Variables

### Configuration Override

**Variable**: `gmail_assistant_CONFIG`
**Purpose**: Override config file location
**Priority**: 2nd (after CLI argument, before project/user configs)

```bash
export gmail_assistant_CONFIG=/etc/gmail-assistant/prod.json
gmail-assistant fetch
```

### Path Overrides

**Variables** (in `gmail_assistant.core.constants`):

| Variable | Purpose | Default |
|----------|---------|---------|
| `GMAIL_ASSISTANT_CONFIG_DIR` | Config directory | `{PROJECT_ROOT}/config` |
| `GMAIL_ASSISTANT_DATA_DIR` | Data directory | `{PROJECT_ROOT}/data` |
| `GMAIL_ASSISTANT_BACKUP_DIR` | Backup directory | `{PROJECT_ROOT}/backups` |
| `GMAIL_ASSISTANT_CREDENTIALS_DIR` | Credentials directory | `{CONFIG_DIR}/security` |
| `GMAIL_ASSISTANT_CACHE_DIR` | Cache directory | `~/.gmail_assistant_cache` |

**Usage**:
```bash
export GMAIL_ASSISTANT_BACKUP_DIR=/mnt/external_drive/backups
gmail-assistant fetch
```

---

## See Also

- [CLI Reference](0109-1500_CLI_REFERENCE.md) - Command-line options and usage
- [Public API Reference](0109-1700_PUBLIC_API_REFERENCE.md) - Programmatic configuration access
- [Constants Reference](0109-1800_CONSTANTS_REFERENCE.md) - Built-in constants and defaults

