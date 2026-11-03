# Verification record

Verified on **October 20, 2026 (America/Denver)** on the user’s Windows computer. Counts change as applications and sockets change. This is a functional verification record, not a certification that the computer is secure.

## Executed successfully

| Check | Actual result |
| --- | --- |
| Environment | Docker Desktop 4.54.0, Docker Engine 29.1.2, desktop-linux context, Microsoft WSL2 kernel. Windows PowerShell collector cmdlets were available. |
| Windows collector | Real TCP/UDP, interface, neighbor-cache, process/service and ActiveStore firewall-profile reads succeeded. Initial collection took about 8 seconds; subsequent collections typically took about 1.5–5 seconds. |
| Transport | Authenticated Windows loopback upload reached the real Docker API. Host bind mounting had shown an empty directory in the initial environment test, so the final deployment does not depend on a host-folder mount. |
| Docker runtime | Image built and container became healthy. Published endpoint was 127.0.0.1:9090, user 10001:10001, read-only filesystem, all capabilities dropped. No host mount or Docker socket. |
| Live freshness | `/api/snapshot` returned mode `live`, recent collected timestamps and stale=false. It did not substitute demonstration data. |
| End-to-end listener test | `scripts/Verify-Portlight.ps1` opened a temporary loopback TCP listener on OS-assigned port 56160. The collector → authenticated upload → Docker analysis API path reported it with loopback scope and info priority. After closing and recollecting, it disappeared. |
| Automated application/API tests | **14 tests passed** on local Python 3.11.7 and separately inside the Python 3.13 Linux Docker verification image. |
| Browser overview | Real host endpoint/connection counts, review queue, collector status and multi-snapshot activity trend rendered in the embedded browser. |
| Browser finding details | Opened the actual MySQL-port review finding and confirmed evidence, confidence, rationale and manual hardening guidance. |
| Browser filters | Combined a visible process search with low priority, TCP and public-remote scope; one matching connection remained. Reset restored the full view. |
| Browser device/service view | SQL search found the observed Windows SQL service/process mapping. Non-applicable filters were disabled. |
| Demo mode | Prominent synthetic-data banner, synthetic host, demo API mode and empty fabricated-history-free activity view. Returning to live restored actual telemetry. |
| Pause/freshness UI | Paused refresh while the collector kept running. At 77 seconds of displayed snapshot age, the browser explicitly showed `Collector stale` and `STALE SNAPSHOT`. Resuming restored a fresh observation. |
| Background lifecycle | Started a hidden managed collector, stopped it with `Stop-Portlight.ps1`, verified the process record and container were gone, then restarted successfully in background mode. No login task was installed. |
| JavaScript | `node --check app/static/app.js` passed. |

The application/API tests include IPv4 and IPv6 scope handling (including mapped loopback), conservative vulnerability/exposure claims, inbound matching, partial/stale data, disabled firewall profiles, schema failures, blocked file paths, Host-header protection, rejected unauthenticated/browser-origin uploads, successful authenticated in-memory ingestion, demo isolation and history behavior.

## Real observations deserving human review

- Non-loopback listeners were observed on ports **135, 139, 445, 1433 and 3306**. The owning process names included `svchost`/`System`, `sqlservr` and `mysqld`. Multiple address bindings are grouped into five service review findings while the inventory preserves individual endpoints.
- These findings do **not** prove the services are unnecessary, accessible from the internet or running vulnerable versions. Some bindings were virtual or link-local interfaces. The user must assess dependencies and intended access before hardening.
- Domain, Private and Public Windows firewall profiles all reported **enabled**, default inbound **Block**, and default outbound **Allow**. Effective per-application and per-port rules were not evaluated.
- Some executable paths were unavailable, particularly for system/protected/exited process rows. These visibility gaps appeared in the UI. The computer’s changing live connections were not classified as malicious.

No hostnames, IP lists, full exports or raw telemetry are recorded in this source-controlled report. The screenshot in `docs/dashboard-demo.png` shows explicitly synthetic data.

## Untested or outside this scope

- **Actual internet reachability was not tested.** No public-IP lookup, router inspection, port-forward/UPnP evaluation, off-network test, remote host scan or subnet service scan occurred.
- No packet capture, UDP-flow analysis, bandwidth measurement, DNS resolution, encrypted content inspection, threat-intelligence query, software-version inventory, CVE feed matching, exploit test or comprehensive malware detection was performed.
- No hardening was applied. Remediation effectiveness and the impact of any future user changes remain untested.
- The embedded browser was inspected at its available narrow viewport. Layout is responsive by CSS, but a full matrix of browsers, screen sizes, assistive technologies and operating systems was not tested.
- The JSON export button was exercised in demo mode; the embedded browser did not provide a saved-file location in the default Windows Downloads folder. Saved-file delivery was not independently captured. Verify downloads in a regular browser if needed for class submission.
- Waiting-for-collector and corrupt-data states were verified by API tests; the initial missing-mount live environment also visibly showed the waiting state. Not every Windows cmdlet permission/failure combination was induced on the real host.
- No third-party firewall, VPN, domain-policy, router/IPv6 perimeter or container-image vulnerability audit was completed. A healthy web container is separate from healthy/fresh collection.

## State left for handoff

The Docker dashboard and a managed background Windows collector are running locally. Open http://127.0.0.1:9090. Use `scripts/Stop-Portlight.ps1` to stop both, and `scripts/Start-Portlight.ps1 -BackgroundCollector` to start them again. Runtime telemetry, collector configuration and logs live under `%LOCALAPPDATA%\Portlight`. No public site was published.
