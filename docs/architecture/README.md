# Architecture Documentation

System design and architectural decisions.

## Contents

| Document | Description |
|----------|-------------|
| [overview.md](overview.md) | High-level architecture overview |
| [component-deep-dive.md](component-deep-dive.md) | Detailed component analysis |
| [diagrams.md](diagrams.md) | Architecture diagrams |
| [adr/](adr/) | Architecture Decision Records |

## Package Structure

```
src/gmail_assistant/
├── cli/          # Click-based CLI
├── core/         # Core functionality (auth, fetch, config)
├── parsers/      # Email parsing and conversion
├── analysis/     # Email analysis tools
├── deletion/     # Deletion workflows
└── utils/        # Shared utilities
```
