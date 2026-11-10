#!/usr/bin/env python3
"""docs-content: what a page can only be judged on against the rest of the corpus.

Continuity of a worked example across a guide sequence, whether a page's structure matches what
pages of its kind do, whether a concept is taught before it is used, and coverage of a documented
surface. None of that is decidable from one file: it needs the norms the corpus establishes, which is
why this is its own tier and not more `docs-lint`.

No rules yet, and the reason is not effort. Every candidate here has a measured base rate but no
threshold — 261 verbatim-repeated prose groups and 121 near-duplicates say what the corpus looks
like, not what a page should look like — and a rule that fires on a majority of pages describes the
corpus instead of diagnosing a page. Thresholds come from adjudicated labels (the plan's Phase 3),
so this subskill reports nothing until they exist, rather than reporting something unfounded.

    python3 content.py docs/            # a run that is honestly empty
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

SUBSKILL = "content"
# No rule ids yet: nothing here has a threshold that adjudication has justified.
EMITS: frozenset[str] = frozenset()

try:
    POLICY = policy_module.load("docs-content")
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
    print(f"{SUBSKILL}: no rules yet (thresholds are gated on adjudicated labels)")


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
