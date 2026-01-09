@echo off
REM Test Runner Batch File - Keeps all test files in tests folder
REM Usage: run_tests.bat [test_file_name] [additional_pytest_args]

cd /d "%~dp0"
echo Working directory: %CD%

if "%1"=="--help" (
    echo Usage:
    echo   run_tests.bat                    - Run all tests with coverage
    echo   run_tests.bat test_file.py       - Run specific test file
    echo   run_tests.bat --report-only      - Generate coverage report only
    echo   run_tests.bat -k keyword         - Run tests matching keyword
    goto :eof
)

python run_tests.py %*
if errorlevel 1 (
    echo Tests failed with exit code %errorlevel%
    exit /b %errorlevel%
)

echo.
echo All test artifacts are contained in the tests folder:
echo   - Coverage reports: tests\htmlcov\
echo   - Coverage data: tests\.coverage
echo   - JSON report: tests\coverage.json
echo   - Pytest cache: tests\.pytest_cache\
