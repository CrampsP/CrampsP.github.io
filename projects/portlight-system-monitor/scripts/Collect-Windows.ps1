#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$OutputDirectory = (Join-Path $env:LOCALAPPDATA 'Portlight\data'),
    [ValidateRange(5, 3600)][int]$IntervalSeconds = 10,
    [switch]$Once,
    [switch]$NoPublish
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Run this collector in Windows PowerShell, not inside WSL or a container.' }
$null = New-Item -ItemType Directory -Path $OutputDirectory -Force
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path
$targetFile = Join-Path $OutputDirectory 'latest.json'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$runtimeDirectory = Join-Path $env:LOCALAPPDATA 'Portlight'
$tokenPath = Join-Path $runtimeDirectory 'collector.key'
$endpointPath = Join-Path $runtimeDirectory 'endpoint.txt'
$publishUrl = 'http://127.0.0.1:9090'
if (Test-Path -LiteralPath $endpointPath) { $publishUrl = [System.IO.File]::ReadAllText($endpointPath).Trim() }
$endpoint = [Uri]$publishUrl
if ($endpoint.Scheme -ne 'http' -or $endpoint.Host -notin @('127.0.0.1','localhost','[::1]')) { throw 'Collector upload is restricted to local HTTP loopback.' }
$collectorToken = $null
if (Test-Path -LiteralPath $tokenPath) { $collectorToken = [System.IO.File]::ReadAllText($tokenPath).Trim() }
Write-Host 'Portlight: read-only Windows socket collector. Ctrl+C stops monitoring.' -ForegroundColor Cyan
Write-Host ('Telemetry stays in: ' + $OutputDirectory)
Write-Host 'No network scan, firewall changes, packet capture, or external lookups.'

function Get-Snapshot {
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    $gaps = New-Object 'System.Collections.Generic.List[string]'
    $processMap = @{}
    $serviceMap = @{}
    try {
        Get-Process -ErrorAction Stop | ForEach-Object {
            $executablePath = $null
            try { $executablePath = $_.Path } catch { }
            $processMap[[int]$_.Id] = @{ process_name = [string]$_.ProcessName; process_path = $executablePath }
        }
    } catch { $gaps.Add('Process enumeration failed: ' + $_.Exception.Message) }
    try {
        Get-CimInstance -ClassName Win32_Service -Filter 'ProcessId > 0' -ErrorAction Stop | ForEach-Object {
            $ownerId = [int]$_.ProcessId
            if (-not $serviceMap.ContainsKey($ownerId)) { $serviceMap[$ownerId] = @() }
            $serviceMap[$ownerId] += [string]$_.Name
        }
    } catch { $gaps.Add('Windows service mapping unavailable: ' + $_.Exception.Message) }

    function Get-Identity([int]$OwnerId) {
        $name = 'Unknown / exited'
        $path = $null
        if ($processMap.ContainsKey($OwnerId)) {
            $name = $processMap[$OwnerId].process_name
            $path = $processMap[$OwnerId].process_path
        }
        $services = @()
        if ($serviceMap.ContainsKey($OwnerId)) { $services = @($serviceMap[$OwnerId]) }
        return @{ process_name=$name; process_path=$path; services=$services }
    }

    $listeners = @()
    $connections = @()
    try {
        $tcpRows = @(Get-NetTCPConnection -ErrorAction Stop)
        foreach ($socket in $tcpRows) {
            $identity = Get-Identity ([int]$socket.OwningProcess)
            $row = @{
                protocol='TCP'; local_address=[string]$socket.LocalAddress; local_port=[int]$socket.LocalPort
                pid=[int]$socket.OwningProcess; process_name=$identity.process_name
                process_path=$identity.process_path; services=@($identity.services); state=[string]$socket.State
            }
            if ([string]$socket.State -eq 'Listen') { $listeners += $row }
            elseif ([string]$socket.State -ne 'Bound') {
                $row.remote_address = [string]$socket.RemoteAddress
                $row.remote_port = [int]$socket.RemotePort
                $connections += $row
            }
        }
    } catch { $gaps.Add('TCP socket collection failed: ' + $_.Exception.Message) }
    try {
        foreach ($socket in @(Get-NetUDPEndpoint -ErrorAction Stop)) {
            $identity = Get-Identity ([int]$socket.OwningProcess)
            $listeners += @{
                protocol='UDP'; local_address=[string]$socket.LocalAddress; local_port=[int]$socket.LocalPort
                pid=[int]$socket.OwningProcess; process_name=$identity.process_name
                process_path=$identity.process_path; services=@($identity.services); state='Bound'
            }
        }
    } catch { $gaps.Add('UDP endpoint collection failed: ' + $_.Exception.Message) }

    $interfaces = @()
    try {
        $interfaces = @(Get-NetIPAddress -ErrorAction Stop | ForEach-Object {
            @{address=[string]$_.IPAddress; prefix_length=[int]$_.PrefixLength; alias=[string]$_.InterfaceAlias; family=[string]$_.AddressFamily}
        })
    } catch { $gaps.Add('Interface enumeration failed: ' + $_.Exception.Message) }
    $neighbors = @()
    try {
        $neighbors = @(Get-NetNeighbor -ErrorAction Stop | Where-Object { [string]$_.State -notin @('Unreachable','Incomplete') } | ForEach-Object {
            @{address=[string]$_.IPAddress; mac=[string]$_.LinkLayerAddress; state=[string]$_.State; interface=[string]$_.InterfaceAlias}
        })
    } catch { $gaps.Add('Passive neighbor cache unavailable: ' + $_.Exception.Message) }
    $profiles = @()
    try {
        $profiles = @(Get-NetFirewallProfile -PolicyStore ActiveStore -ErrorAction Stop | ForEach-Object {
            @{name=[string]$_.Name; enabled=([string]$_.Enabled -eq 'True'); default_inbound=[string]$_.DefaultInboundAction; default_outbound=[string]$_.DefaultOutboundAction}
        })
    } catch { $gaps.Add('Firewall profiles unavailable: ' + $_.Exception.Message) }
    $activeProfiles = @()
    try {
        $activeProfiles = @(Get-NetConnectionProfile -ErrorAction Stop | ForEach-Object {
            if ([string]$_.NetworkCategory -eq 'DomainAuthenticated') { 'Domain' } else { [string]$_.NetworkCategory }
        } | Select-Object -Unique)
    } catch { $gaps.Add('Active network profiles unavailable: ' + $_.Exception.Message) }
    $watch.Stop()
    return @{
        schema_version=1; host=$env:COMPUTERNAME; collected_at=[DateTime]::UtcNow.ToString('o')
        interval_seconds=$IntervalSeconds; collection_duration_ms=$watch.ElapsedMilliseconds
        listeners=@($listeners); connections=@($connections); interfaces=@($interfaces)
        neighbors=@($neighbors); firewall_profiles=@($profiles); active_profiles=@($activeProfiles); errors=@($gaps.ToArray())
    }
}

do {
    $snapshot = Get-Snapshot
    $json = ConvertTo-Json -InputObject $snapshot -Depth 10 -Compress
    $temporaryFile = Join-Path $OutputDirectory ('snapshot-' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [System.IO.File]::WriteAllText($temporaryFile, $json, $utf8)
        # Atomic replacement keeps readers from seeing a half-written JSON document.
        if ([System.IO.File]::Exists($targetFile)) { [System.IO.File]::Replace($temporaryFile, $targetFile, [System.Management.Automation.Language.NullString]::Value) }
        else { [System.IO.File]::Move($temporaryFile, $targetFile) }
    } finally {
        if (Test-Path -LiteralPath $temporaryFile) { Remove-Item -LiteralPath $temporaryFile }
    }
    Write-Host ('{0} | {1} endpoints | {2} connections | {3} collection gaps | {4} ms' -f $snapshot.collected_at, $snapshot.listeners.Count, $snapshot.connections.Count, $snapshot.errors.Count, $snapshot.collection_duration_ms)
    if (-not $NoPublish) {
        if ($collectorToken) {
            try {
                $null = Invoke-RestMethod -Uri ($publishUrl + '/api/ingest') -Method Post -ContentType 'application/json; charset=utf-8' -Headers @{Authorization=('Bearer ' + $collectorToken)} -Body $utf8.GetBytes($json) -TimeoutSec 10 -ErrorAction Stop
            } catch { Write-Warning 'Local dashboard upload failed. Snapshot saved locally; check Docker and rerun Start-Portlight.ps1.' }
        } else { Write-Warning 'No collector token yet. Run scripts/Start-Portlight.ps1 to connect to Docker, or use -NoPublish for file-only collection.' }
    }
    if (-not $Once) { Start-Sleep -Seconds $IntervalSeconds }
} while (-not $Once)
