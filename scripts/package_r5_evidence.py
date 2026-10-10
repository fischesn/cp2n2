"""Create a local, credential-scanned R5 candidate; never publishes anything.

Frozen bytes, including the disclosed R4 export repair, are preserved. Provider
budget metadata is retained locally for author review, NOT authorized for public
release. Do not call this an independently reproduced or published artifact.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = 'f5802a3d1c2695637a5840ab5ed94d46ce64063c'
ARCHIVES = [
    'r2-recovery-confirmatory-20261009-01',
    'r3-direct-confirmatory-20261010-01', 'r3-state-confirmatory-20261010-01',
    'r3-agent-reference-20261010-01', 'r3-agent-live-qwen-20261010-01',
    'r4-selection-confirmatory-20261010-01', 'r4-contention-confirmatory-20261010-01',
    'r4-overhead-confirmatory-20261010-01', 'r4-transport-confirmatory-20261010-01',
    'r4-container-confirmatory-20261010-01', 'r5-reproduction-20261010-01']
FORBIDDEN_PARTS = {'.git', '.venv', '.env', '.aws', 'node_modules', '__pycache__'}
SECRET_FIELD = re.compile(rb'"(?:api[_-]?key|authorization|access[_-]?token|password|client[_-]?secret)"\s*:\s*"(?!redacted|REDACTED|dummy|test|fake|none|null)[^"\s]{8,}"', re.I)
def digest(data): return hashlib.sha256(data).hexdigest()
def scan(name, data):
    components = Path(name).parts
    if any(x in FORBIDDEN_PARTS or (x.startswith('.env.') and x != '.env.example') for x in components):
        raise ValueError('Forbidden archive path: ' + name)
    if name.lower().endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(data)) as nested:
            for item in nested.infolist():
                if not item.is_dir(): scan(name + '/' + item.filename, nested.read(item))
    elif name.lower().endswith(('.json', '.jsonl', '.txt', '.md', '.log', '.py', '.ps1')):
        if SECRET_FIELD.search(data): raise ValueError('Potential credential field: ' + name)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', required=True)
    args = parser.parse_args(); output = (ROOT / args.output).resolve()
    if (ROOT / '.cp2n2').resolve() not in output.parents: raise ValueError('Output must be under .cp2n2')
    output.mkdir(parents=True, exist_ok=False)
    payload = {}
    for name in ARCHIVES:
        base = ROOT / '.cp2n2' / name
        if not (base / 'verification.json').is_file(): raise FileNotFoundError(name)
        for path in sorted(base.rglob('*')):
            if not path.is_file(): continue
            relative = path.relative_to(base)
            if name.startswith('r5-') and relative.parts[0] in ('checkout', 'pytest'): continue
            if '__pycache__' in relative.parts: continue
            key = 'evidence/' + name + '/' + relative.as_posix()
            data = path.read_bytes(); scan(key, data); payload[key] = data
    source = output / 'cp2n2-evaluation-source.zip'
    subprocess.run(['git', 'archive', '--format=zip', '--output=' + str(source), CHECKPOINT], cwd=ROOT, check=True)
    payload['cp2n2-evaluation-source.zip'] = source.read_bytes()
    payload['package_r5_evidence.py'] = Path(__file__).read_bytes()
    payload['run_r5_reproduction.py'] = (ROOT / 'scripts/run_r5_reproduction.py').read_bytes()
    for path in sorted((ROOT / 'docs/revision').glob('*.md')):
        payload['documentation/' + path.name] = path.read_bytes()
    payload['documentation/ieee-access-revision-roadmap.md'] = (ROOT / 'docs/ieee-access-revision-roadmap.md').read_bytes()
    for name, data in payload.items(): scan(name, data)
    manifest = {
        'schema': 'cp2n2-r5-local-evidence-candidate-v1',
        'source_commit': CHECKPOINT, 'published': False,
        'credential_field_scan_passed': True, 'human_privacy_release_review_pending': True,
        'provider_budget_metadata_retained_for_local_author_review': True,
        'independent_coauthor_reproduction': False,
        'old_campaign_changed': False,
        'r4_container_packaging_repair': 'Preserved prior inventory plus corrected root export inventory; measurements and nested manifests unchanged. See evidence/r4-container-confirmatory-20261010-01/packaging-repair.',
        'files': {name: {'bytes': len(data), 'sha256': digest(data)} for name, data in sorted(payload.items())}}
    payload['R5-EVIDENCE-MANIFEST.json'] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    readme = ('CP2N2 R5 local evidence candidate\n\n'
              'NOT PUBLISHED. Author approval/privacy review is required before release.\n'
              'Frozen raw bytes are preserved; provider budget metadata remains local.\n'
              'No credentials matched the structured-field/path scan; this is not a\n'
              'guarantee against arbitrary secrets hidden in binary content.\n'
              'All software evidence is E0–E3; no physical or biological measurement.\n'
              'Source checkpoint: ' + CHECKPOINT + '\n'
              'Reproduction reuses the same host and Python environment. Hosted-model\n'
              'and container archives are verified, not rerun; overhead is recomputed,\n'
              'not remeasured. Consult the per-campaign protocols and limitations.\n'
              'Original historical campaigns are retained unchanged in their prior archive.\n'
              'R4 container export inventory repair is disclosed in the manifest.\n')
    payload['README.txt'] = readme.encode('utf-8')
    final = output / 'cp2n2-r5-local-evidence-candidate.zip'
    with zipfile.ZipFile(final, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 10, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(final) as archive:
        assert archive.testzip() is None
        for name, item in manifest['files'].items(): assert digest(archive.read(name)) == item['sha256']
    result = {'archive': str(final), 'bytes': final.stat().st_size,
              'sha256': digest(final.read_bytes()), 'inventory_files': len(manifest['files']),
              'crc_and_payload_hashes_verified': True, 'public_release_authorized': False}
    (output / 'R5-PACKAGE-VERIFICATION.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
if __name__ == '__main__': main()
