#!/usr/bin/env python3
"""docs-test: what has to be true of the API, not of the prose.

Whether a documented field exists in the schema, whether an enum value is one the code accepts,
whether an endpoint path and method are real, whether a webhook event name is emitted, whether a state
transition is reachable, whether a link resolves, and whether a documented request actually works when
a reader pastes it into a terminal.

This is the only tier that needs anything outside the docs - the monorepo, the network, or a sandbox
organization - which is what separates it from `docs-lint`'s JSON syntax check: that a body parses is a
property of the file, that its fields are real is a property of the API.

Probes for all of this exist in `dev/`, and they have already found defects execution catches and
schema comparison cannot (a `document_type` the spec types as a free string and the code constrains to
a fixed set). None of it ships yet: a claim about the API is only worth reporting if a second,
independent implementation re-derives it, and the sandbox path needs credentials handled by the
skill's config rather than by a checker.

    python3 apicheck.py docs/           # a run that is honestly empty
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parents[2] / "docs-review" / "scripts"
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

import policy as policy_module  # noqa: E402
from findings import (  # noqa: E402
    Finding,
    collect_files,
    input_error,
    policy_stamp,
    render_text,
    report_order,
    scorecard,
)

SUBSKILL = "test"
# No rule ids yet: every claim here needs an independent second implementation first.
EMITS: frozenset[str] = frozenset()

try:
    POLICY = policy_module.load("docs-test")
    POLICY.require(EMITS)
except policy_module.PolicyError as exc:  # pragma: no cover - exercised through the CLI
    sys.exit(f"policy error: {exc}")

RULES: dict[str, tuple[bool, str]] = {}
PROJECTS = POLICY.projects()


def run(files: list[Path], project: str | None, rules: list[str] | None) -> list[Finding]:
    """No findings, and no pretence of any: an empty tier reports nothing."""
    del files, project, rules
    return []


def print_rules() -> None:
    print(policy_stamp())
    print(f"{SUBSKILL}: no rules yet")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path, help="markdown files or directories")
    ap.add_argument("--project", choices=PROJECTS, help="override project detection")
    ap.add_argument("--strict-only", action="store_true", help="hide flexible notes")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--rule", action="append", help="only report these rule ids")
    ap.add_argument("--list-rules", action="store_true", help="print every rule with its provenance")
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
    findings = report_order(run(files, args.project, args.rule))
    card = scorecard(findings, len(files))
    if args.format == "json":
        print(json.dumps({"scorecard": card, "findings": [vars(x) for x in findings]}, indent=2))
    else:
        print(render_text(findings, card, show_flexible=not args.strict_only))
    return 1 if card["strict_failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
