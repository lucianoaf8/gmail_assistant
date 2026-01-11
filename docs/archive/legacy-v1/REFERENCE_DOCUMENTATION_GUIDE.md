# Technical Reference Documentation Guide

Quick navigation guide to the Gmail Assistant technical reference documentation suite.

---

## Documentation Files

### 1. Technical Reference Index
**File**: `0109-1400_TECHNICAL_REFERENCE_INDEX.md`

Main navigation hub for all technical documentation. Start here to find what you need.

**Use this for**:
- Finding documentation by topic
- Understanding document organization
- Quick lookups (27+ indexed entries)
- Common task examples
- API specifications
- Cross-referencing between documents

---

### 2. CLI Reference
**File**: `0109-1500_CLI_REFERENCE.md`

Complete command-line interface documentation for the `gmail-assistant` command.

**Contains**:
- Entry point and global options
- 5 commands: auth, fetch, delete, analyze, config
- All CLI parameters with type, defaults, ranges
- Exit codes (0-5) with meanings
- Configuration resolution (5-level priority)
- Gmail search query syntax
- Practical examples and workflows

**Use this for**:
- Command-line usage
- Understanding CLI options
- Exit code reference
- Shell scripting
- Automating operations
- Query syntax examples

---

### 3. Configuration Reference
**File**: `0109-1600_CONFIGURATION_REFERENCE.md`

Complete configuration file schema and parameter documentation.

**Contains**:
- AppConfig main configuration (6 parameters)
- AI newsletter detection configuration
- Email organization patterns
- Analysis pipeline settings
- Deletion pattern configurations
- Validation rules with code examples
- Security considerations
- Environment variable overrides

**Use this for**:
- Creating/modifying config files
- Understanding parameter validation
- Setting up custom configurations
- Troubleshooting configuration errors
- Production deployments
- Path and environment variable setup

---

### 4. Public API Reference
**File**: `0109-1700_PUBLIC_API_REFERENCE.md`

Complete Python API documentation for programmatic use.

**Contains**:
- Core classes: AppConfig, GmailFetcher, GmailAPIClient
- Data models: Email, EmailParticipant, result DTOs
- Protocol interfaces for type hints
- Exception hierarchy
- Configuration loading and access
- Code examples and best practices
- Type hint patterns

**Use this for**:
- Writing Python code using gmail-assistant
- Understanding class methods and signatures
- Exception handling
- Working with Email models
- Dependency injection patterns
- Code examples

---

### 5. Constants Reference
**File**: `0109-1800_CONSTANTS_REFERENCE.md`

Complete reference of all constants and hardcoded values.

**Contains**:
- Application metadata
- OAuth scope constants
- Default path constants
- Rate limiting constants
- API limits
- Output format options
- Organization type options
- Keyring configuration
- Logging configuration
- Environment variable overrides

**Use this for**:
- Understanding default values
- Configuring rate limits
- Overriding paths via environment variables
- Supported output formats
- Supported organization types
- Keyring storage details

---

## Documentation by User Type

### Command-Line Users
1. Read: `0109-1500_CLI_REFERENCE.md`
2. Reference: `0109-1400_TECHNICAL_REFERENCE_INDEX.md` (Examples section)
3. For help: See "Finding Information" in Index

### System Administrators
1. Read: `0109-1600_CONFIGURATION_REFERENCE.md`
2. Reference: `0109-1800_CONSTANTS_REFERENCE.md`
3. Navigation: Use `0109-1400_TECHNICAL_REFERENCE_INDEX.md`

### Python Developers
1. Read: `0109-1700_PUBLIC_API_REFERENCE.md`
2. Reference: `0109-1800_CONSTANTS_REFERENCE.md`
3. Navigation: Use `0109-1400_TECHNICAL_REFERENCE_INDEX.md`

### Project Maintainers
- Reference all documents for API changes
- Update relevant docs when making changes
- Use Index for consistency checking

---

## Quick Lookup Guide

### "How do I..."

| Question | File | Section |
|----------|------|---------|
| Use the CLI? | CLI Reference | Commands |
| Fetch emails? | CLI Reference | fetch command |
| Delete emails safely? | CLI Reference | delete command |
| Configure the app? | Configuration Reference | AppConfig |
| Load config in Python? | Public API Reference | AppConfig.load() |
| Handle errors? | Public API Reference | Exception Hierarchy |
| Override paths? | Constants Reference | Environment Variables |
| Set rate limit? | Configuration Reference | rate_limit_per_second |
| Find exit codes? | CLI Reference | Exit Codes |
| Use search queries? | CLI Reference | Examples |
| Understand protocols? | Public API Reference | Protocols |
| Store credentials securely? | Constants Reference | Keyring Configuration |

---

## File Locations

All documentation files are in the `docs/` directory:

```
C:\_Lucx\Projects\gmail_assistant\docs\
├── 0109-1400_TECHNICAL_REFERENCE_INDEX.md
├── 0109-1500_CLI_REFERENCE.md
├── 0109-1600_CONFIGURATION_REFERENCE.md
├── 0109-1700_PUBLIC_API_REFERENCE.md
├── 0109-1800_CONSTANTS_REFERENCE.md
├── 0109-2300_TECHNICAL_REFERENCE_DELIVERY_SUMMARY.md
└── REFERENCE_DOCUMENTATION_GUIDE.md (this file)
```

---

## Documentation Features

### Comprehensive Coverage
- All CLI commands documented
- All configuration parameters documented
- All public APIs documented
- All constants documented
- Exit codes mapped
- Example code provided

### Easy Navigation
- Table of contents in each document
- Cross-references between documents
- Index with 27+ quick lookup entries
- Search-friendly formatting

### Verified Accuracy
- All parameters verified from source code
- All ranges verified from validation logic
- All exit codes verified from exception mapping
- All defaults verified from actual code

### Consistent Structure
- Standardized format across documents
- Uniform parameter documentation
- Code examples in each section
- Clear hierarchy (H1, H2, H3, H4)

---

## Starting Your Journey

### I want to use gmail-assistant from the command line
→ Start with `0109-1500_CLI_REFERENCE.md`

### I want to configure gmail-assistant
→ Start with `0109-1600_CONFIGURATION_REFERENCE.md`

### I want to integrate it into Python code
→ Start with `0109-1700_PUBLIC_API_REFERENCE.md`

### I want to understand all available settings
→ Start with `0109-1800_CONSTANTS_REFERENCE.md`

### I'm not sure where to start
→ Start with `0109-1400_TECHNICAL_REFERENCE_INDEX.md`

---

## Version Information

**Documentation Version**: 2.0.0
**Gmail Assistant Version**: 2.0.0
**Last Updated**: 2026-01-09
**Status**: Production Ready

---

## Support Resources

If you can't find what you need in the documentation:

1. Check the **Index** (`0109-1400_TECHNICAL_REFERENCE_INDEX.md`) - 27+ quick lookup entries
2. Review **Cross-References** at the bottom of each document
3. Search for keywords in the document filenames
4. Look for code examples in relevant sections

---

## Maintenance

These documents are maintained as the codebase evolves:

- CLI changes → Update CLI Reference
- Configuration changes → Update Configuration Reference
- API changes → Update Public API Reference
- Constant changes → Update Constants Reference

All documentation follows consistent formatting for easy updates.

---

**Welcome to the Gmail Assistant Technical Reference Documentation!**

