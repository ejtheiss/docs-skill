#!/usr/bin/env python3
"""Scaffold model-authored drafts and validate bounded iterations; never invent prose."""
from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import yaml

from mode_support import CONFIG, HERE, PROJECTS, review, revision, source, read_snapshot, snapshot_source

TEMPLATES = HERE.parent / 'references/templates'
DESTINATIONS = tuple(sorted(p.stem for p in TEMPLATES.glob('*.md')))
DEFAULT_MAX = yaml.safe_load((CONFIG / 'draft.yaml').read_text())['max_iterations']
SMALL_EDIT = re.compile(r'\APath: `([^`\n]+)`\nHeading: ([^\n]+)\n\s*Quote:\n\s*```text\n(.*?)\n```\n\s*Replacement:\n\s*```text\n(.*?)\n```\s*\Z', re.S)


def brief_data(path: Path) -> dict:
    brief = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(brief, dict):
        raise ValueError('brief must be a mapping')
    if not isinstance(brief.get('question'), str) or not brief['question'].strip():
        raise ValueError('brief requires a question')
    if (not isinstance(brief.get('destination'), str) or brief['destination'] not in DESTINATIONS or
            not isinstance(brief.get('project'), str) or brief['project'] not in PROJECTS):
        raise ValueError('brief requires a known destination and project')
    evidence = brief.get('evidence')
    if not isinstance(evidence, list) or not evidence:
        raise ValueError('brief requires verified evidence items')
    for item in evidence:
        if (not isinstance(item, dict) or item.get('verified') is not True or
                any(not isinstance(item.get(k), str) or not item[k].strip() for k in ('claim', 'source'))):
            raise ValueError('each evidence item needs claim, source and verified: true')
    if brief['destination'] == 'small-edit':
        target = brief.get('target')
        if not isinstance(target, dict) or any(not isinstance(target.get(k), str) or not target[k].strip()
                                               for k in ('repo', 'path', 'heading')):
            raise ValueError('small-edit requires target repo, path and heading')
        relative = Path(target['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('small-edit path must be repository-relative without ..')
        if 'ref' in target and (not isinstance(target['ref'], str) or not target['ref'].strip()):
            raise ValueError('target ref must be a nonempty string')
    fields = brief.get('fields', {})
    if not isinstance(fields, dict) or any(not isinstance(v, str) for v in fields.values()):
        raise ValueError('fields must map placeholder names to authored strings')
    return brief


def fingerprint(brief: dict) -> str:
    return hashlib.sha256(json.dumps(brief, sort_keys=True).encode()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def scaffold(brief_path: Path, out: Path, maximum: int, snapshot_dir: Path | None = None) -> dict:
    if maximum < 1:
        raise ValueError('max iterations must be positive')
    brief = brief_data(brief_path)
    if snapshot_dir is not None:
        read_snapshot(snapshot_dir)
        brief['snapshot'] = str(snapshot_dir.resolve())
    if out.exists() and any(out.iterdir()):
        raise ValueError('output directory must be empty; existing work is never overwritten')
    out.mkdir(parents=True, exist_ok=True)
    fields = dict(brief.get('fields', {}))
    if brief['destination'] == 'small-edit':
        fields.update(path=brief['target']['path'], heading=brief['target']['heading'])
    template = (TEMPLATES / (brief['destination'] + '.md')).read_text()
    template = re.sub(r'\{\{([a-z_]+)\}\}', lambda m: fields.get(m[1], m[0]), template)
    if brief['destination'] == 'api-reference-change':
        (out / 'instructions.md').write_text(template, encoding='utf-8')
        write_json(out / 'candidate.json', dict(target='reference/modern-treasury-api.json', patch=[]))
    else:
        (out / 'candidate.md').write_text(template, encoding='utf-8')
    (out / 'brief.yaml').write_text(yaml.safe_dump(brief, sort_keys=False), encoding='utf-8')
    state = dict(iterations=0, max_iterations=maximum, brief_hash=fingerprint(brief))
    write_json(out / 'state.json', state)
    return dict(status='scaffolded; model authors the candidate', destination=brief['destination'], **state)


def section_span(text: str, heading: str) -> tuple[int, int]:
    lines = text.splitlines(keepends=True)
    offset, start, level, ends, matches, fence = 0, None, 0, [], [], ''
    for line in lines:
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            fence = '' if fence and marker[1][0] == fence else fence or marker[1][0]
        found = None if fence else re.match(r'^(#{1,6})\s+(.+?)\s*#*\s*$', line.strip())
        if found:
            if start is not None and len(found[1]) <= level:
                ends.append((start, offset))
                start = None
            if found[2] == heading:
                matches.append(offset)
                start, level = offset, len(found[1])
        offset += len(line)
    if start is not None:
        ends.append((start, len(text)))
    if len(matches) != 1:
        raise ValueError('target heading must exist exactly once at the ref')
    return next(span for span in ends if span[0] == matches[0])


def small_edit(text: str, brief: dict, out: Path, snapshot_dir: Path | None = None) -> dict:
    match = SMALL_EDIT.fullmatch(text)
    if not match:
        raise ValueError('small-edit must contain only Path, Heading, Quote and Replacement in template format')
    path, heading, quoted, replacement = match.groups()
    target = brief['target']
    if path != target['path'] or heading != target['heading']:
        raise ValueError('candidate path and heading must match the brief target')
    if not quoted.strip() or not replacement.strip() or quoted == replacement:
        raise ValueError('quote and replacement must be nonempty and different')
    repo = Path(target['repo']).expanduser()
    ref = target.get('ref', 'origin/v2.0')
    provenance = {}
    snapshot_dir = snapshot_dir or brief.get('snapshot')
    if snapshot_dir:
        original, entry = snapshot_source(Path(snapshot_dir), repo.name, path)
        sha, ref = entry['sha'], 'snapshot'
        provenance = dict(source_url=entry['url'])
    else:
        sha = revision(repo, ref)
        original = source(repo, sha, path)
    start, end = section_span(original, heading)
    section = original[start:end]
    if section.count(quoted) != 1:
        raise ValueError('quote must exist verbatim exactly once under the target heading at the ref')
    changed = original[:start] + section.replace(quoted, replacement, 1) + original[end:]
    touched = set()
    for tag, _a, _b, a, b in SequenceMatcher(None, original.splitlines(), changed.splitlines(), autojunk=False).get_opcodes():
        if tag in ('insert', 'replace'):
            touched.update(range(a + 1, b + 1))
    if not touched:
        raise ValueError('replacement must change at least one current line')
    with tempfile.TemporaryDirectory(prefix='draft-review-') as folder:
        candidate = Path(folder) / 'page.md'
        candidate.write_text(changed, encoding='utf-8')
        report = review(candidate, brief['project'])
    findings = [f for f in report['findings'] if f['line'] in touched]
    return dict(strict_failures=sum(f['strict'] for f in findings), findings=findings,
                changed_lines=sorted(touched), repo=str(repo), ref=ref, sha=sha,
                policy=report['scorecard']['policy'], scope='changed lines only; existing findings outside them excluded', **provenance)


def spec_patch(text: str) -> dict:
    data = json.loads(text)
    if not isinstance(data, dict) or set(data) != {'target', 'patch'} or data['target'] != 'reference/modern-treasury-api.json':
        raise ValueError('API reference output must target reference/modern-treasury-api.json, not Markdown')
    if not isinstance(data['patch'], list) or not data['patch']:
        raise ValueError('spec patch must contain at least one JSON Patch operation')
    for op in data['patch']:
        if not isinstance(op, dict) or op.get('op') not in ('add', 'replace', 'remove', 'test', 'move', 'copy'):
            raise ValueError('invalid JSON Patch operation')
        if not isinstance(op.get('path'), str) or not op['path'].startswith('/'):
            raise ValueError('JSON Patch path must be a non-root JSON pointer')
        if op['op'] in ('add', 'replace', 'test') and 'value' not in op:
            raise ValueError('JSON Patch operation requires value')
        if op['op'] in ('move', 'copy') and (not isinstance(op.get('from'), str) or not op['from'].startswith('/')):
            raise ValueError('JSON Patch operation requires from pointer')
    return dict(strict_failures=0, findings=[], scope='spec patch structure only; product correctness is reviewer judgment')


def validate(out: Path, maximum: int | None = None, snapshot_dir: Path | None = None) -> dict:
    brief = brief_data(out / 'brief.yaml')
    state = json.loads((out / 'state.json').read_text())
    if (not isinstance(state, dict) or not isinstance(state.get('brief_hash'), str) or
            type(state.get('iterations')) is not int or state['iterations'] < 0 or
            type(state.get('max_iterations')) is not int or state['max_iterations'] < 1):
        raise ValueError('invalid draft iteration state')
    if state['brief_hash'] != fingerprint(brief):
        raise ValueError('brief changed; scaffold a new evidence-bound draft')
    limit = state['max_iterations'] if maximum is None else min(state['max_iterations'], maximum)
    if limit < 1 or state['iterations'] >= limit:
        return dict(status='iteration limit reached; stop for reviewer judgment', strict_failures=1,
                    iterations=state['iterations'], max_iterations=limit)
    state['iterations'] += 1
    state['max_iterations'] = limit
    write_json(out / 'state.json', state)
    try:
        filename = 'candidate.json' if brief['destination'] == 'api-reference-change' else 'candidate.md'
        text = (out / filename).read_text(encoding='utf-8')
        if '{{' in text or '}}' in text:
            raise ValueError('candidate still contains unfilled placeholders')
        if brief['destination'] == 'small-edit':
            result = small_edit(text, brief, out, snapshot_dir)
        elif brief['destination'] == 'api-reference-change':
            result = spec_patch(text)
        else:
            report = review(out / filename, brief['project'])
            result = dict(strict_failures=report['scorecard']['strict_failures'], findings=report['findings'],
                          policy=report['scorecard']['policy'], scope='whole new page')
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        result = dict(strict_failures=1, findings=[], error=str(exc))
    result.update(iterations=state['iterations'], max_iterations=limit,
                  status='valid' if result['strict_failures'] == 0 else 'edit and validate again')
    write_json(out / 'validation.json', result)
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    validating = bool(argv and argv[0] == 'validate')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='draft directory for validate, otherwise a YAML brief')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--max-iterations', type=int)
    parser.add_argument('--snapshot', type=Path, help='plain-directory snapshot for small-edit quote validation')
    args = parser.parse_args(argv[1:] if validating else argv)
    if args.max_iterations is not None and args.max_iterations < 1:
        parser.error('--max-iterations must be positive')
    if not validating and args.out is None:
        parser.error('scaffolding requires --out')
    try:
        result = validate(args.input, args.max_iterations, args.snapshot) if validating else scaffold(args.input, args.out, args.max_iterations or DEFAULT_MAX, args.snapshot)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f'draft error: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return int(bool(result.get('strict_failures', 0)))


if __name__ == '__main__':
    raise SystemExit(main())
