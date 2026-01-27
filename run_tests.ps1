# One-click test runner for Windows PowerShell
$ErrorActionPreference = "Stop"
$venvPath = Join-Path $PSScriptRoot ".venv"

if (!(Test-Path $venvPath)) {
    python -m venv $venvPath
}

& "$venvPath\Scripts\Activate.ps1"
pip install --upgrade pip
pip install -r "$PSScriptRoot\requirements-dev.txt"

# Run pytest with basic report
pytest -q --disable-warnings --maxfail=1

# Optional performance smoke
python "$PSScriptRoot\perf_test.py" --quick
