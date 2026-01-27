#!/usr/bin/env bash
set -euo pipefail
VENV="${VENV:-.venv}"
if [[ ! -d "$VENV" ]]; then
  python -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install --upgrade pip
pip install -r requirements-dev.txt
pytest -q --disable-warnings --maxfail=1
python perf_test.py --quick
