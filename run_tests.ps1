Set-StrictMode -Version Latest
python -m pip install -r requirements-dev.txt -r requirements.txt
pytest -q
