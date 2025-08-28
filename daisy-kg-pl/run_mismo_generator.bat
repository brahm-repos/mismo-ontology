@echo off
echo Starting MISMO 3.6 Ontology Instance Generation...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if the script exists
if not exist "generate_mismo_instances.py" (
    echo Error: generate_mismo_instances.py not found
    echo Please ensure you are in the correct directory
    pause
    exit /b 1
)

REM Run the MISMO generator
echo Running MISMO instance generator...
python generate_mismo_instances.py

if errorlevel 1 (
    echo.
    echo Error: Failed to generate MISMO instances
    pause
    exit /b 1
)

echo.
echo MISMO instance generation completed successfully!
echo Check the output files:
echo - mismo_generated_instances.ttl
echo - mismo_generated_instances.json
echo.
pause

