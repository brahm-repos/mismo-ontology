@echo off
REM Run Enhanced Knowledge Graph Generator
REM This script runs the enhanced knowledge graph generator to process the test data

echo Starting Enhanced Knowledge Graph Generation...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.6+ and try again
    pause
    exit /b 1
)

REM Check if the script exists
if not exist "generate_enhanced_kg.py" (
    echo Error: generate_enhanced_kg.py not found
    echo Please ensure you are in the correct directory
    pause
    exit /b 1
)

REM Check if test data exists
if not exist "test-data\dataextracted_333_888_999_123321_v1.json" (
    echo Error: Test data file not found
    echo Please ensure test-data\dataextracted_333_888_999_123321_v1.json exists
    pause
    exit /b 1
)

REM Create output directory if it doesn't exist
if not exist "output" mkdir output

echo Processing test data file...
echo Input: test-data\dataextracted_333_888_999_123321_v1.json
echo Output: output\enhanced_kg.ttl
echo.

REM Run the enhanced knowledge graph generator
python generate_enhanced_kg.py --input "test-data\dataextracted_333_888_999_123321_v1.json" --output "output\enhanced_kg.ttl" --verbose

if errorlevel 1 (
    echo.
    echo Error: Knowledge graph generation failed
    pause
    exit /b 1
) else (
    echo.
    echo Enhanced Knowledge Graph generation completed successfully!
    echo Output file: output\enhanced_kg.ttl
    echo.
    echo You can now view the generated TTL file in the output directory
)

pause
