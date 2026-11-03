#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$runtimeDirectory = Join-Path $env:LOCALAPPDATA 'Portlight'
$endpointPath = Join-Path $runtimeDirectory 'endpoint.txt'
if (-not (Test-Path -LiteralPath $endpointPath)) { throw 'Start Portlight first with scripts/Start-Portlight.ps1.' }
$baseUrl = [System.IO.File]::ReadAllText($endpointPath).Trim()
$endpoint = [Uri]$baseUrl
if ($endpoint.Host -notin @('127.0.0.1','localhost','[::1]') -or $endpoint.Scheme -ne 'http') { throw 'Verification is restricted to local HTTP loopback.' }
$health = Invoke-RestMethod -Uri ($baseUrl + '/api/health') -TimeoutSec 5
if ($health.status -ne 'ok') { throw 'Dashboard health check failed.' }
$listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, 0)
try {
    $listener.Start()
    $testPort = $listener.LocalEndpoint.Port
    & (Join-Path $PSScriptRoot 'Collect-Windows.ps1') -Once
    $snapshot = Invoke-RestMethod -Uri ($baseUrl + '/api/snapshot') -TimeoutSec 5
    $matches = @($snapshot.listeners | Where-Object { $_.protocol -eq 'TCP' -and $_.local_port -eq $testPort -and $_.local_address -eq '127.0.0.1' })
    if ($snapshot.mode -ne 'live' -or $snapshot.stale -or $matches.Count -ne 1 -or $matches[0].scope -ne 'loopback' -or $matches[0].priority -ne 'info') { throw 'Loopback listener was not correctly observed in the live Docker dashboard.' }
    if ($snapshot.summary.internet_exposure -ne 'Unverified') { throw 'Internet exposure was overstated.' }
    Write-Host ('PASS: temporary loopback TCP port ' + $testPort + ' appeared with info priority, in live data.') -ForegroundColor Green
} finally { $listener.Stop() }
& (Join-Path $PSScriptRoot 'Collect-Windows.ps1') -Once
$after = Invoke-RestMethod -Uri ($baseUrl + '/api/snapshot') -TimeoutSec 5
if (@($after.listeners | Where-Object { $_.local_port -eq $testPort -and $_.local_address -eq '127.0.0.1' }).Count -ne 0) { throw 'Closed test listener was still present.' }
$demo = Invoke-RestMethod -Uri ($baseUrl + '/api/snapshot?mode=demo') -TimeoutSec 5
if ($demo.mode -ne 'demo' -or $demo.host -notlike 'DEMO*' -or $demo.history.Count -ne 0) { throw 'Demo labeling / isolation failed.' }
Write-Host 'PASS: closed listener disappeared. Demo is explicitly labeled and isolated. No firewall settings changed.' -ForegroundColor Green
