import importlib.util
import json
from pathlib import Path
import re
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


def test_installed_skills_have_no_machine_local_paths():
    for path in (ROOT / 'skill').rglob('*'):
        if path.is_file() and path.suffix in ('.py', '.md', '.yaml', '.json', '.txt'):
            assert not re.search(r'~/work|/home/ubuntu', path.read_text()), path


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
    assert row['properties']['Has Draft'] == '__YES__'


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
    assert sum('## Draft\n' in r['body'] for r in rows) == CONFIG['draft_cap']
    assert rows[0]['properties']['Stage'] == 'Shipped elsewhere'


def test_mcp_payload_is_verbatim_flat_properties_and_markdown():
    c = candidate()
    c.update(effort_level='Small', product_area=['Payments'])
    decision = autopilot.admit(c, CONFIG)
    record = autopilot.row(c, decision, 'Ready to Push', '2026-11-10', 'Create a record.')
    payload = autopilot.notion_payload(record)
    assert set(payload) == {'op', 'properties', 'body'} and payload['op'] == 'create'
    p = payload['properties']
    assert set(p) == {'Task name', 'Stage', 'Signal Count', 'Answer Complexity', 'Destination', 'Target Path',
                      'Has Draft', 'Open Questions', 'Sources', 'Review Passes', 'Product Area', 'Model', 'Effort level',
                      'Admission', 'date:Run Date:start', 'date:Run Date:end', 'date:Run Date:is_datetime'}
    assert p['Has Draft'] == '__YES__' and p['Product Area'] == '["Payments"]'
    assert p['date:Run Date:start'] == '2026-11-10' and p['date:Run Date:end'] is None
    assert p['Signal Count'] == 2 and p['Effort level'] == 'Small' and p['Model'] == 'Unknown'
    assert '## Draft\n\n`````markdown\nCreate a record.\n`````' in payload['body']
    record.update(operation='update', id='notion-page')
    assert autopilot.notion_payload(record)['page_id'] == 'notion-page'
    record['id'] = ''
    with pytest.raises(ValueError, match='page_id'):
        autopilot.notion_payload(record)
    record['operation'] = 'delete'
    with pytest.raises(ValueError, match='operation'):
        autopilot.notion_payload(record)


def test_writers_has_no_publish_and_live_cli_has_no_writer_dispatch():
    import ast
    tree = ast.parse((SKILL / 'scripts/writers.py').read_text())
    assert not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))
    text = (SKILL / 'scripts/autopilot.py').read_text()
    assert 'writers.publish' not in text and 'spec_from_file_location' not in text
    assert "'LIVE-PLAN' if args.live else 'DRY-RUN'" in text


@pytest.mark.parametrize('stage', ['Harvested', 'Researched', 'Drafted', 'In Review', 'Ready to Push',
                                 'Needs SME Review', 'Needs Human Answer', 'Not Generalizable',
                                 'Watching', 'Shipped elsewhere'])
@pytest.mark.parametrize('draft', [None, '', '<Callout>Text</Callout>\n```json\n{}\n```'])
def test_body_template_and_draft_invariant_for_every_stage(stage, draft):
    c = candidate()
    source = 'https://example.invalid/source'
    c.update(sources=[source], target_path='docs/page.md', open_questions=['Confirm ' + source])
    decision = autopilot.admit(c, CONFIG)
    decision['gap'] = 'Missing guidance: ' + source
    record = autopilot.row(c, decision, stage, '2026-11-10', draft)
    payload = autopilot.notion_payload(record)
    body = payload['body']
    assert (payload['properties']['Has Draft'] == '__YES__') == (draft is not None)
    assert ('\n## Draft\n' in '\n' + body) == (draft is not None)
    expected = (['Why this exists', 'Proposed target', 'Draft', 'Review record', 'Signal'] if draft is not None else
                ['Why this is blocked', 'What was established', 'What is needed to unblock', 'Signal'])
    assert re.findall(r'^## (.+)$', body, re.M) == expected
    if draft is not None:
        assert '`````markdown\n' + draft + '\n`````' in body
    assert source not in body.split('## Signal\n')[0]
    assert source in body.split('## Signal\n')[1] and payload['properties']['Sources'] == source


def test_digest_quiet_plural_and_row_links():
    assert autopilot.digest([]) == 'nothing qualified\n'
    c = candidate()
    record = autopilot.row(c, autopilot.admit(c, CONFIG), 'Needs SME Review', '2026-11-10', 'Text')
    dm = autopilot.digest([record])
    assert '1 draft;' in dm and '0 watching items;' in dm
    assert f'{c["question"]} | Needs SME Review | {{{{notion_url:{c["id"]}}}}}' in dm
    assert '2 drafts;' in autopilot.digest([record, record])
    for stage, noun in [('Watching', 'watching item'), ('Needs Human Answer', 'open question'), ('Shipped elsewhere', 'shipped item')]:
        record = autopilot.row(c, autopilot.admit(c, CONFIG), stage, '2026-11-10')
        assert '1 ' + noun in autopilot.digest([record])
        assert '2 ' + noun + 's' in autopilot.digest([record, record])


@pytest.mark.parametrize('text,rule', [('Use this — then continue.', 'em-dash'), ('Use our powerful API.', 'marketing-words')])
@pytest.mark.parametrize('surface', ['draft', 'body', 'dm'])
def test_generated_text_rejected_before_output(tmp_path, monkeypatch, text, rule, surface):
    c = candidate()
    if surface == 'draft':
        (tmp_path / 'draft.md').write_text(text)
        c.update(draft_file='draft.md', model_generalization_passed=True)
    elif surface == 'body':
        c['open_questions'] = [text]
    else:
        c['question'] = text
    if surface != 'draft':
        c['checks']['answer']['complexity'] = 'A3 Open'
    monkeypatch.setattr(autopilot, 'generalization', lambda *args: dict(passed=True, violations=[]))
    out = tmp_path / 'out'
    with pytest.raises(ValueError, match='generated-text check failed.*' + rule):
        autopilot.dry_run({'candidates': [c]}, tmp_path, out, CONFIG)
    assert not out.exists()
