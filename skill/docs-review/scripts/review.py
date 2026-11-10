#!/usr/bin/env python3
"""docs-review: run the four subskills as one review.

    python3 review.py docs/                        # all four, one log
    python3 review.py docs/ --only lint            # one tier
    python3 review.py docs/ --only lint --only test
    python3 review.py --list-rules

The four subskills are separable because they are dependency tiers, not topics: `docs-lint` needs
only the file, `docs-content` needs the corpus, `docs-maintain` needs all three repos, `docs-test`
needs the monorepo, the network or a sandbox. That is also why they are individually addressable —
a pre-commit hook can afford the first and not the last.

They report as one log all the same: one findings format, one severity vocabulary, one scorecard, one
policy stamp. Four tools' output is four things to learn; a compiler prints one.

Selection is by subskill, and `--only` names one. Default is all four, because a reviewer who has to
remember which tier catches which defect has been handed the tool's problem.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

SHARED = Path(__file__).resolve().parent
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

import policy as policy_module  # noqa: E402
from contexts import add_arguments  # noqa: E402
from findings import (  # noqa: E402
    Finding,
    collect_files,
    input_error,
    policy_stamp,
    render_text,
    report_order,
    scorecard,
)

SKILL_ROOT = SHARED.parents[1]
# subskill -> the module that decides its tier. Every one exposes EMITS, RULES and
# run(files, project, rules); nothing else about a subskill is the umbrella's business.
SUBSKILLS = {
    "lint": SKILL_ROOT / "docs-lint" / "scripts" / "lint.py",
    "content": SKILL_ROOT / "docs-content" / "scripts" / "content.py",
    "maintain": SKILL_ROOT / "docs-maintain" / "scripts" / "maintain.py",
    "test": SKILL_ROOT / "docs-test" / "scripts" / "apicheck.py",
}

try:
    POLICY = policy_module.load_all()
except policy_module.PolicyError as exc:  # pragma: no cover - exercised through the CLI
    sys.exit(f"policy error: {exc}")

PROJECTS = POLICY.projects()


def load_subskill(name: str) -> ModuleType:
    """Import a subskill by path, so a checker is found where it ships and not on `sys.path`."""
    path = SUBSKILLS[name]
    if not path.exists():
        sys.exit(f"missing subskill: {name} ({path})")
    spec = importlib.util.spec_from_file_location(f"docs_review_{name}", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        sys.exit(f"cannot load subskill: {name} ({path})")
    module = importlib.util.module_from_spec(spec)
    # Registered before execution: `@dataclass` resolves its annotations through `sys.modules`, so a
    # module executed outside it cannot define one.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def unimplemented_rules(modules: dict[str, ModuleType]) -> list[str]:
    """Rules the policy defines that no loaded subskill can decide.

    Not fatal: a rule row can land in Notion before its checker exists, and during the build-out
    most of them do. It is printed, because a rule nobody implements is a policy a reader believes
    is enforced.
    """
    claimed: set[str] = set()
    for module in modules.values():
        claimed |= set(getattr(module, "EMITS", frozenset()))
    return sorted(set(POLICY.rules) - claimed)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path, help="markdown files or directories")
    ap.add_argument("--only", action="append", choices=sorted(SUBSKILLS),
                    help="run just this subskill (repeatable); default is all four")
    ap.add_argument("--project", choices=PROJECTS, help="override project detection")
    ap.add_argument("--strict-only", action="store_true", help="hide flexible notes")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--rule", action="append",
                    help="only report these rule ids (the scorecard then covers the filtered set)")
    ap.add_argument("--list-rules", action="store_true", help="print every rule with its provenance")
    add_arguments(ap)
    return ap


def selected(only: list[str] | None) -> list[str]:
    return sorted(set(only)) if only else sorted(SUBSKILLS)


def print_rules(modules: dict[str, ModuleType]) -> None:
    print(policy_stamp())
    for name, module in modules.items():
        rules: dict[str, tuple[bool, str]] = getattr(module, "RULES", {})
        if not rules:
            print(f"{name:<9} no rules yet")
            continue
        for rule, (strict, provenance) in sorted(rules.items()):
            guide = POLICY.rules[rule].guide_severity
            note = f"[guide: {guide}] " if guide != ("strict" if strict else "flexible") else ""
            print(f"{name:<9} {'STRICT' if strict else 'flex  '} {rule:<26} {note}[contexts: {', '.join(POLICY.rules[rule].applies_to)}] {provenance}")
    if orphaned := unimplemented_rules(modules):
        print(f"unimplemented by the selected subskill(s): {', '.join(orphaned)}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    modules = {name: load_subskill(name) for name in selected(args.only)}

    if args.list_rules:
        print_rules(modules)
        return 0

    if not args.paths:
        ap.error("give at least one markdown file or directory")

    known = {rule for module in modules.values() for rule in getattr(module, "RULES", {})}
    unknown = sorted(r for r in (args.rule or []) if r not in known)
    if unknown:
        print(f"unknown rule id(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    files = collect_files(args.paths)
    if error := input_error(files, args.project, PROJECTS):
        print(error, file=sys.stderr)
        return 2

    findings: list[Finding] = []
    notes = ['leak-names inactive: no --names list supplied'] if 'lint' in modules and args.names is None else []
    try:
        for name, module in modules.items():
            options = {'names': args.names} if name == 'lint' else {'spec': args.spec} if name == 'test' else {}
            if name == 'test':
                options['spec'] = module.resolve_spec(args.spec)
                notes.extend(module.spec_notes(options['spec'], args.rule))
            findings.extend(module.run(files, args.project, args.rule, args.mode, args.base, **options))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    findings = report_order(findings)
    card = scorecard(findings, len(files))
    card["subskills"] = sorted(modules)
    card['notes'] = notes
    if args.format == "json":
        print(json.dumps({"scorecard": card, "findings": [vars(x) for x in findings]}, indent=2))
    else:
        for note in notes:
            print('note: ' + note)
        print(render_text(findings, card, show_flexible=not args.strict_only))
    return 1 if card["strict_failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
