# Test Suite Fix Plan
**Created**: 2026-01-11 02:28
**Author**: Claude Code (Test Engineer)

## Current Status
- **Total Tests**: 2,300
- **Passing**: 85.96%
- **Failing**: 215 tests
- **Errors**: 13 tests
- **Skipped**: 95 tests

## Root Cause Analysis

### 1. Auth Test Failures (17 failures)
**Issue**: Mock credential_manager methods return wrong types
- `validate_scopes()` must return `tuple[bool, list[str]]`, not `Mock`
- Tests unpacking the return value fail with "cannot unpack non-iterable Mock object"

**Files Affected**:
- `tests/unit/test_auth.py`
- `tests/unit/cli/test_auth.py`

**Fix**: Update mock fixtures to return proper tuple:
```python
mock_credential_manager.validate_scopes.return_value = (True, [])
```

### 2. CLI Test Failures (15 failures)
**Issue**: CLI commands execute real authentication instead of being mocked
- Tests expect stub output but get authentication errors
- Exit code 3 (auth error) instead of 0 (success)

**Files Affected**:
- `tests/unit/test_cli_main.py`

**Fix**: Mock the command implementations or AppConfig to prevent real execution

### 3. Skipped Tests (95 total)
**Issue**: Module dependency issues and mocked API tests

**Breakdown**:
- `test_eml_to_markdown` - 44 skipped (module import issues)
- `test_integration` - 34 skipped (mocked API tests)
- Other modules - 17 skipped

**Fix Strategy**:
- Check for missing dependencies and install if needed
- Review skip decorators and remove if conditions are now met
- Convert integration tests to use proper fixtures

### 4. Zero Coverage Module
**Issue**: `core.output.plugin_manager` has 0% coverage (200 lines untested)

**Fix**: Create comprehensive test file for plugin_manager

## Implementation Plan

### Phase 1: Fix Auth Tests (High Priority)
1. Update `tests/unit/test_auth.py` mock fixture
2. Update `tests/unit/cli/test_auth.py` mocks
3. Run auth tests to verify fixes
4. **Expected Impact**: Fix 17 failures

### Phase 2: Fix CLI Tests (High Priority)
1. Add proper mocking for CLI command implementations
2. Mock AppConfig and authentication layers
3. Update assertions to match stub implementations
4. **Expected Impact**: Fix 15 failures

### Phase 3: Address Skipped Tests (Medium Priority)
1. Check `test_eml_to_markdown` dependencies
2. Install missing optional dependencies if needed
3. Remove or update skip decorators
4. **Expected Impact**: Reduce skipped from 95 to <10

### Phase 4: Create Plugin Manager Tests (Medium Priority)
1. Analyze `plugin_manager.py` functionality
2. Create comprehensive test file
3. Achieve >80% coverage
4. **Expected Impact**: Increase overall coverage by ~1%

### Phase 5: Fix Remaining Failures (Low Priority)
1. Address test_ui failures (20)
2. Address test_analyze failures (13)
3. **Expected Impact**: Fix remaining 33 failures

## Success Criteria
- [ ] All auth tests passing (17 fixes)
- [ ] All CLI tests passing (15 fixes)
- [ ] Skipped tests < 10 (85 fixes)
- [ ] Plugin manager coverage > 80%
- [ ] Overall test pass rate > 95%
- [ ] Overall line coverage > 85%

## Testing Strategy
- Fix one category at a time
- Run tests after each fix to verify
- Document any new issues discovered
- Update this plan as work progresses
