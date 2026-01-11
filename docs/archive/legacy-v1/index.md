# Gmail Assistant Documentation

**Version**: 2.0.0
**Status**: Beta (Packaging Release)

## Quick Start

```bash
# Install
pip install -e .

# Authenticate
gmail-assistant auth

# Fetch emails
gmail-assistant fetch --query "is:unread" --max 100
```

## Documentation Index

### User Guides

| Document | Description |
|----------|-------------|
| [README.md](../README.md) | Project overview and quick start |
| [CHANGELOG.md](../CHANGELOG.md) | Release notes and version history |
| [BREAKING_CHANGES.md](../BREAKING_CHANGES.md) | v2.0.0 migration guide |

### Architecture

| Document | Description |
|----------|-------------|
| [ADR-0001: Package Layout](adr/ADR-0001-package-layout.md) | src-layout and Hatchling decisions |
| [ADR-0002: Compatibility](adr/ADR-0002-compatibility.md) | Clean break strategy for v2.0.0 |
| [ADR-0003: CLI Framework](adr/ADR-0003-cli-framework.md) | Click adoption rationale |
| [ADR-0004: Exception Taxonomy](adr/ADR-0004-exception-taxonomy.md) | Unified error hierarchy |

### Configuration

| Document | Description |
|----------|-------------|
| [config/default.json.template](../config/default.json.template) | Configuration template |
| [config/schema/config.schema.json](../config/schema/config.schema.json) | JSON Schema for validation |

### Development

| Document | Description |
|----------|-------------|
| [Implementation Plan](Implementation_Plan_Final_Release_Edition.md) | Full migration plan |
| [Full Project Documentation](full_project_documentation.md) | Comprehensive project docs |

### Internal Documentation

Historical and internal documents are in [claude-docs/](claude-docs/).

## CLI Reference

```
gmail-assistant [OPTIONS] COMMAND [ARGS]

Commands:
  auth      Run OAuth authentication flow
  fetch     Fetch and backup emails
  delete    Delete emails matching query
  analyze   Analyze email content
  config    Manage configuration

Options:
  --version                  Show version
  --config PATH              Custom config file
  --allow-repo-credentials   Allow credentials in repository
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Usage error |
| 3 | Authentication error |
| 4 | Network error |
| 5 | Configuration error |

## Package Structure

```
src/gmail_assistant/
├── __init__.py          # Package root, __version__
├── __main__.py          # python -m entry point
├── cli/                 # Click-based CLI
│   ├── main.py          # Main CLI app
│   └── commands/        # Subcommand modules
├── core/                # Business logic
│   ├── config.py        # Configuration loader
│   ├── exceptions.py    # Exception taxonomy
│   ├── auth/            # OAuth handling
│   └── fetch/           # Email fetching
├── analysis/            # Email analysis
├── deletion/            # Email deletion
├── parsers/             # Email parsing
└── utils/               # Utilities
```

## Version History

- **v2.0.0** (Current): Packaging and restructuring release
- **v1.x**: Legacy script collection (deprecated)

## Support

- [GitHub Issues](https://github.com/yourusername/gmail-assistant/issues)
- [CLAUDE.md](../CLAUDE.md) - AI assistant context
