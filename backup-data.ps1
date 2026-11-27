# Back up Home Inventory's live data (database, photos, labels, import inbox).
# Usage: .\backup-data.ps1 [-Destination D:\HomeInventoryBackups] [-Keep 30]
#
# The database is copied with SQLite's online backup API, so the snapshot is
# consistent even while the app is running and writing to it. A run creates a
# timestamped folder only if something changed since the newest one; only the
# newest -Keep folders are kept, so they are always the last -Keep real changes.
# Registered as the weekly (Sunday 3 AM) "HomeInventory Data Backup" scheduled task.
#
# Off-site copy (QW-6, decision PD-16): after a new snapshot, the snapshot folder
# is packed with Windows' tar and encrypted with age to the PUBLIC key in
# backup-offsite.recipient, then written as <snapshot>.tar.age into
# -OffsiteDestination (default: the OneDrive-synced folder), which OneDrive
# uploads. Only the newest -OffsiteKeep encrypted files are kept there. The
# private key is NOT on this PC: it is on the Recovery Sheet and a USB stick.
# An off-site failure never touches the local snapshot; the script exits 2.
#
# Restore from an off-site file (any computer with age installed):
#   age -d -i home-inventory-backup.agekey -o snapshot.tar <snapshot>.tar.age
#   tar -xf snapshot.tar
# The extracted folder holds inventory.sqlite3, photos, labels and import-inbox;
# copy them into outputs\home-inventory-app\data with the app stopped.

param(
    [string]$Destination = 'D:\HomeInventoryBackups',
    [int]$Keep = 30,
    [string]$OffsiteDestination = $(if ($env:OneDrive) { Join-Path $env:OneDrive 'HomeInventoryBackups' } else { '' }),
    [int]$OffsiteKeep = 3,
    [string]$RecipientFile = '',
    [string]$AgePath = '',
    [switch]$NoOffsite
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

if (-not $RecipientFile) { $RecipientFile = Join-Path $root 'backup-offsite.recipient' }

function Resolve-Age {
    if ($AgePath) {
        if (Test-Path $AgePath) { return $AgePath }
        throw "age not found at -AgePath $AgePath"
    }
    $cmd = Get-Command age.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $winget = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\age.exe'
    if (Test-Path $winget) { return $winget }
    throw 'age.exe not found (install with: winget install FiloSottile.age, or pass -AgePath).'
}

# Encrypt one local snapshot folder to <OffsiteDestination>\<name>.tar.age.
# Uses files, not a PowerShell pipeline: Windows PowerShell 5.1 corrupts binary
# data piped between native programs.
function Write-Offsite([string]$snapshotDir) {
    $name = Split-Path $snapshotDir -Leaf
    if (-not $OffsiteDestination) { throw 'No off-site destination (OneDrive not found; pass -OffsiteDestination).' }
    if (-not (Test-Path $RecipientFile)) { throw "Public key file not found: $RecipientFile" }
    New-Item -ItemType Directory -Force -Path $OffsiteDestination | Out-Null
    $final = Join-Path $OffsiteDestination "$name.tar.age"
    if (Test-Path $final) {
        Write-Log "OFFSITE  already present for $name"
        return
    }
    $age = Resolve-Age
    $tar = Join-Path $env:SystemRoot 'System32\tar.exe'
    $tarFile = Join-Path $Destination "_offsite-$name.tar"
    $partial = "$final.partial"
    try {
        & $tar -cf $tarFile -C $Destination $name
        if ($LASTEXITCODE -ne 0) { throw "tar failed (exit $LASTEXITCODE)." }
        & $age -R $RecipientFile -o $partial $tarFile
        if ($LASTEXITCODE -ne 0) { throw "age failed (exit $LASTEXITCODE)." }
        # Rename only when complete, so OneDrive never uploads a half-written file.
        Move-Item -Path $partial -Destination $final -Force
    } finally {
        if (Test-Path $tarFile) { Remove-Item $tarFile -Force -Confirm:$false }
        if (Test-Path $partial) { Remove-Item $partial -Force -Confirm:$false }
    }
    $sizeMb = [math]::Round((Get-Item $final).Length / 1MB, 1)
    Write-Log "OFFSITE OK  $final  $sizeMb MB"

    # Keep only the newest $OffsiteKeep encrypted files. Only the off-site folder is pruned.
    Get-ChildItem $OffsiteDestination -File |
        Where-Object { $_.Name -match '^\d{8}-\d{6}\.tar\.age$' } |
        Sort-Object Name -Descending |
        Select-Object -Skip $OffsiteKeep |
        ForEach-Object {
            Remove-Item $_.FullName -Force -Confirm:$false
            Write-Log "OFFSITE  pruned $($_.Name)"
        }
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
        $snapshotDir = $latest.FullName
    } else {
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
        $snapshotDir = $target

        # 4. Keep only the newest $Keep backups (each one a real change).
        Get-ChildItem $Destination -Directory |
            Where-Object { $_.Name -match '^\d{8}-\d{6}$' } |
            Sort-Object Name -Descending |
            Select-Object -Skip $Keep |
            ForEach-Object {
                Remove-Item $_.FullName -Recurse -Force -Confirm:$false
                Write-Log "Pruned old backup $($_.Name)"
            }
    }
} catch {
    Write-Log "FAILED  $($_.Exception.Message)"
    exit 1
}

# 5. Off-site encrypted copy (QW-6). Runs after a new snapshot, and also after a
#    skipped run if the newest snapshot isn't off-site yet (catch-up).
if (-not $NoOffsite) {
    try {
        Write-Offsite $snapshotDir
    } catch {
        Write-Log "OFFSITE FAILED  $($_.Exception.Message)"
        exit 2
    }
}
exit 0
