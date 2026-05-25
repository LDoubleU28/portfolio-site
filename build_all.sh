#!/usr/bin/env bash
set -euo pipefail
. .venv/bin/activate
python -m pytest -q
python scripts/build_kb.py
python build.py --theme neutral --tier public --out build/neutral
python checks/leak_gate.py build/neutral
echo "Public build clean."
