import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import URLError

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / 'skill/docs-review/scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location('mode_' + name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


locate, draft, sweep = load('locate'), load('draft'), load('sweep')
TARGET = 'docs/Customer Onboarding/onboard-a-business/required-fields-for-businesses.md'
QUOTE = 'P.O. boxes are not accepted.'
REPLACEMENT = "P.O. boxes are not accepted. This page does not specify whether a registered agent's address is supported."


def run_git(repo, *args):
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
           'GIT_COMMITTER_NAME': 'Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid'}
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True,
                          text=True, env=env).stdout


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / 'docs-readme-payments'
    repo.mkdir()
    run_git(repo, 'init', '-q', '-b', 'fixture')
    pages = {
        TARGET: '---\ntitle: Required Fields for Businesses\n---\n## Required Fields for Businesses\n\n' + QUOTE + '\n',
        'docs/accounts/index.md': '---\ntitle: Account setup\n---\n# Prepare accounts\n\nUse `external_account` for the example.\n',
        'reference/legal-entity-identifications.md': '---\ntitle: Legal Entity Identification\n---\n# Identification types\n\nLegal Entity identification types include `ad_nrt`.\n',
    }
    for path, text in pages.items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    run_git(repo, 'add', '--', *pages)
    run_git(repo, 'commit', '-qm', 'Fixture evidence')
    run_git(repo, 'update-ref', 'refs/remotes/origin/v2.0', 'HEAD')
    return repo


@pytest.fixture
def brief(repo, tmp_path):
    value = dict(question="Is a registered agent's address supported?", destination='small-edit', project='payments',
                 evidence=[dict(claim=QUOTE, source=TARGET + ' at origin/v2.0', verified=True),
                           dict(claim='The source does not specify registered-agent address behavior.',
                                source=TARGET + ' at origin/v2.0', verified=True)],
                 target=dict(repo=str(repo), path=TARGET, heading='Required Fields for Businesses', ref='origin/v2.0'),
                 fields=dict(quote=QUOTE, replacement=REPLACEMENT))
    path = tmp_path / 'brief.yaml'
    path.write_text(yaml.safe_dump(value))
    return path, value


def test_locate_ref_only_is_deterministic_and_ignores_working_tree(repo):
    path = repo / 'docs/accounts/index.md'
    path.write_text('uncommitted_unique_token\n')
    before = run_git(repo, 'status', '--porcelain')
    first = locate.locate('`external_account`', [repo], web=False, prs=False)
    assert first == locate.locate('`external_account`', [repo], web=False, prs=False)
    candidate = first['candidates'][0]
    assert candidate['heading'] == 'Prepare accounts'
    assert candidate['url'] == 'https://docs.moderntreasury.com/payments/docs/accounts'
    assert candidate['quote'] in run_git(repo, 'show', 'origin/v2.0:docs/accounts/index.md')
    assert 'reviewer judgment' in first['judgment']
    assert locate.locate('uncommitted_unique_token', [repo], web=False, prs=False)['status'] == 'not found'
    assert run_git(repo, 'status', '--porcelain') == before


def test_terms_phrases_code_synonyms_empty_and_bad_ref(repo):
    groups = locate.terms('Does a beneficial owner use `legal_entity` and "postal address"?')
    assert any('beneficial_owner' in group for group in groups)
    assert any('legal_entity' in group for group in groups)
    assert ['postal address'] in groups
    assert locate.terms('does the a on') == []
    report = locate.locate('needle_without_matches', [repo], ref='missing', web=False, prs=False)
    assert report['status'] == 'not found'
    assert report['searched']['repositories'][0]['sha'] is None
    assert 'error' in report['searched']['repositories'][0]
    assert 'searched:' in locate.render(report)


def test_url_slug_index_and_reference(repo):
    assert locate.public_url(repo, 'docs/a/index.md', '---\nslug: custom-route\n---\n') == 'https://docs.moderntreasury.com/payments/docs/custom-route'
    assert locate.public_url(repo, 'reference/a.md', '').endswith('/platform/reference/a')


def test_web_ok_mismatch_empty_incomplete_and_unreachable(monkeypatch):
    candidates = [dict(url='https://docs.moderntreasury.com/payments/docs/a', quote='exact quote'),
                  dict(url='https://docs.moderntreasury.com/platform/docs/b', quote='missing quote')]
    def fake(url):
        text = 'exact quote' if url.endswith('/a.md') else 'other content'
        if '/ledgers/llms.txt' in url:
            text = ''
        return dict(url=url, status='live', text=text)
    monkeypatch.setattr(locate, 'fetch', fake)
    results = locate.web_check(candidates)
    assert [c['web']['status'] for c in candidates] == ['ok', 'mismatch']
    assert {'empty', 'incomplete'}.issubset({r['status'] for r in results})
    monkeypatch.undo()
    def offline(*args, **kwargs):
        raise URLError('offline')
    monkeypatch.setattr(locate, 'urlopen', offline)
    assert locate.fetch('https://example.invalid')['status'] == 'unreachable'


def test_pr_search_patch_only_and_unavailable_sources(repo, monkeypatch):
    monkeypatch.setattr(locate.shutil, 'which', lambda _: None)
    assert 'gh missing' in locate.pr_search([repo], [['identification']], 90)['notes'][0]
    monkeypatch.setattr(locate.shutil, 'which', lambda _: '/gh')
    def api(endpoint, query=None):
        if endpoint == 'search/issues':
            return dict(total_count=101, items=[dict(url='issue-url', number=176,
                        repository_url='https://api.github.com/repos/Modern-Treasury/docs-readme-payments')])
        if '/files?' in endpoint:
            return [dict(filename='reference/spec.json', patch='+ identification_types: ad_nrt'), dict(filename='binary.png')]
        return dict(number=176, title='Contract update', body='', state='closed', merged_at='2026-11-01T00:00:00Z', html_url='https://github.com/example/pull/176')
    monkeypatch.setattr(locate, 'gh_api', api)
    report = locate.pr_search([repo], [['identification', 'identification_types']], 90)
    assert report['matches'][0]['number'] == 176
    assert report['matches'][0]['matched_lines'] == ['reference/spec.json: + identification_types: ad_nrt']
    assert any('incomplete PR search' in note for note in report['notes'])
    assert any('incomplete patches' in note for note in report['notes'])
    def denied(*args):
        raise ValueError('access denied')
    monkeypatch.setattr(locate, 'gh_api', denied)
    report = locate.pr_search([repo], [['identification']], 90)
    assert not report['matches']
    assert any('access denied' in note for note in report['notes'])
    assert 'PR search not run' in report['notes'][-1]


def test_registered_agent_small_edit_zero_strict_and_no_repo_writes(brief, repo, tmp_path):
    path, data = brief
    out = tmp_path / 'draft'
    original = run_git(repo, 'show', 'origin/v2.0:' + TARGET)
    before = run_git(repo, 'status', '--porcelain')
    assert draft.scaffold(path, out, 3)['iterations'] == 0
    candidate = (out / 'candidate.md').read_text()
    assert draft.SMALL_EDIT.fullmatch(candidate)
    assert REPLACEMENT in candidate and not candidate.startswith('---')
    result = draft.validate(out)
    assert result['strict_failures'] == 0, result
    assert result['iterations'] == 1
    assert result['changed_lines'] == [6]
    assert (repo / TARGET).read_text() == original
    assert run_git(repo, 'status', '--porcelain') == before


def test_small_edit_missing_quote_strict_replacement_and_iteration_cap(brief, tmp_path):
    path, _ = brief
    out = tmp_path / 'draft'
    draft.scaffold(path, out, 2)
    candidate = out / 'candidate.md'
    text = candidate.read_text()
    candidate.write_text(text.replace(QUOTE, 'Absent quotation', 1))
    assert draft.validate(out)['strict_failures'] == 1
    candidate.write_text(text.replace(REPLACEMENT, 'MT accepts this address.'))
    result = draft.validate(out)
    assert result['strict_failures'] > 0
    assert any(f['rule'] == 'mt-shorthand' for f in result['findings'])
    assert draft.validate(out, 99)['status'].startswith('iteration limit')
    assert json.loads((out / 'state.json').read_text())['iterations'] == 2


@pytest.mark.parametrize('change', ['evidence', 'target', 'question'])
def test_invalid_briefs_rejected(brief, change):
    path, data = brief
    data[change] = None
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError):
        draft.brief_data(path)


def test_placeholders_changed_brief_existing_directory_and_wrong_heading(brief, tmp_path):
    path, data = brief
    data.pop('fields')
    path.write_text(yaml.safe_dump(data))
    out = tmp_path / 'draft'
    draft.scaffold(path, out, 3)
    assert 'placeholders' in draft.validate(out)['error']
    with pytest.raises(ValueError, match='empty'):
        draft.scaffold(path, out, 3)
    saved = yaml.safe_load((out / 'brief.yaml').read_text())
    saved['question'] = 'changed'
    (out / 'brief.yaml').write_text(yaml.safe_dump(saved))
    with pytest.raises(ValueError, match='brief changed'):
        draft.validate(out)
    with pytest.raises(ValueError, match='heading'):
        draft.section_span('# Other\ntext\n', 'Absent')


def test_invalid_state_target_paths_and_empty_evidence(brief, tmp_path):
    path, data = brief
    out = tmp_path / 'draft'
    draft.scaffold(path, out, 2)
    (out / 'state.json').write_text('{}')
    with pytest.raises(ValueError, match='iteration state'):
        draft.validate(out)
    for target_path in ('../escape.md', '/absolute.md'):
        data['target']['path'] = target_path
        path.write_text(yaml.safe_dump(data))
        with pytest.raises(ValueError, match='repository-relative'):
            draft.brief_data(path)
    data['evidence'] = []
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match='verified evidence'):
        draft.brief_data(path)


def test_api_spec_patch_not_markdown_and_new_page_review(brief, tmp_path):
    path, data = brief
    data['destination'] = 'api-reference-change'
    path.write_text(yaml.safe_dump(data))
    out = tmp_path / 'spec'
    draft.scaffold(path, out, 3)
    assert (out / 'instructions.md').exists() and not (out / 'candidate.md').exists()
    assert draft.validate(out)['strict_failures'] == 1
    patch = dict(target='reference/modern-treasury-api.json', patch=[dict(op='replace', path='/info/description', value='Verified description')])
    (out / 'candidate.json').write_text(json.dumps(patch))
    assert draft.validate(out)['strict_failures'] == 0
    for invalid in ('# Markdown', json.dumps({**patch, 'target': 'docs/endpoint.md'}),
                    json.dumps({**patch, 'patch': [dict(op='replace', path='/info')]})):
        with pytest.raises(ValueError):
            draft.spec_patch(invalid)
    data['destination'] = 'docs-page'
    data['fields'] = dict(title='Example documentation', heading='Prepare the example', purpose='Create a record.',
                          prerequisite='Confirm test access.', action='Create a record.', verification='Retrieve the record.',
                          link_label='Workflow guidance', slug='workflow-guidance')
    path.write_text(yaml.safe_dump(data))
    page = tmp_path / 'page'
    draft.scaffold(path, page, 2)
    assert draft.validate(page)['strict_failures'] == 0


def test_sweep_rank_and_cli_snapshot_are_read_only(repo, capsys):
    assert sweep.rank([], 5) == []
    assert [r['rule'] for r in sweep.rank([dict(rule='a', path='x', strict=True), dict(rule='b', path='x', strict=True),
                                         dict(rule='b', path='y', strict=True), dict(rule='c', path='z', strict=False)], 5)] == ['b', 'a']
    before = run_git(repo, 'status', '--porcelain')
    assert sweep.main(['--repos', str(repo), '--top', '2']) == 0
    output = capsys.readouterr().out
    assert 'SCAFFOLD' in output and 'unknown' in output and 'body-h1' not in output
    assert run_git(repo, 'status', '--porcelain') == before


def test_mode_clis_and_skill_contract(repo, brief, tmp_path, capsys):
    assert locate.main(['external_account', '--repos', str(repo), '--no-web', '--no-prs', '--json']) == 0
    assert json.loads(capsys.readouterr().out)['candidates']
    path, _ = brief
    out = tmp_path / 'cli-draft'
    assert draft.main([str(path), '--out', str(out), '--max-iterations', '2']) == 0
    capsys.readouterr()
    assert draft.main(['validate', str(out)]) == 0
    assert json.loads(capsys.readouterr().out)['iterations'] == 1
    text = (ROOT / 'skill/docs-review/SKILL.md').read_text()
    assert len(text.splitlines()) < 500
    for phrase in ('writing', 'editing', 'reviewing', 'is X documented', 'where do the docs say',
                   'docs-readme-*', 'docs.moderntreasury.com', 'reviewer judgment', 'iteration cap'):
        assert phrase in text
