# Testing Guide

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov --cov-report=html

# Run specific markers
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m "not slow"     # Skip slow tests
```

## Test Organization

```
tests/
├── conftest.py          # Shared fixtures
├── fixtures/            # Test data files
├── analysis/            # Analysis module tests
├── integration/         # Integration tests
├── .coverage            # Coverage data (auto-generated)
├── .pytest_cache/       # Pytest cache (auto-generated)
└── htmlcov/             # HTML coverage report (auto-generated)
```

## Test Markers

| Marker | Description |
|--------|-------------|
| `unit` | Unit tests (no external deps) |
| `integration` | Tests with mocked external services |
| `api` | Tests requiring real Gmail API credentials |
| `slow` | Tests taking >5 seconds |

## Coverage

Coverage artifacts are configured to output to `tests/`:

- **Data file**: `tests/.coverage`
- **HTML report**: `tests/htmlcov/index.html`
- **Cache**: `tests/.pytest_cache/`

### View Coverage Report

```bash
pytest --cov --cov-report=html
# Open tests/htmlcov/index.html in browser
```

### Coverage Thresholds

- **Minimum**: 70% (configured in `pyproject.toml`)
- **Target**: 90%+

## Configuration

All test config lives in `pyproject.toml`:

- `[tool.pytest.ini_options]` - pytest settings
- `[tool.coverage.run]` - coverage collection
- `[tool.coverage.report]` - coverage reporting
- `[tool.coverage.html]` - HTML report output

## Writing Tests

### Naming Convention

- Files: `test_*.py`
- Classes: `Test*`
- Functions: `test_*`

### Example

```python
import pytest
from gmail_assistant.core import Container

@pytest.mark.unit
def test_container_initialization():
    """Test Container initializes correctly."""
    container = Container()
    assert container is not None
```

## CI Integration

Tests run automatically on:
- Pull requests
- Main branch pushes

Use `pytest --tb=short` for concise failure output in CI.
