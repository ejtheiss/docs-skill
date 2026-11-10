import importlib.util
import json
import os
from pathlib import Path

import pytest

GATE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gate', GATE / 'gate.py')


def cases():
    selected = os.environ.get('DOCS_GATE_RULE')
    return [(p.parent.name, case) for p in sorted((GATE / 'fixtures').glob('*/expectations.json'))
            if not selected or p.parent.name == selected
            for case in json.loads(p.read_text())]


@pytest.mark.parametrize('rule,case', cases(), ids=lambda value: value if isinstance(value, str) else value['file'])
def test_real_checker_fixture(rule, case):
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    path = GATE / 'fixtures' / rule / case['file']
    findings = gate.check([path], json.loads(os.environ.get('DOCS_GATE_ARGS', '[]')), project=case['project'])['findings']
    assert [f['line'] for f in findings if f['rule'] == rule] == case['lines']
    actual = [{k: v for k, v in f.items() if k != 'path'} for f in findings]
    assert actual == case['findings']


def test_fixture_categories():
    for rule in {r for r, _ in cases()}:
        selected = [case for r, case in cases() if r == rule]
        assert {'positive', 'negative', 'boundary'} <= {case['kind'] for case in selected}
        assert any(case['lines'] for case in selected)
        assert any(not case['lines'] for case in selected)
        assert all(case.get('edge') for case in selected if case['kind'] == 'boundary')
