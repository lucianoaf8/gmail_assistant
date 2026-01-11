# Gmail Fetcher Data Architecture Analysis Report

**Date**: 2026-01-08
**Version**: 1.0
**Author**: Data Architecture Analysis

---

## Executive Summary

This report provides a comprehensive analysis of the Gmail Fetcher project's data architecture, examining data flow patterns, storage strategies, transformation pipelines, and scalability considerations. The project demonstrates a well-structured approach to email backup and management with multiple storage formats and processing capabilities, though several areas present opportunities for architectural improvement.

**Key Findings**:
- Multi-format storage strategy (EML, Markdown, JSON, SQLite) provides flexibility but introduces data synchronization complexity
- Robust transformation pipelines with multiple parsing strategies and quality scoring
- Good metadata preservation across formats with YAML front matter
- Incremental processing and memory management capabilities
- Some architectural gaps in data lineage tracking and cross-format consistency

---

## 1. Data Flow Patterns and Transformation Pipelines

### 1.1 Primary Data Flow Architecture

```
                     Gmail API
                         |
                         v
              +-------------------+
              | GmailFetcher      |
              | (gmail_fetcher.py)|
              +-------------------+
                    |         |
                    v         v
              +--------+  +--------+
              |  EML   |  |   MD   |
              | Files  |  | Files  |
              +--------+  +--------+
                    |         |
                    v         v
              +-------------------+
              | EML-to-MD         |
              | Converter         |
              +-------------------+
                         |
                         v
              +-------------------+
              | Advanced Parser   |
              | (Quality Scoring) |
              +-------------------+
                         |
                         v
              +-------------------+
              | Email Data        |
              | Extractor         |
              +-------------------+
                         |
                         v
              +-------------------+
              | Monthly JSON      |
              | Files             |
              +-------------------+
                         |
                         v
              +-------------------+
              | SQLite Database   |
              | (emails_final.db) |
              +-------------------+
                         |
                         v
              +-------------------+
              | Email Classifier  |
              | (Analytics)       |
              +-------------------+
```

### 1.2 Transformation Pipeline Details

#### Stage 1: Gmail API to Raw Files
**Component**: `GmailFetcher` class
**Input**: Gmail API message objects
**Output**: EML files and/or Markdown files

**Key Transformations**:
- Base64 decoding with URL-safe character handling and padding correction
- Header extraction from Gmail API payload structure
- MIME boundary construction for multipart messages
- HTML-to-Markdown conversion via `html2text`

**Data Quality Considerations**:
- Base64 padding correction handles Gmail API quirks
- Unicode encoding with error handling for malformed content
- Filename sanitization for filesystem compatibility

#### Stage 2: EML to Clean Markdown
**Components**:
- `gmail_eml_to_markdown_cleaner.py`
- `robust_eml_converter.py`
- `advanced_email_parser.py`

**Multi-Strategy Parsing Architecture**:
```
Input HTML Content
        |
        v
+-------------------+
| Strategy Router   |
| (Email Type Det.) |
+-------------------+
        |
        +---> Smart Strategy (custom per email type)
        |---> Readability Strategy (readability-lxml)
        |---> Trafilatura Strategy (content extraction)
        |---> HTML2Text Strategy (direct conversion)
        +---> Markdownify Strategy (structural conversion)
        |
        v
+-------------------+
| Quality Scorer    |
| (Best Result Sel.)|
+-------------------+
        |
        v
Final Markdown Output
```

**Quality Scoring Formula**:
- Content preservation: 40% weight (ratio of output to input text length)
- Structure quality: 30% weight (headers, lists, links presence)
- Readability: 20% weight (average line length 20-120 chars optimal)
- Formatting quality: 10% weight (proper spacing, header formatting)

#### Stage 3: Markdown to Structured JSON
**Component**: `EmailDataExtractor`

**Extraction Pattern**:
- Parses Markdown table format for metadata extraction
- Regex-based date parsing with 10+ format support
- Content normalization and whitespace cleanup
- Monthly aggregation for batch processing

#### Stage 4: JSON to SQLite Database
**Component**: `EmailDatabaseImporter`

**Database Schema Features**:
- Full-text search via FTS5 virtual tables
- Automatic FTS index maintenance with triggers
- Import batch tracking for idempotency
- WAL journaling for concurrent access

### 1.3 Data Flow Observations

**Strengths**:
1. Multi-strategy parsing provides resilience to varied email formats
2. Quality scoring enables automatic best-result selection
3. Progressive loading supports large dataset processing
4. Batch processing with checkpoint tracking

**Weaknesses**:
1. No formal data lineage tracking between transformations
2. Multiple entry points can lead to inconsistent data states
3. Error handling varies across pipeline stages
4. No schema validation between transformation stages

---

## 2. Data Storage Strategies

### 2.1 File-Based Storage

#### EML Format
**Purpose**: Native email preservation
**Structure**: RFC 2822 compliant with Gmail extensions

```
Essential Headers:
  Message-ID, Date, From, To, CC, BCC, Subject

Gmail Extensions:
  X-Gmail-Message-ID
  X-Gmail-Thread-ID
  X-Gmail-Labels

Content Structure:
  MIME-Version: 1.0
  Content-Type: multipart/alternative
    - text/plain
    - text/html
```

**Advantages**:
- Full fidelity preservation
- Email client compatible
- Thread/label relationship preservation

**Disadvantages**:
- Larger file sizes
- Complex parsing required for content access
- Binary attachments increase storage needs

#### Markdown Format
**Purpose**: Human-readable archive
**Structure**: YAML front matter + content body

```yaml
---
source_file: "path/to/original.eml"
subject: "Email Subject"
from: ["Name <email@domain.com>"]
to: ["Recipient <recipient@domain.com>"]
date: "2025-03-31T12:00:00+00:00"
message_id: "<unique-id@domain.com>"
labels: ["INBOX", "UNREAD"]
---

## Message Content

[Converted body content in Markdown]
```

**Advantages**:
- Human-readable without tools
- Git-friendly for version control
- Searchable with standard tools
- Metadata preservation via front matter

**Disadvantages**:
- Lossy conversion from HTML
- Attachment handling complexity
- Formatting inconsistencies across converters

### 2.2 Structured Storage

#### JSON Format
**Purpose**: Intermediate data exchange
**Structure**: Monthly aggregated files

```json
{
  "year_month": "2025-03",
  "email_count": 150,
  "date_range": {
    "first_email": "2025-03-01T08:00:00",
    "last_email": "2025-03-31T23:59:00"
  },
  "extraction_info": {
    "extracted_at": "2025-04-01T10:00:00",
    "source_folder": "/path/to/backup"
  },
  "emails": [
    {
      "filename": "...",
      "gmail_id": "...",
      "subject": "...",
      "sender": "...",
      "message_content": "..."
    }
  ]
}
```

**Advantages**:
- Schema flexibility
- Easy serialization/deserialization
- Human-readable
- Language-agnostic exchange format

**Disadvantages**:
- No referential integrity
- Potential for large file sizes
- No built-in indexing

#### SQLite Database
**Purpose**: Queryable archive with full-text search
**Schema Design**:

```sql
-- Primary Emails Table
CREATE TABLE emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    gmail_id TEXT,
    thread_id TEXT,
    date_received TEXT,
    parsed_date TEXT,
    year_month TEXT NOT NULL CHECK(length(year_month) = 7),
    sender TEXT,
    recipient TEXT,
    subject TEXT,
    labels TEXT,
    message_content TEXT,
    extraction_timestamp TEXT NOT NULL,
    import_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Classification columns (Phase 2)
    primary_category TEXT,
    domain_category TEXT,
    priority_level TEXT,
    source_type TEXT,
    action_required TEXT,
    confidence_score REAL,
    classification_rules TEXT,  -- JSON
    sender_frequency INTEGER,
    is_thread BOOLEAN,
    has_unsubscribe BOOLEAN,
    automated_score REAL
);

-- Full-Text Search Virtual Table
CREATE VIRTUAL TABLE emails_fts USING fts5(
    subject,
    message_content,
    sender,
    content='emails',
    content_rowid='id'
);

-- Import Tracking
CREATE TABLE import_batches (
    id INTEGER PRIMARY KEY,
    year_month TEXT UNIQUE,
    email_count INTEGER,
    source_file TEXT,
    import_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Statistics Tracking
CREATE TABLE email_stats (
    id INTEGER PRIMARY KEY,
    stat_date TEXT DEFAULT CURRENT_TIMESTAMP,
    total_emails INTEGER,
    unique_senders INTEGER,
    months_covered INTEGER
);
```

**Index Strategy**:
```sql
CREATE INDEX idx_emails_year_month ON emails(year_month);
CREATE INDEX idx_emails_gmail_id ON emails(gmail_id);
CREATE INDEX idx_emails_thread_id ON emails(thread_id);
CREATE INDEX idx_emails_sender ON emails(sender);
CREATE INDEX idx_emails_parsed_date ON emails(parsed_date);
CREATE INDEX idx_emails_subject ON emails(subject);
CREATE INDEX idx_primary_category ON emails(primary_category);
```

**Advantages**:
- ACID compliance
- Full-text search capability
- Efficient querying
- Portable single-file format
- No external dependencies

**Disadvantages**:
- Single-writer limitation
- No native replication
- Limited concurrent access

### 2.3 Storage Architecture Assessment

| Format | Use Case | Data Fidelity | Query Capability | Portability |
|--------|----------|---------------|------------------|-------------|
| EML | Archive | High | Low | High |
| Markdown | Reading | Medium | Medium | High |
| JSON | Exchange | Medium | Low | High |
| SQLite | Analysis | Medium | High | High |

**Recommendation**: The current multi-format approach is appropriate, but would benefit from:
1. Single source of truth designation (SQLite)
2. Derivation tracking metadata
3. Automated synchronization mechanisms

---

## 3. Data Organization Schemes

### 3.1 Hierarchical Organization

#### By Date (Default)
```
gmail_backup/
  +-- 2024/
  |     +-- 01/
  |     |     +-- 2024-01-15_120000_subject_msgid.eml
  |     |     +-- 2024-01-15_120000_subject_msgid.md
  |     +-- 02/
  |     +-- ...
  +-- 2025/
        +-- 01/
        +-- ...
```

**Filename Pattern**: `{YYYY-MM-DD}_{HHMMSS}_{sanitized_subject}_{gmail_message_id}.{ext}`

**Advantages**:
- Natural chronological browsing
- Easy archival policy implementation (delete by year/month)
- Predictable file location
- Filesystem-level partitioning

#### By Sender
```
gmail_backup/
  +-- john_doe/
  |     +-- 2025-01-15_120000_subject_msgid.eml
  +-- newsletter_service/
  |     +-- 2025-01-16_080000_weekly_digest_msgid.eml
```

**Advantages**:
- Communication history by contact
- Easy sender-based archival
- Natural grouping for correspondence

### 3.2 Deduplication Strategy

**Implementation**: PowerShell script `dedupe_merge.ps1`

**Message ID Extraction**:
```powershell
# Extract Gmail message ID from filename
# Pattern: _([0-9A-Fa-f]{8,})\.(eml|md)$
$id = [regex]::Match($Name, '_([0-9A-Fa-f]{8,})\.(eml|md)$')
```

**Conflict Resolution Policies**:
1. `larger`: Keep larger file (more complete content)
2. `destination`: Keep existing destination file
3. `source`: Replace with source file

**Process**:
1. Build index of destination files by message ID
2. Scan source files for each year/month
3. Compare files:
   - Same size: Remove source (duplicate)
   - Different size: Apply conflict policy
4. Move unique files to destination
5. Cleanup empty source directories

---

## 4. Metadata Handling and Preservation

### 4.1 Metadata Extraction

**Email Header Parsing**:
```python
essential_headers = [
    'message-id', 'date', 'from', 'to', 'cc', 'bcc',
    'subject', 'reply-to', 'in-reply-to', 'references'
]

gmail_specific_headers = [
    'X-Gmail-Message-ID',
    'X-Gmail-Thread-ID',
    'X-Gmail-Labels'
]
```

**Date Parsing Formats** (10+ supported):
```python
date_formats = [
    '%a, %d %b %Y %H:%M:%S %z',     # RFC 2822
    '%a, %d %b %Y %H:%M:%S %Z',     # With timezone name
    '%d %b %Y %H:%M:%S %z',         # Without day name
    '%Y-%m-%d %H:%M:%S %z',         # ISO 8601
    '%Y-%m-%d',                      # Date only
    # ... additional formats
]
```

### 4.2 Metadata Preservation Strategy

**YAML Front Matter** (Markdown files):
```yaml
---
source_file: "relative/path/to/source.eml"
subject: "Email Subject Line"
from: ["Display Name <email@domain.com>"]
to: ["Recipient <recipient@domain.com>"]
date: "2025-03-31T12:00:00+00:00"  # ISO 8601
message_id: "<unique-message-id@domain.com>"
labels: ["INBOX", "UNREAD", "CATEGORY_UPDATES"]
conversion_strategy: "smart"
quality_score: 0.85
---
```

**Database Metadata**:
- All email headers stored
- Classification metadata (phase 2)
- Extraction/import timestamps
- Source file references

### 4.3 Metadata Gap Analysis

**Currently Captured**:
- Core email headers
- Gmail-specific identifiers
- Thread relationships
- Label/category information
- Processing metadata

**Missing/Recommended**:
- Attachment metadata (names, sizes, types)
- Full conversation thread reconstruction
- Reply chain visualization
- Sender reputation scores
- Historical label changes

---

## 5. Data Integrity Considerations

### 5.1 Current Integrity Mechanisms

**Database Level**:
- UNIQUE constraint on `file_path` prevents duplicate imports
- CHECK constraint on `year_month` format
- Foreign key support enabled
- WAL journaling for crash recovery

**File Level**:
- Message ID embedded in filename enables deduplication
- Size comparison for conflict resolution
- Directory structure preserves temporal relationships

**Processing Level**:
- Batch tracking prevents re-processing
- Quality scoring validates transformation output
- Encoding detection with fallback strategies

### 5.2 Integrity Gaps

1. **Cross-Format Consistency**: No mechanism to verify EML, Markdown, and database entries match
2. **Schema Evolution**: No version tracking for schema changes
3. **Referential Integrity**: JSON files have no foreign key equivalent
4. **Checksum Validation**: No hash-based content verification

### 5.3 Recommended Integrity Improvements

**Add Content Hashing**:
```python
import hashlib

def compute_email_hash(content: str) -> str:
    """Compute deterministic hash for email content"""
    # Normalize whitespace before hashing
    normalized = ' '.join(content.split())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
```

**Implement Cross-Format Validation**:
```sql
-- Add hash column to emails table
ALTER TABLE emails ADD COLUMN content_hash TEXT;

-- Validation query
SELECT gmail_id, COUNT(DISTINCT content_hash) as hash_count
FROM emails
GROUP BY gmail_id
HAVING hash_count > 1;  -- Indicates inconsistency
```

---

## 6. Scalability Assessment

### 6.1 Current Scalability Features

**Memory Management** (`memory_manager.py`):
```python
class MemoryTracker:
    threshold_warning = 500 * 1024 * 1024   # 500MB
    threshold_critical = 1024 * 1024 * 1024  # 1GB

class StreamingEmailProcessor:
    chunk_size = 100  # Process in batches

class ProgressiveLoader:
    batch_size = 1000  # Load incrementally
```

**Streaming Processing**:
- Generator-based email processing
- Chunk-based file writing
- Memory-conscious cache with LRU eviction
- Automatic garbage collection triggers

**Incremental Processing** (`incremental_fetcher.py`):
- Queries database for latest email date
- Fetches only new emails since last sync
- Maintains year/month directory structure

### 6.2 Scalability Limitations

| Component | Current Limit | Bottleneck |
|-----------|---------------|------------|
| SQLite | ~10M rows | Single writer, file locking |
| JSON files | ~50MB per file | Memory load for parsing |
| File system | ~100K files/dir | Directory traversal |
| API rate | 10 req/sec | Gmail API quota |

### 6.3 Scalability Recommendations

**For 100K+ Emails**:
1. Partition SQLite by year into separate databases
2. Implement file-based sharding (year/month subdirectories)
3. Add connection pooling for database access
4. Implement parallel processing with multiprocessing

**For 1M+ Emails**:
1. Migrate to PostgreSQL for concurrent access
2. Implement message queue for processing pipeline
3. Add caching layer (Redis) for frequent queries
4. Consider columnar storage (Parquet) for analytics

**Suggested Partitioning Strategy**:
```
data/
  +-- databases/
  |     +-- emails_2024.db
  |     +-- emails_2025.db
  |     +-- emails_metadata.db  # Cross-year queries
  +-- parquet/
        +-- emails_2024.parquet
        +-- emails_2025.parquet
```

---

## 7. Data Format Analysis

### 7.1 Format Decision Matrix

| Criterion | EML | Markdown | JSON | SQLite | Parquet |
|-----------|-----|----------|------|--------|---------|
| Data Fidelity | 5 | 3 | 4 | 4 | 4 |
| Human Readable | 2 | 5 | 4 | 2 | 1 |
| Query Performance | 1 | 2 | 2 | 4 | 5 |
| Storage Efficiency | 2 | 3 | 3 | 4 | 5 |
| Schema Flexibility | 3 | 4 | 5 | 3 | 2 |
| Tool Compatibility | 4 | 5 | 5 | 4 | 3 |

*Scale: 1 (Poor) to 5 (Excellent)*

### 7.2 Current Format Usage Assessment

**EML Format**: Appropriate use
- Full backup fidelity requirement satisfied
- Email client restoration capability maintained

**Markdown Format**: Appropriate use
- Human-readable archive goal achieved
- Quality varies based on email complexity
- Recommendation: Add quality threshold for production use

**JSON Format**: Could be optimized
- Currently used as intermediate format
- Large monthly files could cause memory issues
- Recommendation: Consider streaming JSON (JSONL) format

**SQLite Format**: Appropriate use
- Query and analysis capabilities well-utilized
- FTS5 enables effective search
- Classification schema supports analytics

### 7.3 Format Recommendations

**Add Parquet Support for Analytics**:
```python
# Suggested implementation
import pyarrow as pa
import pyarrow.parquet as pq

schema = pa.schema([
    ('gmail_id', pa.string()),
    ('thread_id', pa.string()),
    ('date', pa.timestamp('ms')),
    ('sender', pa.string()),
    ('subject', pa.string()),
    ('category', pa.string()),
    ('word_count', pa.int32()),
])

# Enable efficient columnar queries
pq.write_table(table, 'emails_2025.parquet',
               compression='snappy',
               row_group_size=100000)
```

**Consider JSONL for Streaming**:
```json
{"gmail_id": "abc123", "subject": "Hello", "date": "2025-03-31"}
{"gmail_id": "def456", "subject": "Re: Hello", "date": "2025-03-31"}
```

---

## 8. Architecture Recommendations

### 8.1 High Priority Recommendations

#### 8.1.1 Implement Single Source of Truth
**Current State**: Multiple storage formats without clear hierarchy
**Recommendation**: Designate SQLite database as authoritative source

```
Authoritative: SQLite Database (emails_final.db)
    |
    +-- Derived: EML files (archive/restoration)
    +-- Derived: Markdown files (human reading)
    +-- Derived: JSON exports (data exchange)
```

#### 8.1.2 Add Data Lineage Tracking
**Implementation**: Add metadata tracking table

```sql
CREATE TABLE data_lineage (
    id INTEGER PRIMARY KEY,
    email_id INTEGER REFERENCES emails(id),
    operation_type TEXT,  -- 'import', 'transform', 'classify'
    source_format TEXT,   -- 'gmail_api', 'eml', 'markdown'
    target_format TEXT,
    operation_timestamp TEXT,
    operator_version TEXT,
    checksum_before TEXT,
    checksum_after TEXT
);
```

#### 8.1.3 Implement Schema Validation
**Between Stages**: Add validation contracts

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class EmailRecord:
    """Schema validation for email records"""
    gmail_id: str
    thread_id: str
    date: str
    sender: str
    subject: str
    content: str
    labels: List[str]

    def validate(self) -> bool:
        """Validate required fields"""
        return all([
            self.gmail_id,
            self.date,
            self.sender
        ])
```

### 8.2 Medium Priority Recommendations

#### 8.2.1 Enhance Deduplication
**Add content-based deduplication**:
```python
def compute_content_signature(email: dict) -> str:
    """Create signature from email content for dedup"""
    components = [
        email.get('sender', ''),
        email.get('subject', ''),
        email.get('date', ''),
        email.get('content', '')[:500]  # First 500 chars
    ]
    combined = '|'.join(components)
    return hashlib.md5(combined.encode()).hexdigest()
```

#### 8.2.2 Implement Configuration Management
**Centralize all configuration**:
```yaml
# config/data_architecture.yaml
storage:
  primary: "sqlite"
  formats:
    - type: "eml"
      enabled: true
      retention_days: 365
    - type: "markdown"
      enabled: true
      quality_threshold: 0.7

processing:
  batch_size: 100
  memory_limit_mb: 512
  parallel_workers: 4

validation:
  checksum_enabled: true
  schema_validation: true
```

#### 8.2.3 Add Monitoring and Metrics
```python
class DataArchitectureMetrics:
    def __init__(self):
        self.metrics = {
            'emails_processed': 0,
            'transformation_errors': 0,
            'average_quality_score': 0.0,
            'storage_bytes': 0,
            'processing_time_ms': 0
        }

    def record_transformation(self, success: bool, quality: float, time_ms: int):
        """Record transformation metrics"""
        self.metrics['emails_processed'] += 1
        if not success:
            self.metrics['transformation_errors'] += 1
        # Update rolling average
        n = self.metrics['emails_processed']
        self.metrics['average_quality_score'] = (
            (self.metrics['average_quality_score'] * (n-1) + quality) / n
        )
```

### 8.3 Low Priority / Future Considerations

1. **Multi-tenant support**: Partition by user/account
2. **Real-time sync**: Webhook-based incremental updates
3. **Search enhancement**: Elasticsearch integration for advanced queries
4. **Machine learning pipeline**: Feature extraction for intelligent classification
5. **Backup automation**: Scheduled incremental backups with retention policies

---

## 9. Conclusion

The Gmail Fetcher project demonstrates a well-architected approach to email backup and management with thoughtful consideration of multiple use cases (archival, analysis, human reading). The multi-format storage strategy, quality-scored transformation pipeline, and classification system provide a solid foundation.

**Key Strengths**:
1. Multi-strategy parsing with quality scoring
2. Comprehensive metadata preservation
3. Memory-efficient processing for large datasets
4. Full-text search capability
5. Flexible organization schemes

**Primary Improvement Areas**:
1. Establish clear data lineage tracking
2. Implement cross-format consistency validation
3. Enhance scalability for larger email archives
4. Add monitoring and metrics collection
5. Centralize configuration management

The architecture is well-suited for personal or small-team email backup scenarios (up to ~100K emails). For larger deployments, the recommendations in Section 8 should be considered to ensure continued performance and maintainability.

---

## Appendix A: Entity Relationship Diagram

```
+------------------+       +------------------+
|     emails       |       | import_batches   |
+------------------+       +------------------+
| id (PK)          |       | id (PK)          |
| gmail_id         |       | year_month (UK)  |
| thread_id        |       | email_count      |
| file_path (UK)   |       | source_file      |
| year_month       |       | import_timestamp |
| sender           |       +------------------+
| subject          |
| message_content  |       +------------------+
| parsed_date      |       | email_stats      |
| labels           |       +------------------+
| primary_category |       | id (PK)          |
| domain_category  |       | stat_date        |
| confidence_score |       | total_emails     |
| classification   |       | unique_senders   |
+------------------+       | months_covered   |
        |                  +------------------+
        v
+------------------+
|   emails_fts     |
| (FTS5 virtual)   |
+------------------+
| subject          |
| message_content  |
| sender           |
+------------------+
```

## Appendix B: Data Flow Sequence

```
1. Gmail API Request
   |
   v
2. Message ID List Retrieved
   |
   v
3. Full Message Details Fetched (format='full')
   |
   v
4. Base64 Decoding (URL-safe, padding correction)
   |
   v
5. Header Extraction (essential + Gmail-specific)
   |
   v
6. Body Extraction (text/plain, text/html)
   |
   v
7. EML File Creation (MIME structure)
   |
   +---> 7a. Direct Write to disk
   |
   v
8. Markdown Conversion
   |
   +---> 8a. Email Type Detection
   +---> 8b. Multi-Strategy Parsing
   +---> 8c. Quality Scoring
   +---> 8d. Best Result Selection
   |
   v
9. Front Matter Generation (YAML)
   |
   v
10. Markdown File Write
    |
    v
11. Metadata Extraction (from Markdown)
    |
    v
12. Monthly JSON Aggregation
    |
    v
13. Database Import
    |
    +---> 13a. Duplicate Check
    +---> 13b. Insert/Skip Decision
    +---> 13c. FTS Index Update
    |
    v
14. Classification (optional)
    |
    +---> 14a. Sender Pattern Analysis
    +---> 14b. Subject Pattern Analysis
    +---> 14c. Content Keyword Analysis
    +---> 14d. Confidence Scoring
    |
    v
15. Statistics Update
```

---

*Report generated: 2026-01-08*
*Analysis scope: Gmail Fetcher project full codebase*
