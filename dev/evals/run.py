#!/usr/bin/env python3
"""Execute fixture plumbing; model reasoning and trigger routing require Claude."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote

import yaml

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'skill/docs-review/scripts'
AUTOPILOT = ROOT / 'skill/docs-autopilot/scripts/autopilot.py'


def command(args, allowed=(0,)):
    process = subprocess.run([str(a) for a in args], text=True, capture_output=True, timeout=120,
                             env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    if process.returncode not in allowed:
        raise AssertionError(f'command exit {process.returncode}: {process.stderr or process.stdout}')
    return process.stdout


def fixture_snapshot(folder, repo, pages):
    folder.mkdir(parents=True)
    entries = []
    for relative, content in pages.items():
        path = folder / repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        entries.append(dict(repo=repo, path=relative, sha='live',
                            url=f'https://example.invalid/fixture/{repo}/{quote(relative, safe="/")}'))
    (folder / 'manifest.json').write_text(json.dumps(dict(entries=entries)))
    return folder


def validate_edit(files, sandbox, prefix=''):
    brief_file = files / (prefix + '-brief.yaml' if prefix else 'brief.yaml')
    source_file = files / (prefix + '-source.md' if prefix else 'source.md')
    edit_file = files / (prefix + '-edit.md' if prefix else 'candidate.md')
    brief = yaml.safe_load(brief_file.read_text())
    snapshot = fixture_snapshot(sandbox / ('snapshot-' + (prefix or 'edit')), 'docs-readme-payments',
                                {brief['target']['path']: source_file.read_text()})
    before = {str(p): p.read_bytes() for p in snapshot.rglob('*') if p.is_file()}
    brief['target']['repo'] = 'docs-readme-payments'
    brief_file = sandbox / ((prefix or 'edit') + '-brief.yaml')
    brief_file.write_text(yaml.safe_dump(brief))
    out = sandbox / ((prefix or 'edit') + '-validation')
    command([sys.executable, REVIEW / 'draft.py', brief_file, '--snapshot', snapshot, '--out', out, '--max-iterations', '2'])
    (out / 'candidate.md').write_text(edit_file.read_text())
    result = json.loads(command([sys.executable, REVIEW / 'draft.py', 'validate', out]))
    assert result['strict_failures'] == 0, result
    text = (out / 'candidate.md').read_text()
    assert text.startswith('Path: `') and '\nHeading: ' in text and '\nQuote:' in text and '\nReplacement:' in text
    assert not text.startswith('---')
    assert result['sha'] == 'live' and result['ref'] == 'snapshot'
    assert before == {str(p): p.read_bytes() for p in snapshot.rglob('*') if p.is_file()}
    return result


def autopilot_case(case, files, sandbox):
    out = sandbox / 'out'
    command([sys.executable, AUTOPILOT, 'dry-run', files / 'window.json', '--out', out])
    run = json.loads((out / 'run.json').read_text())
    rows = [json.loads(line) for line in (out / 'notion-rows.jsonl').read_text().splitlines()]
    dm = (out / 'dm.txt').read_text()
    expected = case['expect']
    assert run['mode'] == 'DRY-RUN' and run['network_writes'] == 0 and run['live_writers_imported'] is False
    assert run['schema_changes_applied'] is False
    assert len(rows) == expected['rows'], rows
    if expected.get('stage'):
        assert all(row['properties']['Stage'] == expected['stage'] for row in rows)
    if expected.get('admitted'):
        assert any(d['id'] == expected['admitted'] and d['status'] == 'Admitted' for d in run['decisions'])
    if expected.get('closed'):
        assert rows[0]['page_id'] == expected['closed'] and '#109' not in json.dumps(rows)
        assert '/176' in rows[0]['properties']['Sources'] and '/192' in rows[0]['properties']['Sources']
        assert all(row.get('page_id') != expected['not_closed'] for row in rows)
    if expected.get('no_draft'):
        assert all(row['properties']['Has Draft'] == '__NO__' and '## Draft\n' not in row['body'] for row in rows)
    if expected.get('quiet'):
        assert dm == 'nothing qualified\n' and not rows
    serialized = '\n'.join(path.read_text() for path in out.iterdir())
    for banned in expected.get('banned', []):
        assert not re.search(re.escape(banned), serialized, re.I), 'customer information leaked'
    for required in expected.get('required', []):
        assert required in serialized, required
    if expected.get('effort_level'):
        assert all(row['properties']['Effort level'] == expected['effort_level'] for row in rows)
    for row in rows:
        assert set(row) == {'op', 'properties', 'body'} | ({'page_id'} if row['op'] == 'update' else set())
        assert row['op'] in ('create', 'update') and isinstance(row['body'], str)
    if expected.get('reserve_regex'):
        assert not re.search(r'reserve.{0,100}(?:%|percent)|(?:%|percent).{0,100}reserve', serialized, re.I | re.S)
    for prefix in expected.get('validate_edits', []):
        validate_edit(files, sandbox, prefix)
    if expected.get('locate'):
        snapshot = fixture_snapshot(sandbox / 'snapshot', 'docs-readme-platform',
                                    {'reference/Payments/legal-entities/identifications/index.md': (files / 'identifications-source.md').read_text()})
        located = json.loads(command([sys.executable, REVIEW / 'locate.py', 'Which identification types are supported on a legal entity?', '--snapshot', snapshot, '--no-web', '--no-prs', '--json']))
        assert located['candidates'] and 'identification' in located['candidates'][0]['quote'].lower()
        (sandbox / 'locate.json').write_text(json.dumps(located, indent=2))


def fence_case(files, sandbox):
    results = {}
    for tag in ('curl', 'shell', 'bash'):
        report = json.loads(command([sys.executable, REVIEW / 'review.py', files / ('onboard-a-business-' + tag + '.md'),
                                     '--project', 'payments', '--only', 'lint', '--rule', 'fence-language', '--format', 'json'], allowed=(0, 1)))
        findings = report['findings']
        assert bool(findings) == (tag != 'curl')
        assert all(f['rule'] == 'fence-language' and 'curl' in f['message'] for f in findings)
        results[tag] = findings
    (sandbox / 'fences.json').write_text(json.dumps(results, indent=2))


def run(out, selected=None):
    if out.exists() and any(out.iterdir()):
        raise ValueError('eval output directory must be empty')
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted((ROOT / 'skill').glob('*/evals/*/case.yaml')):
        case = yaml.safe_load(path.read_text())
        if selected and case['id'] != selected:
            continue
        folder = out / case['id']
        folder.mkdir()
        files = folder / 'files'
        shutil.copytree(path.parent / 'files', files)
        try:
            if case['kind'] == 'autopilot': autopilot_case(case, files, folder)
            elif case['kind'] == 'fence': fence_case(files, folder)
            elif case['kind'] == 'draft': validate_edit(files, folder)
            else: raise AssertionError('unknown case kind')
            status, detail = 'PASS', ''
        except (AssertionError, ValueError, OSError) as exc:
            status, detail = 'FAIL', str(exc)
        results.append(dict(case=case['id'], deterministic=status, detail=detail, model='needs model grader (Claude)'))
    if not results:
        raise ValueError('no matching eval cases')
    for skill in ('docs-autopilot', 'docs-review'):
        triggers = yaml.safe_load((ROOT / 'skill' / skill / 'evals/triggering.yaml').read_text())
        assert len([q for q in triggers if q['should_trigger'] is True]) == (13 if skill == 'docs-autopilot' else 10)
        assert len([q for q in triggers if q['should_trigger'] is False]) == 10
    (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    print('| Case | Deterministic | Model |')
    print('|---|---|---|')
    for result in results:
        print(f'| {result["case"]} | {result["deterministic"]} | {result["model"]} |')
        if result['detail']:
            print(result['detail'])
    print('Triggering sets: autopilot 13 positive + 10 near misses; review 10 + 10; structure verified, model routing unmeasured.')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case')
    args = parser.parse_args()
    try:
        results = run(args.out, args.case)
        return int(any(r['deterministic'] != 'PASS' for r in results))
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
