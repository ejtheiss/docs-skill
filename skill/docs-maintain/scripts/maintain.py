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

No rules yet. What this tier reports must be a duplication a maintainer would act on, and *what* to do
about one - merge, trim, or turn into a reusable block - is an editorial decision about SEO and product
intent that no measurement settles. The measured inventory (2 undefined blocks, 10 orphans, 1 typo-like
near miss) is evidence, not a rule.

    python3 maintain.py docs/           # a run that is honestly empty
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

SUBSKILL = "maintain"
# No rule ids yet: what to do about a duplication is an editorial decision, not a measurement.
EMITS: frozenset[str] = frozenset()

try:
    POLICY = policy_module.load("docs-maintain")
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
