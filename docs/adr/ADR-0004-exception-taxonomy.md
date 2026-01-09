# ADR-0004: Exception Taxonomy (Single Hierarchy)

## Status

Accepted

## Context

The codebase had exceptions defined in multiple locations:
- `ConfigError` in config.py
- Various error handling scattered across modules
- No consistent exit code mapping
- Difficult to catch domain-specific errors

We needed a consistent exception strategy that:
- Provides a single source of truth
- Maps to CLI exit codes
- Allows catching all domain errors
- Distinguishes error categories

## Decision

We established a **single exception hierarchy** in `core/exceptions.py`:

```python
GmailAssistantError (base)
├── ConfigError      # Exit code 5
├── AuthError        # Exit code 3
├── NetworkError     # Exit code 4
└── APIError         # Exit code 1
```

Key principles:
1. **Single source of truth**: All exceptions defined in `exceptions.py`
2. **Common base class**: `GmailAssistantError` for catching all domain errors
3. **Exit code mapping**: Each exception type maps to a specific CLI exit code
4. **Import only**: Other modules must import, never define duplicates

Exit code rationale:
- 0: Success
- 1: General/API error
- 2: Usage error (Click handles this)
- 3: Authentication error
- 4: Network error
- 5: Configuration error

## Consequences

### Positive

- Consistent error handling across codebase
- Easy to catch all domain errors with base class
- Predictable CLI exit codes for scripting
- Clear error categorization
- No duplicate exception definitions

### Negative

- Requires updating all modules to import from central location
- Must remember to add new exceptions to the hierarchy
- Exit codes must be documented and maintained
- Breaking change for any code catching old exceptions
