# PlaceMux — Phase 2 · one-command setup (Windows / PowerShell)
# Creates an isolated .venv and installs everything all 25 tasks need.
#
#   Right-click > Run with PowerShell,  OR  from a terminal:
#     powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

Write-Host "==> PlaceMux Phase 2 setup" -ForegroundColor Cyan

# 1. Find a Python 3
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) { throw "Python 3 not found. Install it from https://www.python.org/downloads/ and re-run." }

Write-Host "==> Using $($py.Source)"

# 2. Create the venv (once)
if (-not (Test-Path ".venv")) {
    Write-Host "==> Creating virtual environment (.venv) ..."
    & $py.Source -m venv .venv
} else {
    Write-Host "==> Reusing existing .venv"
}

$vpy = Join-Path $root ".venv\Scripts\python.exe"

# 3. Install dependencies
Write-Host "==> Installing dependencies (this may take a few minutes) ..."
& $vpy -m pip install --upgrade pip
& $vpy -m pip install -r requirements.txt

Write-Host ""
Write-Host "==> Done. The environment is ready." -ForegroundColor Green
Write-Host "    Run any task with:  .\run_task.ps1 <1-25> [demo|serve]"
Write-Host "    Example:            .\run_task.ps1 3          # runs Task 3's demo"
Write-Host "                        .\run_task.ps1 3 serve    # starts Task 3's API"
