@echo off
REM Run MISMO XSD to TTL Transformer (FIXED VERSION)
REM This script transforms MISMO_3.6.0_B367.xsd into RDF/RDFS/OWL TTL format
REM with enhanced collection type detection and proper hierarchy establishment

echo Starting MISMO XSD to TTL Transformation (FIXED VERSION)...
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
if not exist "transform_mismo_xsd.py" (
    echo Error: transform_mismo_xsd.py not found
    echo Please ensure you are in the correct directory
    pause
    exit /b 1
)

REM Check if MISMO XSD file exists
if not exist "mismo-3.6\MISMO_3.6.0_B367.xsd" (
    echo Error: MISMO XSD file not found
    echo Please ensure mismo-3.6\MISMO_3.6.0_B367.xsd exists
    pause
    exit /b 1
)

REM Create output directory if it doesn't exist
if not exist "output" mkdir output

echo Processing MISMO XSD file...
echo Input: mismo-3.6\MISMO_3.6.0_B367.xsd
echo Output: output\mismo_ontology_fixed.ttl
echo.

REM Run the transformer
python transform_mismo_xsd.py --input "mismo-3.6\MISMO_3.6.0_B367.xsd" --output "output\mismo_ontology_fixed.ttl" --verbose

if errorlevel 1 (
    echo.
    echo Error: XSD to TTL transformation failed
    pause
    exit /b 1
) else (
    echo.
    echo MISMO XSD to TTL transformation completed successfully!
    echo Output file: output\mismo_ontology_fixed.ttl
    echo.
    echo This version includes fixes for:
    echo - Enhanced collection type detection (MESSAGE, etc.)
    echo - Proper hierarchy establishment
    echo - No duplicate class definitions
    echo - Correct Pattern 007 handling
    echo.
    echo You can now view the generated TTL file in the output directory
)

pause
