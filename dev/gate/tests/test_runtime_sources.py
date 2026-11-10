import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'skill/docs-review/scripts'))
import draft
import locate
import mode_support
import sweep

FIXTURES = ROOT / 'dev/fixtures'
SNAPSHOT = FIXTURES / 'snapshot'


@pytest.fixture
def snapshot(tmp_path):
    return shutil.copytree(SNAPSHOT, tmp_path / 'snapshot')


def forbidden(*args, **kwargs):
    raise AssertionError('snapshot/connector mode must not access Git or gh')


def test_snapshot_locate_connector_and_provenance(monkeypatch, capsys):
    monkeypatch.setattr(locate, 'git', forbidden)
    monkeypatch.setattr(locate, 'gh_api', forbidden)
    assert locate.main(['external_account', '--snapshot', str(SNAPSHOT), '--prs', str(FIXTURES / 'prs.json'),
                        '--no-web', '--json']) == 0
    report = json.loads(capsys.readouterr().out)
    candidate = report['candidates'][0]
    assert candidate['sha'] == 'live'
    assert candidate['quote'] in (SNAPSHOT / candidate['repo'] / candidate['path']).read_text()
    assert candidate['source_url'].endswith('required-fields-for-businesses.md')
    assert report['searched']['prs']['matches'][0]['number'] == 123
    assert report['searched']['repositories'][1]['sha'] == '0' * 40
    assert 'reviewer judgment' in locate.render(report)


def test_empty_terms_no_hits_and_empty_manifest(snapshot):
    for question in ('does the a', 'token_without_hits'):
        report = locate.locate(question, [], snapshot_dir=snapshot, web=False, prs=False)
        assert report['status'] == 'not found'
        assert report['searched']['repositories']
    (snapshot / 'manifest.json').write_text('{"entries": []}')
    assert locate.locate('external_account', [], snapshot_dir=snapshot, web=False, prs=False)['candidates'] == []


@pytest.mark.parametrize('field,value,message', [
    ('sha', 'invented', 'Git SHA'), ('url', '', 'requires string'),
    ('url', 'file:///etc/passwd', 'https'), ('repo', 'unknown', 'known repo'),
    ('path', '../outside.md', 'safe repository-relative'), ('path', '/absolute.md', 'safe repository-relative'),
    ('path', 'missing.md', 'file missing'), ('path', 'anything.py', 'Markdown'),
])
def test_invalid_snapshot_entries(snapshot, field, value, message):
    manifest = json.loads((snapshot / 'manifest.json').read_text())
    manifest['entries'][0][field] = value
    (snapshot / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=message):
        mode_support.read_snapshot(snapshot)


@pytest.mark.parametrize('manifest,message', [
    ('not json', 'cannot read snapshot'), ('[]', 'entries array'),
    ('{"entries": [null]}', 'requires string'), ('{"entries": {}}', 'entries array'),
])
def test_bad_manifest_shape(snapshot, manifest, message):
    (snapshot / 'manifest.json').write_text(manifest)
    with pytest.raises(ValueError, match=message):
        mode_support.read_snapshot(snapshot)


def test_duplicate_and_escaping_symlink(snapshot, tmp_path):
    manifest = json.loads((snapshot / 'manifest.json').read_text())
    original = json.dumps(manifest)
    manifest['entries'].append(manifest['entries'][0])
    (snapshot / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='duplicate'):
        mode_support.read_snapshot(snapshot)
    (snapshot / 'manifest.json').write_text(original)
    entry = manifest['entries'][0]
    page = snapshot / entry['repo'] / entry['path']
    page.unlink()
    outside = tmp_path / 'outside.md'
    outside.write_text('not a snapshot source')
    page.symlink_to(outside)
    with pytest.raises(ValueError, match='outside snapshot'):
        mode_support.read_snapshot(snapshot)


def test_snapshot_small_edit_quote_checks_and_saved_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(draft, 'revision', forbidden)
    value = dict(question='What does the fixture specify?', destination='small-edit', project='payments',
                 evidence=[dict(claim='The fixture excludes P.O. boxes.', source='Synthetic fixture.', verified=True)],
                 target=dict(repo='docs-readme-payments', path='docs/required-fields-for-businesses.md',
                             heading='Required Fields for Businesses'),
                 fields=dict(quote='P.O. boxes are not accepted.', replacement='Do not use a P.O. box.'))
    brief = tmp_path / 'brief.yaml'
    brief.write_text(yaml.safe_dump(value))
    out = tmp_path / 'draft'
    draft.scaffold(brief, out, 3, SNAPSHOT)
    result = draft.validate(out)
    assert result['status'] == 'valid' and result['strict_failures'] == 0
    assert result['sha'] == 'live' and result['ref'] == 'snapshot'
    assert result['source_url'].endswith('required-fields-for-businesses.md')
    candidate = out / 'candidate.md'
    candidate.write_text(candidate.read_text().replace('P.O. boxes are not accepted.', 'Absent quote.'))
    assert 'quote' in draft.validate(out)['error'].lower()
    with pytest.raises(ValueError, match='not listed'):
        mode_support.snapshot_source(SNAPSHOT, 'docs-readme-payments', 'docs/unlisted.md')


def test_snapshot_sweep_only_manifest_pages(snapshot, capsys):
    (snapshot / 'docs-readme-payments/docs/unlisted.md').write_text('# Do not review unlisted pages\n')
    assert sweep.main(['--snapshot', str(snapshot)]) == 0
    output = capsys.readouterr().out
    assert 'SCAFFOLD' in output and "'sha': 'live'" in output
    assert 'body-h1' not in output and 'unlisted.md' not in output


@pytest.mark.parametrize('main,args', [(locate.main, ['question']), (sweep.main, [])])
def test_explicit_source_required(main, args, capsys):
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2
    assert 'provide --snapshot' in capsys.readouterr().err


def test_pr_missing_gh_and_empty_connector_input(monkeypatch, tmp_path):
    monkeypatch.setattr(locate.shutil, 'which', lambda _: None)
    report = locate.locate('external_account', mode_support.default_repos(), snapshot_dir=SNAPSHOT, web=False)
    assert 'PR search not run' in locate.render(report)
    path = tmp_path / 'prs.json'
    path.write_text('{"items": []}')
    assert locate.connector_prs(path, [['external_account']], 90)['matches'] == []


def test_connector_pr_merged_state_patch_match_and_window(tmp_path):
    data = json.loads((FIXTURES / 'prs.json').read_text())
    data[0].update(title='Contract update', state='closed', merged_at=datetime.now(timezone.utc).isoformat())
    data[0]['repo'] = 'docs-readme-payments'
    path = tmp_path / 'prs.json'
    path.write_text(json.dumps({'items': data}))
    result = locate.connector_prs(path, [['external_account']], 90)
    assert result['matches'][0]['state'] == 'merged'
    assert result['matches'][0]['merged_at'] == data[0]['merged_at']
    data[0]['merged_at'] = '2000-01-01T00:00:00Z'
    path.write_text(json.dumps(data))
    assert locate.connector_prs(path, [['external_account']], 90)['matches'] == []


@pytest.mark.parametrize('data,message', [
    ({}, 'items array'), ([{}], 'number'), ([{'number': 1}], 'title and state'),
])
def test_bad_connector_input(tmp_path, data, message):
    path = tmp_path / 'prs.json'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match=message):
        locate.connector_prs(path, [['example']], 90)


@pytest.mark.parametrize('field,value,message', [
    ('repo', [], 'string repo'), ('repo', 'other/repo', 'known repo'),
    ('body', [], 'must be strings'), ('patch', {}, 'must be strings'),
    ('merged_at', 'not a date', 'ISO timestamp'), ('merged_at', '2026-11-01', 'ISO timestamp'),
    ('state', 'merged', 'requires merged_at'),
])
def test_bad_connector_fields(tmp_path, field, value, message):
    data = json.loads((FIXTURES / 'prs.json').read_text())
    data[0][field] = value
    path = tmp_path / 'prs.json'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match=message):
        locate.connector_prs(path, [['external_account']], 90)
