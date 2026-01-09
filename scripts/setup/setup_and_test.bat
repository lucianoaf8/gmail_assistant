@echo off
echo Setting up Email Parser Workflow Test Environment
echo ================================================

echo.
echo Step 1: Creating virtual environment...
python -m venv venv_email_parser

echo.
echo Step 2: Activating virtual environment...
call venv_email_parser\Scripts\activate

echo.
echo Step 3: Installing required packages...
pip install python-frontmatter beautifulsoup4 html5lib markdownify chardet mdformat

echo.
echo Step 4: Running workflow test...
python email_parser_workflow_test.py --backup-dir "backup_unread" --output-dir "workflow_test_output" --verbose

echo.
echo Setup and test complete!
pause