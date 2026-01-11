# Gmail Assistant Test Suite Report

**Generated**: 2026-01-10 08:53 AM
**Project**: gmail_assistant v2.0.0
**Test Framework**: pytest 9.0.1
**Python Version**: 3.13.9
**Platform**: Windows (win32)

---

## Executive Summary

### Overall Test Results

| Metric | Value | Status |
|--------|-------|--------|
| **Total Tests Collected** | 693 tests | ✅ |
| **Tests Passed** | 633 tests | ✅ |
| **Tests Failed** | 55 tests | ⚠️ |
| **Tests Skipped** | 2 tests | ℹ️ |
| **Collection Errors** | 3 files | ❌ |
| **Overall Pass Rate** | 91.3% | ✅ |
| **Code Coverage (Unit Tests)** | 54.3% | ❌ |
| **Coverage Target** | 70.0% | ❌ |
| **Coverage Gap** | -15.7% | ❌ |

### Test Suite Health: OPERATIONAL WITH ISSUES

The test suite is **functional** but has **significant issues** requiring attention:
- 55 failing tests (primarily CLI and security tests)
- Coverage 15.7% below target
- 3 test files with collection errors
- pytest capture system issues on Windows

---

## Test Results by Type

### 1. Unit Tests (tests/unit/)

**Status**: ✅ MOSTLY PASSING

| Metric | Value |
|--------|-------|
| Total Tests | 619 |
| Passed | 600 |
| Failed | 19 |
| Pass Rate | 96.9% |
| Execution Time | 22.82 seconds |

#### Failed Unit Tests (19 failures)

**CLI Command Tests (15 failures)** - `tests/unit/test_cli_main.py`
- All CLI command tests failing with exit code 3 or 5
- Root cause: CLI commands are stub implementations (deferred to v2.1.0)
- Expected behavior per CLAUDE.md documentation
- Files affected:
  - `test_fetch_*` (5 tests) - Exit code 3
  - `test_delete_*` (5 tests) - Exit code 3
  - `test_analyze_*` (3 tests) - Exit code 5
  - `test_auth_runs` (1 test) - Exit code 3
  - Edge case tests (1 test) - Exit code 3

**Input Validator Tests (2 failures)** - `tests/unit/test_input_validator.py`
- `test_valid_relative_path`: Path resolution mismatch
  - Expected: `WindowsPath('test_folder/test.txt')`
  - Got: `WindowsPath('C:/_Lucx/Projects/gmail_assistant/test_folder/test.txt')`
- `test_path_traversal_blocked`: Error message format mismatch
  - Expected regex: 'dangerous'
  - Actual: "Path contains traversal component '..'"

**Memory Manager Tests (2 failures)** - `tests/unit/test_memory_manager.py`
- `test_get_updates_access_order`: Cache ordering issue
  - Expected: 'key1'
  - Got: 'key2'
- `test_get_stats_with_items`: Item count mismatch
  - Expected: 2
  - Got: 1

#### Unit Test Coverage by Module

Based on coverage report from unit tests only:

| Module | Coverage | Status |
|--------|----------|--------|
| `__init__.py` | 100% | ✅ |
| `cli/__init__.py` | 100% | ✅ |
| `core/auth/__init__.py` | 100% | ✅ |
| `core/auth/credential_manager.py` | 100% | ✅ |
| `utils/__init__.py` | 100% | ✅ |
| `core/config.py` | 99% | ✅ |
| `utils/circuit_breaker.py` | 98% | ✅ |
| `constants.py` | 96% | ✅ |
| `core/auth/base.py` | 94% | ✅ |
| `utils/rate_limiter.py` | 93% | ✅ |
| `utils/memory_manager.py` | 88% | ✅ |
| `utils/cache_manager.py` | 87% | ✅ |
| `core/exceptions.py` | 86% | ✅ |
| `core/container.py` | 85% | ✅ |
| `utils/input_validator.py` | 83% | ✅ |
| `core/auth/rate_limiter.py` | 81% | ⚠️ |
| `utils/secure_logger.py` | 79% | ⚠️ |
| `core/protocols.py` | 74% | ⚠️ |
| `utils/error_handler.py` | 66% | ❌ |
| `cli/main.py` | 63% | ❌ |
| `core/schemas.py` | 49% | ❌ |
| `utils/pii_redactor.py` | 27% | ❌ |
| `core/config_schemas.py` | 0% | ❌ |
| `core/output/plugin_manager.py` | 0% | ❌ |
| `export/parquet_exporter.py` | 0% | ❌ |
| `utils/config_schema.py` | 0% | ❌ |
| `utils/manifest.py` | 0% | ❌ |
| `utils/metrics.py` | 0% | ❌ |
| `utils/secure_file.py` | 0% | ❌ |

**Modules Excluded from Coverage** (per pyproject.toml):
- `core/fetch/*` - Requires Gmail API (integration tests)
- `core/processing/*` - Requires Gmail API
- `core/ai/*` - Requires Gmail API
- `deletion/*` - Requires Gmail API
- `analysis/*` - Requires optional dependencies
- `parsers/*` - Requires optional dependencies
- `cli/commands/*` - Stub implementations (v2.1.0)

---

### 2. Security Tests (tests/security/)

**Status**: ⚠️ PARTIALLY PASSING

| Metric | Value |
|--------|-------|
| Total Tests | 74 |
| Passed | 33 |
| Failed | 36 |
| Errors | 3 |
| Skipped | 2 |
| Pass Rate | 44.6% |

#### Failed Security Tests (36 failures)

**PII Redaction Tests (6 failures)** - `tests/security/test_m4_pii_redaction.py`
- `test_phone_redaction`
- `test_ssn_redaction`
- `test_credit_card_redaction`
- `test_ip_address_redaction`
- `test_logger_redacts_pii`
- `test_logger_preserves_non_pii`

**PowerShell Injection Tests (8 failures)** - `tests/security/test_m6_powershell_injection.py`
- `test_sanitization_function_exists`
- `test_dangerous_chars_removed`
- `test_input_length_limits`
- `test_control_chars_removed`
- `test_command_substitution_blocked`
- `test_pipeline_injection_blocked`
- `test_semicolon_injection_blocked`

**File Permissions Tests (3 failures)** - `tests/security/test_m7_file_permissions.py`
- `test_file_permissions_restrictive`
- `test_directory_permissions_restrictive`
- `test_existing_file_permissions_fixed`

**Subprocess Injection Tests (3 errors)** - `tests/security/test_h2_subprocess_injection.py`
- `test_path_traversal_blocked` - ERROR
- `test_dangerous_characters_blocked` - ERROR
- `test_valid_paths_allowed` - ERROR

#### Security Test Collection Errors (1 file)

**Syntax Error** - `tests/security/test_m5_config_schema.py`
```
IndentationError: expected an indented block after 'for' statement on line 74
```

---

### 3. Integration Tests (tests/integration/)

**Status**: ❌ NOT RUNNABLE

| Metric | Value |
|--------|-------|
| Collection Status | ❌ Failed |
| Error | ModuleNotFoundError |

**Issue**: Missing optional dependency `pyarrow`
- Required for: `gmail_assistant.analysis.email_data_converter`
- Optional dependency group: `[analysis]`
- Install command: `pip install -e ".[analysis]"`

**Files Affected**:
- `tests/integration/test_gmail_api.py`
- All tests importing from `gmail_assistant.analysis.*`

---

### 4. Analysis Tests (tests/analysis/)

**Status**: ❌ NOT RUNNABLE

| Metric | Value |
|--------|-------|
| Collection Status | ❌ Failed |
| Error | ModuleNotFoundError |

**Issue**: Missing optional dependencies
- Required: `pyarrow`, `pandas`, `numpy`
- Optional dependency group: `[analysis]`
- Install command: `pip install -e ".[analysis]"`

---

### 5. Other Tests (tests/*.py root level)

**Status**: ⚠️ COLLECTION ISSUES

Multiple test files in `tests/` root directory with pytest capture errors:
- `test_base64_content.py`
- `test_comprehensive_runner.py`
- `test_core_container.py`
- `test_core_gmail_assistant.py`
- `test_core_protocols.py`
- `test_core_simple.py`
- `test_deletion_functionality.py`
- `test_email_classification_comprehensive.py`
- `test_email_processing_comprehensive.py`
- `test_fix_specific_email.py`
- `test_fixed_eml.py`
- `test_improved_coverage.py`
- `test_parsers_advanced_email.py`
- `test_rich_progress.py`

**Issue**: pytest capture system error on Windows
```
ValueError: I/O operation on closed file
```

**Root Cause**: pytest-9.0.1 capture mechanism incompatibility with Python 3.13.9 on Windows

---

## Coverage Analysis

### Coverage Statistics (Unit Tests Only)

| Category | Statements | Missing | Branches | Partial | Coverage |
|----------|-----------|---------|----------|---------|----------|
| **Total** | 3,684 | 1,600 | 960 | 64 | **54.3%** |
| **Target** | - | - | - | - | **70.0%** |
| **Gap** | - | - | - | - | **-15.7%** |

### Coverage by Feature Area

| Feature | Files | Coverage | Status |
|---------|-------|----------|--------|
| **Core Config** | 1 | 99% | ✅ |
| **Authentication** | 3 | 92% avg | ✅ |
| **Utils (High Priority)** | 4 | 92% avg | ✅ |
| **Container/DI** | 1 | 85% | ✅ |
| **Core Protocols** | 1 | 74% | ⚠️ |
| **Error Handling** | 1 | 66% | ❌ |
| **CLI Main** | 1 | 63% | ❌ |
| **PII Redaction** | 1 | 27% | ❌ |
| **Not Tested** | 8 | 0% | ❌ |

### Files with 0% Coverage (Excluded by Design)

These modules are intentionally excluded from unit test coverage per `pyproject.toml`:

1. **CLI Commands** (stub implementations, v2.1.0):
   - `cli/commands/analyze.py`
   - `cli/commands/auth.py`
   - `cli/commands/config_cmd.py`
   - `cli/commands/delete.py`
   - `cli/commands/fetch.py`

2. **Feature Modules** (require optional dependencies or Gmail API):
   - `core/fetch/*` - Gmail API required
   - `core/processing/*` - Gmail API required
   - `core/ai/*` - Gmail API required
   - `deletion/*` - Gmail API required
   - `analysis/*` - Optional deps (pandas, pyarrow)
   - `parsers/*` - Optional deps (beautifulsoup4, etc.)

3. **Utility Modules** (complex or low priority):
   - `utils/config_schema.py`
   - `utils/manifest.py`
   - `utils/metrics.py`
   - `utils/secure_file.py`
   - `export/parquet_exporter.py`
   - `core/output/plugin_manager.py`

---

## Critical Issues

### 1. pytest Capture System Failure

**Severity**: HIGH
**Impact**: Cannot run root-level tests (153+ tests)

**Error**:
```
ValueError: I/O operation on closed file
  File "...\_pytest\capture.py", line 591, in snap
    self.tmpfile.seek(0)
```

**Cause**: pytest-9.0.1 output capture incompatibility with Python 3.13.9 on Windows

**Workaround Attempts**:
- `-s` flag (disable capture) - FAILED
- Output redirection to file - FAILED
- `--tb=short` - FAILED

**Resolution Options**:
1. Downgrade pytest to 8.x series
2. Downgrade Python to 3.12.x
3. Reorganize root-level tests into subdirectories
4. Wait for pytest patch release

---

### 2. Missing Optional Dependencies

**Severity**: MEDIUM
**Impact**: Cannot run integration and analysis tests (13+ test files)

**Missing Dependencies**:
- `pyarrow>=15.0.0` (analysis group)
- `pandas>=2.1.0` (analysis group)
- `numpy>=1.26.0` (analysis group)
- `beautifulsoup4>=4.12.3` (advanced-parsing group)
- `readability-lxml>=0.8.1` (content-extraction group)

**Resolution**:
```bash
pip install -e ".[all]"
```

---

### 3. Coverage Below Target

**Severity**: MEDIUM
**Impact**: Quality gate failure

**Current**: 54.3%
**Target**: 70.0%
**Gap**: 15.7 percentage points

**Improvement Opportunities**:
1. PII Redactor (27% → 80%) = +2.4%
2. CLI Main (63% → 80%) = +1.0%
3. Error Handler (66% → 80%) = +0.9%
4. Core Schemas (49% → 80%) = +1.2%
5. Add tests for 0% modules = +5-10%

**Estimated effort**: 12-16 hours to reach 70% coverage

---

### 4. Security Test Failures

**Severity**: HIGH
**Impact**: Security vulnerabilities unverified

**Failed Categories**:
- PII Redaction (6 tests) - Data privacy risk
- PowerShell Injection (8 tests) - Command injection risk
- File Permissions (3 tests) - Privilege escalation risk
- Subprocess Injection (3 tests) - Code execution risk

**Recommendation**: Fix security tests BEFORE v2.1.0 release

---

## Test Environment

### Dependencies Installed

**Core Dependencies** (all present):
- click 8.1.0+
- google-api-python-client 2.140.0+
- google-auth 2.27.0+
- html2text 2024.2.26+
- tenacity 8.2.0+

**Dev Dependencies** (all present):
- pytest 9.0.1
- pytest-cov 4.1.0+
- pytest-mock 3.12.0+
- pytest-asyncio 1.3.0
- pytest-playwright 0.7.2

**Optional Dependencies** (MISSING):
- ❌ pyarrow (analysis)
- ❌ pandas (analysis)
- ❌ numpy (analysis)
- ❌ beautifulsoup4 (advanced-parsing)
- ❌ readability-lxml (content-extraction)

---

## Recommendations

### Immediate Actions (Priority 1)

1. **Fix pytest capture issue**
   - Test downgrading to pytest 8.x
   - OR reorganize root-level tests into `tests/core/` subdirectory
   - Estimated effort: 2-4 hours

2. **Fix security test failures**
   - PII redaction tests (6 tests)
   - PowerShell injection tests (8 tests)
   - File permissions tests (3 tests)
   - Estimated effort: 4-6 hours

3. **Fix test_m5_config_schema.py syntax error**
   - Line 74 indentation issue
   - Estimated effort: 5 minutes

### Short-term Actions (Priority 2)

4. **Install optional dependencies for full test suite**
   ```bash
   pip install -e ".[all]"
   ```
   - Enables integration and analysis tests
   - Estimated effort: 5 minutes

5. **Fix failing unit tests**
   - Input validator path tests (2 tests)
   - Memory manager tests (2 tests)
   - Estimated effort: 1-2 hours

6. **Increase code coverage to 70%**
   - Focus on high-impact modules (PII, error handling, schemas)
   - Add tests for currently untested utilities
   - Estimated effort: 12-16 hours

### Long-term Actions (Priority 3)

7. **Document CLI stub behavior**
   - Update test expectations for v2.0.0 stub implementations
   - Add integration tests for v2.1.0 functional CLI
   - Estimated effort: 2-3 hours

8. **Improve test organization**
   - Move root-level tests to appropriate subdirectories
   - Create clear separation: unit, integration, e2e, security
   - Estimated effort: 3-4 hours

9. **Add missing test types**
   - Performance tests for email processing
   - End-to-end workflow tests
   - Gmail API mocking for offline testing
   - Estimated effort: 8-12 hours

---

## Test Execution Commands

### Run All Passing Tests
```bash
# Unit tests only (works)
pytest tests/unit/ --cov=gmail_assistant --cov-report=html

# Security tests (exclude broken file)
pytest tests/security/ --ignore=tests/security/test_m5_config_schema.py

# With full dependencies installed
pytest tests/ --ignore=tests/test_*.py -v
```

### Run Specific Test Categories
```bash
# Unit tests for specific module
pytest tests/unit/test_config.py -v

# Security tests by severity
pytest tests/security/test_h1_*.py -v  # High severity
pytest tests/security/test_m*.py -v    # Medium severity
pytest tests/security/test_l*.py -v    # Low severity

# With coverage for specific module
pytest tests/unit/test_auth.py --cov=gmail_assistant.core.auth
```

### Debugging Failed Tests
```bash
# Show full output for failed tests
pytest tests/unit/test_cli_main.py -vv --tb=long

# Run single failing test
pytest tests/unit/test_memory_manager.py::TestMemoryOptimizedCacheGet::test_get_updates_access_order -vv

# Show warnings
pytest tests/unit/ -v --tb=short -W default
```

---

## Appendix: Test File Inventory

### Unit Tests (tests/unit/) - 13 files
- ✅ `test_auth.py` - Authentication module tests
- ✅ `test_cache_manager.py` - Cache management tests
- ✅ `test_circuit_breaker.py` - Circuit breaker pattern tests
- ⚠️ `test_cli_main.py` - CLI command tests (15 failures)
- ✅ `test_config.py` - Configuration tests
- ✅ `test_constants.py` - Constants module tests
- ✅ `test_container.py` - DI container tests
- ✅ `test_credential_manager.py` - Credential storage tests
- ✅ `test_error_handler.py` - Error handling tests
- ✅ `test_exceptions.py` - Exception hierarchy tests
- ⚠️ `test_input_validator.py` - Input validation tests (2 failures)
- ⚠️ `test_memory_manager.py` - Memory management tests (2 failures)
- ✅ `test_protocols.py` - Protocol definition tests
- ✅ `test_rate_limiter.py` - Rate limiting tests

### Security Tests (tests/security/) - 10 files
- ✅ `test_h1_credential_security.py` - Credential security (passed)
- ⚠️ `test_h2_subprocess_injection.py` - Subprocess safety (3 errors)
- ✅ `test_l1_environment_paths.py` - Path security (passed)
- ✅ `test_l2_rate_limiting.py` - Rate limit security (passed)
- ✅ `test_m1_path_traversal.py` - Path traversal prevention (passed)
- ✅ `test_m2_redos.py` - ReDoS protection (passed)
- ✅ `test_m3_api_validation.py` - API validation (passed)
- ❌ `test_m4_pii_redaction.py` - PII redaction (6 failures)
- ❌ `test_m5_config_schema.py` - Config schema (syntax error)
- ❌ `test_m6_powershell_injection.py` - PowerShell safety (8 failures)
- ❌ `test_m7_file_permissions.py` - File permissions (3 failures)

### Integration Tests (tests/integration/) - Cannot run
- ❌ `test_gmail_api.py` - Gmail API integration (missing pyarrow)

### Analysis Tests (tests/analysis/) - Cannot run
- ❌ `test_daily_analyzer.py` - Daily email analysis (missing pyarrow)
- ❌ Other analysis tests (missing pandas/numpy)

### Root-Level Tests (tests/*.py) - Cannot run
- ⚠️ 15+ test files with pytest capture errors

---

**Report End**
