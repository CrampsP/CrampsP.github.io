# Portlight

A local, Docker-based Windows host security dashboard for a human-in-the-loop class project. View it at **http://127.0.0.1:9090** after starting it. The dark dashboard provides review priorities, refreshing TCP connection tables, listening/bound endpoints, process and Windows service associations, passive device discovery, filters, JSON exports, and evidence with hardening recommendations.

The project observes the authorized computer. It does not change firewall settings, terminate processes, scan a subnet, or claim that an open port is a confirmed vulnerability.

## Start on Windows with Docker Desktop + WSL2

1. Start Docker Desktop in **Linux containers** mode. An internet connection is needed for the first Python base-image download. No Python or Node installation is required to run the Docker application.
2. Open **Windows PowerShell**, rather than a WSL terminal, and change to this project directory:

   ```powershell
   Set-Location .\projects\portlight-system-monitor
   .\scripts\Start-Portlight.ps1
   ```

3. Open **http://127.0.0.1:9090**. Leave the collector terminal running. The first collection may take several seconds. The container restarts automatically with Docker, but fresh Windows telemetry requires the collector.
4. If Windows execution policy blocks these local scripts, review them first, then use a session-only policy in that PowerShell window:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\scripts\Start-Portlight.ps1
   ```

   This affects only that PowerShell process. The project does not change execution policy automatically. Start without elevation; inaccessible process paths and collection failures are explicitly shown. An administrator terminal may provide more visibility, but is optional and still cannot guarantee visibility into every protected process.

If port 9090 is already in use, run ` .\scripts\Start-Portlight.ps1 -Port 9091` and open the printed address. The selected endpoint is remembered under local AppData.

To stop, press **Ctrl+C** in the collector terminal, then run:

```powershell
.\scripts\Stop-Portlight.ps1
```

To resume a collector with an already-running container:

```powershell
.\scripts\Collect-Windows.ps1
```

The starter can be rerun to rebuild/restart the entire project. The container stores only in-memory telemetry and history; restarting it clears these until the collector uploads again. The collector overwrites its local `latest.json`, rather than accumulating a disk history.

For a managed background collector instead of a foreground terminal, use `.\scripts\Start-Portlight.ps1 -BackgroundCollector`. It opens no interactive window, records only its process identity under local AppData, and is stopped by `Stop-Portlight.ps1`. Logs are overwritten on each background launch; for long sessions use foreground mode to avoid accumulating terminal logs. No login startup task is installed. Do not run foreground and background collectors at the same time.

## What the dashboard includes

| Navigation | Function |
| --- | --- |
| Overview | Review counts, non-loopback endpoint counts, public remote connections, collection gaps and a session activity trend. No invented security score. |
| Security findings | Explainable priority, observed evidence, confidence, reasoning and suggested human review/hardening steps. |
| Listening ports | TCP listeners and UDP bindings, addresses, PID, process path when available, port-based service hints, and associated observed Windows services. |
| Connections | TCP local/remote endpoints, state, process, inferred direction and first observation in the current server session. |
| Devices & services | Local interfaces, the Windows neighbor cache and local service/process mappings. Neighbor entries can be stale, virtual or multicast. |
| Evidence & limits | Definitions, rule criteria, blind spots, assumptions and the effects of the two human answers. |

Search process names, ports, addresses and service text. Filter the relevant views by priority, protocol and address scope; use Reset to clear filters. Disabled controls do not apply to that view. Refresh manually or pause automatic refresh. An age indicator continues updating while paused and marks old data stale. Export downloads a JSON snapshot with an explicit `live` or `demo` label.

**Explore demo** is a deliberate, separate mode with a prominent synthetic-data banner. Demo data is never substituted when real collection fails. Its connection history is empty because it is not a real time series. Return to live data before interpreting your computerâ€™s status.

## Architecture and scope

```text
Windows socket/process/service/firewall APIs (read-only)
        |
Collect-Windows.ps1 in Windows PowerShell
        |-- overwrites %LOCALAPPDATA%\Portlight\data\latest.json
        |
        +-- authenticated HTTP upload to 127.0.0.1:<port>/api/ingest
                    |
            Docker Desktop / WSL2 Linux container
            Python standard-library server + explainable rules
                    |
            local browser dashboard (polls every 5 seconds)
```

Docker Desktopâ€™s Linux VM does not provide a complete Windows socket/process inventory. A native Windows collector is necessary. Authenticated loopback uploads also avoid relying on Windows directory mounts, which did not show host files in this environment during verification. The Docker dashboard has **no host directories mounted, no Docker socket, no privileged mode, no shell-control API and no host network mode**.

The container runs as UID/GID 10001, with a read-only filesystem, all Linux capabilities dropped, no-new-privileges and resource/log limits. Compose publishes only `127.0.0.1`, not all network interfaces. It serves local static assets without CDN libraries, external fonts, analytics or cloud telemetry. Do not expose this single-user dashboard through a LAN binding, public tunnel or reverse proxy without adding suitable access control.

`Start-Portlight.ps1` creates a random 256-bit collector token in `%LOCALAPPDATA%\Portlight\collector.key` and supplies it to Docker through an environment variable. It is never embedded in browser JavaScript or printed. Uploads require that token, a valid bounded JSON snapshot and a local Host header; requests with a browser Origin are rejected. There are no cross-origin permissions. Local OS users can view the dashboard; Docker administrators can inspect container environment variables. This token is not a defense against a compromised host or privileged local user.

Runtime files live under `%LOCALAPPDATA%\Portlight`, outside this OneDrive project by default. The project `.env` contains only the selected dashboard port. Do not share runtime files or full exports casually: they include hostnames, local/remote IPs, PIDs and executable paths. This program collects no command lines, passwords or packet payloads. Discovery is limited to the current host and its existing neighbor cache; no remote devices are queried or scanned.

## How findings are prioritized

Priorities describe **review order**, not confirmed exploitability or CVSS scores. Listener findings with the same protocol, PID and port are grouped across addresses. Endpoint counts still count individual bindings.

| Priority | Evidence / rule | Interpretation |
| --- | --- | --- |
| High | A non-loopback endpoint on ports 21, 23, 135, 139, 445, 1433, 2375, 3306, 3389, 5432, 5900, 6379 or 27017. Or an ActiveStore firewall profile reports disabled and matches an active network profile. | Common sensitive services deserve an early necessity and access review. Port identity and external reachability remain unverified. |
| Medium | Other non-loopback TCP listeners or lower-range UDP bindings; likely outbound established/SynSent TCP from a common Windows script host to a public address; or an inactive firewall profile is disabled. | Review with application and environment context. A UDP binding is not proof of a listening server. |
| Low | Other likely outbound established/SynSent TCP to a public address on a port outside the common-egress list. | A low-confidence prompt to identify the application; many legitimate apps use uncommon ports. |
| Info | An observation with no matching review rule, including loopback endpoints and dynamic UDP bindings (49152â€“65535). | Still visible in inventory. Info does not mean safe. |

The common-egress list is 53, 80, 123, 443, 465, 587, 853, 993, 995, 3478 and 5228. Script hosts are powershell, pwsh, cmd, wscript, cscript and mshta. These simple rules are transparent and intentionally do not claim to detect malware. A public IP alone, a new destination alone, or a missing executable path does not trigger a malicious-connection verdict. The rule code is in `app/analysis.py`.

**Observed:** bindings, TCP state, reported owning PID, available process path, Windows service mapping and firewall profile configuration.

**Inferred:** conventional service labels from ports and likely direction from a same-PID/port/address listener match. No listener match is only evidence for likely outbound traffic; it is not reliable packet-level direction.

**Suspected:** a non-loopback service may expose attack surface; unusual/script-host egress may need investigation. Service necessity, malware and vulnerable versions are not established.

**Unverified:** actual internet exposure, effective filtering, router forwarding, UPnP, destination reputation and product/version-specific CVEs. **Confirmed CVE count is zero because no CVE assessment is performed**, not because the system has been proved free of vulnerabilities.

## Suggested human hardening workflow

1. Review the high-priority entries and their observed owning processes / Windows services. Confirm which applications you recognize and still need. Check dependencies before disabling services.
2. For locally used databases or development servers, use that applicationâ€™s documented configuration to restrict binding to loopback where practical. Ensure IPv4 and IPv6 are considered. Confirm the actual software and version before choosing product-specific instructions.
3. If a service must accept remote connections, open **Windows Defender Firewall with Advanced Security** (`wf.msc`) and review inbound rules by application, port, active profile and remote-address scope. This project does not evaluate rule precedence or make those changes for you.
4. Review your routerâ€™s forwarding / UPnP and remote-access configuration. A wildcard Windows listener may be blocked by a firewall or NAT; IPv6 also needs an appropriate perimeter review. Confirm public reachability only through a separate, explicitly authorized external test.
5. For an unexplained outbound connection, verify the process path and the application action that caused it. You can inspect a known executableâ€™s signature with `Get-AuthenticodeSignature -LiteralPath 'C:\path\to\program.exe'`; a signature alone does not prove safety. Review application/security logs and run a Windows Security scan if behavior remains unexplained.
6. Make your chosen changes, recollect, and confirm that the relevant listener/connection and application behavior changed as expected. No automated hardening is included.

## Functional verification

With the Docker dashboard already running, use a **second Windows PowerShell terminal**:

```powershell
.\scripts\Verify-Portlight.ps1
```

This creates a temporary loopback-only TCP listener on an OS-assigned port, collects Windows telemetry, confirms the listener appears in the real Docker API with loopback scope and info priority, closes it, recollects, and confirms it disappears. It also verifies demo labeling/isolation. It does not change firewall policy or send a probe to another device.

For application tests (optional local Python 3.11+):

```powershell
python -m unittest discover -s tests -v
```

Tests cover IPv4/IPv6 classification, inferred inbound handling, conservative risk assertions, partial/stale snapshots, disabled profiles, invalid schemas, read-only routes, Host-header protection, authenticated ingestion, rejected browser/unauthorized uploads, demo isolation and bounded/deduplicated session history.

Manual UI checks:

1. Open Connections; search for a visible process, change priority/protocol/scope, and Reset. Confirm the displayed result count matches the table.
2. Open a finding. Verify its evidence, confidence and recommended review steps. Close with the close button or Escape.
3. Pause automatic refresh. The age should keep increasing. Resume and confirm a fresh timestamp.
4. Stop the collector with Ctrl+C. After three configured intervals (at least 45 seconds), the dashboard must show **STALE SNAPSHOT**. The container health endpoint only checks the web server; telemetry freshness is a separate indicator.
5. Explore demo; verify its banner. Return to live data; no synthetic host should remain. Export a demo snapshot if a non-sensitive class example is needed.

For a Docker-only app-test run, without a local Python installation:

```powershell
docker build --target verification -t portlight-verification .
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges:true --tmpfs /tmp portlight-verification
```

See `VERIFICATION.md` for what was actually tested in this environment and what remains untested.

## Monitoring limits and assumptions

- Local, single-user use on the userâ€™s Windows computer is the authorized scope. No subnet, router or public-IP scan is assumed authorized.
- Only this hostâ€™s services are discovered. Neighbors are passive cached entries; this is not complete whole-network service discovery or packet monitoring.
- Collection repeats every 10 seconds **plus collection time**, so short-lived sockets may be missed. `-IntervalSeconds` accepts 5â€“3600. The browser polls every 5 seconds and labels old data stale after `max(45, 3 Ã— interval)` seconds.
- UDP flow direction, packet contents, bandwidth, DNS names, TLS contents and destinationsâ€™ reputations are not collected. Conventional port labels may be wrong. Windows VPN/WSL/container traffic can appear under proxy/backend processes.
- Executable paths may be unavailable for protected, exited or system processes. TCP state and process/service queries are not atomic; PID reuse and socket churn can affect associations. Associated services in a shared process are not proven to own an individual socket.
- Firewall profile settings are not an effective per-port firewall analysis. Third-party security products, domain policy, rule precedence, network topology and perimeter policy are not evaluated.
- No software version/binary inventory, vulnerability feed, exploit test, CVE matching, content inspection or threat intelligence is included. Common-port malicious traffic may generate no finding. Zero findings cannot certify safety.
- Recent history is memory-only: at most 120 observed snapshots per server session and at most 5,000 first-seen destination keys. History only advances when the API reads a distinct uploaded snapshot; this is not a durable event log. First seen means first seen by this server, not the connectionâ€™s creation time.
- No automatic remediation, signature verification or Windows policy changes occur. You decide and execute hardening separately.

## How the two human answers shaped the result

**Answer 1 â€” Windows, Docker Desktop/WSL2, and â€œjust my computerâ€:** selected Windows-native read-only collection and a Linux-container dashboard, instead of assuming a Linux host or scanning a network. It limited discovery to the computer and its passive cache, kept the interface on loopback, and prevented container-local sockets from being misrepresented as the host inventory.

**Answer 2 â€” internet exposure, unnecessary listeners, suspicious outbound traffic; dark mode, summary, live tables and filters; self-directed hardening:** selected those review categories, an explicit unverified-internet-exposure label, the dark six-view dashboard, filtering/refresh/export controls and explanatory findings. Hardening is guidance, not automatic action.

The humanâ€™s scope decision reduced unauthorized collection; platform details improved technical correctness; stated priorities improved usefulness; and reserving hardening decisions for the user made uncertainty visible and preserved oversight. Exactly two clarification questions were asked before implementation. Remaining assumptions are documented here and in the dashboard.

## Primary references

- [Microsoft Get-NetTCPConnection](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-nettcpconnection): source of socket state, endpoint and PID observations.
- [Microsoft Get-NetUDPEndpoint](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-netudpendpoint): local UDP endpoint collection.
- [Microsoft Get-NetFirewallProfile](https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallprofile): profile-level settings, not a complete effective rule evaluation.
- [Microsoft Windows Firewall configuration](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/configure): human firewall review.
- [Docker Desktop networking](https://docs.docker.com/desktop/features/networking/): host/VM/backend separation and published-port behavior.
