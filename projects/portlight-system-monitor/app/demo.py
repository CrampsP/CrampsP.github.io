"""Explicit demonstration only. Never used as a fallback for missing live telemetry."""
from datetime import datetime, timezone

def demo_snapshot():
    return dict(schema_version=1, collected_at=datetime.now(timezone.utc).isoformat(),
        interval_seconds=10, host='DEMO-WORKSTATION · synthetic data', collection_duration_ms=640,
        listeners=[
            dict(protocol='TCP', local_address='0.0.0.0', local_port=3389, pid=1040, process_name='svchost', process_path='C:\\Windows\\System32\\svchost.exe', services=['TermService'], state='Listen'),
            dict(protocol='TCP', local_address='127.0.0.1', local_port=9090, pid=2220, process_name='docker-backend', process_path='', services=[], state='Listen'),
            dict(protocol='TCP', local_address='0.0.0.0', local_port=8080, pid=8210, process_name='python', process_path='C:\\Demo\\python.exe', services=[], state='Listen'),
            dict(protocol='UDP', local_address='0.0.0.0', local_port=5353, pid=6110, process_name='browser', process_path='', services=[], state='Bound')],
        connections=[
            dict(protocol='TCP', local_address='192.168.50.10', local_port=51001, remote_address='1.1.1.1', remote_port=443, state='Established', pid=6110, process_name='browser', process_path='C:\\Demo\\browser.exe', services=[]),
            dict(protocol='TCP', local_address='192.168.50.10', local_port=51002, remote_address='8.8.8.8', remote_port=4444, state='Established', pid=7330, process_name='powershell', process_path='C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe', services=[])],
        interfaces=[dict(address='192.168.50.10', prefix_length=24, alias='Demo Ethernet', family='IPv4')],
        neighbors=[dict(address='192.168.50.1', mac='02-00-00-00-00-01', state='Reachable', interface='Demo Ethernet')],
        firewall_profiles=[dict(name='Public', enabled=True, default_inbound='Block', default_outbound='Allow')],
        active_profiles=['Public'], errors=[])
