# ADR-0002: Compatibility Strategy (Clean Break)

## Status

Accepted

## Context

During the v2.0.0 restructuring, we had to decide how to handle backward compatibility with the existing codebase. Options considered:

1. **Shim layer**: Maintain old import paths via compatibility shims
2. **Gradual migration**: Deprecate old paths, maintain both during transition
3. **Clean break**: Remove old paths entirely, document migration

## Decision

We chose **clean break** with:
- Version bump to 2.0.0 (major version for breaking changes)
- No backward compatibility shims
- Comprehensive BREAKING_CHANGES.md documentation
- Clear migration guide for users

Rationale:
- Shims add maintenance burden and technical debt
- Dual support complicates testing and documentation
- Clean break reduces codebase complexity
- Major version bump clearly signals incompatibility

## Consequences

### Positive

- Simpler codebase without compatibility layers
- No technical debt from shim maintenance
- Clear boundaries between versions
- Easier to reason about imports and dependencies
- Reduced testing surface area

### Negative

- Users must migrate scripts and configurations
- No gradual transition period
- Potential friction for existing users
- Requires comprehensive migration documentation
