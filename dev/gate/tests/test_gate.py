import ast
import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / 'dev/gate'


def load_gate():
    spec = importlib.util.spec_from_file_location('gate', GATE / 'gate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gate_exists():
    assert (GATE / 'gate.py').is_file(), 'gate entry point is missing'


@pytest.mark.parametrize('rule', ['leak-names', 'leak-internal', 'filler'])
def test_fixture_witness_waiver_is_scoped_and_preserves_other_gates(rule):
    gate = load_gate()
    measurement = dict(firing=None, non_firing='clean.md', projects={'payments': dict(over_half=False)})
    result = dict(measurements={'draft': measurement}, mutation=dict(kill_rate=1),
                  fixtures=dict(positive=1, negative=1, boundary=1))
    entry = dict(fixture_witness_admission='admitted on fixture witnesses, 2026-11-11, by Eric')
    assert gate.gate_failed(rule, result, {})
    assert gate.gate_failed(rule, result, entry) == (rule == 'filler')
    result['mutation']['kill_rate'] = .94
    assert gate.gate_failed(rule, result, entry)
    result['mutation']['kill_rate'] = 1
    measurement['projects']['payments']['over_half'] = True
    assert gate.gate_failed(rule, result, entry)
    measurement['projects']['payments']['over_half'] = False
    measurement['non_firing'] = None
    assert gate.gate_failed(rule, result, entry)
    measurement['non_firing'] = 'clean.md'
    result['fixtures']['positive'] = 0
    assert gate.gate_failed(rule, result, entry)


def test_config_rejects_waiver_for_other_rules(tmp_path, monkeypatch):
    gate = load_gate()
    (tmp_path / 'rules.yaml').write_text('filler:\n  fixture_witness_admission: not authorized\n')
    monkeypatch.setattr(gate, 'HERE', tmp_path)
    with pytest.raises(ValueError, match='not permitted'):
        gate.rule_config(['filler'])


def test_corpus_evidence_requires_explicit_environment(monkeypatch, tmp_path):
    gate = load_gate()
    monkeypatch.delenv('DOCS_CORPUS_ROOT', raising=False)
    monkeypatch.delenv('DOCS_GATE_CORPUS', raising=False)
    with pytest.raises(ValueError, match='opt-in: set DOCS_CORPUS_ROOT'):
        gate.corpus_root()
    monkeypatch.setenv('DOCS_CORPUS_ROOT', str(tmp_path / 'missing'))
    with pytest.raises(ValueError, match='does not exist'):
        gate.corpus_root()
    monkeypatch.setenv('DOCS_CORPUS_ROOT', str(tmp_path))
    assert gate.corpus_root() == tmp_path
    monkeypatch.delenv('DOCS_CORPUS_ROOT')
    monkeypatch.setenv('DOCS_GATE_CORPUS', str(tmp_path))
    assert gate.corpus_root() == tmp_path


def test_mutation_operators_are_deterministic():
    gate = load_gate()
    source = 'def target(x):\n    if x > 2 and not x == 3:\n        add(1, "rule", "text")\n    return False\n'
    mutations = gate.mutants(source, ['target'])
    assert mutations == gate.mutants(source, ['target'])
    assert {'comparison', 'boolean', 'not-remove', 'not-insert', 'number', 'string', 'emit-delete', 'early-return'} <= {m['operator'] for m in mutations}
    assert all(ast.parse(m['source']) for m in mutations)
    assert not gate.mutants(source, ['other'])


def test_unknown_rule_fails_closed():
    gate = load_gate()
    with pytest.raises(ValueError, match='unmapped'):
        gate.rule_config(['no-such-rule'])


def test_checker_invalid_option_fails_closed():
    gate = load_gate()
    with pytest.raises(RuntimeError, match='checker exit 2'):
        gate.check([GATE / 'fixtures/filler/negative.md'], ['--not-a-real-option'], project='payments')


def test_no_corpus_pages_fails_closed():
    gate = load_gate()
    with pytest.raises(RuntimeError, match='missing checker input'):
        gate.check([GATE / 'fixtures/absent'], project='payments')


def test_missing_boundary_is_rejected():
    gate = load_gate()
    with pytest.raises(ValueError, match='missing boundary coverage'):
        gate.fixture_inventory('filler', {'boundaries': ['new-uncovered-edge']})


def test_aggregation_includes_clean_pages_and_deterministic_witnesses():
    gate = load_gate()
    files = [Path('/corpus/docs-readme-payments/b.md'), Path('/corpus/docs-readme-payments/a.md')]
    findings = [{'rule': 'x', 'path': str(files[0]), 'line': 1}]
    result = gate.measure('x', files, findings)
    assert result['projects']['payments'] == {'pages': 2, 'fired': 1, 'findings': 1, 'over_half': False}
    assert result['firing'] == str(files[0])
    assert result['non_firing'] == str(files[1])
    assert gate.measure('x', files, [])['firing'] is None
    assert gate.measure('x', files, findings * 2)['projects']['payments']['findings'] == 2
    assert gate.measure('x', [], [])['total']['pages'] == 0


def test_corpus_modes_preserve_passthrough_unless_explicitly_selected():
    gate = load_gate()
    assert gate.corpus_modes([], None) == ['review']
    assert gate.corpus_modes(['--mode', 'draft'], None) == ['draft']
    assert gate.corpus_modes(['--mode=draft'], ['review', 'draft', 'review']) == ['review', 'draft']


def test_evidence_reports_inactive_context_and_both_modes():
    gate = load_gate()
    files = [Path('/corpus/docs-readme-payments/a.md')]
    measurements = {mode: gate.measure('image-alt', files, []) for mode in ('review', 'draft')}
    mutation = dict(killed=1, generated=1, kill_rate=1, survivors=[])
    report = gate.render('image-alt', measurements, dict(positive=1, negative=1, boundary=1), mutation)
    assert '### review' in report and '### draft' in report
    assert 'none (inactive or corpus-silent)' in report
    assert 'bar ≥0.950: PASS' in report


def test_skill_does_not_reference_dev():
    import re
    skill = Path(os.environ.get('DOCS_GATE_SKILL', ROOT / 'skill'))
    for path in skill.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        try:
            source = path.read_text()
        except UnicodeError:
            continue
        if path.suffix == '.py':
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    assert all(n.name.split('.')[0] != 'dev' for n in node.names), path
                if isinstance(node, ast.ImportFrom):
                    assert (node.module or '').split('.')[0] != 'dev', path
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if ast.get_docstring(node) is not None:
                        node.body = node.body[1:]
            assert not re.search(r'(?<![\w-])dev[/\\.]', ast.unparse(tree)), path
        else:
            # The shipped prose describes the external harness; it must not load it.
            assert not re.search(r'(?:import|require|include)\s*\(?[\s\x27\x22]*dev[/\\.]', source), path
