import copy
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.analysis import address_scope, analyze, validate_snapshot
from app.demo import demo_snapshot
from app.server import SnapshotStore, make_handler


class AnalysisTests(unittest.TestCase):
    def test_non_loopback_is_not_confirmed_internet_exposure_or_cve(self):
        s = analyze(demo_snapshot())
        self.assertGreater(s['summary']['network_listeners'], 0)
        self.assertEqual(s['summary']['internet_exposure'], 'Unverified')
        self.assertEqual(s['summary']['confirmed_cves'], 0)
        self.assertTrue(all(f['status'].startswith('Potential') for f in s['findings']))
        self.assertFalse(any('9090' in f['title'] for f in s['findings']))

    def test_address_scopes_include_ipv6_and_ipv4_mapped(self):
        for value, expected in [('::1','loopback'),('::ffff:127.0.0.1','loopback'),
            ('0.0.0.0','wildcard'),('::','wildcard'),('192.168.1.2','private / special'),
            ('100.64.0.1','private / special'),('fe80::123%12','link-local'),
            ('224.0.0.1','multicast'),('2001:4860:4860::8888','public'),
            ('203.0.113.3','private / special'),('not-an-ip','unknown')]:
            with self.subTest(value=value): self.assertEqual(address_scope(value), expected)

    def test_listener_matching_avoids_flagging_inbound_as_script_egress(self):
        raw=demo_snapshot()
        raw['listeners'][0]['process_name']='powershell'
        row=copy.deepcopy(raw['connections'][1])
        row.update(pid=1040,local_port=3389)
        raw['connections']=[row]
        result=analyze(raw)
        self.assertEqual(result['connections'][0]['direction'],'Likely inbound')
        self.assertFalse(any(f['category']=='Outbound connections' for f in result['findings']))

    def test_common_https_is_not_automatically_malicious(self):
        result=analyze(demo_snapshot())
        browser=result['connections'][0]
        self.assertEqual(browser['priority'],'info')
        self.assertEqual(result['connections'][1]['priority'],'medium')
        self.assertTrue(any(f['confidence']=='low' for f in result['findings'] if f['category']=='Outbound connections'))

    def test_stale_and_partial_data_are_explicit(self):
        raw=demo_snapshot()
        raw['collected_at']=(datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat()
        raw['firewall_profiles']=[]
        raw['errors']=['TCP socket collection failed: access denied']
        result=analyze(raw)
        self.assertTrue(result['stale'])
        self.assertGreater(result['summary']['visibility_gaps'],0)
        self.assertTrue(any('TCP socket' in gap for gap in result['errors']))

    def test_disabled_firewall_is_observed_configuration(self):
        raw=demo_snapshot()
        raw['firewall_profiles'][0]['enabled']=False
        result=analyze(raw)
        finding=next(f for f in result['findings'] if f['category']=='Firewall posture')
        self.assertEqual(finding['priority'],'high')
        self.assertEqual(finding['status'],'Observed configuration')

    def test_reject_malformed_schema(self):
        for mutate in (lambda r:r.update(schema_version=2),lambda r:r.update(listeners={}),
                       lambda r:r.update(collected_at='yesterday'),
                       lambda r:r['listeners'][0].update(local_port=70000),
                       lambda r:r['connections'][0].update(remote_port='443')):
            raw=demo_snapshot();mutate(raw)
            with self.assertRaises(ValueError):validate_snapshot(raw)


class StoreTests(unittest.TestCase):
    def test_history_deduplication_and_demo_isolation(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'latest.json'
            raw=demo_snapshot()
            path.write_text(json.dumps(raw))
            store=SnapshotStore(folder)
            one=store.read()
            store.read()
            self.assertEqual(len(one['history']),1)
            self.assertEqual(len(store.history),1)
            demo=store.read(demo=True)
            self.assertEqual(demo['mode'],'demo')
            self.assertEqual(demo['history'],[])
            self.assertEqual(len(store.history),1)
            first=one['connections'][0]['first_seen']
            raw['collected_at']=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
            path.write_text(json.dumps(raw))
            two=store.read()
            self.assertEqual(len(two['history']),2)
            self.assertEqual(two['connections'][0]['first_seen'],first)

    def test_no_live_fallback_to_demo(self):
        with tempfile.TemporaryDirectory() as folder:
            store=SnapshotStore(folder)
            with self.assertRaises(FileNotFoundError):store.read()
            self.assertEqual(store.read(demo=True)['mode'],'demo')


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(SnapshotStore(self.folder.name)))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.folder.cleanup()

    def test_read_only_security_and_waiting_contract(self):
        with urlopen(self.base+'/') as response:
            self.assertEqual(response.status,200)
            self.assertEqual(response.headers['Cache-Control'],'no-store')
            self.assertIn("frame-ancestors 'none'",response.headers['Content-Security-Policy'])
        for path,code in [('/api/snapshot',503),('/../analysis.py',404),('/.env',404)]:
            with self.assertRaises(HTTPError) as context:urlopen(self.base+path)
            self.assertEqual(context.exception.code,code)
        request=Request(self.base+'/api/health',headers={'Host':'attacker.example'})
        with self.assertRaises(HTTPError) as context:urlopen(request)
        self.assertEqual(context.exception.code,403)
        request=Request(self.base+'/api/snapshot',data=b'{}',method='POST')
        with self.assertRaises(HTTPError) as context:urlopen(request)
        self.assertEqual(context.exception.code,404)

    def test_demo_explicit_live_ingestion_and_corrupt_snapshot(self):
        with urlopen(self.base+'/api/snapshot?mode=demo') as response:
            self.assertEqual(json.load(response)['mode'],'demo')
        path=Path(self.folder.name)/'latest.json'
        path.write_text(json.dumps(demo_snapshot()))
        with urlopen(self.base+'/api/snapshot') as response:
            self.assertEqual(json.load(response)['mode'],'live')
        path.write_text('{partial')
        with self.assertRaises(HTTPError) as context:urlopen(self.base+'/api/snapshot')
        self.assertEqual(context.exception.code,503)


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(SnapshotStore(self.folder.name),'test-secret'))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.folder.cleanup()

    def post(self, token='test-secret', origin=None, data=None):
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        request=Request(self.base+'/api/ingest',data=json.dumps(data or demo_snapshot()).encode(),headers=headers,method='POST')
        return urlopen(request)

    def test_authenticated_ingestion_reaches_live_api_without_mount(self):
        with self.post() as response:self.assertEqual(json.load(response)['status'],'accepted')
        with urlopen(self.base+'/api/snapshot') as response:
            data=json.load(response)
            self.assertEqual(data['mode'],'live')
            self.assertEqual(len(data['listeners']),4)
        self.assertFalse((Path(self.folder.name)/'latest.json').exists())

    def test_unauthorized_and_browser_uploads_are_rejected(self):
        for token,origin in [('wrong',None),('test-secret','http://127.0.0.1:9090'),('test-secret','https://evil.example')]:
            with self.subTest(token=token,origin=origin):
                with self.assertRaises(HTTPError) as context:self.post(token,origin)
                self.assertEqual(context.exception.code,403)

    def test_malformed_ingest_is_rejected_without_overwriting(self):
        with self.post():pass
        with self.assertRaises(HTTPError) as context:self.post(data={'schema_version':2})
        self.assertEqual(context.exception.code,400)
        with urlopen(self.base+'/api/snapshot') as response:self.assertEqual(len(json.load(response)['listeners']),4)


if __name__=='__main__':unittest.main()
