# Gmail Fetcher Suite Documentation Hub

This document centralizes the operational and technical knowledge for the Gmail Fetcher Suite. It explains how the tooling is organized, how data flows through each processing stage, and which automation scripts and configuration assets support the workflows.

## 1. System Overview
- Purpose: back up Gmail mailboxes, convert content to human-friendly formats, enrich metadata, and automate cleanup of low-value traffic (newsletters, promotions, etc.).
- Design pillars: reproducible backups, deterministic content normalization, auditable AI-driven classification, and safety-first dry-run modes for destructive actions.
- Primary personas: data custodians exporting Gmail, analysts reviewing large mail stores, and operators performing bulk cleanup.

## 2. End-to-End Architecture (Pipelines)
| Stage | Responsibilities | Key Assets |
| --- | --- | --- |
| Ingestion | Authenticate with Gmail and download raw EML plus Markdown representations. | `main.py`, `src/core/gmail_fetcher.py`, `examples/samples.py`, `scripts/setup/quick_start.ps1` |
| Normalization | Rebuild Markdown from EML, repair tables, enforce formatting hygiene. | `src/parsers/gmail_eml_to_markdown_cleaner.py`, `src/cleanup/cleanup_markdown.py`, `src/cleanup/markdown_post_fixer.py`, `src/utils/comprehensive_email_processor.py` |
| Structuring | Extract structured payloads and persist into JSON bundles and SQLite. | `src/core/email_data_extractor.py`, `data/monthly`, `src/core/email_database_importer.py`, `data/databases/emails_final.db` |
| Enrichment | Compute plaintext variants, classify intent, tag AI newsletters. | `src/core/email_plaintext_processor.py`, `src/core/email_classifier.py`, `src/core/gmail_ai_newsletter_cleaner.py` |
| Automation & Cleanup | Run AI newsletter deletion, essential-email triage, dedupe backups. | `src/core/gmail_api_client.py`, `src/utils/gmail_organizer.py`, `scripts/maintenance/complete_cleanup.sh`, `scripts/backup/dedupe_merge.ps1` |
| Operations | Wrap common scenarios and maintenance tasks for operators. | `examples/samples.py`, `scripts/operations/run_comprehensive.ps1`, `scripts/backup/move_backup_years.ps1` |

## 3. Repository Layout Cheat Sheet
| Path | Description |
| --- | --- |
| `main.py` | Top-level CLI with `fetch`, `parse`, `tools`, `samples`, and `config` subcommands. |
| `src/core/` | Core Gmail integration, data extraction, database ingestion, classification, and cleanup engines. |
| `src/parsers/` | HTML-to-Markdown conversion strategies and Markdown regeneration from raw EML. |
| `src/cleanup/` | Markdown normalization utilities (idempotent formatters, post-fixers, regeneration helpers). |
| `src/utils/` | Higher-level orchestration utilities (comprehensive/ultimate processors, organizer). |
| `scripts/` | PowerShell, Bash, and batch wrappers for setup, dedupe, comprehensive runs, and cleanup workflows. |
| `config/` | Runtime configuration (`config/app/*.json`) and API credentials (`config/security`). |
| `data/` | Structured outputs, including SQLite databases (`data/databases`), monthly JSON, and working logs. |
| `backup_unread`, `backups/` | Large email backup trees (EML and Markdown). Treat as PII-bearing archives. |
| `docs/` | Generated reports and documentation (current hub, classification report, workflow notes). |
| `trash/` | Archived or superseded datasets and legacy documentation kept for reference. |

## 4. Command-Line Entry Points (`main.py`)
- `python main.py fetch`: Calls `src/core/gmail_fetcher.GmailFetcher`.
  - Flags: `--query`, `--max`, `--output`, `--format (eml|markdown|both)`, `--organize (date|sender|none)`, `--auth-only`.
  - Output: Nested directories under the target root containing `.eml` and/or `.md` files.
- `python main.py parse`: Bulk convert EML directories to clean Markdown via `src/parsers/gmail_eml_to_markdown_cleaner.EMLToMarkdownConverter`.
  - Flags: `--input`, `--format`, `--strategy`, `--clean`.
- `python main.py tools cleanup`: Normalizes Markdown using `src/cleanup/cleanup_markdown` pipeline.
  - Flags: `--target`, `--type (markdown|duplicates|all)`.
- `python main.py tools ai-cleanup`: Runs AI newsletter analysis through `src/core/gmail_ai_newsletter_cleaner` (dry-run by default, `--delete` to act).
  - Flags: `--input`, `--delete`, `--threshold`.
- `python main.py samples <scenario>`: Dispatches predefined fetch scenarios (`examples/samples.py`).
- `python main.py config --show/--setup`: Inspect or scaffold `config/` directories.

## 5. Core Python Components
### 5.1 Gmail API and Data Layer (`src/core`)
- `gmail_fetcher.py`: Authenticates via OAuth, searches using Gmail query syntax, downloads messages, produces EML and Markdown with metadata tables, and organizes output trees.
- `gmail_api_client.py`: Higher-privilege Gmail client (`gmail.modify` scope) for unread fetches, deletes, trashes, and batch operations. Integrates with AI newsletter detector for actionable cleanup.
- `gmail_ai_newsletter_cleaner.py`: Provides `EmailData` dataclass, pattern-based detector (`AINewsletterDetector`), and `GmailCleaner` orchestrator supporting JSON/CSV input, dry runs, logging, and summaries. Configurable via `config/app/config.json`.
- `email_data_extractor.py`: Reads regenerated Markdown, extracts structured fields, groups emails into per-month JSON payloads, and writes extraction summaries.
- `email_database_importer.py`: Creates SQLite schema with FTS5 mirrors, imports monthly JSON, deduplicates by file path, and produces roll-up statistics.
- `email_plaintext_processor.py`: Adds `plain_text_content` column to `emails` table, converts Markdown to plain text (tables, headers, links stripped), and supports batch processing with logging and sampling utilities.
- `email_classifier.py`: Multi-phase classification engine. Phase 1 uses sender/label heuristics, Phase 2 adds subject/content patterning, Phase 3 scores confidence and temporal features. Persists category, priority, domain, and action suggestions back to SQLite and generates rich reports.

### 5.2 Parsing and Cleanup (`src/parsers`, `src/cleanup`)
- `advanced_email_parser.py`: Strategy manager combining BeautifulSoup, readability, trafilatura, html2text, and markdownify. Scores output quality and selects best Markdown.
- `gmail_eml_to_markdown_cleaner.py`: Windows-friendly walker that processes EML trees, extracts metadata/front matter, normalizes Markdown, handles attachments, and optionally mdformat's output.
- `cleanup/cleanup_markdown.py`: Idempotent Markdown normalizer (line endings, metadata tables, quoting, spacing) with CLI supporting dry-run, stats-only, and output tree selection.
- `cleanup/markdown_post_fixer.py` and `markdown_post_fixer_stage2.py`: Post-processing fixes for header separators, collapsed tables, horizontal rules, and metadata consistency.
- `cleanup/regenerate_markdown_from_eml.py`: Rebuilds Markdown directly from EML sources for cases where initial export failed.

### 5.3 Utility Orchestrators (`src/utils`)
- `comprehensive_email_processor.py`: Four-layer pipeline (safe metadata extraction, intelligent content analysis, quality-driven processing, professional output generation) with test-mode sampling and detailed summaries.
- `ultimate_email_processor.py`: Variant emphasizing YAML-safe metadata plus high-quality markdown extraction, generating `_ultimate.md` outputs.
- `gmail_organizer.py`: Essential email classifier that separates keep/delete actions with categories (work, urgent, financial, legal, tax, etc.) and produces actionable reports (`EmailOrganizer`).

## 6. Data Workflows
### 6.1 Backup and Normalization
1. Fetch emails: `python main.py fetch --query "is:unread" --max 500 --output backup_unread --format both`.
2. Normalize Markdown: `python main.py tools cleanup --target backup_unread --type markdown`.
3. (Optional) Regenerate Markdown from EML for tricky messages: `python src/cleanup/regenerate_markdown_from_eml.py --base backup_unread`.

### 6.2 Structured Data & Analytics
1. Extract structured records: `python src/core/email_data_extractor.py --input backup_unread_clean --output data/monthly`.
2. Import to SQLite with indexes and FTS: `python src/core/email_database_importer.py --db data/databases/emails_final.db --json-folder data/monthly`.
3. Generate plaintext column: `python src/core/email_plaintext_processor.py --db data/databases/emails_final.db --batch-size 200`.
4. Run classification phases: `python src/core/email_classifier.py --db data/databases/emails_final.db --phase all`.

### 6.3 Newsletter Cleanup
- Offline analysis: `python src/core/gmail_ai_newsletter_cleaner.py data/monthly/2025-07_emails.json` (dry run).
- Gmail API execution: `python src/core/gmail_api_client.py --credentials config/security/credentials.json --max-emails 1000 --delete`.
- Combined cleanup + organizer: `scripts/maintenance/complete_cleanup.sh data/monthly/2025-07_emails.json --execute`.

### 6.4 Essential Email Organization
- Analyze and log actions: `python src/utils/gmail_organizer.py data/monthly/2025-07_emails.json`.
- Execute with Gmail moves/deletions when ready: add `--execute`.

### 6.5 Backup Maintenance
- Merge overlap between backup trees: `scripts/backup/dedupe_merge.ps1 -Source backup_unread_part2 -Destination backup_unread -Years 2024,2025 -Prefer larger`.
- Re-home yearly archives: `scripts/backup/move_backup_years.ps1` (moves `YYYY` folders). |
- Quick validation run: `scripts/operations/quick_test.ps1` (smoke tests for parser stack).

## 7. Automation Scripts (Highlights)
| Script | Purpose |
| --- | --- |
| `scripts/setup/quick_start.ps1` | Interactive Windows setup: dependency install, credential validation, guided fetch. |
| `scripts/setup/quick_start.bat` | Batch analog for quick start on Windows CMD. |
| `scripts/operations/run_comprehensive.ps1` / `.bat` | Orchestrate end-to-end processing (fetch, normalize, extract, import). |
| `scripts/backup/dedupe_in_place.ps1` | Remove duplicate backups within a single tree using message IDs. |
| `scripts/backup/dedupe_merge.ps1` | Merge two backup roots while resolving conflicts by size/preference. |
| `scripts/backup/move_backup_years.ps1` | Consolidate year folders under canonical backup root. |
| `scripts/maintenance/complete_cleanup.sh` | Two-step AI newsletter removal plus essential email triage (dry-run or execute). |
| `scripts/operations/quick_test.ps1` | Lightweight regression runner for parsing utilities. |

## 8. Configuration and Secrets
- `config/app/gmail_fetcher_config.json`: Default Gmail queries, output preferences, cleanup suggestions.
- `config/app/config.json`: AI newsletter detection patterns (keywords, domains, regexes, weights, thresholds).
- `config/organizer_config.json`: Patterns for essential email categorization (work, urgent, financial, legal, deletions).
- `config/security/credentials.json` and `token.json`: OAuth secrets and refresh tokens (keep private; regenerate via `main.py fetch --auth-only`).

## 9. Data & Reports
- Backups: `backup_unread/` (active), `backups/processed/backup_unread_processed/` (normalized outputs by year/month). Avoid committing or sharing without redaction.
- Structured JSON: `data/monthly/*.json` plus `data/monthly/extraction_summary.json`.
- Database: `data/databases/emails_final.db` with WAL/SHM sidecars.
- Logs & reports: `logs/` for runtime logs if enabled, `data/working/email_organizer_*.txt` for organizer runs, `docs/email_classification_report.md` and `docs/email_report_workflow.md` for generated insights.
- Legacy references: `docs/legacy/*` and `trash/documentation/*` retain historical analyses and plans.

## 10. Logging & Observability
- Many core scripts employ rotating log files: e.g., `email_plaintext_processor.log`, `email_classifier.log`, `gmail_ai_newsletter_cleaner` logs under working directory, `gmail_cleanup_*.txt` and `email_organizer_*.txt` summarizing dry runs vs executed actions.
- For reproducibility, the AI cleaner and organizer write timestamped logs with confidence scores, reasons, and proposed actions. Always review these before enabling destructive flags.

## 11. Dependencies & Environment
- Base requirements: `requirements.txt` (Gmail API client stack, html2text).
- Advanced tooling: see `docs/legacy/requirements_advanced.txt` for optional extras (`beautifulsoup4`, `markdownify`, `readability-lxml`, `trafilatura`, `mdformat`, `chardet`, `python-frontmatter`).
- Python version: 3.8+ recommended. Some modules expect 3.11/3.12 features (dataclasses, typing annotations).
- External services: Google Cloud project with Gmail API enabled, OAuth desktop credentials.

## 12. Safety Practices
- Work in dry-run mode (`--auth-only`, `--delete` absent, `--dry-run` flags) until confident in outputs.
- Treat directories under `backup_unread`, `backups`, and `data/monthly` as sensitive; enforce access controls.
- For production Gmail operations, confirm scopes (`readonly` vs `modify`) and rotate credentials regularly.
- Keep trusted backups before running destructive scripts like `gmail_api_client.py --delete` or organizer with `--execute`.

## 13. Quick Reference Commands
- Authenticate only: `python main.py fetch --auth-only`.
- Fetch unread sample: `python main.py fetch --query "is:unread" --max 200 --output backup_unread --format both`.
- Normalize Markdown tree: `python main.py tools cleanup --target backup_unread --type markdown`.
- Parse EML directory: `python main.py parse --input backup_unread --format markdown --strategy auto`.
- Import structured data: `python src/core/email_database_importer.py --db data/databases/emails_final.db --json-folder data/monthly`.
- Classify emails: `python src/core/email_classifier.py --db data/databases/emails_final.db --phase all`.
- AI newsletter dry run: `python src/core/gmail_ai_newsletter_cleaner.py data/monthly/2025-07_emails.json`.
- Gmail cleanup with delete: `python src/core/gmail_api_client.py --credentials config/security/credentials.json --max-emails 500 --delete`.

## 14. Related Documentation
- `README.md`: High-level marketing overview and getting started guide.
- `docs/email_classification_report.md`: Sample analytics output from classifier.
- `docs/email_report_workflow.md`: Narrative walkthrough of processing stages.
- `docs/legacy/*` and `trash/documentation/*`: Historical analyses, planning documents, and alternative instructions.

Keep this hub updated as workflows evolve so operators and developers share a single source of truth for the Gmail Fetcher Suite.
