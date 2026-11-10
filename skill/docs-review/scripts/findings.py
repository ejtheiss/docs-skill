#!/usr/bin/env python3
"""What a finding is and how a run is reported.

Every subskill produces the same `Finding` and is rendered by the same functions, so a review is one
compiler log rather than four tools' output: same columns, same underlining, one scorecard, one
policy stamp. A subskill that wants its own format is a subskill a reader has to learn twice.
"""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

SHARED = Path(__file__).resolve().parent
if str(SHARED) not in sys.path:  # policy.py ships beside this module
    sys.path.insert(0, str(SHARED))


EVIDENCE_LIMIT = 200
EVIDENCE_INDENT = "                        > "


@dataclass
class Finding:
    path: str
    line: int
    rule: str
    strict: bool
    message: str
    evidence: str = ""
    fix: str = ""
    col: int = 0
    end_col: int = 0  # col..end_col is 1-based and inclusive, into `evidence`; 0 means unpinned


def clip_evidence(evidence: str, span: tuple[int, int] | None) -> tuple[str, int, int]:
    """Trim `evidence` to what the report prints and move `span` with it.

    Columns are 1-based inclusive offsets into the returned text, not into the source line: prose
    evidence comes from the resolved text channel, where inline code is blanked and soft breaks are
    spaces, so a raw-file column would be wrong. A span that the trimming would cut reads as unpinned.
    """
    lead = len(evidence) - len(evidence.lstrip())
    text = evidence.strip()[:EVIDENCE_LIMIT]
    if span is None:
        return text, 0, 0
    start, end = span[0] - lead, span[1] - lead
    if start < 0 or end > len(text) or end <= start:
        return text, 0, 0
    return text, start + 1, end


# --------------------------------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------------------------------


def rule_counts(findings: list[Finding]) -> list[tuple[str, int]]:
    """Rule ids with their counts, most frequent first, ties broken by rule id."""
    return sorted(Counter(x.rule for x in findings).items(), key=lambda kv: (-kv[1], kv[0]))


def report_order(findings: list[Finding]) -> list[Finding]:
    """The order a report prints, which is the file's order and not the checker's.

    Findings are sorted rather than emitted in evaluation order because evaluation order is an
    implementation detail: which of two findings on one line comes first depended on the order of a
    word list, so re-ordering a policy table would otherwise reorder a report without changing a
    verdict.
    """
    return sorted(findings, key=lambda r: (r.path, r.line, r.rule, r.message, r.evidence))


def scorecard(findings: list[Finding], pages: int) -> dict:
    strict = [x for x in findings if x.strict]
    return {
        "pages": pages,
        "strict_failures": len(strict),
        "flexible_notes": len(findings) - len(strict),
        "pages_with_strict_failures": len({x.path for x in strict}),
        "pages_clean": pages - len({x.path for x in strict}),
        "by_rule": dict(rule_counts(findings)),
        "verdict": "PASS" if not strict else "FAIL",
        "policy": policy_stamp(),
    }


def policy_stamp(subskill: str | None = None) -> str:
    """`policy <id>`: which policy this run applied.

    Every report carries it, so a verdict can be reproduced against the exact rules and tables that
    produced it, and a precision measurement can be pinned to them. The id is computed from the
    merged policy's decisive fields, never quoted from the file, so an edited file cannot be reported
    under an id that no longer describes it.

    With no argument it stamps every subskill's policy merged, which is what the umbrella runs
    under; naming one stamps just that subskill's.

    Reading the policy never fails a run here: an unreadable one says so, because the stamp is
    provenance rather than a rule. The rules themselves refuse to load in that case, which is a
    separate and louder failure.
    """
    try:
        import policy as policy_module
        loaded = policy_module.load(subskill) if subskill else policy_module.load_all()
        return f"policy {loaded.policy_id[:12]}"
    except policy_module.PolicyError as exc:
        return f"policy unreadable ({exc})"
    except Exception:  # pragma: no cover - the stamp must never be what breaks a run
        return "policy unreadable"


def render_finding(finding: Finding) -> list[str]:
    tag = "STRICT " if finding.strict else "flex   "
    rows = [f"  {tag} {finding.line:>5}  {finding.rule:<24} {finding.message}"]
    if finding.evidence:
        rows.append(f"{EVIDENCE_INDENT}{finding.evidence}")
    if finding.col:
        pad = " " * (len(EVIDENCE_INDENT) + finding.col - 1)
        rows.append(pad + "^" * (finding.end_col - finding.col + 1))
    if finding.fix:
        rows.append(f"                        fix: {finding.fix}")
    return rows


def render_text(findings: list[Finding], card: dict, show_flexible: bool) -> str:
    shown = [x for x in findings if x.strict or show_flexible]
    out: list[str] = []
    for path in sorted({x.path for x in shown}):
        out.append(f"\n{path}")
        rows = [x for x in shown if x.path == path]
        for finding in sorted(rows, key=lambda r: (r.line, r.rule, r.message, r.evidence)):
            out.extend(render_finding(finding))
    out.append(
        f"\n{card['verdict']}: {card['pages']} page(s), {card['strict_failures']} strict failure(s), "
        f"{card['flexible_notes']} flexible note(s), {card['pages_clean']} page(s) clean of strict failures."
    )
    if shown:
        ranked = rule_counts(shown)[:8]
        out.append("Most frequent: " + ", ".join(f"{rule} {n}" for rule, n in ranked))
    out.append(card["policy"])
    return "\n".join(out)


# --------------------------------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------------------------------


def collect_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        candidates = sorted(path.rglob("*.md")) if path.is_dir() else [path]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(candidate)
    return files


def detect_project(path: Path, override: str | None, projects: tuple[str, ...]) -> str | None:
    if override:
        return override
    parts = [p.lower() for p in path.resolve().parts]
    if "reference" in parts:
        return "reference"
    for name in [p for p in projects if p != "reference"]:
        if any(name in p for p in parts):
            return name
    return None


def input_error(files: list[Path], project: str | None, projects: tuple[str, ...]) -> str:
    """The reason these files cannot be checked, or "" when they can."""
    if not files:
        return "no markdown files found"
    undetected = next((f for f in files if detect_project(f, project, projects) is None), None)
    if undetected:
        return (f"cannot tell which project {undetected} belongs to; pass --project "
                f"({'/'.join(projects)})")
    return ""
