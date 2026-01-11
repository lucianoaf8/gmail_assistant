# Testing Documentation

Test guides, frameworks, and execution reports.

## Contents

| Document | Description |
|----------|-------------|
| [testing-guide.md](testing-guide.md) | Comprehensive testing guide |
| [quick-reference.md](quick-reference.md) | Quick test commands |
| [reports/](reports/) | Test execution reports |

## Quick Commands

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=gmail_assistant --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/security/
```

## Test Reports

Latest reports in `reports/` directory with timestamped naming.
