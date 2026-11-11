import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
SKILL = Path(os.environ.get('DOCS_GATE_SKILL', ROOT / 'skill'))
SHARED = SKILL / 'docs-review/scripts'
sys.path.insert(0, str(SHARED))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


api = load('phase_c_api', SKILL / 'docs-test/scripts/apicheck.py')
reuse = load('phase_c_reuse', SKILL / 'docs-maintain/scripts/maintain.py')
lint = load('phase_c_lint', SKILL / 'docs-lint/scripts/lint.py')


@pytest.mark.parametrize('mode', ['review', 'draft'])
def test_openapi_remains_strict_in_both_modes(mode):
    assert api.POLICY.rules['openapi-field-exists'].strict_for('payments', mode)


@pytest.mark.parametrize('mode', ['review', 'draft'])
def test_leak_rules_are_strict_and_draft_only(tmp_path, mode):
    page = tmp_path / 'page.md'
    page.write_text('PrivateFixture https://team.slack.com/archives/C1/p2\n')
    names = tmp_path / 'names.txt'
    names.write_text('PrivateFixture\n')
    found = lint.run([page], 'payments', ['leak-names', 'leak-internal'], mode=mode, names=names)
    assert {f.rule for f in found} == ({'leak-names', 'leak-internal'} if mode == 'draft' else set())
    assert all(f.strict for f in found)


def test_composed_ref_inventory_and_cycle():
    schema = json.loads((ROOT / 'dev/fixtures/openapi.json').read_text())
    schema['components']['schemas']['Shared']['properties'] = {'recursive': {'$ref': '#/components/schemas/Shared'}}
    schema['parameters'] = [{'schema': {'enum': ['unowned']}}]
    keys, enums, free = api.inventory(schema)
    assert {'internal_account_id', 'rows', 'amount', 'currency', 'description', 'recursive'} <= keys
    assert enums['currency'] == {'USD', 'EUR', 'pending', 'completed', 'unowned'}
    assert free == {'metadata'}
    schema['components']['schemas']['Base']['properties']['free_form'] = {'additionalProperties': {}}
    assert 'free_form' in api.inventory(schema)[2]
    for ref in ('#/missing', 'https://example.invalid/schema'):
        with pytest.raises(ValueError):
            api.inventory({'$ref': ref})


def test_schema_missing_invalid_and_empty_json(tmp_path):
    page = tmp_path / 'page.md'
    page.write_text('---\ntitle: Example\n---\n# Prepare\n')
    missing = tmp_path / 'schema.json'
    assert api.run([page], 'payments', None, spec=missing) == []
    assert api.spec_notes(missing) == ['openapi-field-exists not run: no spec snapshot']
    missing.write_text('null')
    with pytest.raises(ValueError, match='object with paths'):
        api.run([page], 'payments', None, spec=missing)
    assert list(api.examples('```json\ninvalid\n```\n')) == []
    assert list(api.examples('```json\n{"third_party":"anything"}\n```\n')) == []


def test_explicit_non_mt_scope_and_shell_variables():
    text = '<!-- docs-review: non-mt-json -->\n```json\n{"internal_account_id":"third-party"}\n```\n'
    assert list(api.examples(text)) == []
    text = '```curl\ncurl https://app.moderntreasury.com/api/example -d "$BODY"\n```\n'
    assert list(api.examples(text)) == []


def test_global_vocabulary_enum_arrays_and_free_maps():
    output = []
    api.check_fields([{'status': ['bad', 'pending'], 'metadata': {'secret': 'free'}}, {'rows': [{'typo/~': 1}]}],
                     {'status', 'metadata', 'rows'}, {'status': {'pending'}}, {'metadata'}, lambda *a: output.append(a))
    assert output == [('status', 'enum', 'bad', '/0/status'), ('typo/~', 'field', 'typo/~', '/1/rows/0/typo~1~0')]
    output.clear()
    api.check_fields(None, set(), {}, set(), lambda *a: output.append(a))
    assert not output


def test_names_beginning_newline_exact_boundaries_and_missing_list(tmp_path):
    found = []
    lint.check_names('\nFremont wyoming Fractionalized', ['Fremont', 'Wyoming', 'Fractional'], lambda *x: found.append(x))
    assert found == [(2, 'leak-names', 'Fremont'), (2, 'leak-names', 'wyoming')]
    assert lint.read_names(None) == []
    with pytest.raises(ValueError):
        lint.read_names(tmp_path / 'absent')


def test_internal_newline_prefix_boundaries_and_crm_context():
    found = []
    lint.check_internal('\nENG-1\nSalesforce 001AbcDefGhiJkl\n', lambda *x: found.append(x))
    assert found == [(2, 'leak-internal', 'ENG-1'), (3, 'leak-internal', '001AbcDefGhiJkl')]
    found.clear()
    lint.check_internal('ISO-20022 SHA-256 UTF-8 ACH-123\n' + 'x' * 100 + '\n001AbcDefGhiJkl', lambda *x: found.append(x))
    assert not found


def test_reuse_repository_definitions_exports_and_escaping(tmp_path):
    directory = tmp_path / 'components'
    directory.mkdir()
    (directory / 'parts.jsx').write_text('export function Exported() {}')
    assert {'parts', 'Exported'} <= reuse.definitions(tmp_path)
    found = []
    reuse.check_reuse('\\<Escaped>\n<Callout/>\n<Exported />\n<Missing icon="x" />', reuse.definitions(tmp_path), lambda *x: found.append(x))
    assert found == [(4, 'Missing')]
    found.clear()
    reuse.check_reuse('<EarlyAccess />\n<SandboxDetails />', set(), lambda *x: found.append(x))
    assert found == [(2, 'SandboxDetails')]


def test_candidate_raw_adjacent_and_registered_address():
    candidate = load('adjacent_candidate', ROOT / 'dev/gate/candidates/code_span_adjacent.py')
    assert len(candidate.scan('`a``b` and `c` `d`')) == 2
    assert not candidate.scan('`business_registeredprimary`')
    assert not candidate.scan('```text\n`a` `b`\n```\n')
    assert not candidate.scan('`a`\n\n`b`')
    assert len(candidate.scan('<td>`a` `b`</td>')) == 1


def test_independent_raw_spec_oracle():
    sys.path.insert(0, str(ROOT / 'dev/gate'))
    phase = load('phase_c_evidence', ROOT / 'dev/gate/phase_c.py')
    raw = '{"properties":{"known":{}},"enum":["allowed"],"example":"mentioned"}'
    findings = [dict(path='page.md', line=1, evidence=json.dumps(dict(kind=kind, value=value, pointer='/field')))
                for kind, value in [('field', 'missing'), ('enum', 'allowed'), ('enum', 'mentioned')]]
    report = phase.oracle(raw, findings)
    assert report['confirmed'] == 2
    assert report['agreement'] == 2 / 3
    assert phase.oracle(raw, [])['agreement'] is None
