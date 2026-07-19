# PlaceMux — Phase 2 · run any task by number (Windows / PowerShell)
#
#   .\run_task.ps1 <1-25> [demo|serve]
#
#   demo  (default) : runs the task's demo / evaluation script (prints metrics)
#   serve           : starts the task's FastAPI service on http://localhost:<8000+N>
#                     (only tasks 1-17 expose an API; 18-25 are demo-only)

param(
    [Parameter(Mandatory = $true)][int]$Task,
    [ValidateSet("demo", "serve")][string]$Mode = "demo"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$vpy  = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $vpy)) { throw "No .venv found. Run  .\setup.ps1  first." }

# folder name per task number (matches the "Phase 2 Task N - ..." directories)
$folder = Get-ChildItem -Path $root -Directory |
    Where-Object { $_.Name -match "^Phase 2 Task $Task( |-)" } |
    Select-Object -First 1
if (-not $folder) { throw "Task $Task folder not found." }

# demo entrypoint per task (relative to the task folder)
$demo = @{
    1="matching.py"; 2="match_vectors.py"; 3="demo.py"; 4="match.py";
    5="matching_engine.py"; 6="run_pipeline.py"; 7="src/train_model.py";
    8="models/matching_model.py"; 9="src/compare.py"; 10="src/signoff.py";
    11="src/model.py"; 12="parser/evaluate.py"; 13="src/model.py";
    14="scripts/demo_walkthrough.py"; 15="scripts/demo_walkthrough.py";
    16="test_system.py"; 17="demo.py"; 18="demo.py"; 19="demo.py";
    20="src/run_validation.py"; 21="demo.py"; 22="demo.py"; 23="demo.py";
    24="demo.py"; 25="demo.py"
}
# uvicorn "module:app" per task that has an API
$serve = @{
    1="app:app"; 2="app:app"; 3="app:app"; 4="app:app"; 5="app:app";
    6="src.api.app:app"; 7="api.app:app"; 8="api.app:app"; 9="api.app:app";
    10="api.app:app"; 11="api.app:app"; 12="api.app:app"; 13="api.app:app";
    14="api.app:app"; 15="api.app:app"; 16="api.app:app"; 17="src.api.app:app"
}

$env:PYTHONUTF8 = "1"
$env:PYTHONPATH = $folder.FullName
Set-Location $folder.FullName

if ($Mode -eq "serve") {
    if (-not $serve.ContainsKey($Task)) { throw "Task $Task has no API (demo-only). Use: .\run_task.ps1 $Task demo" }
    $port = 8000 + $Task
    Write-Host "==> Task $Task API -> http://localhost:$port  (docs at /docs). Ctrl+C to stop." -ForegroundColor Cyan
    & $vpy -m uvicorn $serve[$Task] --app-dir $folder.FullName --port $port --reload
} else {
    Write-Host "==> Task $Task demo: $($demo[$Task])" -ForegroundColor Cyan
    & $vpy $demo[$Task]
}
