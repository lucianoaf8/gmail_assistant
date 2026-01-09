@echo off
echo ================================================================
echo COMPREHENSIVE EMAIL PROCESSOR - DEFINITIVE SOLUTION
echo ================================================================

echo.
echo Step 1: Quick test with basic processing (no dependencies required)
echo ----------------------------------------------------------------
python test_comprehensive.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ Quick test failed. Check error messages above.
    pause
    exit /b 1
)

echo.
echo Step 2: Running comprehensive processor in test mode...
echo ----------------------------------------------------------------
python comprehensive_email_processor.py --test-mode --verbose

echo.
echo Step 3: Optional - Install dependencies for advanced processing
echo ----------------------------------------------------------------
echo If you want advanced HTML processing, run:
echo   pip install python-frontmatter beautifulsoup4 html5lib markdownify chardet
echo.
echo Then run: python comprehensive_email_processor.py --test-mode --verbose

echo.
echo ================================================================
echo PROCESSING COMPLETE
echo ================================================================
pause