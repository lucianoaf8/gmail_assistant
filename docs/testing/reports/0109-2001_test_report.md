# Test Report - 2026-01-09 20:01

## Summary

| Metric | Value |
|--------|-------|
| Tests Passed | 33 |
| Tests Failed | 0 |
| Collection Errors | 8 |
| Execution Time | 0.05s |

## Artifact Reorganization

**Completed:**
- Moved `.coverage` → `tests/.coverage`
- Moved `.pytest_cache/` → `tests/.pytest_cache/`
- Moved `htmlcov/` → `tests/htmlcov/`

**Config Updates (pyproject.toml):**
- `cache_dir = "tests/.pytest_cache"`
- `data_file = "tests/.coverage"`
- `[tool.coverage.html] directory = "tests/htmlcov"`

## Test Results

### Passing Tests (33/33)

**test_core_container.py** (17 tests)
- `test_container_creation`
- `test_register_instance`
- `test_register_factory`
- `test_register_factory_transient`
- `test_register_type`
- `test_resolve_not_found`
- `test_try_resolve_not_found`
- `test_has_service`
- `test_method_chaining`
- `test_clear`
- `test_get_registered_services`
- `test_create_scope`
- `test_scope_context_manager`
- `test_descriptor_with_instance`
- `test_descriptor_with_factory`
- `test_no_circular_dependency`
- `test_multiple_services_integration`

**test_core_protocols.py** (16 tests)
- `test_email_metadata_creation`
- `test_email_metadata_defaults`
- `test_fetch_result_creation`
- `test_fetch_result_with_error`
- `test_delete_result_creation`
- `test_delete_result_post_init`
- `test_parse_result_creation`
- `test_gmail_client_protocol_implementation`
- `test_email_fetcher_protocol_implementation`
- `test_cache_protocol_implementation`
- `test_output_plugin_protocol_implementation`
- `test_implements_protocol_positive`
- `test_implements_protocol_negative`
- `test_assert_protocol_success`
- `test_assert_protocol_failure`
- `test_rate_limiter_implementation`

## Collection Errors (8)

### Missing Dependencies

| Module | Missing Dependency |
|--------|-------------------|
| `tests/analysis/test_daily_analyzer.py` | `pyarrow` |
| `tests/test_email_analysis_integration.py` | `pyarrow` |
| `tests/test_base64_content.py` | `frontmatter` |
| `tests/test_fix_specific_email.py` | `frontmatter` |
| `tests/test_deletion_functionality.py` | `rich` |
| `tests/test_rich_progress.py` | `rich` |

### Import Errors

| Test File | Error |
|-----------|-------|
| `tests/test_core_gmail_assistant.py` | `AINewsletterCleaner` not found in `newsletter_cleaner.py` |
| `tests/test_gmail_api_integration.py` | `IncrementalFetcher` not found in `incremental.py` |

## Recommendations

1. **Install optional deps for full test coverage:**
   ```bash
   pip install ".[analysis,ui,advanced-parsing]"
   ```

2. **Fix import errors in:**
   - `src/gmail_assistant/core/ai/__init__.py`
   - `src/gmail_assistant/core/fetch/__init__.py`

3. **Run specific test subsets when optional deps not installed:**
   ```bash
   pytest tests/test_core_container.py tests/test_core_protocols.py
   ```
