#!/usr/bin/env bash
set -euo pipefail
DEMO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$DEMO_ROOT"
if [[ ! -x .venv/bin/python ]]; then
  echo 'Missing local .venv/bin/python. Use the existing project environment.' >&2
  exit 1
fi
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
unset PYTHONPATH
exec .venv/bin/python demo/benchmark/server.py "$@"
