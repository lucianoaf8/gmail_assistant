# ADR-0003: CLI Framework (Click)

## Status

Accepted

## Context

Gmail Assistant needed a command-line interface with:
- Multiple subcommands (fetch, delete, analyze, auth, config)
- Type-safe argument parsing
- Good help text generation
- Consistent error handling

Options evaluated:
1. **argparse**: Standard library, verbose configuration
2. **Click**: Third-party, decorator-based, widely adopted
3. **Typer**: Built on Click, uses type hints
4. **Fire**: Google's library, auto-generates CLI from functions

## Decision

We chose **Click** because:

1. **Better UX than argparse**:
   - Automatic help formatting
   - Color support
   - Progress bars built-in
   - Cleaner syntax via decorators

2. **Good subcommand support**:
   - Command groups
   - Nested commands
   - Shared options via context

3. **Widespread adoption**:
   - Battle-tested in production
   - Extensive documentation
   - Large community

4. **Explicit over implicit**:
   - Clear decorator syntax
   - No magic from type hints (unlike Typer)
   - Predictable behavior

## Consequences

### Positive

- Clean, readable CLI code
- Excellent help text generation
- Easy to add new subcommands
- Good testing support via CliRunner
- Consistent error handling patterns

### Negative

- Additional dependency (not stdlib)
- Learning curve for decorator syntax
- Slightly more verbose than Typer
- Must manually define types (vs type hint inference)
