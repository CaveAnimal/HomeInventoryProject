# Start script for Home Inventory app
# Usage: Open PowerShell in this folder and run: .\start.ps1
# This script will create a .venv (if missing), install requirements,
# initialize the database (migrations + optional seed), and start the app
# bound to 0.0.0.0 so it's reachable from other devices on the LAN.

param(
    [switch]$NoSeed,
    # 'bonsai' (default) uses the local Bonsai 2 27B llama.cpp server on :1080
    # through the OpenAI-compatible vision client. 'ollama' restores the old
    # qwen3-vl path. Both are LLM vision; only the endpoint differs.
    [ValidateSet('bonsai', 'ollama')]
    [string]$VisionProvider = 'bonsai'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
Set-Location $root

Write-Host "Starting Home Inventory from $root" -ForegroundColor Cyan

$ollamaModel = 'qwen3-vl:8b-instruct'
$bonsaiUrl = 'http://127.0.0.1:1080'
$bonsaiModel = 'bonsai2-27b'

# Choose a python executable. Prefer py -3.12 if available, then py -3.11, then py -3, then system
function Resolve-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try { return (& py -3.12 -c "import sys; print(sys.executable)") } catch {}
        try { return (& py -3.11 -c "import sys; print(sys.executable)") } catch {}
        try { return (& py -3 -c "import sys; print(sys.executable)") } catch {}
    }
    $which = Get-Command python -ErrorAction SilentlyContinue
    if ($which) { return $which.Path }
    throw "No Python interpreter found. Install Python 3.11 or 3.12 and retry."
}

# Only a missing .venv needs a system interpreter. Resolving one unconditionally
# made an existing, perfectly good .venv fail to launch whenever `py`/`python`
# was off PATH - which is exactly the case for the SYSTEM account that runs this
# at boot, where nobody's per-user PATH applies.
$venvDir = Join-Path $root ".venv"
if (-not (Test-Path $venvDir)) {
    $python = Resolve-Python
    if (-not $python) { throw "Unable to resolve Python" }
    Write-Host "Using Python: $python"
    Write-Host "Creating virtual environment..."
    & $python -m venv $venvDir
}

$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) { throw "Virtual environment not found at $venvPython" }

Write-Host "Upgrading pip, setuptools, wheel..."
& $venvPython -m pip install --upgrade pip setuptools wheel | Out-Null

# Install requirements from the app folder
$req = Join-Path $root "outputs\home-inventory-app\requirements.txt"
if (-not (Test-Path $req)) { throw "requirements.txt not found at $req" }
Write-Host "Installing Python requirements (may take a few minutes)..."
& $venvPython -m pip install -r $req

# Initialize DB (run migrations). Optionally seed with sample data.
Write-Host "Initializing database (migrations)..."
Push-Location (Join-Path $root "outputs\home-inventory-app")
& $venvPython -m app.database $(if ($NoSeed) { '' } else { '--seed' })
Pop-Location

# Determine host/port and set env vars so app shows the correct phone URL
$bindHost = '0.0.0.0'
$port = 1800
if ($VisionProvider -eq 'bonsai') {
    # Bonsai serves live capture (thinking off), the nightly deep scan
    # (thinking on) and cost-lookup extraction - see app/services/vision.py.
    [System.Environment]::SetEnvironmentVariable('VISION_PROVIDER', 'bonsai', 'Process')
    [System.Environment]::SetEnvironmentVariable('BONSAI_URL', $bonsaiUrl, 'Process')
    [System.Environment]::SetEnvironmentVariable('BONSAI_VISION_MODEL', $bonsaiModel, 'Process')
    [System.Environment]::SetEnvironmentVariable('COST_LOOKUP_LLM', 'bonsai', 'Process')
} else {
    [System.Environment]::SetEnvironmentVariable('VISION_PROVIDER', 'ollama', 'Process')
    [System.Environment]::SetEnvironmentVariable('OLLAMA_VISION_MODEL', $ollamaModel, 'Process')
    [System.Environment]::SetEnvironmentVariable('COST_LOOKUP_LLM', 'ollama', 'Process')
}
[System.Environment]::SetEnvironmentVariable('HOME_INVENTORY_HOST', $bindHost, 'Process')
[System.Environment]::SetEnvironmentVariable('HOME_INVENTORY_PORT', "$port", 'Process')

if ($VisionProvider -eq 'bonsai') {
    # Warn rather than throw: the app serves the whole inventory UI fine without
    # vision, and this script also runs unattended at boot, where a hard failure
    # over a not-yet-warm model server would take the site down with it.
    Write-Host "Vision: Bonsai at $bonsaiUrl (model $bonsaiModel)"
    try {
        $null = Invoke-WebRequest -Uri "$bonsaiUrl/v1/models" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "Bonsai server is up." -ForegroundColor Green
    } catch {
        Write-Warning "Bonsai server not reachable at $bonsaiUrl - photo detection will error until it is running. Starting the app anyway."
    }
} else {
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        throw "Ollama CLI not found. Install Ollama first, then retry."
    }

    Write-Host "Ensuring Ollama is running..."
    $ollamaReady = $false
    try {
        & ollama list | Out-Null
        $ollamaReady = $true
    } catch {
        Write-Host "Ollama is not running. Starting 'ollama serve' in background..."
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden | Out-Null
    }

    if (-not $ollamaReady) {
        for ($i = 0; $i -lt 20; $i++) {
            try {
                & ollama list | Out-Null
                $ollamaReady = $true
                break
            } catch {
                # retry loop
            }
        }
    }

    if (-not $ollamaReady) {
        throw "Ollama did not become ready. Start Ollama manually and run .\start.ps1 again."
    }

    $modelList = (& ollama list) -join "`n"
    if ($modelList -notmatch [regex]::Escape($ollamaModel)) {
        Write-Host "Pulling vision model $ollamaModel (first run can take a while)..."
        & ollama pull $ollamaModel
    }
}

Write-Host "Starting app on ${bindHost}:$port (accessible from other devices on your LAN)"
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Yellow

# Start uvicorn in the outputs/home-inventory-app folder so paths resolve correctly
Push-Location (Join-Path $root "outputs\home-inventory-app")
& $venvPython -m uvicorn app.main:app --host $bindHost --port $port
Pop-Location
