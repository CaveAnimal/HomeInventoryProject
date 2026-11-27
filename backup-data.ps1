# Back up Home Inventory's live data (database, photos, labels, import inbox).
# Usage: .\backup-data.ps1 [-Destination D:\HomeInventoryBackups] [-Keep 30]
#
# The database is copied with SQLite's online backup API, so the snapshot is
# consistent even while the app is running and writing to it. A run creates a
# timestamped folder only if something changed since the newest one; only the
# newest -Keep folders are kept, so they are always the last -Keep real changes.
# Registered as the weekly (Sunday 3 AM) "HomeInventory Data Backup" scheduled task.

param(
    [string]$Destination = 'D:\HomeInventoryBackups',
    [int]$Keep = 30
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$dataDir = Join-Path $root 'outputs\home-inventory-app\data'
$dbPath = Join-Path $dataDir 'inventory.sqlite3'
$python = Join-Path $root '.venv\Scripts\python.exe'
$logPath = Join-Path $Destination 'backup.log'

function Write-Log([string]$message) {
    $line = "{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $message
    Write-Host $line
    Add-Content -Path $logPath -Value $line -Encoding utf8
}

if (-not (Test-Path (Split-Path $Destination -Qualifier))) {
    throw "Backup drive for $Destination is not connected."
}
New-Item -ItemType Directory -Force -Path $Destination | Out-Null

try {
    if (-not (Test-Path $dbPath)) { throw "Database not found at $dbPath" }
    if (-not (Test-Path $python)) { throw "Python not found at $python" }

    # 1. Consistent database snapshot into a staging folder, then an integrity check.
    $staging = Join-Path $Destination '_staging'
    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force -Confirm:$false }
    New-Item -ItemType Directory -Force -Path $staging | Out-Null
    $dbCopy = Join-Path $staging 'inventory.sqlite3'
    $check = & $python -c @"
import sqlite3, sys
src = sqlite3.connect(sys.argv[1])
dst = sqlite3.connect(sys.argv[2])
src.backup(dst)
src.close()
ok = dst.execute('PRAGMA integrity_check').fetchone()[0]
boxes = dst.execute('SELECT COUNT(*) FROM boxes').fetchone()[0]
items = dst.execute('SELECT COUNT(*) FROM box_items').fetchone()[0]
dst.close()
print(f'{ok} containers={boxes} items={items}')
"@ $dbPath $dbCopy
    if ($LASTEXITCODE -ne 0) { throw "Database backup failed." }
    if ($check -notmatch '^ok ') { throw "Backup integrity check failed: $check" }

    # 2. Skip the run if nothing changed since the newest snapshot. The fingerprint
    #    is the database content hash plus every photo/label/inbox file's path,
    #    size and timestamp. Skipping matters: otherwise idle days would fill the
    #    -Keep slots with identical copies and prune the older, different ones.
    $lines = @("db " + (Get-FileHash $dbCopy -Algorithm SHA256).Hash)
    foreach ($sub in 'photos', 'labels', 'import-inbox') {
        $src = Join-Path $dataDir $sub
        if (Test-Path $src) {
            Get-ChildItem $src -Recurse -File | Sort-Object FullName | ForEach-Object {
                $lines += "{0} {1} {2}" -f $_.FullName.Substring($dataDir.Length), $_.Length, $_.LastWriteTimeUtc.Ticks
            }
        }
    }
    $fingerprint = $lines -join "`n"
    $latest = Get-ChildItem $Destination -Directory | Where-Object { $_.Name -match '^\d{8}-\d{6}$' } |
        Sort-Object Name -Descending | Select-Object -First 1
    $latestPrint = if ($latest) { Join-Path $latest.FullName 'fingerprint.txt' }
    if ($latestPrint -and (Test-Path $latestPrint) -and ((Get-Content $latestPrint -Raw).TrimEnd() -eq $fingerprint)) {
        Remove-Item $staging -Recurse -Force -Confirm:$false
        Write-Log "SKIPPED  no changes since $($latest.Name)"
        return
    }

    $target = Join-Path $Destination (Get-Date -Format 'yyyyMMdd-HHmmss')
    Rename-Item $staging (Split-Path $target -Leaf)
    Set-Content -Path (Join-Path $target 'fingerprint.txt') -Value $fingerprint -Encoding utf8

    # 3. Photos, labels and import inbox. robocopy exit codes below 8 mean success.
    foreach ($sub in 'photos', 'labels', 'import-inbox') {
        $src = Join-Path $dataDir $sub
        if (Test-Path $src) {
            & robocopy $src (Join-Path $target $sub) /E /R:2 /W:2 /NFL /NDL /NJH /NJS /NP | Out-Null
            if ($LASTEXITCODE -ge 8) { throw "Copying $sub failed (robocopy exit $LASTEXITCODE)." }
        }
    }
    $global:LASTEXITCODE = 0

    $fileCount = (Get-ChildItem $target -Recurse -File).Count
    Write-Log "OK  $target  $check  files=$fileCount"

    # 4. Keep only the newest $Keep backups (each one a real change).
    Get-ChildItem $Destination -Directory |
        Where-Object { $_.Name -match '^\d{8}-\d{6}$' } |
        Sort-Object Name -Descending |
        Select-Object -Skip $Keep |
        ForEach-Object {
            Remove-Item $_.FullName -Recurse -Force -Confirm:$false
            Write-Log "Pruned old backup $($_.Name)"
        }
} catch {
    Write-Log "FAILED  $($_.Exception.Message)"
    exit 1
}
