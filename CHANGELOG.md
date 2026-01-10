# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-01-09

### Added

#### Data Model Foundation (Phase 1)
- **Unified Email Schema** (`core/schemas.py`): Canonical Pydantic model replacing duplicate `EmailMetadata`/`EmailData` structures
- **Config Schema Validation** (`core/config_schemas.py`): Pydantic validation for all JSON config files with `load_validated_config()` utility
- **Idempotent Database Writes** (`core/processing/database_extensions.py`): Upsert operations using `gmail_id` as unique key with soft delete support

#### Reliability Infrastructure (Phase 2)
- **Gmail Batch API** (`core/fetch/batch_api.py`): Batch operations for 80-90% latency reduction (100 messages per API call)
- **Checkpoint Persistence** (`core/fetch/checkpoint.py`): Sync state persistence for resume capability after interruptions
- **Dead Letter Queue** (`core/fetch/dead_letter_queue.py`): SQLite-backed DLQ with exponential backoff retry scheduling

#### Advanced Features (Phase 3)
- **Database Normalization Migration** (`scripts/migration/002_normalize_schema.py`): Migration script for `email_participants`, `email_labels`, and `sync_state` tables
- **Gmail History API Sync** (`core/fetch/history_sync.py`): True incremental sync fetching only changes since last `historyId`
- **Integrated Error Handler** (`utils/error_handler.py`): `IntegratedErrorHandler` class combining error classification with circuit breaker

#### Optimization & Observability (Phase 4)
- **Parquet Export** (`export/parquet_exporter.py`): Columnar export for analytics with partitioning and compression support
- **Metrics Collection** (`utils/metrics.py`): Thread-safe metrics with counters, gauges, histograms, and `@timed` decorator
- **Backup Manifest** (`utils/manifest.py`): SHA-256 checksums for backup integrity verification

### Changed
- Extended `utils/error_handler.py` with `IntegratedErrorHandler` class and circuit breaker integration
- Added backward compatibility aliases (`EmailMetadataCompat`, `EmailDataCompat`) in `core/schemas.py` with deprecation warnings

### Technical Details
- Batch API: `GmailBatchClient` with `batch_get_messages()`, `batch_delete_messages()`, `batch_modify_labels()`
- Checkpoint: `SyncCheckpoint` dataclass with `SyncState` enum for tracking sync progress
- DLQ: `FailureType` enum with 10 failure categories, 5 retry attempts with exponential backoff
- History Sync: `HistorySyncClient` with `sync_from_history()` and `perform_incremental_sync()`
- Parquet: Optional PyArrow dependency, partitioned by `year_month` with snappy compression
- Metrics: `get_metrics()`, `inc_counter()`, `set_gauge()`, `timer()` convenience functions

## [2.0.1] - 2026-01-09

### Changed
- Reorganized `scripts/` - moved 8 standalone scripts into categorized subdirectories (`operations/`, `utilities/`, `setup/`, `analysis/`, `validation/`)
- Reorganized `archive/` into purpose-based structure (`legacy/`, `planning/`, `reports/`)
- Moved permanent reference docs to `docs/reference/`
- Moved testing documentation to `docs/testing/`

### Removed
- Empty `src/plugins/` directory tree (leftover from previous cleanup)

## [2.0.0] - 2026-01-09

### Added
- Click-based CLI with subcommands (`fetch`, `delete`, `analyze`, `auth`, `config`)
- Secure configuration system with `~/.gmail-assistant/` defaults
- Centralized exception hierarchy (`GmailAssistantError`, `ConfigError`, `AuthError`, `NetworkError`, `APIError`)
- JSON Schema for configuration validation (`config/schema/config.schema.json`)
- Comprehensive test suite with 66 tests and 81.52% coverage
- Pre-commit hooks for code quality (ruff, mypy, gitleaks)
- CI/CD pipeline with GitHub Actions
- Architecture Decision Records (ADRs) in `docs/adr/`
- Unified verification pipeline (`scripts/verify_all.ps1`)
- Release validation checks (`scripts/validation/release_checks.ps1`)

### Changed
- **BREAKING**: Migrated to src-layout package structure (`src/gmail_assistant/`)
- **BREAKING**: All imports now use `gmail_assistant.*` prefix
- **BREAKING**: CLI completely redesigned with Click framework
- **BREAKING**: Configuration paths changed to `~/.gmail-assistant/`
- **BREAKING**: Entry point changed from `python main.py` to `gmail-assistant`
- Minimum Python version raised to 3.10
- Package name changed from `gmail-fetcher` to `gmail-assistant`

### Removed
- Legacy entry points (`main.py`, `src/cli/main.py`)
- `sys.path` manipulation in source files
- Flat import structure
- Old argparse-based CLI

### Security
- Credentials now default to user home directory (`~/.gmail-assistant/`)
- Added repo-safety checks for credential paths
- Added gitleaks integration for secret detection
- Added `--allow-repo-credentials` flag for explicit opt-in

### Documentation
- Created `BREAKING_CHANGES.md` with migration guide
- Updated `README.md` with new installation and CLI usage
- Added ADR documents for architectural decisions

## [1.x.x] - Previous

See git history for previous versions.

---

## Migration from v1.x

See [BREAKING_CHANGES.md](BREAKING_CHANGES.md) for detailed migration instructions.

### Quick Migration

1. Install: `pip install -e .`
2. Move credentials: `mv credentials.json ~/.gmail-assistant/`
3. Update CLI: `gmail-assistant fetch` instead of `python src/gmail_assistant.py`
4. Update imports: `from gmail_assistant.core.config import AppConfig`
