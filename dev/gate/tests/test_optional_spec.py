import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / 'dev/fixtures'
REVIEW = ROOT / 'skill/docs-review/scripts/review.py'
API = ROOT / 'skill/docs-test/scripts/apicheck.py'


def check(script, page=None, args=(), env=None):
    clean = {k: v for k, v in os.environ.items() if k != 'DOCS_REVIEW_SPEC'}
    return subprocess.run([sys.executable, str(script), str(page or FIXTURES / 'openapi-page.md'),
                           '--project', 'payments', *args], text=True, capture_output=True,
                          env={**clean, 'PYTHONDONTWRITEBYTECODE': '1', **(env or {})})


@pytest.mark.parametrize('script', [REVIEW, API])
@pytest.mark.parametrize('missing', [False, True])
def test_unavailable_spec_is_not_run_in_log_and_scorecard(script, missing, tmp_path):
    args = ['--spec', str(tmp_path / 'missing.json')] if missing else []
    result = check(script, args=[*args, '--format', 'json'])
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert 'openapi-field-exists not run: no spec snapshot' in report['scorecard']['notes']
    assert not any(f['rule'] == 'openapi-field-exists' for f in report['findings'])
    result = check(script, args=args)
    assert result.returncode == 0, result.stderr
    assert 'openapi-field-exists not run: no spec snapshot' in result.stdout


@pytest.mark.parametrize('script', [REVIEW, API])
def test_explicit_spec_and_environment_precedence(script, tmp_path):
    spec = FIXTURES / 'openapi.json'
    result = check(script, args=['--spec', str(spec), '--format', 'json'])
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report['scorecard']['strict_failures'] == 1
    assert 'invented_field' in report['findings'][0]['message']
    assert not any('no spec snapshot' in note for note in report['scorecard']['notes'])
    result = check(script, args=['--format', 'json'], env={'DOCS_REVIEW_SPEC': str(spec)})
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)['findings'] == report['findings']
    result = check(script, args=['--spec', str(tmp_path / 'missing'), '--format', 'json'],
                   env={'DOCS_REVIEW_SPEC': str(spec)})
    assert result.returncode == 0 and 'no spec snapshot' in result.stdout


@pytest.mark.parametrize('script', [REVIEW, API])
@pytest.mark.parametrize('content,message', [('not json', 'cannot load OpenAPI'), ('null', 'object with paths')])
def test_invalid_provided_spec_is_an_input_error(script, content, message, tmp_path):
    spec = tmp_path / 'invalid.json'
    spec.write_text(content)
    result = check(script, args=['--spec', str(spec)])
    assert result.returncode == 2
    assert message in result.stderr


def test_no_spec_does_not_suppress_other_strict_failures(tmp_path):
    page = tmp_path / 'page.md'
    page.write_text('---\ntitle: Example\n---\n# Prepare\n\nhttps://example.com/reference\n')
    result = check(REVIEW, page, args=['--format', 'json'])
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report['scorecard']['strict_failures'] == 1
    assert report['findings'][0]['rule'] == 'link-bare-url'
    assert 'openapi-field-exists not run: no spec snapshot' in report['scorecard']['notes']
    result = check(REVIEW, page, args=['--only', 'lint', '--format', 'json'])
    assert not any('no spec snapshot' in note for note in json.loads(result.stdout)['scorecard']['notes'])


def test_empty_page_with_spec(tmp_path):
    page = tmp_path / 'empty.md'
    page.write_text('')
    result = check(API, page, args=['--spec', str(FIXTURES / 'openapi.json'), '--format', 'json'])
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['findings'] == []


def test_corpus_supplement_is_opt_in(monkeypatch):
    monkeypatch.delenv('DOCS_CORPUS_ROOT', raising=False)
    monkeypatch.delenv('DOCS_GATE_CORPUS', raising=False)
    sys.path.insert(0, str(ROOT / 'dev/gate'))
    spec = importlib.util.spec_from_file_location('runtime_phase_c', ROOT / 'dev/gate/phase_c.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match='opt-in: set DOCS_CORPUS_ROOT'):
        module.supplementary()


def test_corpus_openapi_gate_refuses_skipped_measurement(monkeypatch, tmp_path):
    sys.path.insert(0, str(ROOT / 'dev/gate'))
    import gate
    page = tmp_path / 'docs-readme-payments/page.md'
    page.parent.mkdir()
    page.write_text('---\ntitle: Example\n---\n# Prepare\n')
    monkeypatch.setenv('DOCS_CORPUS_ROOT', str(tmp_path))
    monkeypatch.delenv('DOCS_REVIEW_SPEC', raising=False)
    monkeypatch.setattr(sys, 'argv', ['gate.py', '--rule', 'openapi-field-exists', '--out', str(tmp_path / 'out.md')])
    with pytest.raises(SystemExit) as exc:
        gate.main()
    assert exc.value.code == 2
    assert not (tmp_path / 'out.md').exists()
