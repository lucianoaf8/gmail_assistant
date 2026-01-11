# ADR-0001: Package Layout and Build Backend

## Status

Accepted

## Context

Gmail Assistant was originally a collection of scripts without proper Python packaging. This made it difficult to:
- Install the tool via pip
- Import modules cleanly without sys.path manipulation
- Distribute the application
- Maintain consistent imports across the codebase

We needed to choose:
1. A package layout (flat vs src-layout)
2. A build backend (setuptools, flit, hatchling, poetry, etc.)
3. A scripting language for automation (bash, PowerShell, Python)

## Decision

We chose:

1. **src-layout** (`src/gmail_assistant/`) - Industry best practice that:
   - Prevents accidental imports from the development directory
   - Forces proper package installation for testing
   - Clearly separates source from tests and scripts

2. **Hatchling** as build backend because:
   - Modern and fast
   - Correct src-layout defaults out of the box
   - Simple configuration
   - Good PEP 621 compliance
   - Active maintenance

3. **PowerShell** for automation scripts because:
   - Cross-platform via PowerShell Core (pwsh)
   - Windows-first project environment
   - Strong support for file operations

4. **User home** (`~/.gmail-assistant/`) for configuration default because:
   - Security-first: credentials outside any git repository by default
   - Standard location for user configuration
   - Repo-local requires explicit opt-in

## Consequences

### Positive

- Clean imports using `gmail_assistant.*` prefix everywhere
- Proper `pip install -e .` for development
- Console script entry point (`gmail-assistant`) works out of box
- Clear separation of concerns in directory structure
- Credentials safe from accidental git commits by default

### Negative

- All imports must be updated from bare module names
- Existing scripts need path adjustments
- Requires PowerShell Core on Linux/macOS for running automation
- Breaking change for existing users (migration required)
