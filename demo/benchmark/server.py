"""Read-only, loopback demo of frozen benchmark artifacts. No model execution."""
from __future__ import annotations
import argparse
from collections import Counter

from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen
from urllib.error import URLError
import socket
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT.parent / 'uafeg'
HERE = Path(__file__).resolve().parent
CACHE = HERE / 'generated'
sys.path[:0] = [str(ROOT), str(RESEARCH / 'src')]
import yaml
from src.data import benchmark_v2, benchmark_v3
from src.data.benchmark_qa import c2_audit
from src.schemas.packet import EvidencePacket
from src.schemas.claim import ClaimRecord
from uafeg.graph import build_graph


def read(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def sha(content):
    return hashlib.sha256(content).hexdigest()


def fingerprint(repo):
    digest = hashlib.sha256()
    digest.update(subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD']))
    lock = repo / 'benchmark.lock.json'
    if lock.exists(): digest.update(lock.read_bytes())
    for folder in ('src', 'tests', 'configs', 'demo/benchmark'):
        for path in sorted((repo / folder).rglob('*')):
            if path.is_file() and path.suffix in ('.py', '.yaml', '.js', '.css', '.html') and '__pycache__' not in path.parts:
                digest.update(str(path.relative_to(repo)).encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


def run_tests():
    CACHE.mkdir(exist_ok=True)
    results = []
    for title, repo in [('Repo A', ROOT), ('UAFEG', RESEARCH)]:
        xml = CACHE / ('tests-a.xml' if repo == ROOT else 'tests-b.xml')
        command = [str(repo / '.venv/bin/python'), '-m', 'pytest', '-q', f'--junitxml={xml}']
        # Default suite never executes specialist models, including cached NLI.
        env = os.environ.copy(); env.pop('PYTHONPATH', None)
        env.update(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        proc = subprocess.run(command, cwd=repo, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (CACHE / (xml.stem + '.log')).write_text(proc.stdout)
        print(proc.stdout, flush=True)
        cases = []
        if xml.exists():
            for case in ET.parse(xml).iter('testcase'):
                status = 'FAIL' if case.find('failure') is not None or case.find('error') is not None else 'SKIP' if case.find('skipped') is not None else 'PASS'
                cases.append({'name': case.get('classname', '') + '::' + case.get('name', ''), 'status': status, 'seconds': float(case.get('time', 0))})
        groups = {
            'Schema': ['schema', 'claim', 'contract'], 'Deterministic generation': ['determin', 'generation'],
            'Split integrity': ['split', 'group'], 'Duplicate leakage': ['duplicate', 'leakage'],
            'Provenance': ['provenance', 'source'], 'EvidencePacket': ['packet', 'contract'],
            'EvidenceGraph': ['graph', 'node', 'edge'], 'Condition generation': ['condition', 'benchmark_v', 'benign', 'inpaint'],
            'Reproducibility': ['reproduc', 'hash', 'lock', 'determin']}
        results.append({'repository': title, 'command': command, 'exit_code': proc.returncode,
                        'counts': dict(Counter(c['status'] for c in cases)), 'seconds': sum(c['seconds'] for c in cases),
                        'cases': cases, 'purpose_groups': {k: [c for c in cases if any(t in c['name'].lower() for t in terms)] for k, terms in groups.items()},
                        'fingerprint': fingerprint(repo), 'timestamp': datetime.now(timezone.utc).isoformat()})
    (CACHE / 'tests.json').write_text(json.dumps(results, indent=2))
    return results


class Demo:
    def __init__(self):
        self.base = ROOT / 'data/manifests/benchmark_v3'
        self.claims = lines(self.base / 'manifest.jsonl')
        self.lookup = {c['claim_id']: c for c in self.claims}
        self.packets = {p['claim']['claim_id']: p for p in lines(self.base / 'evidence_packets.jsonl')}
        self.audit = read(self.base / 'dataset_audit.json')
        self.sources = {s['source_image_id']: s for s in self.audit['sources']}
        self.summary = read(ROOT / 'qa_summary.json')
        self.pixels = {r['claim_id']: r for rows in read(ROOT / 'qa_v3_pixels.json').values() for r in rows}
        self.c2 = {r['claim_id']: r for r in c2_audit(self.claims, self.sources)}
        self.v2claims = {c['claim_id']: c for c in lines(ROOT / 'data/manifests/benchmark_v2/manifest.jsonl')}
        self.v2c2 = read(ROOT / 'qa_measurements.json')['c2']
        self.registry = yaml.safe_load((ROOT / 'configs/benchmark_conditions_v2.yaml').read_text())['conditions']
        self.config = yaml.safe_load((ROOT / 'configs/benchmark_v3.yaml').read_text())
        self.allowed = set()
        for c in list(self.claims) + list(self.v2claims.values()):
            for p in (c['image_path'], c['provenance']['source_image_path'], c['transformation']['parameters'].get('mask_path')):
                if p: self.allowed.add((ROOT / p).resolve())
        missing = [str(p) for p in self.allowed if not p.is_file()]
        if missing: raise FileNotFoundError(f'{len(missing)} missing image paths; first: {missing[0]}')
        self.reproduction = self.reproduce()

    def reproduce(self):
        selected = [next(c for c in self.claims if c['condition'] == 'C3'),
                    next(c for c in self.claims if c['transformation']['parameters'].get('subtype') == 'C8_RESIZE'),
                    next(c for c in self.claims if c['condition'] == 'C10')]
        out = []
        for c in selected:
            source = self.sources[c['source_image_id']]
            config = {**self.config, 'seed': c['transformation']['seed']}
            if c['condition'] == 'C8':
                content, _ = benchmark_v3.benign_control(ROOT, source, 'C8_RESIZE', config)
            else:
                result, _ = benchmark_v2.localized_transform(ROOT, source, c['condition'], config)
                content = benchmark_v2.png_bytes(result[0], config.get('png_compression_level', 9))
            expected = c['transformation']['image_sha256']
            generated = sha(content); stored = sha((ROOT / c['image_path']).read_bytes())
            out.append({'claim_id': c['claim_id'], 'condition': c['condition'], 'seed': config['seed'],
                        'expected': expected, 'generated': generated, 'stored': stored,
                        'status': 'MATCH' if expected == generated == stored else 'MISMATCH',
                        'method': 'Existing canonical operator; in-memory encoding; no files written'})
        return out

    def claim(self, identifier):
        c = self.lookup.get(identifier) or self.v2claims[identifier]
        packet = self.packets.get(identifier)
        graph = None
        ClaimRecord.model_validate(c)
        if packet:
            model = EvidencePacket.model_validate(packet)
            graph = build_graph(model).model_dump(mode="json")
        return {'claim': c, 'version': 'v3' if identifier in self.lookup else 'v2 (historical)',
                'packet': packet, 'graph': graph, 'qa': self.c2.get(identifier) or self.pixels.get(identifier),
                'donors': [self.sources[s] for s in c['transformation']['donor_source_image_ids'] if s in self.sources],
                'status': 'REVIEW REQUIRED', 'human_review': 'NOT PERFORMED'}

    def overview(self):
        groups = {s: {c['source_image_id'] for c in self.claims if c['split'] == s} for s in ('train', 'validation', 'test')}
        source_split = {c['source_image_id']: c['split'] for c in self.claims}
        violations = sum(source_split[d] != c['split'] for c in self.claims for d in c['transformation']['donor_source_image_ids'])
        tests = read(CACHE / 'tests.json') if (CACHE / 'tests.json').exists() else []
        for result, repo in zip(tests, (ROOT, RESEARCH)):
            result['current'] = result['fingerprint'] == fingerprint(repo)
        return {'counts': {'downloaded': self.audit['images_available'], 'accepted': len(self.sources), 'claims': len(self.claims)},
                'conditions': dict(Counter(c['condition'] for c in self.claims)), 'labels': dict(Counter(c['expected_label'] for c in self.claims)),
                'registry': self.registry, 'summary': self.summary, 'duplicates': self.audit['duplicates'],
                'source_counts': {k: len(v) for k,v in groups.items()},
                'overlaps': {f'{a} ∩ {b}': len(groups[a] & groups[b]) for a,b in [('train','validation'),('train','test'),('validation','test')]},
                'duplicate_counts': {kind: sum(kind in pair['reasons'] for pair in self.audit['duplicates']['pairs']) for kind in ('file_exact', 'pixel_exact', 'near_duplicate_candidate')},
                'donor_violations': violations, 'tests': tests, 'reproduction': self.reproduction,
                'manifest_sha256': sha((self.base / 'manifest.jsonl').read_bytes()),
                'lock': read(RESEARCH / 'benchmark.lock.json'), 'v2_c2': self.v2c2,
                'c2': list(self.c2.values()), 'exclusions': read(self.base / 'exclusions.json'),
                'index': [{**{k:c[k] for k in ('claim_id','source_image_id','condition','split','image_path')}, 'subtype': c['transformation']['parameters'].get('subtype')} for c in self.claims]}


def serve(demo, port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            request = urlparse(self.path); query = parse_qs(request.query)
            try:
                if request.path == '/api/overview':
                    content = json.dumps(demo.overview(), ensure_ascii=False).encode(); mime = 'application/json'
                elif request.path == '/api/claim':
                    content = json.dumps(demo.claim(query['id'][0]), ensure_ascii=False).encode(); mime = 'application/json'
                elif request.path == '/image':
                    path = (ROOT / query['path'][0]).resolve()
                    if path not in demo.allowed: self.send_error(403); return
                    content = path.read_bytes(); mime = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
                elif request.path in ('/', '/demo', '/app.js', '/style.css'):
                    path = HERE / ('index.html' if request.path in ('/', '/demo') else request.path[1:])
                    content = path.read_bytes(); mime = mimetypes.guess_type(str(path))[0]
                else: self.send_error(404); return
                self.send_response(200); self.send_header('Content-Type', mime + ('; charset=utf-8' if mime.startswith(('text/', 'application/json')) else ''))
                self.send_header('Content-Length', str(len(content))); self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff'); self.end_headers(); self.wfile.write(content)
            except (KeyError, ValueError): self.send_error(400)
            except FileNotFoundError: self.send_error(404)
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'\nUAFEG Benchmark Demo → http://127.0.0.1:{port}/\nPresentation → http://127.0.0.1:{port}/demo\nCtrl+C to stop. Offline, read-only benchmark access.\n', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--refresh-tests', action='store_true'); parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not args.check:
        # Reuse the existing demo; never terminate an unknown port owner.
        address = f'http://127.0.0.1:{args.port}'
        with socket.socket() as probe:
            occupied = probe.connect_ex(('127.0.0.1', args.port)) == 0
        if occupied:
            try:
                with urlopen(address, timeout=3) as response:
                    is_demo = b'<title>UAFEG' in response.read(4096)
            except (URLError, OSError):
                is_demo = False
            if is_demo:
                print(f'La demo ya está ejecutándose. Abre {address}/demo')
                print('No hace falta iniciarla otra vez. Recarga el navegador con Ctrl+Shift+R.')
                sys.exit(0)
            print(f'El puerto {args.port} está ocupado por otro servicio. Usa ./run_demo.sh --port {args.port + 1}', file=sys.stderr)
            sys.exit(1)
    if args.refresh_tests or not (CACHE / 'tests.json').exists(): run_tests()
    demo = Demo()
    if args.check:
        overview = demo.overview()
        print(json.dumps({'counts': overview['counts'], 'overlaps': overview['overlaps'], 'reproduction': overview['reproduction']}, indent=2))
        if any(r['status'] != 'MATCH' for r in demo.reproduction): sys.exit(1)
    else: serve(demo, args.port)
