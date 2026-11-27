# Back up all of drive E: to D:\E-Backup.
# Usage: .\backup-e-drive.ps1 [-Source E:\] [-Destination D:\E-Backup]
#
# Copies new and changed files only. It deliberately never deletes anything
# from the backup: a true mirror (/MIR) would also delete from the backup any
# file deleted or wiped on E:, which defeats the point of having one. Files
# deleted from E: therefore stay on D: until you remove them yourself.
#
# Files that are locked while the copy runs are skipped and picked up on the
# next run. Registered as the weekly (Sunday 4 AM) "E Drive Backup to D" scheduled task.
# A per-run log is written to D:\E-Backup-logs; summary lines go to summary.log.

param(
    [string]$Source = 'E:\',
    [string]$Destination = 'D:\E-Backup',
    [string]$LogDir = 'D:\E-Backup-logs',
    [int]$KeepLogs = 60
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Source)) { throw "Source $Source is not available." }
if (-not (Test-Path (Split-Path $Destination -Qualifier))) { throw "Backup drive for $Destination is not connected." }
New-Item -ItemType Directory -Force -Path $Destination, $LogDir | Out-Null

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$runLog = Join-Path $LogDir "robocopy-$stamp.log"
$summary = Join-Path $LogDir 'summary.log'

# /E all subfolders incl. empty   /XJ skip junctions (avoids loops)
# /COPY:DAT /DCOPY:DAT  data, attributes, timestamps   /R:1 /W:1 don't stall on locked files
# /MT:16 multithreaded   No /MIR or /PURGE: nothing is ever deleted from the backup.
$robocopyArgs = @(
    $Source, $Destination,
    '/E', '/XJ', '/COPY:DAT', '/DCOPY:DAT', '/R:1', '/W:1', '/MT:16',
    '/XD', (Join-Path $Source '$RECYCLE.BIN'), (Join-Path $Source 'System Volume Information'), (Join-Path $Source 'Config.Msi'),
    '/NP', '/NDL', '/TEE', "/UNILOG:$runLog"
)

$started = Get-Date
& robocopy @robocopyArgs | Out-Null
$code = $LASTEXITCODE

# Copying a drive root marks the destination folder hidden+system; undo that so it's visible.
& attrib -s -h $Destination 2>$null

$elapsed = [math]::Round(((Get-Date) - $started).TotalMinutes, 1)
# robocopy: 0-7 = success (1 = files copied, 2/3 = extras or mismatches), 8+ = some failures.
$status = if ($code -lt 8) { 'OK' } else { 'ERRORS' }
$line = "{0}  {1}  robocopy exit {2}  {3} min  log {4}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $status, $code, $elapsed, $runLog
Add-Content -Path $summary -Value $line -Encoding utf8
Write-Host $line

Get-ChildItem $LogDir -Filter 'robocopy-*.log' | Sort-Object Name -Descending | Select-Object -Skip $KeepLogs |
    Remove-Item -Force -Confirm:$false

# Some failures (e.g. a few locked or permission-protected files) are normal for a live drive;
# check the run log for "ERROR" lines. Exit non-zero only for robocopy's fatal code (16).
if ($code -ge 16) { exit 1 }
exit 0
