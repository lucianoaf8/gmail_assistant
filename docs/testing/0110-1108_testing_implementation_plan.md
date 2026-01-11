# Testing Implementation Plan

**Target**: 90% coverage (unit & integration) | 85% success rate
**Created**: 2026-01-10
**Status**: Implementation Ready

---

## Executive Summary

### Current State (ACTUAL)

| Metric | Reported | Actual | Gap |
|--------|----------|--------|-----|
| Total statements | 3,704 | **10,888** | Coverage only measures imported files |
| Covered statements | 2,087 | 2,087 | - |
| Unit coverage | 54% | **19.2%** | True coverage across ALL source files |
| Integration coverage | 10% | **~3%** | Most modules untested |
| Functions to test | ~200 | **867** | 77% of functions have no tests |

### Target State

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| Unit coverage | 19.2% | 90% | +70.8% |
| Integration coverage | ~3% | 90% | +87% |
| Success rate | 95.9% | 85% | Already met |
| Statements to cover | 2,087 | 9,799 | +7,712 |

---

## Phase Overview

| Phase | Focus | Priority | Tests | Coverage Gain | Duration |
|-------|-------|----------|-------|---------------|----------|
| 1 | Critical Utils | P0-CRITICAL | ~120 | +15% | 2-3 days |
| 2 | Core Fetch | P0-CRITICAL | ~180 | +16% | 3-4 days |
| 3 | Core Auth & Processing | P1-HIGH | ~150 | +12% | 3-4 days |
| 4 | CLI Commands | P1-HIGH | ~80 | +5% | 2 days |
| 5 | Parsers & Analysis | P2-MEDIUM | ~200 | +18% | 4-5 days |
| 6 | Integration Tests | P1-HIGH | ~100 | +14% | 3-4 days |
| 7 | Deletion & Export | P2-MEDIUM | ~70 | +5% | 2 days |
| 8 | Edge Cases & Hardening | P3-LOW | ~100 | +5% | 2-3 days |
| **TOTAL** | | | **~1,000** | **90%** | **21-29 days** |

---

## Phase 1: Critical Utils (P0-CRITICAL)

**Goal**: Test core utilities that ALL other modules depend on
**Coverage target**: 95%+ for these modules
**Risk**: HIGH - failures here cascade everywhere

### 1.1 secure_file.py (0% → 95%)

**File**: `src/gmail_assistant/utils/secure_file.py`
**Lines**: 328 | **Functions**: 8 | **Current**: 0%

| Test File | Test Cases | Priority |
|-----------|------------|----------|
| `tests/unit/test_secure_file.py` | | |
| | `test_write_secure_creates_file` | P0 |
| | `test_write_secure_sets_permissions_unix` | P0 |
| | `test_write_secure_atomic_rename` | P0 |
| | `test_write_secure_handles_unicode` | P1 |
| | `test_write_secure_bytes_binary_content` | P0 |
| | `test_write_secure_bytes_permissions` | P0 |
| | `test_create_secure_directory_mode` | P0 |
| | `test_create_secure_directory_parents` | P1 |
| | `test_secure_existing_file_success` | P1 |
| | `test_secure_existing_file_nonexistent` | P1 |
| | `test_verify_permissions_secure` | P1 |
| | `test_verify_permissions_insecure` | P1 |
| | `test_windows_permissions_fallback` | P2 |
| | `test_cleanup_temp_on_failure` | P0 |
| | `test_convenience_functions` | P2 |

**Estimated tests**: 15

### 1.2 pii_redactor.py (29% → 95%)

**File**: `src/gmail_assistant/utils/pii_redactor.py`
**Lines**: 199 | **Functions**: 6 | **Current**: 29%

| Test File | Test Cases | Priority |
|-----------|------------|----------|
| `tests/unit/test_pii_redactor.py` | | |
| | `test_redact_email_standard` | P0 |
| | `test_redact_email_short_local` | P0 |
| | `test_redact_email_invalid` | P1 |
| | `test_redact_email_empty` | P1 |
| | `test_redact_subject_truncation` | P0 |
| | `test_redact_subject_short` | P1 |
| | `test_redact_subject_empty` | P1 |
| | `test_redact_phone_us_format` | P0 |
| | `test_redact_phone_international` | P0 |
| | `test_redact_phone_empty` | P1 |
| | `test_redact_log_message_email` | P0 |
| | `test_redact_log_message_credit_card` | P0 |
| | `test_redact_log_message_ssn` | P0 |
| | `test_redact_log_message_ip` | P0 |
| | `test_redact_log_message_mixed` | P0 |
| | `test_redact_dict_sensitive_keys` | P0 |
| | `test_redact_dict_nested` | P1 |
| | `test_redact_dict_lists` | P1 |
| | `test_redact_alias_method` | P2 |

**Estimated tests**: 19

### 1.3 config_schema.py (0% → 95%)

**File**: `src/gmail_assistant/utils/config_schema.py`
**Lines**: 326 | **Functions**: 7 | **Current**: 0%

| Test File | Test Cases | Priority |
|-----------|------------|----------|
| `tests/unit/test_config_schema_utils.py` | | |
| | `test_schema_validation_valid_config` | P0 |
| | `test_schema_validation_missing_required` | P0 |
| | `test_schema_validation_invalid_type` | P0 |
| | `test_schema_default_values` | P0 |
| | `test_schema_nested_validation` | P1 |
| | `test_schema_array_validation` | P1 |
| | `test_config_merge_override` | P0 |
| | `test_config_merge_deep` | P1 |
| | `test_config_load_from_file` | P0 |
| | `test_config_load_missing_file` | P1 |
| | `test_config_save_to_file` | P0 |
| | `test_config_environment_override` | P1 |

**Estimated tests**: 12

### 1.4 manifest.py (0% → 90%)

**File**: `src/gmail_assistant/utils/manifest.py`
**Lines**: 504 | **Functions**: 20 | **Current**: 0%

| Test File | Test Cases | Priority |
|-----------|------------|----------|
| `tests/unit/test_manifest.py` | | |
| | `test_manifest_create` | P0 |
| | `test_manifest_add_entry` | P0 |
| | `test_manifest_remove_entry` | P0 |
| | `test_manifest_update_entry` | P0 |
| | `test_manifest_find_by_id` | P0 |
| | `test_manifest_find_by_query` | P1 |
| | `test_manifest_save` | P0 |
| | `test_manifest_load` | P0 |
| | `test_manifest_load_corrupted` | P1 |
| | `test_manifest_versioning` | P1 |
| | `test_manifest_integrity_check` | P1 |
| | `test_manifest_backup` | P2 |
| | `test_manifest_restore` | P2 |
| | `test_manifest_merge` | P2 |
| | `test_manifest_export_csv` | P2 |
| | `test_manifest_concurrent_access` | P1 |

**Estimated tests**: 16

### 1.5 metrics.py (0% → 90%)

**File**: `src/gmail_assistant/utils/metrics.py`
**Lines**: 470 | **Functions**: 25 | **Current**: 0%

| Test File | Test Cases | Priority |
|-----------|------------|----------|
| `tests/unit/test_metrics.py` | | |
| | `test_counter_increment` | P0 |
| | `test_counter_reset` | P0 |
| | `test_gauge_set` | P0 |
| | `test_gauge_increase_decrease` | P0 |
| | `test_histogram_observe` | P0 |
| | `test_histogram_percentiles` | P1 |
| | `test_timer_context_manager` | P0 |
| | `test_timer_decorator` | P0 |
| | `test_metrics_registry` | P0 |
| | `test_metrics_export_json` | P1 |
| | `test_metrics_export_prometheus` | P2 |
| | `test_metrics_labels` | P1 |
| | `test_metrics_thread_safety` | P1 |
| | `test_metrics_aggregation` | P2 |

**Estimated tests**: 14

### 1.6 secure_logger.py (77% → 95%)

**File**: `src/gmail_assistant/utils/secure_logger.py`
**Lines**: 80 | **Functions**: 12 | **Current**: 77%

| Test File | Test Cases | Priority |
|-----------|------------|----------|
| `tests/unit/test_secure_logger.py` | | |
| | `test_get_secure_logger` | P0 |
| | `test_log_pii_redaction` | P0 |
| | `test_log_level_filtering` | P1 |
| | `test_log_format` | P1 |
| | `test_file_handler_permissions` | P1 |
| | `test_rotation_config` | P2 |

**Estimated tests**: 6

### 1.7 Remaining Utils Coverage Improvements

| File | Current | Target | Tests Needed |
|------|---------|--------|--------------|
| error_handler.py | 67% | 90% | 25 |
| input_validator.py | 83% | 95% | 12 |
| cache_manager.py | 87% | 95% | 10 |
| memory_manager.py | 88% | 95% | 8 |

**Estimated tests**: 55

### Phase 1 Summary

| Metric | Value |
|--------|-------|
| **Total tests** | ~120 |
| **Files covered** | 11 |
| **Expected coverage gain** | +15% |
| **Priority** | P0-CRITICAL |
| **Duration** | 2-3 days |

---

## Phase 2: Core Fetch (P0-CRITICAL)

**Goal**: Test email fetching - the primary application function
**Coverage target**: 90%+ for fetch modules
**Risk**: HIGH - core business logic

### 2.1 gmail_assistant.py (0% → 90%)

**File**: `src/gmail_assistant/core/fetch/gmail_assistant.py`
**Lines**: 530 | **Functions**: 17 | **Current**: 0%

| Test File | Test Cases | Priority |
|-----------|------------|----------|
| `tests/unit/test_gmail_fetcher.py` | | |
| | `test_fetcher_init_with_credentials` | P0 |
| | `test_fetcher_authenticate_success` | P0 |
| | `test_fetcher_authenticate_failure` | P0 |
| | `test_fetcher_get_profile` | P0 |
| | `test_fetcher_search_emails_query` | P0 |
| | `test_fetcher_search_emails_pagination` | P0 |
| | `test_fetcher_fetch_email_by_id` | P0 |
| | `test_fetcher_fetch_email_not_found` | P1 |
| | `test_fetcher_download_emails` | P0 |
| | `test_fetcher_download_with_format_eml` | P0 |
| | `test_fetcher_download_with_format_md` | P0 |
| | `test_fetcher_organize_by_date` | P1 |
| | `test_fetcher_organize_by_sender` | P1 |
| | `test_fetcher_content_extraction` | P0 |
| | `test_fetcher_attachment_handling` | P1 |
| | `test_fetcher_memory_management` | P1 |
| | `test_fetcher_rate_limiting_integration` | P1 |
| | `test_fetcher_error_recovery` | P1 |

**Estimated tests**: 18

### 2.2 gmail_api_client.py (0% → 90%)

**File**: `src/gmail_assistant/core/fetch/gmail_api_client.py`
**Lines**: 391 | **Functions**: 13 | **Current**: 0%

| Test Cases | Priority |
|------------|----------|
| `test_client_initialization` | P0 |
| `test_client_list_messages` | P0 |
| `test_client_get_message` | P0 |
| `test_client_trash_message` | P0 |
| `test_client_delete_message` | P0 |
| `test_client_batch_get` | P1 |
| `test_client_search_with_operators` | P0 |
| `test_client_pagination_handling` | P1 |
| `test_client_error_handling` | P0 |
| `test_client_retry_logic` | P1 |
| `test_client_quota_management` | P1 |

**Estimated tests**: 11

### 2.3 batch_api.py (0% → 85%)

**File**: `src/gmail_assistant/core/fetch/batch_api.py`
**Lines**: 443 | **Functions**: 17 | **Current**: 0%

| Test Cases | Priority |
|------------|----------|
| `test_batch_request_creation` | P0 |
| `test_batch_request_add_single` | P0 |
| `test_batch_request_add_multiple` | P0 |
| `test_batch_execute_success` | P0 |
| `test_batch_execute_partial_failure` | P1 |
| `test_batch_size_limits` | P1 |
| `test_batch_callback_handling` | P0 |
| `test_batch_error_aggregation` | P1 |
| `test_batch_retry_failed` | P1 |
| `test_batch_parallel_execution` | P2 |

**Estimated tests**: 10

### 2.4 async_fetcher.py (0% → 85%)

**File**: `src/gmail_assistant/core/fetch/async_fetcher.py`
**Lines**: 397 | **Functions**: 18 | **Current**: 0%

| Test Cases | Priority |
|------------|----------|
| `test_async_fetch_single` | P0 |
| `test_async_fetch_batch` | P0 |
| `test_async_concurrency_limit` | P1 |
| `test_async_cancellation` | P1 |
| `test_async_progress_callback` | P1 |
| `test_async_error_handling` | P0 |
| `test_async_throttling` | P1 |
| `test_async_context_manager` | P1 |

**Estimated tests**: 8

### 2.5 checkpoint.py (0% → 90%)

**File**: `src/gmail_assistant/core/fetch/checkpoint.py`
**Lines**: 441 | **Functions**: 18 | **Current**: 0%

| Test Cases | Priority |
|------------|----------|
| `test_checkpoint_create` | P0 |
| `test_checkpoint_save` | P0 |
| `test_checkpoint_load` | P0 |
| `test_checkpoint_resume` | P0 |
| `test_checkpoint_progress_tracking` | P0 |
| `test_checkpoint_state_validation` | P1 |
| `test_checkpoint_cleanup` | P1 |
| `test_checkpoint_corruption_recovery` | P1 |
| `test_checkpoint_concurrent_access` | P2 |

**Estimated tests**: 9

### 2.6 dead_letter_queue.py (0% → 85%)

**File**: `src/gmail_assistant/core/fetch/dead_letter_queue.py`
**Lines**: 514 | **Functions**: 17 | **Current**: 0%

| Test Cases | Priority |
|------------|----------|
| `test_dlq_enqueue` | P0 |
| `test_dlq_dequeue` | P0 |
| `test_dlq_retry` | P0 |
| `test_dlq_max_retries` | P1 |
| `test_dlq_persistence` | P1 |
| `test_dlq_priority_ordering` | P2 |
| `test_dlq_cleanup_expired` | P1 |
| `test_dlq_stats` | P2 |

**Estimated tests**: 8

### 2.7 Remaining Fetch Modules

| File | Target | Tests |
|------|--------|-------|
| streaming.py | 85% | 8 |
| incremental.py | 85% | 10 |
| history_sync.py | 80% | 12 |

**Estimated tests**: 30

### Phase 2 Summary

| Metric | Value |
|--------|-------|
| **Total tests** | ~180 |
| **Files covered** | 10 |
| **Expected coverage gain** | +16% |
| **Priority** | P0-CRITICAL |
| **Duration** | 3-4 days |

---

## Phase 3: Core Auth & Processing (P1-HIGH)

### 3.1 Auth Module (base.py, rate_limiter.py)

**Current coverage**: 81-94%
**Target**: 95%

| File | Tests Needed |
|------|--------------|
| base.py | 8 |
| rate_limiter.py | 6 |

### 3.2 Processing Module (0% → 85%)

| File | Lines | Tests Needed |
|------|-------|--------------|
| classifier.py | 970 | 35 |
| database.py | 534 | 20 |
| database_extensions.py | 450 | 15 |
| extractor.py | 368 | 15 |
| plaintext.py | 461 | 12 |

### 3.3 Core Other (schemas, protocols, etc.)

| File | Current | Target | Tests |
|------|---------|--------|-------|
| schemas.py | 49% | 90% | 20 |
| protocols.py | 74% | 90% | 15 |
| config_schemas.py | 0% | 90% | 12 |
| container.py | 85% | 95% | 8 |

### Phase 3 Summary

| Metric | Value |
|--------|-------|
| **Total tests** | ~150 |
| **Files covered** | 13 |
| **Expected coverage gain** | +12% |
| **Priority** | P1-HIGH |
| **Duration** | 3-4 days |

---

## Phase 4: CLI Commands (P1-HIGH)

**Goal**: Fix 15 failing CLI tests + add coverage for command modules
**Note**: CLI commands are stubs awaiting v2.1.0 implementation

### 4.1 Fix Existing Failures

Current failures in `tests/unit/test_cli_main.py`:
- `test_fetch_runs` - exit code 3
- `test_fetch_with_query` - exit code 3
- `test_delete_with_query` - exit code 5
- ... (15 total)

**Action**: Create proper stub responses or mark as `@pytest.mark.skip(reason="stub implementation")`

### 4.2 CLI Command Module Tests

| File | Lines | Tests Needed |
|------|-------|--------------|
| commands/fetch.py | 162 | 15 |
| commands/delete.py | 139 | 12 |
| commands/analyze.py | 258 | 18 |
| commands/auth.py | 136 | 10 |
| main.py | 421 | 25 |

### Phase 4 Summary

| Metric | Value |
|--------|-------|
| **Total tests** | ~80 |
| **Files covered** | 5 |
| **Expected coverage gain** | +5% |
| **Priority** | P1-HIGH |
| **Duration** | 2 days |

---

## Phase 5: Parsers & Analysis (P2-MEDIUM)

### 5.1 Parsers (0% → 85%)

| File | Lines | Functions | Tests |
|------|-------|-----------|-------|
| advanced_email_parser.py | 685 | 27 | 40 |
| gmail_eml_to_markdown_cleaner.py | 439 | 15 | 25 |
| robust_eml_converter.py | 542 | 10 | 20 |

### 5.2 Analysis (0% → 80%)

| File | Lines | Functions | Tests |
|------|-------|-----------|-------|
| daily_email_analyzer.py | 1317 | 49 | 50 |
| daily_email_analysis.py | 853 | 32 | 25 |
| email_analyzer.py | 853 | 32 | 25 |
| email_data_converter.py | 364 | 12 | 15 |

### Phase 5 Summary

| Metric | Value |
|--------|-------|
| **Total tests** | ~200 |
| **Files covered** | 7 |
| **Expected coverage gain** | +18% |
| **Priority** | P2-MEDIUM |
| **Duration** | 4-5 days |

---

## Phase 6: Integration Tests (P1-HIGH)

**Goal**: Test end-to-end workflows with mocked external services

### 6.1 Authentication Flow Integration

```python
# tests/integration/test_auth_flow.py
class TestAuthenticationFlow:
    def test_full_oauth_flow_mocked(self):
        """Test complete OAuth2 flow with mocked Google APIs"""

    def test_token_refresh_flow(self):
        """Test automatic token refresh"""

    def test_auth_failure_recovery(self):
        """Test graceful handling of auth failures"""
```

**Tests**: 15

### 6.2 Fetch Workflow Integration

```python
# tests/integration/test_fetch_workflow.py
class TestFetchWorkflow:
    def test_search_and_download_workflow(self):
        """Test: search → fetch → save to disk"""

    def test_incremental_sync_workflow(self):
        """Test: initial sync → detect changes → sync delta"""

    def test_checkpoint_resume_workflow(self):
        """Test: start → interrupt → resume from checkpoint"""
```

**Tests**: 25

### 6.3 Delete Workflow Integration

```python
# tests/integration/test_delete_workflow.py
class TestDeleteWorkflow:
    def test_search_and_trash_workflow(self):
        """Test: search → preview → trash"""

    def test_dry_run_vs_actual_delete(self):
        """Test dry-run mode prevents deletion"""
```

**Tests**: 15

### 6.4 Analysis Workflow Integration

```python
# tests/integration/test_analysis_workflow.py
class TestAnalysisWorkflow:
    def test_fetch_and_analyze_workflow(self):
        """Test: fetch emails → run analysis → generate report"""

    def test_newsletter_classification_workflow(self):
        """Test: fetch → classify → filter newsletters"""
```

**Tests**: 15

### 6.5 CLI Integration

```python
# tests/integration/test_cli_integration.py
class TestCLIIntegration:
    def test_cli_config_workflow(self):
        """Test: init → show → validate config"""

    def test_cli_fetch_with_real_config(self):
        """Test CLI fetch using actual configuration"""
```

**Tests**: 10

### 6.6 Mock Infrastructure

Create reusable mock fixtures:

```python
# tests/integration/conftest.py

@pytest.fixture
def mock_gmail_service():
    """Provides mocked Gmail API service"""

@pytest.fixture
def mock_credentials():
    """Provides mocked OAuth2 credentials"""

@pytest.fixture
def sample_email_responses():
    """Provides sample Gmail API responses"""

@pytest.fixture
def temp_backup_dir():
    """Provides temporary directory for backups"""
```

**Tests**: 20

### Phase 6 Summary

| Metric | Value |
|--------|-------|
| **Total tests** | ~100 |
| **Integration scenarios** | 6 |
| **Expected coverage gain** | +14% |
| **Priority** | P1-HIGH |
| **Duration** | 3-4 days |

---

## Phase 7: Deletion & Export (P2-MEDIUM)

### 7.1 Deletion Module (0% → 85%)

| File | Lines | Tests |
|------|-------|-------|
| deleter.py | 439 | 25 |
| setup.py | 207 | 12 |
| ui.py | 198 | 10 |

### 7.2 Export Module (0% → 85%)

| File | Lines | Tests |
|------|-------|-------|
| parquet_exporter.py | 487 | 20 |

### 7.3 Core AI Module (0% → 80%)

| File | Lines | Tests |
|------|-------|-------|
| newsletter_cleaner.py | 486 | 25 |
| analysis_integration.py | 657 | 20 |

### Phase 7 Summary

| Metric | Value |
|--------|-------|
| **Total tests** | ~70 |
| **Files covered** | 6 |
| **Expected coverage gain** | +5% |
| **Priority** | P2-MEDIUM |
| **Duration** | 2 days |

---

## Phase 8: Edge Cases & Hardening (P3-LOW)

### 8.1 Error Handling Edge Cases

- Unicode handling in all modules
- Network timeout scenarios
- Disk full conditions
- Concurrent access conflicts
- Memory pressure handling

### 8.2 Security Hardening Tests

- Path traversal attempts
- Injection attack vectors
- Permission boundary violations
- Credential exposure scenarios

### 8.3 Performance Regression Tests

- Large email batch handling
- Memory leak detection
- Rate limit compliance

### Phase 8 Summary

| Metric | Value |
|--------|-------|
| **Total tests** | ~100 |
| **Focus areas** | 3 |
| **Expected coverage gain** | +5% |
| **Priority** | P3-LOW |
| **Duration** | 2-3 days |

---

## Implementation Order & Dependencies

```
Phase 1 (Utils) ──────────────────┐
                                  │
Phase 2 (Core Fetch) ─────────────┼──→ Phase 6 (Integration)
                                  │
Phase 3 (Auth & Processing) ──────┤
                                  │
Phase 4 (CLI) ────────────────────┘

Phase 5 (Parsers & Analysis) ──────────→ Phase 7 (Deletion & Export)
                                                      │
                                                      ↓
                                              Phase 8 (Hardening)
```

---

## Test File Organization

```
tests/
├── unit/
│   ├── utils/
│   │   ├── test_secure_file.py       # Phase 1
│   │   ├── test_pii_redactor.py      # Phase 1
│   │   ├── test_config_schema.py     # Phase 1
│   │   ├── test_manifest.py          # Phase 1
│   │   ├── test_metrics.py           # Phase 1
│   │   └── test_secure_logger.py     # Phase 1
│   ├── fetch/
│   │   ├── test_gmail_fetcher.py     # Phase 2
│   │   ├── test_gmail_api_client.py  # Phase 2
│   │   ├── test_batch_api.py         # Phase 2
│   │   ├── test_async_fetcher.py     # Phase 2
│   │   ├── test_checkpoint.py        # Phase 2
│   │   └── test_dead_letter_queue.py # Phase 2
│   ├── auth/
│   │   └── test_auth_base.py         # Phase 3
│   ├── processing/
│   │   ├── test_classifier.py        # Phase 3
│   │   ├── test_database.py          # Phase 3
│   │   └── test_extractor.py         # Phase 3
│   ├── cli/
│   │   ├── test_cli_fetch.py         # Phase 4
│   │   ├── test_cli_delete.py        # Phase 4
│   │   └── test_cli_analyze.py       # Phase 4
│   ├── parsers/
│   │   ├── test_advanced_parser.py   # Phase 5
│   │   └── test_eml_converter.py     # Phase 5
│   ├── analysis/
│   │   └── test_daily_analyzer.py    # Phase 5
│   ├── deletion/
│   │   └── test_deleter.py           # Phase 7
│   └── export/
│       └── test_parquet_exporter.py  # Phase 7
├── integration/
│   ├── conftest.py                   # Phase 6
│   ├── test_auth_flow.py             # Phase 6
│   ├── test_fetch_workflow.py        # Phase 6
│   ├── test_delete_workflow.py       # Phase 6
│   ├── test_analysis_workflow.py     # Phase 6
│   └── test_cli_integration.py       # Phase 6
└── security/
    └── (existing security tests)
```

---

## Coverage Tracking Commands

### Run Full Coverage Report

```bash
# Unit tests with full coverage
pytest tests/unit/ --cov=src/gmail_assistant --cov-report=html --cov-report=term-missing

# Integration tests
pytest tests/integration/ --cov=src/gmail_assistant --cov-append --cov-report=html

# Combined report
pytest tests/ --cov=src/gmail_assistant --cov-report=html --cov-fail-under=90
```

### Per-Module Coverage

```bash
# Check specific module coverage
pytest tests/unit/utils/ --cov=src/gmail_assistant/utils --cov-report=term-missing

# Check fetch module
pytest tests/unit/fetch/ --cov=src/gmail_assistant/core/fetch --cov-report=term-missing
```

---

## Success Criteria

### Phase Gates

| Phase | Coverage Gate | Pass Criteria |
|-------|---------------|---------------|
| 1 | Utils ≥ 90% | All P0 tests passing |
| 2 | Fetch ≥ 85% | All P0 tests passing |
| 3 | Auth+Processing ≥ 85% | All P0 tests passing |
| 4 | CLI ≥ 80% | No failing tests |
| 5 | Parsers+Analysis ≥ 80% | All P0 tests passing |
| 6 | Integration ≥ 85% | All workflows tested |
| 7 | Deletion+Export ≥ 80% | All P0 tests passing |
| 8 | Overall ≥ 90% | 85%+ success rate |

### Final Validation

```bash
# Must pass before completion
pytest tests/ --cov=src/gmail_assistant --cov-fail-under=90 -v

# Expected output:
# TOTAL                                  10888   1089    ...    90%
# ================ X passed, 0 failed in Y.YYs ================
```

---

## Risk Mitigation

### High-Risk Areas

| Risk | Mitigation |
|------|------------|
| External API dependencies | Comprehensive mocking in Phase 6 |
| File system operations | Use tmp directories, cleanup fixtures |
| Async code complexity | Use pytest-asyncio, proper async fixtures |
| Windows/Unix differences | Platform-specific test markers |

### Test Quality Gates

1. **No hardcoded paths** - Use fixtures and temp directories
2. **No flaky tests** - Proper async handling, deterministic data
3. **Isolated tests** - Each test cleans up after itself
4. **Clear assertions** - Specific, meaningful failure messages

---

## Appendix: Test Templates

### Unit Test Template

```python
"""Tests for module_name functionality."""
import pytest
from unittest.mock import Mock, patch

from gmail_assistant.module_path import TargetClass


class TestTargetClass:
    """Tests for TargetClass."""

    @pytest.fixture
    def instance(self):
        """Create test instance."""
        return TargetClass()

    def test_method_success(self, instance):
        """Test method with valid input."""
        result = instance.method("valid_input")
        assert result == expected_value

    def test_method_invalid_input(self, instance):
        """Test method handles invalid input."""
        with pytest.raises(ValueError):
            instance.method(None)

    def test_method_edge_case(self, instance):
        """Test method edge case behavior."""
        result = instance.method("")
        assert result == default_value
```

### Integration Test Template

```python
"""Integration tests for workflow_name."""
import pytest
from pathlib import Path


class TestWorkflowName:
    """Integration tests for complete workflow."""

    @pytest.fixture
    def setup_environment(self, tmp_path):
        """Setup test environment."""
        # Create necessary directories/files
        yield tmp_path
        # Cleanup

    def test_complete_workflow(self, setup_environment, mock_gmail_service):
        """Test end-to-end workflow."""
        # Arrange
        config = create_test_config(setup_environment)

        # Act
        result = run_workflow(config)

        # Assert
        assert result.success
        assert Path(setup_environment / "output").exists()
```

---

## Summary

| Metric | Current | After Plan |
|--------|---------|------------|
| **Unit Coverage** | 19.2% | 90%+ |
| **Integration Coverage** | ~3% | 90%+ |
| **Test Count** | ~735 | ~1,735 |
| **Success Rate** | 95.9% | ≥85% |
| **Untested Functions** | 667 | <87 |

**Total Estimated Effort**: 21-29 development days

**Recommended Approach**:
1. Execute phases 1-2 (critical path) first
2. Run phase 6 (integration) in parallel with phases 3-4
3. Complete phases 5, 7, 8 based on team capacity
