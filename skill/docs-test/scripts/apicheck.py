#!/usr/bin/env python3
"""docs-test: what has to be true of the API, not of the prose.

Whether a documented field exists in the schema, whether an enum value is one the code accepts,
whether an endpoint path and method are real, whether a webhook event name is emitted, whether a state
transition is reachable, whether a link resolves, and whether a documented request actually works when
a reader pastes it into a terminal.

This is the only tier that needs anything outside the docs - the monorepo, the network, or a sandbox
organization - which is what separates it from `docs-lint`'s JSON syntax check: that a body parses is a
property of the file, that its fields are real is a property of the API.

The shipped check compares the global field and enum vocabulary with a supplied offline snapshot.
It does not prove endpoint-specific validity, runtime behavior or completeness of the snapshot.

    python3 apicheck.py docs/ --spec reference/modern-treasury-api.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parents[2] / "docs-review" / "scripts"
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

import policy as policy_module  # noqa: E402
from contexts import add_arguments, file_context  # noqa: E402
from channels import fences  # noqa: E402
from findings import (  # noqa: E402
    Finding,
    collect_files,
    input_error,
    policy_stamp,
    render_text,
    report_order,
    scorecard,
    detect_project,
)

SUBSKILL = "test"
EMITS = frozenset({'openapi-field-exists'})

try:
    POLICY = policy_module.load("docs-test")
    POLICY.require(EMITS)
except policy_module.PolicyError as exc:  # pragma: no cover - exercised through the CLI
    sys.exit(f"policy error: {exc}")

RULES = {name: (rule.strict, rule.provenance) for name, rule in POLICY.rules.items()}
PROJECTS = POLICY.projects()


def resolve_spec(spec: Path | None = None) -> Path | None:
    value = spec if spec is not None else os.environ.get('DOCS_REVIEW_SPEC')
    return Path(value).expanduser() if value else None


def spec_notes(spec: Path | None = None, rules: list[str] | None = None) -> list[str]:
    if rules and not EMITS.intersection(rules):
        return []
    path = resolve_spec(spec)
    return ['openapi-field-exists not run: no spec snapshot'] if path is None or not path.exists() else []


def run(files: list[Path], project: str | None, rules: list[str] | None,
        mode: str = 'review', base: str | None = None, spec: Path | None = None) -> list[Finding]:
    if rules and not EMITS.intersection(rules):
        return []
    if spec_notes(spec, rules):
        return []
    spec = resolve_spec(spec)
    try:
        schema = json.loads(spec.read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(f'cannot load OpenAPI snapshot {spec}: {exc}') from exc
    if not isinstance(schema, dict) or not isinstance(schema.get('paths'), dict):
        raise ValueError('OpenAPI snapshot must be an object with paths')
    keys, enums, free = inventory(schema)
    findings = []
    rule = POLICY.rules['openapi-field-exists']
    settings = POLICY.values['openapi_scope']
    for path in files:
        if re.search(settings['exclude_paths'], str(path), re.I):
            continue
        text = path.read_text()
        active = detect_project(path, project, PROJECTS)
        context = file_context(path, mode, base)
        for line, payload in examples(text):
            def emit(key, kind, value, pointer):
                pattern = r'"' + re.escape(key) + r'"\s*:'
                location = re.search(pattern, payload)
                number = line + payload.count('\n', 0, location.start()) if location else line
                if rule.applies(active) and context.includes(rule.applies_to, number):
                    evidence = json.dumps(dict(kind=kind, value=value, pointer=pointer), sort_keys=True)
                    findings.append(Finding(str(path), number, rule.id, rule.strict_for(active), rule.says(kind=kind, value=value, pointer=pointer), evidence))
            check_fields(json.loads(payload), keys, enums, free, emit)
    return findings


def inventory(schema):
    keys, enums, free, visited, all_values = set(), {}, set(POLICY.words('openapi_free_keys')), set(), set()
    def visit(node, owner=None):
        if isinstance(node, list):
            for child in node:
                visit(child, owner)
        elif isinstance(node, dict):
            identity = (id(node), owner)
            if identity in visited:
                return
            visited.add(identity)
            if '$ref' in node:
                if not node['$ref'].startswith('#/'):
                    raise ValueError('external OpenAPI refs must be bundled into the offline snapshot')
                target = schema
                try:
                    for part in node['$ref'][2:].split('/'):
                        target = target[part.replace('~1', '/').replace('~0', '~')]
                except (KeyError, TypeError) as exc:
                    raise ValueError(f'unresolved OpenAPI ref: {node["$ref"]}') from exc
                visit(target, owner)
            if 'enum' in node:
                strings = {v for v in node['enum'] if isinstance(v, str)}
                all_values.update(strings)
                if owner:
                    enums.setdefault(owner, set()).update(strings)
            if owner and 'additionalProperties' in node and node['additionalProperties'] is not False and POLICY.values['openapi_scope']['schema_free_maps']:
                free.add(owner)
            for key, child in node.get('properties', {}).items():
                keys.add(key)
                visit(child, key)
            for name, child in node.items():
                if name != 'properties':
                    visit(child, owner)
    visit(schema)
    return keys, {key: all_values for key in enums}, free


def examples(text):
    settings = POLICY.values['openapi_scope']
    lines = text.splitlines(keepends=True)
    for token in fences(text):
        start = token.map[0]
        context = ''.join(lines[max(0, start - 5):start])
        if re.search(settings['exclude_context'], context):
            continue
        language = token.info.split()[0].lower() if token.info else ''
        payloads = []
        if language == 'json':
            payloads.append((start + 2, token.content))
        elif re.search(settings['mt_url'], token.content):
            try:
                words = shlex.split(token.content)
            except ValueError:
                continue
            for index, word in enumerate(words[:-1]):
                if word in ('-d', '--data', '--data-raw', '--data-binary'):
                    payload = words[index + 1]
                    offset = token.content.find(payload)
                    payloads.append((start + 2 + token.content.count('\n', 0, max(0, offset)), payload))
        for line, payload in payloads:
            try:
                data = json.loads(payload)
            except ValueError:
                continue
            serialized = json.dumps(data)
            mt_context = context if language == 'json' else token.content
            discriminator = isinstance(data, dict) and data.get('object') in POLICY.words('openapi_object_values')
            if discriminator or re.search(settings['mt_url'], mt_context) or any(re.search(r'"' + re.escape(key) + r'"\s*:', serialized) for key in POLICY.words('openapi_markers')):
                yield line, payload


def check_fields(value, keys, enums, free, emit, pointer=''):
    if isinstance(value, list):
        for index, item in enumerate(value):
            check_fields(item, keys, enums, free, emit, pointer + '/' + str(index))
    elif isinstance(value, dict):
        for key, item in value.items():
            path = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
            if key not in keys:
                emit(key, 'field', key, path)
            if key in free:
                continue
            values = item if isinstance(item, list) else [item]
            for scalar in values:
                if isinstance(scalar, str) and key in enums and scalar not in enums[key]:
                    emit(key, 'enum', scalar, path)
            check_fields(item, keys, enums, free, emit, path)


def print_rules() -> None:
    print(policy_stamp())
    for name, (strict, provenance) in RULES.items():
        print(f'{name}: strict={strict} contexts={POLICY.rules[name].applies_to} {provenance}')


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path, help="markdown files or directories")
    ap.add_argument("--project", choices=PROJECTS, help="override project detection")
    ap.add_argument("--strict-only", action="store_true", help="hide flexible notes")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--rule", action="append", help="only report these rule ids")
    ap.add_argument("--list-rules", action="store_true", help="print every rule with its provenance")
    add_arguments(ap)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.list_rules:
        print_rules()
        return 0
    if not args.paths:
        ap.error("give at least one markdown file or directory")
    unknown = sorted(r for r in (args.rule or []) if r not in RULES)
    if unknown:
        print(f"unknown rule id(s): {', '.join(unknown)}", file=sys.stderr)
        return 2
    files = collect_files(args.paths)
    if error := input_error(files, args.project, PROJECTS):
        print(error, file=sys.stderr)
        return 2
    try:
        findings = report_order(run(files, args.project, args.rule, args.mode, args.base, args.spec))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    card = scorecard(findings, len(files))
    card['notes'] = spec_notes(args.spec, args.rule)
    if args.format == "json":
        print(json.dumps({"scorecard": card, "findings": [vars(x) for x in findings]}, indent=2))
    else:
        for note in card['notes']:
            print('note: ' + note)
        print(render_text(findings, card, show_flexible=not args.strict_only))
    return 1 if card["strict_failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
