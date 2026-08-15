#!/usr/bin/env bash
set -euo pipefail

python_bin="${PYTHON_BIN:-python3}"
if [[ -x .venv/bin/python ]]; then
  python_bin=.venv/bin/python
fi

"$python_bin" scripts/demo.py
