#!/usr/bin/env bash
# PlaceMux — Phase 2 · one-command setup (macOS / Linux / Git Bash)
#   bash setup.sh
set -e
cd "$(dirname "$0")"

echo "==> PlaceMux Phase 2 setup"
PY=$(command -v python3 || command -v python)
[ -z "$PY" ] && { echo "Python 3 not found."; exit 1; }
echo "==> Using $PY"

[ -d .venv ] || { echo "==> Creating .venv ..."; "$PY" -m venv .venv; }
VPY=".venv/bin/python"; [ -x "$VPY" ] || VPY=".venv/Scripts/python.exe"  # Git Bash on Windows

echo "==> Installing dependencies ..."
"$VPY" -m pip install --upgrade pip
"$VPY" -m pip install -r requirements.txt

echo ""
echo "==> Done. Run any task with:  bash run_task.sh <1-25> [demo|serve]"
