import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'skill/docs-review/scripts/rubric_label.py'
spec = importlib.util.spec_from_file_location('rubric_label', SCRIPT)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


@pytest.fixture
def label():
    return dict(case_hash='a' * 64, page_hash='b' * 64,
                rubric_id='money-losing-mistake', decision='reject',
                rationale='Yes: the retry can duplicate the transfer.', reviewer='test-reviewer',
                timestamp='2026-11-10T12:00:00Z', policy_id='cc311b98b5af')


def test_append_preserves_previous_labels_and_escapes_newlines(tmp_path, label):
    path = tmp_path / 'labels.jsonl'
    helper.append_label(path, label)
    second = {**label, 'decision': 'accept', 'rationale': 'No.\nEvidence confirms the retry contract.'}
    helper.append_label(path, second)
    assert [json.loads(line) for line in path.read_text().splitlines()] == [label, second]


@pytest.mark.parametrize('field,value', [
    ('case_hash', ''), ('page_hash', 'A' * 64), ('policy_id', 'wrong'),
    ('rubric_id', 'filler'), ('decision', 'yes'), ('rationale', '  '),
    ('reviewer', None), ('timestamp', '2026-11-10'),
    ('timestamp', '2026-11-10T12:00:00'), ('timestamp', 'invalid'),
])
def test_invalid_label_does_not_create_output(tmp_path, label, field, value):
    path = tmp_path / 'labels.jsonl'
    with pytest.raises(ValueError):
        helper.append_label(path, {**label, field: value})
    assert not path.exists()


@pytest.mark.parametrize('value', [None, [], {}, {'decision': 'accept'}])
def test_empty_or_incomplete_labels_are_rejected(value):
    with pytest.raises(ValueError):
        helper.validate_label(value)


def test_unknown_fields_and_partial_log_are_rejected(tmp_path, label):
    with pytest.raises(ValueError):
        helper.validate_label({**label, 'typo': 'extra'})
    path = tmp_path / 'labels.jsonl'
    path.write_text('{')
    with pytest.raises(ValueError, match='newline'):
        helper.append_label(path, label)
    assert path.read_text() == '{'


def test_rubric_ids_match_shipped_checklist_and_are_not_reported_rules():
    text = (ROOT / 'skill/docs-review/references/rubric.md').read_text()
    assert set(re.findall(r'^\| `([a-z]+(?:-[a-z]+)+)` \|', text, re.M)) == helper.RUBRIC_IDS
    import yaml
    reported = yaml.safe_load((ROOT / 'skill/docs-lint/config/rules.yaml').read_text())['rules']
    assert not helper.RUBRIC_IDS.intersection(reported)


def test_every_candidate_and_timezone_offset_are_valid(label):
    for rubric_id in helper.RUBRIC_IDS:
        for decision in ('accept', 'reject'):
            entry = {**label, 'rubric_id': rubric_id, 'decision': decision,
                     'timestamp': '2026-11-10T12:00:00+01:00'}
            assert helper.validate_label(entry) == entry


def test_cli_file_stdin_and_error_paths(tmp_path, label):
    source = tmp_path / 'label.json'
    output = tmp_path / 'labels.jsonl'
    source.write_text(json.dumps(label))
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    for source_arg, stdin in ((str(source), None), ('-', json.dumps(label))):
        result = subprocess.run([sys.executable, str(SCRIPT), source_arg, '--out', str(output)],
                                input=stdin, capture_output=True, text=True, env=env)
        assert result.returncode == 0, result.stderr
        assert 'Appended reviewer judgment:' in result.stdout
    before = output.read_bytes()
    for content in ('', '{', 'null', '{}'):
        result = subprocess.run([sys.executable, str(SCRIPT), '-', '--out', str(output)],
                                input=content, capture_output=True, text=True, env=env)
        assert result.returncode == 2
        assert 'label rejected:' in result.stderr
        assert output.read_bytes() == before
    result = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / 'missing'), '--out', str(output)],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 2
    result = subprocess.run([sys.executable, str(SCRIPT), str(source), '--out', str(tmp_path / 'absent' / 'labels.jsonl')],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 2
    assert 'label rejected:' in result.stderr
