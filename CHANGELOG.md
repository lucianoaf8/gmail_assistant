# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
