"""Explainable, conservative rules for observed Windows socket metadata."""
from collections import Counter
from datetime import datetime, timezone
import ipaddress

SERVICE_HINTS = {21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS', 80: 'HTTP',
    135: 'RPC', 139: 'NetBIOS', 443: 'HTTPS', 445: 'SMB', 1433: 'SQL Server',
    2375: 'Docker API (usually plaintext)', 2376: 'Docker API (usually TLS)',
    3306: 'MySQL', 3389: 'Remote Desktop', 5432: 'PostgreSQL', 5900: 'VNC',
    6379: 'Redis', 8000: 'HTTP alternative', 8080: 'HTTP alternative',
    8443: 'HTTPS alternative', 9090: 'Portlight / alternative service', 27017: 'MongoDB',
    1900: 'SSDP', 5353: 'mDNS', 5355: 'LLMNR'}
SENSITIVE = {21, 23, 135, 139, 445, 1433, 2375, 3306, 3389, 5432, 5900, 6379, 27017}
COMMON_EGRESS = {53, 80, 123, 443, 465, 587, 853, 993, 995, 3478, 5228}
SCRIPT_HOSTS = {'powershell', 'pwsh', 'cmd', 'wscript', 'cscript', 'mshta'}
RANK = {'high': 0, 'medium': 1, 'low': 2, 'info': 3}


def address_scope(value):
    try:
        ip = ipaddress.ip_address(str(value).split('%')[0])
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        if ip.is_unspecified: return 'wildcard'
        if ip.is_loopback: return 'loopback'
        if ip.is_multicast: return 'multicast'
        if ip.is_link_local: return 'link-local'
        # is_global alone includes shared-space nuances; public means globally routable.
        if ip.is_global and not ip.is_reserved: return 'public'
        return 'private / special'
    except ValueError:
        return 'unknown'


def snapshot_age(value, now=None):
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if stamp.tzinfo is None: return None
        return max(0, ((now or datetime.now(timezone.utc)) - stamp).total_seconds())
    except (ValueError, TypeError, AttributeError):
        return None


def endpoint(address, port):
    return f'[{address}]:{port}' if ':' in str(address) else f'{address}:{port}'


def validate_snapshot(raw):
    if not isinstance(raw, dict) or raw.get('schema_version') != 1:
        raise ValueError('Unsupported or missing snapshot schema_version (expected 1).')
    for name in ('listeners', 'connections', 'interfaces', 'neighbors', 'firewall_profiles', 'errors'):
        if not isinstance(raw.get(name), list):
            raise ValueError(f'{name} must be an array.')
        if len(raw[name]) > 50000:
            raise ValueError(f'{name} exceeds the 50,000 row limit.')
        if name != 'errors' and not all(isinstance(row, dict) for row in raw[name]):
            raise ValueError(f'{name} contains a non-object row.')
    if snapshot_age(raw.get('collected_at')) is None:
        raise ValueError('collected_at must be a timezone-aware ISO timestamp.')
    for row in raw['listeners'] + raw['connections']:
        if row.get('protocol') not in ('TCP', 'UDP'):
            raise ValueError('Unsupported socket protocol.')
        for key in ('local_port', 'pid'):
            value = row.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f'Invalid socket {key}.')
        if row['local_port'] > 65535:
            raise ValueError('Invalid local port.')
    for row in raw['connections']:
        port = row.get('remote_port')
        if not isinstance(port, int) or isinstance(port, bool) or not 0 <= port <= 65535:
            raise ValueError('Invalid remote port.')
    return raw


def analyze(raw, demo=False, first_seen=None):
    validate_snapshot(raw)
    findings, listeners, connections = [], [], []
    def finding(fid, title, priority, category, evidence, rationale, steps, confidence='medium', observed=False):
        findings.append(dict(id=fid, title=title, priority=priority, category=category,
            evidence=evidence, rationale=rationale, remediation=steps, confidence=confidence,
            status='Observed configuration' if observed else 'Potential risk · needs review'))

    listener_keys = set()
    reported_listeners = set()
    for i, source in enumerate(raw['listeners']):
        row = dict(source)
        scope = address_scope(row.get('local_address'))
        row.update(scope=scope, service_hint=SERVICE_HINTS.get(row['local_port'], 'Unclassified'),
            internet_exposure='Unverified', priority='info')
        if row['protocol'] == 'TCP':
            listener_keys.add((row['pid'], row['local_port'], row.get('local_address')))
        network_bound = scope not in ('loopback', 'unknown')
        # Dynamic UDP bindings often represent clients, not remotely accessible services.
        review_binding = network_bound and (row['protocol'] == 'TCP' or row['local_port'] < 49152)
        if review_binding:
            sensitive = row['local_port'] in SENSITIVE
            row['priority'] = 'high' if sensitive else 'medium'
            group_key = (row['protocol'], row['pid'], row['local_port'])
            if group_key in reported_listeners:
                listeners.append(row)
                continue
            reported_listeners.add(group_key)
            bindings = [endpoint(r.get('local_address'), r['local_port']) for r in raw['listeners']
                if (r['protocol'], r['pid'], r['local_port']) == group_key
                and address_scope(r.get('local_address')) not in ('loopback','unknown')]
            evidence = f"{row['protocol']} {', '.join(bindings)} {'listening' if row['protocol']=='TCP' else 'bound'}; process {row.get('process_name', 'unknown')} (PID {row['pid']})."
            finding(f"listener-{row['protocol']}-{row['pid']}-{row['local_port']}", f"Review {row['service_hint']} on port {row['local_port']}",
                row['priority'], 'Listening ports', evidence,
                'A non-loopback binding may accept traffic from other interfaces. This is a review priority, not proof of internet reachability, a vulnerable version, or an unnecessary service.',
                ['Confirm this process and associated Windows services are needed before changing anything.',
                 'If local use is sufficient, configure the application to bind only to 127.0.0.1 and/or ::1.',
                 'If remote access is needed, review inbound rules in wf.msc; restrict the program, profiles and remote addresses. Check IPv4 and IPv6.',
                 'Review router port forwarding / UPnP and remote-access settings yourself. Recollect after changes; external reachability requires a separately authorized off-network test.'])
        listeners.append(row)

    missing_identity = 0
    for i, source in enumerate(raw['connections']):
        row = dict(source)
        remote_scope = address_scope(row.get('remote_address'))
        local_address = str(row.get('local_address', ''))
        wildcard = '::' if ':' in local_address else '0.0.0.0'
        inbound_match = any((row['pid'], row['local_port'], addr) in listener_keys
                            for addr in (local_address, wildcard))
        direction = 'Likely inbound' if inbound_match else 'Likely outbound'
        if row.get('state') not in ('Established', 'SynSent', 'CloseWait', 'FinWait1', 'FinWait2'):
            direction = 'Unknown'
        key = f"{row.get('process_name')}|{row.get('remote_address')}|{row.get('remote_port')}"
        row.update(remote_scope=remote_scope, direction=direction, priority='info',
            service_hint=SERVICE_HINTS.get(row.get('remote_port'), 'Unclassified'),
            first_seen=(first_seen or {}).get(key, raw['collected_at']))
        public_egress = remote_scope == 'public' and direction == 'Likely outbound' and row.get('state') in ('Established', 'SynSent')
        if not row.get('process_path'):
            missing_identity += 1
        if public_egress:
            name = str(row.get('process_name', '')).lower().removesuffix('.exe')
            script = name in SCRIPT_HOSTS
            unusual = row.get('remote_port') not in COMMON_EGRESS
            if script or unusual:
                row['priority'] = 'medium' if script else 'low'
                finding(f'egress-{i}', 'Review script-host egress' if script else 'Review uncommon outbound port',
                    row['priority'], 'Outbound connections',
                    f"{row.get('process_name', 'unknown')} (PID {row['pid']}) → {endpoint(row.get('remote_address'), row.get('remote_port'))}, {row.get('state')}; direction inferred from listener matching.",
                    'A script host contacting a public address deserves context.' if script else 'This remote port is outside a small common-egress list. Legitimate apps frequently use other ports; this signal does not establish malicious traffic.',
                    ['Confirm the application and the action that created this connection. A new destination alone is not suspicious.',
                     'Inspect the executable path and signature locally (Get-AuthenticodeSignature) and review the application’s own logs.',
                     'If unexplained, use Windows Security to run a scan and investigate before deciding whether to restrict that application’s outbound access.'], confidence='low')
        connections.append(row)

    active_profiles = set(raw.get('active_profiles', []))
    for profile in raw['firewall_profiles']:
        if str(profile.get('enabled')).lower() in ('false', '0'):
            active = profile.get('name') in active_profiles
            finding(f"firewall-{profile.get('name')}", f"{profile.get('name')} firewall profile is disabled",
                'high' if active else 'medium', 'Firewall posture',
                f"ActiveStore reports Enabled={profile.get('enabled')}; active profile match: {active}.",
                'The Windows firewall profile is disabled. Third-party controls and effective packet filtering are not assessed.',
                ['Review Windows Security → Firewall & network protection, including any third-party security product.',
                 'Enable the appropriate Windows firewall profile if consistent with your environment, then verify required applications still work.'],
                confidence='high', observed=True)
    errors = [str(e) for e in raw['errors']]
    gaps = len(errors) + (1 if missing_identity else 0)
    if not raw['firewall_profiles'] and not any('firewall' in e.lower() for e in errors):
        errors.append('Firewall profile information unavailable.')
        gaps += 1
    if missing_identity:
        errors.append(f'Executable paths unavailable for {missing_identity} connection rows; protected or exited processes are common causes.')
    findings.sort(key=lambda f: (RANK[f['priority']], f['title']))
    counts = Counter(f['priority'] for f in findings)
    age = snapshot_age(raw['collected_at'])
    stale_after = max(45, int(raw.get('interval_seconds', 10)) * 3)
    return dict(schema_version=1, mode='demo' if demo else 'live', host=raw.get('host', 'Windows host'),
        collected_at=raw['collected_at'], collection_duration_ms=raw.get('collection_duration_ms'),
        age_seconds=round(age, 1), stale=age > stale_after, stale_after_seconds=stale_after,
        listeners=listeners, connections=connections, findings=findings,
        interfaces=raw['interfaces'], neighbors=raw['neighbors'], firewall_profiles=raw['firewall_profiles'],
        active_profiles=list(active_profiles), errors=errors,
        summary=dict(high=counts['high'], medium=counts['medium'], low=counts['low'], findings=len(findings),
            network_listeners=sum(r['scope'] not in ('loopback','unknown') for r in listeners),
            public_connections=sum(r['remote_scope']=='public' for r in connections),
            established=sum(r.get('state')=='Established' for r in connections),
            visibility_gaps=gaps, internet_exposure='Unverified', confirmed_cves=0),
        limitations=[
            'A listening or bound socket is observed. Its necessity, exploitability and internet reachability are unverified.',
            'No packet capture, payload inspection, threat-intelligence lookup, CVE matching, remote scan or automatic remediation is performed.',
            'TCP direction is inferred from matching local listeners; socket churn, UDP flows and short-lived traffic limit visibility. Dynamic UDP bindings (ports 49152–65535) are inventoried but do not trigger generic service review.',
            'Neighbor entries are a passive Windows cache, not a complete network inventory. Only this Windows host’s services are collected.',
            'Firewall profiles are observed; per-rule precedence, application scope, third-party firewalls, NAT, router forwarding and IPv6 perimeter controls are not evaluated.',
            'Encrypted traffic can hide malicious behavior on common ports. No findings does not mean the computer is secure.'])
