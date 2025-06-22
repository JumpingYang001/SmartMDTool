@echo off
echo Smart Markdown Tool - LearnPlan Analysis
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not available in PATH
    echo Please install Python 3.7+ and add it to PATH
    pause
    exit /b 1
)

REM Change to the SmartMDTool directory
cd /d "%~dp0"

echo Current directory: %cd%
echo.

REM Ask user what they want to do
echo What would you like to do?
echo 1. Dry run analysis (recommended first)
echo 2. Apply fixes (creates backup automatically)
echo 3. Custom analysis with config file
echo 4. Generate reports only
echo 5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Running dry run analysis...
    python smart_md_tool.py .. --dry-run
) else if "%choice%"=="2" (
    echo Applying fixes with backup...
    python smart_md_tool.py .. --config learnplan_config.json
) else if "%choice%"=="3" (
    echo Running with custom config...
    python smart_md_tool.py .. --config learnplan_config.json --dry-run
) else if "%choice%"=="4" (
    echo Generating reports only...
    python smart_md_tool.py .. --dry-run --no-backup
) else if "%choice%"=="5" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice. Please run the script again.
)

echo.
echo Analysis complete! 
echo Check the generated HTML report for detailed results.
echo.
pause
