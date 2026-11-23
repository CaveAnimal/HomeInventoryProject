# Stop script for Home Inventory app — counterpart to start.ps1
# Usage: Open PowerShell in this folder and run: .\stop.ps1
# Stops the uvicorn app server and the Ollama runtime that start.ps1 launched.
# Use -KeepOllama to stop only the app server (e.g. if other tools use Ollama).

param(
    [switch]$KeepOllama,
    [int]$Port = 1800
)

$ErrorActionPreference = 'Stop'
$stoppedSomething = $false

Write-Host "Stopping Home Inventory..." -ForegroundColor Cyan

# --- 1. Stop the app server (uvicorn) ---
# Primary: whatever process is listening on the app port.
$serverPids = @()
try {
    $serverPids = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
        Select-Object -ExpandProperty OwningProcess -Unique)
} catch {
    # No listener on the port — fall through to the command-line match below.
}

# Fallback/addition: any python process running "uvicorn app.main:app"
# (catches a server started on a non-default port or a stuck reloader child).
$uvicornPids = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" |
    Where-Object { $_.CommandLine -match 'uvicorn\s+app\.main:app' } |
    Select-Object -ExpandProperty ProcessId)

$appPids = @($serverPids + $uvicornPids | Sort-Object -Unique | Where-Object { $_ -and $_ -ne $PID })

if ($appPids.Count -gt 0) {
    foreach ($appPid in $appPids) {
        try {
            $proc = Get-Process -Id $appPid -ErrorAction Stop
            Write-Host "Stopping app server: PID $appPid ($($proc.ProcessName))"
            Stop-Process -Id $appPid -Force -Confirm:$false -ErrorAction Stop
            $stoppedSomething = $true
        } catch {
            Write-Host "Could not stop PID ${appPid}: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    Write-Host "App server stopped." -ForegroundColor Green
} else {
    Write-Host "App server: not running (nothing listening on port $Port)."
}

# --- 2. Stop Ollama (unless -KeepOllama) ---
if ($KeepOllama) {
    Write-Host "Ollama: left running (-KeepOllama)."
} else {
    # 'ollama*' covers ollama.exe (serve), 'ollama app.exe' (desktop tray),
    # and ollama_llama_server.exe model workers.
    $ollamaProcs = @(Get-Process -Name 'ollama*' -ErrorAction SilentlyContinue)
    if ($ollamaProcs.Count -gt 0) {
        foreach ($proc in $ollamaProcs) {
            try {
                Write-Host "Stopping Ollama: PID $($proc.Id) ($($proc.ProcessName))"
                Stop-Process -Id $proc.Id -Force -Confirm:$false -ErrorAction Stop
                $stoppedSomething = $true
            } catch {
                Write-Host "Could not stop PID $($proc.Id): $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        Write-Host "Ollama stopped." -ForegroundColor Green
    } else {
        Write-Host "Ollama: not running."
    }
}

if ($stoppedSomething) {
    Write-Host "Done. Restart everything with .\start.ps1" -ForegroundColor Cyan
} else {
    Write-Host "Nothing was running. Start everything with .\start.ps1" -ForegroundColor Cyan
}
