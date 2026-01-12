# Discovery Manifest

**Assessment Date**: 2026-01-11
**Project**: gmail-assistant v2.0.0

---

## Project Overview

| Attribute | Value |
|-----------|-------|
| Primary Language | Python 3.10+ |
| Framework | Click (CLI), Google API Python Client |
| Package Layout | src-layout (`src/gmail_assistant/`) |
| Build System | Hatchling |
| Version | 2.0.0 |
| License | MIT |

---

## Entry Points

| Type | Location | Description |
|------|----------|-------------|
| CLI Entry | `src/gmail_assistant/cli/main.py:main` | Click-based CLI |
| Package Entry | `src/gmail_assistant/__main__.py` | `python -m` support |
| Script Command | `gmail-assistant` | Installed CLI command |

---

## Core Module Structure

```
src/gmail_assistant/
├── cli/                    # CLI commands (Click)
│   ├── main.py            # CLI entry point
│   └── commands/          # Subcommands (fetch, delete, analyze, auth, config)
├── core/                   # Core business logic
│   ├── auth/              # Authentication (OAuth, credentials, rate limiting)
│   ├── fetch/             # Email fetching (Gmail API, batch, async, streaming)
│   ├── processing/        # Email processing (database, classifier, extractor)
│   ├── ai/                # AI features (newsletter cleaner, analysis)
│   ├── output/            # Output plugins
│   ├── config.py          # Configuration management
│   ├── container.py       # Dependency injection
│   ├── exceptions.py      # Custom exceptions
│   ├── protocols.py       # Type protocols
│   └── schemas.py         # Data schemas
├── parsers/               # Email parsing (EML, HTML→MD)
├── analysis/              # Email analysis modules
├── deletion/              # Email deletion features
├── export/                # Export functionality (parquet)
└── utils/                 # Utilities (security, caching, logging)
```

---

## Source Files Summary

| Directory | Python Files |
|-----------|--------------|
| `src/gmail_assistant/` | 68 files |
| `src/gmail_assistant/cli/` | 7 files |
| `src/gmail_assistant/core/` | 23 files |
| `src/gmail_assistant/utils/` | 11 files |
| `src/gmail_assistant/parsers/` | 4 files |
| `src/gmail_assistant/analysis/` | 5 files |
| `src/gmail_assistant/deletion/` | 4 files |

---

## Test Coverage Structure

| Category | Location | File Count |
|----------|----------|------------|
| Unit Tests | `tests/unit/` | ~60 files |
| Integration Tests | `tests/integration/` | 6 files |
| Security Tests | `tests/security/` | 8 files |
| Test Scripts | `tests/scripts/` | 5 files |
| **Total** | `tests/` | **106 files** |

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/config.json` | AI newsletter detection config |
| `config/gmail_assistant_config.json` | Main fetcher configuration |
| `config/analysis.json` | Analysis settings |
| `config/deletion.json` | Deletion settings |
| `config/schema/config.schema.json` | JSON schema validation |
| `config/security/*.template` | Credential templates |

---

## Dependencies

### Core (Always Installed)
- click >=8.1.0
- google-api-python-client >=2.140.0
- google-auth, google-auth-oauthlib, google-auth-httplib2
- html2text >=2024.2.26
- tenacity >=8.2.0

### Optional Groups
- `analysis`: pandas, numpy, pyarrow
- `ui`: rich, tqdm
- `advanced-parsing`: beautifulsoup4, markdownify, lxml
- `content-extraction`: readability-lxml, trafilatura
- `async`: aiohttp, asyncio-throttle, psutil
- `security`: keyring, regex
- `dev`: pytest, ruff, mypy

---

## Environment Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project configuration |
| `requirements.txt` | Legacy requirements |
| `requirements.lock` | Locked dependencies |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `.gitignore` | Git ignore rules |

---

## Directories Excluded from Analysis

- `node_modules/` (not present)
- `venv/` (not present)
- `.git/`
- `__pycache__/`
- `.mypy_cache/`
- `.ruff_cache/`
- `archive/`
- `backups/`
- `dist/`

---

## Source Directories for Analysis

1. `src/gmail_assistant/` - All source code
2. `tests/` - Test coverage review
3. `config/` - Configuration files
4. `scripts/` - Utility scripts
5. `examples/` - Example usage

---

## Key Findings (Pre-Assessment)

1. **Well-structured src-layout** with clear module separation
2. **Comprehensive test suite** with 106 test files (unit, integration, security)
3. **Security tests present** - 8 dedicated security test files
4. **Multiple optional dependency groups** for modular installation
5. **Typed Python** (`py.typed` marker, mypy configuration)
6. **Coverage configuration** with 70% threshold

---

*Discovery Phase Complete. Proceeding to Phase 2: Agent Execution.*
