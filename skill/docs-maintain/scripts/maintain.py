#!/usr/bin/env python3
"""docs-maintain: what the corpus says about itself, across all three repos.

Reuse and canonical ownership: a paragraph repeated verbatim on fourteen pages, a near-duplicate page,
a ReadMe custom block referenced but never defined, an orphaned block, a block name that is a typo of
the one everybody else uses, and wording drift where the same claim appears in five places in four
wordings. Blocks do not resolve across repos, so drift detection is the only thing holding shared
statements together.

Two modes are planned, and only one of them needs thresholds: a one-time corpus-wide sweep that ranks
duplication by `(occurrences - 1) x length`, and an incremental check of the pages a commit touches
against the existing block inventory. The incremental exact-match case is decidable, which is why it
can ship before the near-duplicate work.

The shipped check reports undefined component usages against ReadMe built-ins and repository-local
definitions. Duplication, ownership and near-miss decisions remain editorial judgments.

    python3 maintain.py docs/
"""

from __future__ import annotations

import argparse
import json
import re
from functools import lru_cache
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parents[2] / "docs-review" / "scripts"
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

import policy as policy_module  # noqa: E402
from contexts import add_arguments, file_context  # noqa: E402
from channels import markup, repo_root  # noqa: E402
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

SUBSKILL = "maintain"
EMITS = frozenset({'reuse-undefined-block'})

try:
    POLICY = policy_module.load("docs-maintain")
    POLICY.require(EMITS)
except policy_module.PolicyError as exc:  # pragma: no cover - exercised through the CLI
    sys.exit(f"policy error: {exc}")

RULES = {name: (rule.strict, rule.provenance) for name, rule in POLICY.rules.items()}
PROJECTS = POLICY.projects()


def run(files: list[Path], project: str | None, rules: list[str] | None,
        mode: str = 'review', base: str | None = None) -> list[Finding]:
    if rules and not EMITS.intersection(rules):
        return []
    findings = []
    rule = POLICY.rules['reuse-undefined-block']
    for path in files:
        active = detect_project(path, project, PROJECTS)
        context = file_context(path, mode, base)
        def emit(line, name):
            if rule.applies(active) and context.includes(rule.applies_to, line):
                findings.append(Finding(str(path), line, rule.id, rule.strict_for(active), rule.says(name=name), name))
        check_reuse(markup(path.read_text()), definitions(repo_root(path)), emit)
    return findings


@lru_cache(maxsize=None)
def definitions(root):
    result = set()
    for directory in POLICY.words('reuse_directories'):
        for path in (root / directory).rglob('*'):
            if path.is_file():
                result.add(path.parent.name if path.stem == 'index' else path.stem)
                if path.suffix in ('.js', '.jsx', '.ts', '.tsx'):
                    result.update(re.findall(r'export\s+(?:default\s+)?(?:function|class|const)\s+(\w+)', path.read_text()))
    return result


def check_reuse(text, defined, emit):
    for match in re.finditer(r'(?<!\\)<([A-Z][A-Za-z0-9_]*)\b(?:\s[^<>]*?|\s*/?)>', text):
        if match[1] not in POLICY.words('readme_builtins') and match[1] not in defined:
            emit(text.count('\n', 0, match.start()) + 1, match[1])


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
        findings = report_order(run(files, args.project, args.rule, args.mode, args.base))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    card = scorecard(findings, len(files))
    if args.format == "json":
        print(json.dumps({"scorecard": card, "findings": [vars(x) for x in findings]}, indent=2))
    else:
        print(render_text(findings, card, show_flexible=not args.strict_only))
    return 1 if card["strict_failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
