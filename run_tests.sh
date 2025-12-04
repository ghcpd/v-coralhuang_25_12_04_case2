#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements-dev.txt -r requirements.txt
pytest -q
