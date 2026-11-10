import importlib.util
import json
from pathlib import Path
import socket
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / 'skill/docs-autopilot'
spec = importlib.util.spec_from_file_location('autopilot', SKILL / 'scripts/autopilot.py')
autopilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(autopilot)
CONFIG = yaml.safe_load((SKILL / 'config/autopilot.yaml').read_text())


def candidate(number=1):
    return dict(id=str(number), question='How is a Legal Entity created?', topics=['KYB'], checks={
        'signal': {'accounts': ['one', 'two'], 'staff_conceded': True},
        'locate': {'searched': True, 'judgment': 'not_answered'},
        'in_flight': {'repos': CONFIG['repositories'], 'notion_checked': True, 'open_prs': [], 'recent_merged_prs': [], 'notion_past_harvested': []},
        'answer': {'complexity': 'A1 Known', 'evidence': [{'label': 'VERIFIED', 'claim': 'Fixture only.', 'source': 'fixture'}]}})


def test_skill_safety_contract():
    text = (SKILL / 'SKILL.md').read_text()
    assert len(text.splitlines()) < 300
    for rule in ('Rule 1: never reference the customer.', 'Rule 2: Notion is the only write target. Never write to GitHub; never post to Slack channels. The single DM to Eric is the one exception.'):
        assert rule in text
    assert 'DRY-RUN' in text and '--live' in text
    assert sum(line.startswith('### ') for line in text.splitlines()) == 9


def test_admission_four_checks_and_unknown_policy():
    c = candidate()
    assert autopilot.admit(c, CONFIG)['status'] == 'Admitted'
    c['checks']['signal']['accounts'] = ['one', 'one']
    assert autopilot.admit(c, CONFIG)['status'] == 'Discarded'
    c = candidate()
    c['checks']['answer']['complexity'] = 'A3 Open'
    assert autopilot.admit(c, CONFIG)['status'] == 'Needs Human Answer'
    c['checks']['in_flight']['repos'] = []
    assert autopilot.admit(c, CONFIG)['status'] == 'Discarded'
    c = candidate()
    c['checks']['locate']['judgment'] = 'hard_to_find'
    assert autopilot.admit(c, CONFIG)['gap'] == 'Small discoverability gap'


def test_caps_and_prior_watching_refresh():
    candidates = [candidate(i) for i in range(12)]
    decisions = [autopilot.admit(c, CONFIG) for c in candidates]
    ranked = autopilot.rank(candidates, decisions, CONFIG)
    assert [r['disposition'] for r in ranked].count('Draft') == 3
    assert [r['disposition'] for r in ranked].count('Watching') == 5
    assert [r['disposition'] for r in ranked].count('Discarded') == 4
    prior = [{'id': 'notion-row', 'properties': {'Stage': 'Watching'}, 'candidate': candidate()}]
    carried = autopilot.carry([], prior)[0]
    assert carried['checks'] == {} and carried['prior_row_id'] == 'notion-row'
    assert autopilot.admit(carried, CONFIG)['status'] != 'Admitted'
    assert len(autopilot.carry([candidate()], prior)) == 1


def test_closure_needs_semantic_coverage_and_merge():
    rows = [{'id': 'row', 'properties': {'Stage': 'Needs SME Review'}}]
    prs = [{'number': 109, 'merged_at': '2026-11-05', 'url': 'https://example.invalid/109'}]
    proof = [{'row_id': 'row', 'reviewed': True, 'answers_question': False, 'pr_numbers': [109]}]
    assert autopilot.close_shipped(rows, prs, proof) == []
    proof[0]['answers_question'] = True
    assert autopilot.close_shipped(rows, prs, proof)[0]['properties']['Stage'] == 'Shipped elsewhere'
    prs[0]['merged_at'] = None
    assert not autopilot.close_shipped(rows, prs, proof)


def test_guard_blocks_network_and_writer_imports():
    previous = socket.create_connection
    with autopilot.WritesGuard():
        with pytest.raises(PermissionError):
            socket.create_connection(('example.invalid', 443))
        writer_spec = importlib.util.spec_from_file_location('autopilot_live_writers', SKILL / 'scripts/writers.py')
        with pytest.raises(RuntimeError, match='forbidden'):
            writer_spec.loader.exec_module(importlib.util.module_from_spec(writer_spec))
    assert socket.create_connection is previous
    assert 'autopilot_live_writers' not in sys.modules


def test_quiet_empty_outputs_and_no_overwrite(tmp_path):
    out = tmp_path / 'out'
    result = autopilot.dry_run({}, tmp_path, out, CONFIG)
    assert result['network_writes'] == 0
    assert (out / 'dm.txt').read_text() == 'nothing qualified\n'
    assert not (out / 'notion-rows.jsonl').read_text()
    with pytest.raises(ValueError, match='empty'):
        autopilot.dry_run({}, tmp_path, out, CONFIG)


def test_gate_blocks_customer_and_private_references(tmp_path):
    names = tmp_path / 'names.md'
    names.write_text('# Customer names\nFremont\n')
    draft = tmp_path / 'draft.md'
    draft.write_text('Fremont https://team.slack.com/archives/C1/p2\n')
    result = autopilot.gate(draft, names)
    assert not result['passed']
    assert {f['rule'] for f in result['violations']} == {'leak-names', 'leak-internal'}
    assert 'Fremont' not in json.dumps(result)


def test_unrecorded_flight_checks_do_not_pass():
    c = candidate()
    del c['checks']['in_flight']['open_prs']
    assert autopilot.admit(c, CONFIG)['status'] == 'Discarded'
    c = candidate()
    c['checks']['in_flight']['recent_merged_prs'] = [192]
    assert autopilot.admit(c, CONFIG)['status'] == 'Discarded'


def test_native_and_flat_watching_exports():
    native = {'results': [{'id': 'prior', 'properties': {
        'Stage': {'type': 'select', 'select': {'name': 'Watching'}},
        'Task name': {'type': 'title', 'title': [{'plain_text': candidate()['question']}]}}}]}
    carried = autopilot.carry([candidate()], native)
    assert len(carried) == 1 and carried[0]['prior_row_id'] == 'prior'
    flat = [{'id': 'prior', 'Stage': 'Watching', 'Task name': candidate()['question']}]
    assert autopilot.carry([], flat)[0]['checks'] == {}
    with pytest.raises(ValueError, match='stable row id'):
        autopilot.carry([], [{'Stage': 'Watching', 'Task name': 'Question'}])


def test_generalization_failure_prevents_drafting_and_does_not_echo_names(tmp_path):
    (tmp_path / 'customer-names.md').write_text('Fremont\n')
    (tmp_path / 'candidate.md').write_text('Use an address.\n')
    c = candidate()
    c.update(question='Does Fremont use an address?', draft_file='candidate.md', model_generalization_passed=True)
    out = tmp_path / 'out'
    result = autopilot.dry_run({'candidates': [c]}, tmp_path, out, CONFIG)
    assert result['rows'] == 0 and result['failures'][0]['reason'] == 'generalization failed'
    assert 'Fremont' not in (out / 'run.json').read_text()


@pytest.mark.parametrize('passes,expected', [(1, 'Ready to Push'), (2, 'Ready to Push'), (3, 'Needs SME Review')])
def test_fresh_review_one_revision_limit(tmp_path, passes, expected):
    (tmp_path / 'customer-names.md').write_text('# No names\n')
    (tmp_path / 'draft.md').write_text('Use a verified address.\n')
    c = candidate()
    c.update(draft_file='draft.md', model_generalization_passed=True, validation={'strict_failures': 0},
             review=dict(strict_failures=0, rubric_passed=True, money_losing_mistake=False, fresh_reviewer=True, passes=passes))
    out = tmp_path / 'out'
    autopilot.dry_run({'candidates': [c]}, tmp_path, out, CONFIG)
    row = json.loads((out / 'notion-rows.jsonl').read_text())
    assert row['properties']['Stage'] == expected
    assert row['properties']['Review Passes'] == passes
    assert row['properties']['Has Draft'] == (expected == 'Ready to Push')


def test_missing_checker_and_names_are_errors(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match='could not run'):
        autopilot.gate(tmp_path / 'absent.md', tmp_path / 'absent-names.md')
    monkeypatch.setattr(autopilot, 'HERE', tmp_path / 'docs-autopilot/scripts')
    with pytest.raises(ValueError, match='not installed'):
        autopilot.gate(tmp_path / 'draft.md', tmp_path / 'names.md')


def test_every_subagent_brief_restates_both_rules():
    text = (SKILL / 'references/subagent-briefs.md').read_text()
    sections = text.split('## ')[1:]
    assert len(sections) == 5
    for section in sections:
        assert 'Rule 1: never reference the customer.' in section
        assert 'Rule 2: Notion is the only write target. Never write to GitHub; never post to Slack channels. The single DM to Eric is the one exception.' in section


def test_shipped_watching_rows_do_not_consume_draft_cap(tmp_path, monkeypatch):
    (tmp_path / 'draft.md').write_text('Use a verified address.\n')
    candidates = [candidate(i) for i in range(4)]
    for i, c in enumerate(candidates):
        c.update(question=f'Generalized address question {i}?', draft_file='draft.md', model_generalization_passed=True,
                 validation={'strict_failures': 0}, review=dict(strict_failures=0, rubric_passed=True,
                 money_losing_mistake=False, fresh_reviewer=True, passes=1))
    prior = [{'id': 'shipped-row', 'properties': {'Stage': 'Watching'}, 'candidate': candidates[0]}]
    bundle = dict(candidates=candidates, prior_rows=prior,
                  merged_prs=[dict(number=176, merged_at='2026-09-04', url='https://example.invalid/176')],
                  coverage=[dict(row_id='shipped-row', reviewed=True, answers_question=True, pr_numbers=[176])])
    monkeypatch.setattr(autopilot, 'generalization', lambda *args: dict(passed=True, violations=[]))
    out = tmp_path / 'out'
    result = autopilot.dry_run(bundle, tmp_path, out, CONFIG)
    rows = [json.loads(line) for line in (out / 'notion-rows.jsonl').read_text().splitlines()]
    assert result['rows'] == 4
    assert sum(bool(r.get('body', {}).get('Draft')) for r in rows) == CONFIG['draft_cap']
    assert rows[0]['properties']['Stage'] == 'Shipped elsewhere'
