# Quick Test Guide - Gmail Fetcher

## 🚀 Quick Start

### Run All Working Tests
```bash
# Navigate to project root
cd /path/to/gmail_assistant

# Run core working tests with coverage
python -m pytest tests/test_core_simple.py tests/test_email_processing_comprehensive.py tests/test_gmail_api_integration_comprehensive.py --cov=src --cov-report=term-missing -v
```

### Expected Output
```
tests/test_core_simple.py::TestGmailFetcherBasics::test_initialization PASSED
tests/test_core_simple.py::TestGmailFetcherBasics::test_html_converter PASSED
[... 10 tests passed ...]

tests/test_email_processing_comprehensive.py::TestEmailConversionWorkflows::test_eml_content_creation_comprehensive PASSED
[... 9 tests passed ...]

tests/test_gmail_api_integration_comprehensive.py::TestGmailAPIAuthentication::test_authentication_flow_with_credentials SKIPPED
[... 12 tests with some skipped if no credentials ...]

============= 31 passed, 13 skipped =============
```

## 📊 Coverage Analysis

### Quick Coverage Check
```bash
# Core modules only
python -m pytest tests/test_core_simple.py tests/test_email_processing_comprehensive.py --cov=src/core --cov-report=term

# Specific module
python -m pytest tests/test_email_processing_comprehensive.py --cov=src/core/gmail_assistant.py --cov-report=term
```

### HTML Coverage Report
```bash
# Generate detailed HTML report
python -m pytest tests/test_core_simple.py tests/test_email_processing_comprehensive.py --cov=src --cov-report=html

# Open htmlcov/index.html in browser
```

## 🔧 Individual Test Suites

### 1. Core Functionality (Always Works)
```bash
python -m pytest tests/test_core_simple.py -v
# ✅ 10/10 tests pass - No dependencies required
```

### 2. Email Processing (Works with or without real data)
```bash
python -m pytest tests/test_email_processing_comprehensive.py -v
# ✅ 9/9 tests pass
# 📁 Uses backup_unread/2025/09/*.eml if available
# 🔄 Falls back to test data if no real files
```

### 3. Gmail API Integration (Requires credentials)
```bash
python -m pytest tests/test_gmail_api_integration_comprehensive.py -v
# ⚠️ Skips tests if no credentials.json
# ✅ Tests real Gmail API when credentials available
```

### 4. Email Classification (Partial - needs fixes)
```bash
python -m pytest tests/test_email_classification_comprehensive.py -v
# ⚠️ 8/13 tests pass (62% success rate)
# 🔧 Method signature issues need fixing
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. "No such file" errors
```bash
# Make sure you're in project root
pwd  # Should show .../gmail_assistant
ls src/  # Should show core/, parsers/, etc.
```

#### 2. Import errors
```bash
# Add src to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
# or on Windows:
set PYTHONPATH=%PYTHONPATH%;%cd%\src
```

#### 3. "ValueError: I/O operation on closed file"
```bash
# Run tests individually instead of all at once
python -m pytest tests/test_core_simple.py
python -m pytest tests/test_email_processing_comprehensive.py
```

## 📋 Test Data Setup (Optional)

### For Maximum Test Coverage

#### 1. Gmail API Tests
```bash
# Place your Gmail API credentials
cp /path/to/your/credentials.json ./credentials.json
```

#### 2. Email Processing Tests
```bash
# Ensure backup directory exists (optional)
# Tests use backup_unread/2025/09/*.eml if available
ls backup_unread/2025/09/  # Should show .eml files
```

#### 3. Database Tests
```bash
# Ensure database exists (optional)
# Tests use data/databases/emails_final.db if available
ls data/databases/emails_final.db
```

## 📈 Current Test Status Summary

| Test Suite | Tests | Pass Rate | Coverage Focus |
|------------|-------|-----------|----------------|
| Core Simple | 10 | 100% | Basic functionality |
| Email Processing | 9 | 100% | EML/Markdown conversion |
| Gmail API | 12 | Variable* | Live API integration |
| Classification | 13 | 62% | Email categorization |

*Depends on credentials availability

## 🎯 Quick Commands Reference

```bash
# Test everything that works reliably
python -m pytest tests/test_core_simple.py tests/test_email_processing_comprehensive.py -v

# Get coverage for core gmail_assistant module
python -m pytest tests/test_core_simple.py tests/test_email_processing_comprehensive.py --cov=src/core/gmail_assistant.py --cov-report=term

# Test with real Gmail API (if credentials available)
python -m pytest tests/test_gmail_api_integration_comprehensive.py -v -s

# Check what tests are available
python -m pytest --collect-only tests/

# Run specific test
python -m pytest tests/test_core_simple.py::TestGmailFetcherBasics::test_initialization -v
```

---
**📖 For detailed information, see:** `TESTING_STATUS_AND_ROADMAP.md`