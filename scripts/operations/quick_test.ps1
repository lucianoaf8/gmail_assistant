# PowerShell script for Email Parser Workflow Test
Write-Host "Setting up Email Parser Workflow Test Environment" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green

Write-Host "`nStep 1: Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv_email_parser

Write-Host "`nStep 2: Activating virtual environment..." -ForegroundColor Yellow
& "venv_email_parser\Scripts\Activate.ps1"

Write-Host "`nStep 3: Installing required packages..." -ForegroundColor Yellow
pip install python-frontmatter beautifulsoup4 html5lib markdownify chardet mdformat

Write-Host "`nStep 4: Running workflow test..." -ForegroundColor Yellow
python email_parser_workflow_test.py --backup-dir "backup_unread" --output-dir "workflow_test_output" --verbose

Write-Host "`nSetup and test complete!" -ForegroundColor Green
Read-Host "Press Enter to continue..."