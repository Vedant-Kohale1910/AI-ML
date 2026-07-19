#!/usr/bin/env bash
# PlaceMux — Phase 2 · run any task by number (macOS / Linux / Git Bash)
#   bash run_task.sh <1-25> [demo|serve]
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"
N="${1:?usage: run_task.sh <1-25> [demo|serve]}"
MODE="${2:-demo}"

VPY="$ROOT/.venv/bin/python"; [ -x "$VPY" ] || VPY="$ROOT/.venv/Scripts/python.exe"
[ -x "$VPY" ] || { echo "No .venv found. Run: bash setup.sh"; exit 1; }

FOLDER=$(find "$ROOT" -maxdepth 1 -type d -name "Phase 2 Task $N -*" | head -1)
[ -z "$FOLDER" ] && FOLDER=$(find "$ROOT" -maxdepth 1 -type d -name "Phase 2 Task $N *" | head -1)
[ -z "$FOLDER" ] && { echo "Task $N folder not found."; exit 1; }

declare -A DEMO=(
 [1]="matching.py" [2]="match_vectors.py" [3]="demo.py" [4]="match.py"
 [5]="matching_engine.py" [6]="run_pipeline.py" [7]="src/train_model.py"
 [8]="models/matching_model.py" [9]="src/compare.py" [10]="src/signoff.py"
 [11]="src/model.py" [12]="parser/evaluate.py" [13]="src/model.py"
 [14]="scripts/demo_walkthrough.py" [15]="scripts/demo_walkthrough.py"
 [16]="test_system.py" [17]="demo.py" [18]="demo.py" [19]="demo.py"
 [20]="src/run_validation.py" [21]="demo.py" [22]="demo.py" [23]="demo.py"
 [24]="demo.py" [25]="demo.py")
declare -A SERVE=(
 [1]="app:app" [2]="app:app" [3]="app:app" [4]="app:app" [5]="app:app"
 [6]="src.api.app:app" [7]="api.app:app" [8]="api.app:app" [9]="api.app:app"
 [10]="api.app:app" [11]="api.app:app" [12]="api.app:app" [13]="api.app:app"
 [14]="api.app:app" [15]="api.app:app" [16]="api.app:app" [17]="src.api.app:app")

export PYTHONUTF8=1
export PYTHONPATH="$FOLDER"
cd "$FOLDER"

if [ "$MODE" = "serve" ]; then
  [ -z "${SERVE[$N]}" ] && { echo "Task $N has no API (demo-only)."; exit 1; }
  PORT=$((8000 + N))
  echo "==> Task $N API -> http://localhost:$PORT (docs at /docs). Ctrl+C to stop."
  exec "$VPY" -m uvicorn "${SERVE[$N]}" --app-dir "$FOLDER" --port "$PORT" --reload
else
  echo "==> Task $N demo: ${DEMO[$N]}"
  exec "$VPY" "${DEMO[$N]}"
fi
