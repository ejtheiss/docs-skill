import importlib.util
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = ROOT / 'skill/docs-review/references/templates'
spec = importlib.util.spec_from_file_location('template_gate', ROOT / 'dev/gate/gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

SAMPLES = {
    'title': 'Example documentation', 'heading': 'Prepare an example workflow',
    'purpose': 'Create an example record and verify the result.',
    'prerequisite': 'Confirm access to the test environment.',
    'action': 'Create a record.', 'verification': 'Retrieve the record and check its status.',
    'link_label': 'Workflow guidance', 'slug': 'workflow-guidance',
    'transition': 'The record enters the documented state.',
    'event': 'example.completed', 'correlation_field': 'id', 'state_field': 'status',
    'next_action': 'Retrieve the record.',
    'bank_transition': 'The bank will provide the final result.',
    'retry_guidance': 'Reuse the documented idempotency key when retrying the same operation.',
    'failure_guidance': 'Stop the workflow on failure and inspect the documented error.',
    'spec_pointer': '/paths/~1example/get/description',
    'evidence': 'Compare the current schema with the verified product contract.',
    'schema_change': '{}', 'concept': 'Describe the supported model.',
    'constraint': 'Limit the example to the verified configuration.',
    'path': 'docs/example.md', 'quote': 'Check the record.',
    'replacement': 'Retrieve the record and check its status.',
}


def render_template(path):
    text = re.sub(r'\{\{([a-z_]+)\}\}', lambda m: SAMPLES[m[1]], path.read_text())
    assert '{{' not in text
    if path.name == 'small-edit.md':
        assert not text.startswith('---') and not re.search(r'^#', text, re.M)
        # The deliverable is a fragment, not a new page; wrap it only for draft validation.
        text = '---\ntitle: Edit validation\n---\n# Change details\n\n' + text
    return text


@pytest.mark.parametrize('template', sorted(TEMPLATES.glob('*.md')), ids=lambda p: p.name)
def test_filled_template_has_no_strict_findings(template, tmp_path):
    path = tmp_path / template.name
    path.write_text(render_template(template))
    report = gate.check([path], ['--mode', 'draft'], project='payments')
    assert report['scorecard']['strict_failures'] == 0, report['findings']


def test_destination_templates_and_integration_gate():
    assert {p.name for p in TEMPLATES.glob('*.md')} == {
        'small-edit.md', 'docs-page.md', 'integration-guide.md',
        'api-reference-change.md', 'topics-page.md',
    }
    integration = render_template(TEMPLATES / 'integration-guide.md')
    assert integration.count('\n***\n') == 2
    assert 'wait for `example.completed` before step 2' in integration
    reference = (TEMPLATES / 'api-reference-change.md').read_text()
    assert 'reference/modern-treasury-api.json' in reference
    assert 'not Markdown edits' in reference


def test_guide_rule_ids_and_housekeeping():
    import yaml
    rules = yaml.safe_load((ROOT / 'skill/docs-lint/config/rules.yaml').read_text())['rules']
    assert len(rules) == 32
    for page in (ROOT / 'skill/docs-review/style').glob('*.md'):
        text = page.read_text()
        assert 'Compiled from Notion' not in text
        assert 'Authored but not enforced' not in text
        assert 'docs-style-review' not in text
        for clause in re.findall(r'\(([^()\n]*)\)', text):
            for rule in re.findall(r'`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`', clause):
                assert rule in rules, (page.name, rule)
    for name in ('style/00-index.md', 'SKILL.md'):
        assert '08-readme-conventions.md' in (ROOT / 'skill/docs-review' / name).read_text()
