"""Build an allowlisted source Skill Pack; exclude local runtime and evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[4]


def build(output):
    fixed = ['START-HERE.md', 'README.md', 'AGENTS.md', 'LICENSE', '.gitignore',
             'runtime.contract.json', 'dependencies.manifest.json', 'config/collection.example.json',
             'docs/bootstrap.zh-cn.md', 'docs/delivery-guide.zh-cn.md', 'docs/runtime-parameters.zh-cn.md']
    files = [ROOT / name for name in fixed]
    for folder in ['.agents/skills/integrated-scraper', 'tests', '.github']:
        for path in (ROOT / folder).rglob('*'):
            if '__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo'):
                continue
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                raise ValueError('Linked path refused: ' + str(path))
            if path.is_file():
                files.append(path)
    records, payloads = [], {}
    for path in sorted(set(files)):
        if not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError('Invalid source: ' + str(path))
        name = path.relative_to(ROOT).as_posix()
        body = path.read_bytes()
        records.append({'path': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()})
        payloads[name] = body
    manifest = {'pack': 'integrated-scraper-skill', 'format': 'online-bootstrap-source-pack',
                'excluded': ['runtime', 'agent_memory', 'collection.local.json', 'business data', '.git'],
                'files': records}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, body in payloads.items():
            archive.writestr('integrated-scraper-skill/' + name, body)
        archive.writestr('integrated-scraper-skill/PACKAGE-MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        for row in records:
            assert hashlib.sha256(archive.read('integrated-scraper-skill/' + row['path'])).hexdigest() == row['sha256']
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    with output.with_suffix('.zip.sha256').open('x', encoding='utf-8') as stream:
        stream.write(digest + '  ' + output.name + '\n')
    print(json.dumps({'zip': str(output), 'files': len(records), 'bytes': output.stat().st_size, 'sha256': digest}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output)
