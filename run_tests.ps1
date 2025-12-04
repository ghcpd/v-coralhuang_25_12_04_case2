# PowerShell run script
python -m pip install -r requirements-dev.txt
pytest -q --durations=10
