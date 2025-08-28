@echo off
echo Running Ontology Instance Generator...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.6+ and try again
    pause
    exit /b 1
)

REM Run the generator script
python generate_ontology_instances.py

echo.
echo Generation complete! Check the output files:
echo - generated_instances.ttl
echo - generated_instances.json
echo.
pause
