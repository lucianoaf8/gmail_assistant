# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for Gmail Assistant.

ADRs document significant architectural decisions made during development, including context, rationale, and consequences.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-0001](ADR-0001-package-layout.md) | Package Layout and Build Backend | Accepted |
| [ADR-0002](ADR-0002-compatibility.md) | Compatibility Strategy (Clean Break) | Accepted |
| [ADR-0003](ADR-0003-cli-framework.md) | CLI Framework (Click) | Accepted |
| [ADR-0004](ADR-0004-exception-taxonomy.md) | Exception Taxonomy (Single Hierarchy) | Accepted |

## ADR Format

Each ADR follows this template:

```markdown
# ADR-XXXX: Title

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[Why this decision was needed]

## Decision
[What was decided]

## Consequences
[Positive and negative outcomes]
```

## Adding New ADRs

1. Create a new file: `ADR-XXXX-short-title.md`
2. Use the next sequential number
3. Follow the template format
4. Update this README with the new entry
