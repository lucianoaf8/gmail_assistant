# Gmail Fetcher - Quick Setup and Run (PowerShell)
# Usage: .\quick_start.ps1

Write-Host "Gmail Fetcher - Quick Setup and Run" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies if requirements.txt exists
if (Test-Path "../requirements.txt") {
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Blue
    try {
        pip install -r ../requirements.txt
        Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error installing dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "⚠️  Warning: requirements.txt not found" -ForegroundColor Yellow
}

# Check for credentials
if (-not (Test-Path "../credentials.json")) {
    Write-Host ""
    Write-Host "❌ ERROR: credentials.json not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Setup Instructions:" -ForegroundColor Yellow
    Write-Host "1. Go to https://console.cloud.google.com/"
    Write-Host "2. Create a new project or select existing"
    Write-Host "3. Enable Gmail API"
    Write-Host "4. Create OAuth 2.0 credentials (Desktop application)"
    Write-Host "5. Download as 'credentials.json' in this folder"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Run authentication check
Write-Host ""
Write-Host "🔐 Testing Gmail API authentication..." -ForegroundColor Blue
try {
    python ../src/gmail_assistant.py --auth-only
    Write-Host "✅ Authentication successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Authentication failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Menu selection
Write-Host ""
Write-Host "Choose what to download:" -ForegroundColor Cyan
Write-Host "1. All unread emails (last 1000)"
Write-Host "2. March 2025 emails" 
Write-Host "3. AI newsletters only"
Write-Host "4. Last 6 months"
Write-Host "5. Custom query"
Write-Host ""

do {
    $choice = Read-Host "Enter choice (1-5)"
} while ($choice -notmatch '^[1-5]$')

switch ($choice) {
    "1" {
        $query = "is:unread"
        $max = 1000
        $output = "unread_emails"
        $description = "All unread emails"
    }
    "2" {
        $query = "after:2025/02/28 before:2025/04/01"
        $max = 500
        $output = "march_2025"
        $description = "March 2025 emails"
    }
    "3" {
        $query = "from:(theresanaiforthat.com OR mindstream.news OR futurepedia.io)"
        $max = 200
        $output = "ai_newsletters"
        $description = "AI newsletters"
    }
    "4" {
        $query = "newer_than:6m"
        $max = 1000
        $output = "last_6_months"
        $description = "Last 6 months"
    }
    "5" {
        $query = Read-Host "Enter Gmail search query"
        $maxInput = Read-Host "Enter max emails (default 100)"
        $max = if ($maxInput) { [int]$maxInput } else { 100 }
        $output = "custom_search"
        $description = "Custom search"
    }
}

Write-Host ""
Write-Host "📥 Downloading emails..." -ForegroundColor Blue
Write-Host "Description: $description" -ForegroundColor Gray
Write-Host "Query: $query" -ForegroundColor Gray
Write-Host "Max emails: $max" -ForegroundColor Gray
Write-Host "Output folder: $output" -ForegroundColor Gray
Write-Host ""

# Run the main script
try {
    python ../src/gmail_assistant.py --query "$query" --max $max --output "$output" --format both --organize date
    
    Write-Host ""
    Write-Host "✅ Download complete! Check the '$output' folder." -ForegroundColor Green
    
    # Open output folder
    $openFolder = Read-Host "Open output folder? (y/n)"
    if ($openFolder -eq "y" -or $openFolder -eq "Y") {
        if (Test-Path $output) {
            Invoke-Item $output
        }
    }
    
} catch {
    Write-Host "❌ Error during download: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "- Review downloaded emails in the output folder"
Write-Host "- Use Gmail web interface to delete/archive original emails"
Write-Host "- Run 'python ../examples/samples.py' to see more backup scenarios"
Write-Host ""

Read-Host "Press Enter to exit"
