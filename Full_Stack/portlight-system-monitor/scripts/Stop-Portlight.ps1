#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$previousToken = $env:PORTLIGHT_INGEST_TOKEN
$tokenPath = Join-Path $env:LOCALAPPDATA 'Portlight\collector.key'
$pidPath = Join-Path $env:LOCALAPPDATA 'Portlight\collector-process.json'
if (Test-Path -LiteralPath $pidPath) {
    $record = Get-Content -LiteralPath $pidPath -Raw | ConvertFrom-Json
    $collector = Get-Process -Id $record.process_id -ErrorAction SilentlyContinue
    $expectedScript = Join-Path $PSScriptRoot 'Collect-Windows.ps1'
    if ($collector -and $record.script_path -eq $expectedScript -and $collector.StartTime.ToUniversalTime().Ticks.ToString() -eq $record.start_ticks) {
        $processDetails = Get-CimInstance Win32_Process -Filter ('ProcessId = ' + [int]$record.process_id)
        if ($processDetails.CommandLine.IndexOf($expectedScript, [StringComparison]::OrdinalIgnoreCase) -ge 0) { Stop-Process -Id $collector.Id }
    }
    Remove-Item -LiteralPath $pidPath
}
if (-not (Test-Path -LiteralPath $tokenPath)) { throw 'No Portlight runtime configuration found.' }
$env:PORTLIGHT_INGEST_TOKEN = [System.IO.File]::ReadAllText($tokenPath).Trim()
Push-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
try { docker compose down; if ($LASTEXITCODE -ne 0) { throw 'Docker Compose did not stop successfully.' } }
finally { $env:PORTLIGHT_INGEST_TOKEN = $previousToken; Pop-Location }
Write-Host 'Dashboard and any managed background collector stopped. If you ran a foreground collector, stop that terminal with Ctrl+C.'
