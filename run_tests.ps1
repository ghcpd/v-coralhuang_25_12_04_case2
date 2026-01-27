# run_tests.ps1 - creates a venv (if needed), installs deps and runs pytest
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt -r requirements-dev.txt; pytest -q