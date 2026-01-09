# PowerShell script for Comprehensive Email Processor
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "COMPREHENSIVE EMAIL PROCESSOR - DEFINITIVE SOLUTION" -ForegroundColor Cyan  
Write-Host "================================================================" -ForegroundColor Cyan

Write-Host "`nStep 1: Quick test with basic processing (no dependencies required)" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Yellow
$result = python test_comprehensive.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Quick test failed. Check error messages above." -ForegroundColor Red
    Read-Host "Press Enter to continue..."
    exit 1
}

Write-Host "`nStep 2: Running comprehensive processor in test mode..." -ForegroundColor Yellow  
Write-Host "----------------------------------------------------------------" -ForegroundColor Yellow
python comprehensive_email_processor.py --test-mode --verbose

Write-Host "`nStep 3: Optional - Install dependencies for advanced processing" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "If you want advanced HTML processing, run:" -ForegroundColor Green
Write-Host "  pip install python-frontmatter beautifulsoup4 html5lib markdownify chardet" -ForegroundColor White
Write-Host "`nThen run: python comprehensive_email_processor.py --test-mode --verbose" -ForegroundColor Green

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "PROCESSING COMPLETE" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Read-Host "Press Enter to continue..."