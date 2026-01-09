# Project Governance Quick Reference

**Created**: 2025-09-22 02:38
**Purpose**: Quick reference for critical project governance rules

## 🚨 CRITICAL RULES (NEVER VIOLATE)

### 1. Resource Discovery First
```
BEFORE creating any file or function:
✅ Search existing code: Glob, Grep, Read
✅ Check all relevant directories
✅ Extend existing code rather than duplicate
```

### 2. No Root Directory Files
```
❌ NEVER place files in project root
✅ Always organize in appropriate folders
✅ Follow established directory structure
```

### 3. Test Files Location
```
❌ NEVER place test files outside tests/
✅ ALL test-related files go in tests/
✅ No exceptions for any test-related content
```

### 4. Documentation Naming
```
❌ WRONG: implementation_plan.md
✅ RIGHT: 0922-0238_implementation_plan.md
❌ WRONG: api_design.json
✅ RIGHT: 0922-1430_api_design.json
```

## 📁 Directory Structure Map

```
gmail_fetcher/
├── src/               # Source code (organized by feature)
│   ├── core/         # Gmail API & main fetcher logic
│   ├── parsers/      # Email parsing & format conversion
│   ├── analysis/     # Email analysis & classification
│   ├── deletion/     # Email deletion & cleanup
│   ├── tools/        # CLI tools & user-facing scripts
│   └── utils/        # Shared utilities & helpers
├── tests/            # ALL test-related files
│   ├── docs/         # Test documentation
│   └── test_*.py     # Test files
├── docs/             # Documentation (timestamped)
├── config/           # Configuration files
├── scripts/          # Utility scripts & automation
├── examples/         # Example usage & demos
├── data/             # Application data & inputs
├── logs/             # Runtime logs & outputs
└── backups/          # Gmail backup storage
```

## 🔍 Pre-Creation Checklist

Before creating ANY file:

1. **Search**: `Glob`, `Grep` for similar functionality
2. **Locate**: Identify correct directory for file purpose
3. **Name**: Apply timestamped naming for documentation
4. **Verify**: Confirm not placing in root directory
5. **Validate**: Ensure follows project structure rules

## ⚡ Quick Decision Tree

**Creating a file? Ask:**

- Is it source code? → `src/` (by feature)
- Is it a test? → `tests/` (ALL test files)
- Is it documentation? → `docs/` (with timestamp)
- Is it configuration? → `config/`
- Is it a utility script? → `scripts/`
- Is it an example? → `examples/`

## 🎯 Common Patterns

### Documentation Files
```bash
# Timestamp format: MMDD-HHMM
0922-0238_feature_plan.md      # Implementation plans
0922-1430_api_documentation.md # API docs
0922-0945_test_report.txt      # Test results
0922-1205_analysis_report.json # Analysis outputs
```

### Test Files
```bash
tests/test_core_functionality.py    # Unit tests
tests/test_email_processing.py      # Integration tests
tests/docs/0922-0238_test_plan.md   # Test documentation
tests/data/sample_emails.json       # Test data
```

### Source Organization
```bash
src/core/gmail_fetcher.py           # Main fetcher
src/parsers/email_parser.py         # Email parsing
src/analysis/classifier.py          # Email classification
src/tools/cli_interface.py          # CLI tools
```

## 🛡️ Enforcement

These rules are **mandatory** and override any default behaviors. Claude must:

- ✅ Always validate against these rules before taking action
- ✅ Refuse to create files that violate organization rules
- ✅ Search for existing resources before creating new ones
- ✅ Apply correct naming conventions automatically

**No exceptions. No compromises. These rules ensure project maintainability and organization.**