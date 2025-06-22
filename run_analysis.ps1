# Smart Markdown Tool - PowerShell Runner
# For LearnPlan project analysis

Write-Host "Smart Markdown Tool - LearnPlan Analysis" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not available in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ and add it to PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Change to the SmartMDTool directory
Set-Location -Path $PSScriptRoot

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Present options to user
Write-Host "What would you like to do?" -ForegroundColor Cyan
Write-Host "1. Dry run analysis (recommended first)" -ForegroundColor White
Write-Host "2. Apply fixes (creates backup automatically)" -ForegroundColor White
Write-Host "3. Custom analysis with config file" -ForegroundColor White
Write-Host "4. Generate reports only" -ForegroundColor White
Write-Host "5. View help" -ForegroundColor White
Write-Host "6. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host "Running dry run analysis..." -ForegroundColor Yellow
        python smart_md_tool.py .. --dry-run
    }
    "2" {
        Write-Host "Applying fixes with backup..." -ForegroundColor Yellow
        python smart_md_tool.py .. --config learnplan_config.json
    }
    "3" {
        Write-Host "Running with custom config..." -ForegroundColor Yellow
        python smart_md_tool.py .. --config learnplan_config.json --dry-run
    }
    "4" {
        Write-Host "Generating reports only..." -ForegroundColor Yellow
        python smart_md_tool.py .. --dry-run --no-backup
    }
    "5" {
        Write-Host "Displaying help..." -ForegroundColor Yellow
        python smart_md_tool.py --help
    }
    "6" {
        Write-Host "Goodbye!" -ForegroundColor Green
        exit 0
    }
    default {
        Write-Host "Invalid choice. Please run the script again." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Analysis complete!" -ForegroundColor Green
Write-Host "Check the generated HTML report for detailed results." -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
