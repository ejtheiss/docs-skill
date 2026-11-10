"""Independent confirmation and supplementary measurements for Phase C."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import gate

ROOT = gate.ROOT
RULES = ('openapi-field-exists', 'reuse-undefined-block', 'leak-names', 'leak-internal')
CORPUS = Path.home() / 'work/corpus-head'
SPEC = CORPUS / 'docs-readme-platform/reference/modern-treasury-api.json'


def oracle(raw, findings):
    """No checker imports or ref traversal: raw keys and independently decoded enum arrays."""
    enum_values = set()
    for array in re.findall(r'"enum"\s*:\s*(\[[^\]]*\])', raw):
        enum_values.update(v for v in json.loads(array) if isinstance(v, str))
    decisions = []
    for finding in findings:
        evidence = json.loads(finding['evidence'])
        value = evidence['value']
        raw_absent = not re.search(re.escape(json.dumps(value)) + (r'\s*:' if evidence['kind'] == 'field' else ''), raw)
        confirmed = raw_absent if evidence['kind'] == 'field' else value not in enum_values
        decisions.append(dict(path=finding['path'], line=finding['line'], **evidence,
                              confirmed=confirmed, literal_raw_absent=raw_absent))
    return dict(findings=len(decisions), confirmed=sum(d['confirmed'] for d in decisions),
                agreement=sum(d['confirmed'] for d in decisions) / len(decisions) if decisions else None,
                literal_raw_agreement=sum(d['literal_raw_absent'] for d in decisions) / len(decisions) if decisions else None,
                decisions=decisions)


def supplementary():
    spec = importlib.util.spec_from_file_location('adjacency', ROOT / 'dev/gate/candidates/code_span_adjacent.py')
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)
    files = sorted(CORPUS.rglob('*.md'))
    findings = [f for path in files for f in candidate.measure(path)]
    report = gate.check([CORPUS], ['--mode', 'review'])
    api = [f for f in report['findings'] if f['rule'] == 'openapi-field-exists']
    names = {}
    for label, name_file in [('empty', 'empty-names.txt'), ('fixture', 'customer-names.txt')]:
        for mode in ('review', 'draft'):
            checked = gate.check([CORPUS], ['--mode', mode, '--names', str(ROOT / 'dev/gate/fixtures' / name_file)])
            names[label + '-' + mode] = gate.measure('leak-names', files, checked['findings'])
    blocks = [f for f in report['findings'] if f['rule'] == 'reuse-undefined-block']
    result = dict(oracle=oracle(SPEC.read_text(), api),
                  spec=dict(path=str(SPEC), sha256=hashlib.sha256(SPEC.read_bytes()).hexdigest()),
                  adjacent=gate.measure('code-span-adjacent', files, findings), adjacent_findings=findings,
                  candidate_admission='NOT ADMITTED: measurement only; independent semantic oracle and adjudicated precision absent. Adjacent enum/options spans are not inherently errors.',
                  registered_address_caught=bool(candidate.scan('`business_registeredprimary`')),
                  registered_address_cells=[dict(path=str(path), line=index, text=line.strip(), caught=bool(candidate.scan(line)))
                                            for path in files for index, line in enumerate(path.read_text().splitlines(), 1)
                                            if 'business_registeredprimary' in line],
                  names=names, undefined_blocks=dict(Counter(f['evidence'] for f in blocks)),
                  undefined_block_witnesses=blocks,
                  top_openapi=Counter((json.loads(f['evidence'])['kind'], json.loads(f['evidence'])['value']) for f in api).most_common(10))
    return result


def append_evidence(path, result=None):
    result = supplementary() if result is None else result
    data = json.loads(path.with_suffix('.json').read_text())
    data['supplementary'] = result
    path.with_suffix('.json').write_text(json.dumps(data, indent=2) + '\n')
    original = path.read_text()
    before, api_section = original.split('## openapi-field-exists', 1)
    api_section = api_section.replace('Gate 5 (independent oracle): NOT ESTABLISHED by this harness.',
                                      'Gate 5 (independent oracle): see independent raw-key / enum-array confirmation below.', 1)
    original = before + '## openapi-field-exists' + api_section
    rows = ['\n## Independent OpenAPI confirmation', '',
            f"Spec: `{result['spec']['path']}`; SHA256 `{result['spec']['sha256']}`.",
            f"Raw key / enum-array oracle: {result['oracle']['confirmed']}/{result['oracle']['findings']} agreement = {result['oracle']['agreement']:.3f}.",
            f"Literal raw-text absence only: {result['oracle']['literal_raw_agreement']:.3f}; enum strings in examples/prose are not enum declarations.",
            'This confirms absence from this snapshot, NOT a documentation error or endpoint validity. No blind adjudication claim.',
            '', '## OpenAPI top 10 diagnostic groups', '', '| Kind | Value | Findings | Representative path:line |', '|---|---|---:|---|']
    for (kind, value), count in result['top_openapi']:
        witness = next(d for d in result['oracle']['decisions'] if d['kind'] == kind and d['value'] == value)
        rows.append(f'| {kind} | `{value}` | {count} | {witness["path"]}:{witness["line"]} |')
    rows += ['', 'Findings cluster in Ledgers and webhook event envelopes, consistent with snapshot gaps, but snapshot absence alone cannot distinguish gaps from stale or incorrect docs. In particular, `posted`, `residential`, file attributes and webhook `event` require contract verification, not automatic doc edits. MT curl literal JSON is supported; shell variables, non-JSON bodies and unanchored/third-party JSON are excluded. Metadata and schema-declared free-form maps are excluded by policy.',
             '', '## Undefined component confirmation', '', json.dumps(result['undefined_blocks'], sort_keys=True),
             'Escaped angle-bracket placeholders and fenced/inline examples are not component uses.',
             '', '## Customer-name measurements', 'Fixture names are test data, not a default customer list. Wyoming can be legitimate public content.']
    for name, measurement in result['names'].items():
        rows += [f'### {name}', '| Project | Pages fired / pages | Findings |', '|---|---:|---:|']
        for project, values in measurement['projects'].items():
            rows.append(f'| {project} | {values["fired"]}/{values["pages"]} | {values["findings"]} |')
    adjacent = result['adjacent']
    rows += ['', '## code-span-adjacent: measurement-only candidate', result['candidate_admission'],
             'Definition: lexical single-backtick spans separated only by whitespace or nothing, within one prose/table block; fences, frontmatter and comments excluded. The raw `` `a``b` `` spelling is counted lexically even though CommonMark can parse it as one span.',
             '| Project | Pages fired / pages | Pairs |', '|---|---:|---:|']
    for project, values in adjacent['projects'].items():
        rows.append(f'| {project} | {values["fired"]}/{values["pages"]} | {values["findings"]} |')
    rows += [f'Firing witness: {adjacent["firing"]}', f'Non-firing witness: {adjacent["non_firing"]}',
             f'`business_registeredprimary` caught: {result["registered_address_caught"]}. It is one span, not adjacent spans.',
             f'Real corpus cell witnesses: {result["registered_address_cells"]}',
             'No shipped rule id, mutation threshold or admission claimed for this measurement-only candidate. Concatenated-identifiers candidate was not implemented.']
    rows += ['', '## Gate scope and admission qualifications',
             'Mutations target the mapped verdict functions; extraction, schema traversal and repository discovery are covered by integration fixtures and direct tests, not claimed as mutation-covered.',
             'Corpus leak-internal and leak-names rates are zero: no real firing witness exists; positive fixtures provide firing examples. Neither names list is a universal ban.',
             'The independent oracle confirms snapshot absence only; no blind human adjudication or runtime API confirmation was performed. The four requested checks ship as strict inventory/leak checks, not as proofs that the documentation is factually wrong.']
    path.write_text(original + '\n'.join(rows) + '\n')
    print('\n'.join(rows))


if __name__ == '__main__':
    append_evidence(Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else None)
