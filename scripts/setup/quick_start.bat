@echo off
echo Gmail Fetcher - Quick Setup and Run
echo =====================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Install dependencies if requirements.txt exists
if exist ..\requirements.txt (
    echo Installing Python dependencies...
    pip install -r ..\requirements.txt
    if errorlevel 1 (
        echo Error installing dependencies
        pause
        exit /b 1
    )
) else (
    echo Warning: requirements.txt not found
)

REM Check for credentials
if not exist ..\credentials.json (
    echo.
    echo ERROR: credentials.json not found!
    echo.
    echo Setup Instructions:
    echo 1. Go to https://console.cloud.google.com/
    echo 2. Create a new project or select existing
    echo 3. Enable Gmail API
    echo 4. Create OAuth 2.0 credentials (Desktop application^)
    echo 5. Download as 'credentials.json' in this folder
    echo.
    pause
    exit /b 1
)

REM Run authentication check
echo.
echo Testing Gmail API authentication...
python ..\src\gmail_assistant.py --auth-only
if errorlevel 1 (
    echo Authentication failed
    pause
    exit /b 1
)

echo.
echo Choose what to download:
echo 1. All unread emails (last 1000^)
echo 2. March 2025 emails 
echo 3. AI newsletters only
echo 4. Last 6 months
echo 5. Custom query
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    set query=is:unread
    set max=1000
    set output=unread_emails
) else if "%choice%"=="2" (
    set query=after:2025/02/28 before:2025/04/01
    set max=500
    set output=march_2025
) else if "%choice%"=="3" (
    set query=from:(theresanaiforthat.com OR mindstream.news OR futurepedia.io^)
    set max=200
    set output=ai_newsletters
) else if "%choice%"=="4" (
    set query=newer_than:6m
    set max=1000
    set output=last_6_months
) else if "%choice%"=="5" (
    set /p query="Enter Gmail search query: "
    set /p max="Enter max emails (default 100): "
    if "%max%"=="" set max=100
    set output=custom_search
) else (
    echo Invalid choice
    pause
    exit /b 1
)

echo.
echo Downloading emails...
echo Query: %query%
echo Max emails: %max%
echo Output folder: %output%
echo.

python ..\src\gmail_assistant.py --query "%query%" --max %max% --output "%output%" --format both --organize date

echo.
echo Download complete! Check the '%output%' folder.
echo.
pause
