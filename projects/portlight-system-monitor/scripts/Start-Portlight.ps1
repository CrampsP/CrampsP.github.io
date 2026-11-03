#requires -Version 5.1
[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port = 9090, [switch]$BackgroundCollector)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDirectory = Join-Path $env:LOCALAPPDATA 'Portlight'
$dataDirectory = Join-Path $runtimeDirectory 'data'
$null = New-Item -ItemType Directory -Path $dataDirectory -Force
$tokenPath = Join-Path $runtimeDirectory 'collector.key'
if (-not (Test-Path -LiteralPath $tokenPath)) {
    $bytes = New-Object byte[] 32
    $random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $random.GetBytes($bytes) } finally { $random.Dispose() }
    $token = -join ($bytes | ForEach-Object { $_.ToString('x2') })
    [System.IO.File]::WriteAllText($tokenPath, $token)
}
$previousToken = $env:PORTLIGHT_INGEST_TOKEN
$env:PORTLIGHT_INGEST_TOKEN = [System.IO.File]::ReadAllText($tokenPath).Trim()
Set-Content -LiteralPath (Join-Path $projectRoot '.env') -Encoding ASCII -Value ('PORTLIGHT_PORT=' + $Port)
Set-Content -LiteralPath (Join-Path $runtimeDirectory 'endpoint.txt') -Encoding ASCII -Value ('http://127.0.0.1:' + $Port)
Push-Location -LiteralPath $projectRoot
try {
    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose failed. Start Docker Desktop in Linux container mode and retry.' }
    Write-Host ('Dashboard: http://127.0.0.1:' + $Port) -ForegroundColor Cyan
    if ($BackgroundCollector) {
        $pidPath = Join-Path $runtimeDirectory 'collector-process.json'
        $existing = $null
        if (Test-Path -LiteralPath $pidPath) {
            $record = Get-Content -LiteralPath $pidPath -Raw | ConvertFrom-Json
            $existing = Get-Process -Id $record.process_id -ErrorAction SilentlyContinue
            if ($existing -and $existing.StartTime.ToUniversalTime().Ticks.ToString() -ne $record.start_ticks) { $existing = $null }
        }
        if ($existing) { Write-Host 'Managed background collector is already running.' }
        else {
            $collectorPath = Join-Path $PSScriptRoot 'Collect-Windows.ps1'
            $collector = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-File',('"' + $collectorPath + '"')) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeDirectory 'collector.log') -RedirectStandardError (Join-Path $runtimeDirectory 'collector-errors.log') -PassThru
            @{process_id=$collector.Id; start_ticks=$collector.StartTime.ToUniversalTime().Ticks.ToString(); script_path=$collectorPath} | ConvertTo-Json | Set-Content -LiteralPath $pidPath -Encoding UTF8
            Write-Host 'Collector started in the background. Use scripts/Stop-Portlight.ps1 to stop it.'
        }
    } else {
        Write-Host 'Starting Windows collector in this terminal. Ctrl+C stops collection; Docker stays running.'
        & (Join-Path $PSScriptRoot 'Collect-Windows.ps1') -OutputDirectory $dataDirectory
    }
} finally { $env:PORTLIGHT_INGEST_TOKEN = $previousToken; Pop-Location }
