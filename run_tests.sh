#!/bin/bash
# One-click test runner for Unix/Linux/macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "Advanced TODO System - Test Suite"
echo "========================================"
echo ""

# Check Python
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✓ Found: $PYTHON_VERSION"
echo ""

# Create virtual environment if needed
echo "[2/5] Setting up environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "[3/5] Installing dependencies..."
pip install -q -r requirements-dev.txt
echo "✓ Dependencies installed"
echo ""

# Run tests
echo "[4/5] Running unit tests..."
python -m pytest tests/ -v --tb=short
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✓ All tests passed!"
    echo ""
else
    echo ""
    echo "⚠ Some tests failed (exit code: $TEST_RESULT)"
    echo ""
fi

# Run performance tests
echo "[5/5] Running performance tests..."
python perf_test.py
PERF_RESULT=$?

# Summary
echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo "✓ Unit tests: PASSED"
else
    echo "✗ Unit tests: FAILED (exit code: $TEST_RESULT)"
fi

if [ $PERF_RESULT -eq 0 ]; then
    echo "✓ Performance tests: PASSED"
else
    echo "⚠ Performance tests: Some targets not met"
fi

echo ""
echo "Run 'deactivate' to exit virtual environment"
echo "========================================"
echo ""

exit $TEST_RESULT
