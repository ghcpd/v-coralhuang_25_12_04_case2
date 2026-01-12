# One-click test runner for Windows PowerShell

# Determine script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir

Write-Host "========================================"
Write-Host "Advanced TODO System - Test Suite"
Write-Host "========================================"
Write-Host ""

# Check Python
Write-Host "[1/5] Checking Python installation..."
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.8+"
    exit 1
}
Write-Host "✓ Found: $pythonVersion"
Write-Host ""

# Create virtual environment if needed
Write-Host "[2/5] Setting up environment..."
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment"
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment"
    exit 1
}
Write-Host "✓ Virtual environment activated"
Write-Host ""

# Install dependencies
Write-Host "[3/5] Installing dependencies..."
pip install -q -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies"
    exit 1
}
Write-Host "✓ Dependencies installed"
Write-Host ""

# Run tests
Write-Host "[4/5] Running unit tests..."
python -m pytest tests/ -v --tb=short
$testResult = $LASTEXITCODE

if ($testResult -eq 0) {
    Write-Host ""
    Write-Host "✓ All tests passed!"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "⚠ Some tests failed (exit code: $testResult)"
    Write-Host ""
}

# Run performance tests
Write-Host "[5/5] Running performance tests..."
python perf_test.py
$perfResult = $LASTEXITCODE

# Summary
Write-Host ""
Write-Host "========================================"
Write-Host "Test Summary"
Write-Host "========================================"
if ($testResult -eq 0) {
    Write-Host "✓ Unit tests: PASSED"
} else {
    Write-Host "✗ Unit tests: FAILED (exit code: $testResult)"
}

if ($perfResult -eq 0) {
    Write-Host "✓ Performance tests: PASSED"
} else {
    Write-Host "⚠ Performance tests: Some targets not met"
}

Write-Host ""
Write-Host "Run 'deactivate' to exit virtual environment"
Write-Host "========================================"
Write-Host ""

# Exit with test result
Pop-Location
exit $testResult
