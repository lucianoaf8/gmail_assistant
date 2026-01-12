# Discovery Manifest
**Assessment Date**: 2026-01-12
**Project**: gmail-assistant v2.0.0

---

## Project Overview

| Attribute | Value |
|-----------|-------|
| Name | gmail-assistant |
| Version | 2.0.0 |
| Language | Python 3.10+ |
| Framework | Click CLI, Google APIs |
| Build System | Hatchling |
| License | MIT |

## Primary Language & Frameworks

- **Primary**: Python 3.10-3.13
- **CLI Framework**: Click 8.x
- **API Integration**: google-api-python-client 2.x
- **Authentication**: google-auth, google-auth-oauthlib
- **Content Processing**: html2text, beautifulsoup4, markdownify
- **Data Analysis**: pandas, numpy, pyarrow (optional)
- **Async**: aiohttp (optional)

## Source Directories

### Include in Analysis
| Directory | Description | File Count |
|-----------|-------------|------------|
| `src/gmail_assistant/` | Main package source | ~78 files |
| `src/gmail_assistant/cli/` | CLI entry points & commands | 9 files |
| `src/gmail_assistant/core/` | Core business logic | ~25 files |
| `src/gmail_assistant/utils/` | Utility modules | ~15 files |
| `src/gmail_assistant/parsers/` | Email parsing logic | 4 files |
| `src/gmail_assistant/analysis/` | Analysis modules | 5 files |
| `src/gmail_assistant/deletion/` | Deletion handlers | 4 files |
| `src/gmail_assistant/export/` | Export functionality | 2 files |

### Exclude from Analysis
- `.git/`
- `.mypy_cache/`
- `.ruff_cache/`
- `__pycache__/`
- `tests/test_results/`
- `archive/`
- `backups/`

## Entry Points

| Entry Point | Location | Description |
|-------------|----------|-------------|
| CLI Main | `src/gmail_assistant/cli/main.py` | Click group entry |
| Package Entry | `src/gmail_assistant/__main__.py` | Module execution |
| Script | `gmail-assistant` | Installed CLI command |

## Core Modules

| Module | Path | Responsibility |
|--------|------|----------------|
| GmailFetcher | `core/fetch/gmail_assistant.py` | Primary email fetching |
| AsyncFetcher | `core/fetch/async_fetcher.py` | Async operations |
| BatchAPI | `core/fetch/batch_api.py` | Batch Gmail API calls |
| Config | `core/config.py` | Configuration management |
| Container | `core/container.py` | Dependency injection |
| Auth | `core/auth/base.py` | OAuth2 authentication |
| Exceptions | `core/exceptions.py` | Custom exceptions |
| Protocols | `core/protocols.py` | Type protocols/interfaces |
| Schemas | `core/schemas.py` | Data schemas |

## Test Coverage Structure

| Directory | Test Type | File Count |
|-----------|-----------|------------|
| `tests/unit/` | Unit tests | ~55 files |
| `tests/integration/` | Integration tests | 6 files |
| `tests/security/` | Security tests | 10 files |
| `tests/analysis/` | Analysis tests | 1 file |
| `tests/scripts/` | Test runners | 5 files |

### Test Markers
- `unit`: No external dependencies
- `integration`: Mocked external services
- `api`: Requires real Gmail credentials
- `slow`: Tests taking >5s

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Build config, dependencies, tool settings |
| `config/config.json` | AI detection configuration |
| `config/gmail_assistant_config.json` | Main fetcher config |
| `config/analysis.json` | Analysis settings |
| `config/deletion.json` | Deletion settings |
| `config/schema/config.schema.json` | JSON schema validation |

## Environment Files

| File | Status |
|------|--------|
| `.gitignore` | Present |
| `.pre-commit-config.yaml` | Present |
| `requirements.txt` | Present (legacy) |
| `requirements.lock` | Present |

## Dependency Groups

| Group | Purpose | Key Packages |
|-------|---------|--------------|
| `core` | Required | click, google-api-python-client, tenacity |
| `analysis` | Data processing | pandas, numpy, pyarrow |
| `ui` | Progress display | rich, tqdm |
| `advanced-parsing` | HTML parsing | beautifulsoup4, lxml |
| `async` | Async support | aiohttp, psutil |
| `security` | Credential management | keyring, regex |
| `dev` | Development | pytest, ruff, mypy |

## Quality Tools

| Tool | Purpose | Config Location |
|------|---------|-----------------|
| pytest | Testing | `pyproject.toml [tool.pytest]` |
| coverage | Code coverage | `pyproject.toml [tool.coverage]` |
| ruff | Linting/formatting | `pyproject.toml [tool.ruff]` |
| mypy | Type checking | `pyproject.toml [tool.mypy]` |
| pre-commit | Git hooks | `.pre-commit-config.yaml` |

## Architecture Notes

- **src-layout**: Package in `src/gmail_assistant/`
- **Typed**: `py.typed` marker present
- **DI Container**: `core/container.py` for dependency injection
- **Protocol-based**: Interfaces defined via `typing.Protocol`
- **Async-ready**: Optional async support with aiohttp

---

## Ready for Phase 2

All source directories identified. Proceeding to sequential agent execution:
1. Architecture Review
2. Code Quality Review
3. Security Audit
