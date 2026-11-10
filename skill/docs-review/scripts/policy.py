#!/usr/bin/env python3
"""The policy a checker runs under, read from the YAML that defines it.

Policy is authored, not compiled. `docs-review/config/policy.yaml` holds the vocabulary and the
Modern Treasury domain facts - severities, projects, what our objects are called - and each subskill's
`config/rules.yaml` holds the rules it emits plus the tables only it reads. This module merges the two
and is the only way a checker reads either.

No decision data lives in checker source. A word list, a severity or a threshold that appears in
Python is a value that can drift away from the guide without anyone noticing, which is the class of
defect this indirection removes; three such disagreements were measured before it existed.

Until 2026-09-03 the policy came from Notion through an 832-line sync: a snapshot captured out of
band, compiled into one artifact, with staleness, tamper detection and shrink guards around the
seam. That machinery existed because a database cell is untrustworthy input - it can carry rich text,
invisible characters, a row someone added minutes ago, or a list that lost half its entries in a bad
fetch. A reviewed file in the repo is none of those things, so the guards it needed are gone with it,
along with the `Active` gate (delete the rule instead), the `<delete>` sentinel (write `""`), and the
separate `exceptions` block (an exemption sits beside the value it exempts).

The loader refuses rather than guesses. A missing file, an unreadable one, a rule the checker emits
that no file defines, or a table defined in two places at once are all fatal: a run under an unknown
policy produces a verdict nobody can reproduce, which is worse than no run.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    sys.exit(f"missing dependency: {exc.name}. Run: pip install markdown-it-py PyYAML")

SHARED = Path(__file__).resolve().parent
SKILLS = SHARED.parents[1]
PARENT = SKILLS / "docs-review" / "config" / "policy.yaml"

SCHEMA_VERSION = 1
SEVERITIES = ("strict", "moderate", "flexible")

# The fields of a rule a verdict depends on. The policy id covers these and nothing else, so the
# stamp on a report answers "would this policy have decided my findings differently?" rather than
# "has anyone touched the guide". Provenance is the counter-example: printed by `--list-rules`,
# read by no decision, and while it was covered, rewording it re-opened the admission gate for every
# rule.
DECISIVE = ("reported", "guide", "scope", "threshold", "applies_to")


class PolicyError(Exception):
    """The policy files cannot be used to decide anything."""


@dataclass(frozen=True)
class Rule:
    """One rule's decisions: how loudly it reports and where it applies."""

    id: str
    reported: str  # the grade a run prints
    guide_severity: str  # what a reviewer applies, which the guide may grade harder
    scope: tuple[str, ...]
    threshold: int | None
    provenance: str  # documentation: printed by --list-rules, read by no decision
    messages: dict[str, str]  # what a finding says; keyed, with "" for a rule that says one thing
    # project -> (reported, guide). The index page promises "where an overlay contradicts base style,
    # the overlay wins for that project"; this is that promise, expressible at last. Empty for every
    # shipped rule, so the capability is dormant and the policy id is unmoved - see `identity`.
    overrides: dict[str, tuple[str, str]]
    applies_to: tuple[str, ...]

    def severity_for(self, project: str | None) -> tuple[str, str]:
        """(reported, guide) for a page in `project` - the override's when one names it."""
        if project and project in self.overrides:
            return self.overrides[project]
        return (self.reported, self.guide_severity)

    def strict_for(self, project: str | None) -> bool:
        return self.severity_for(project)[0] == "strict"

    def says(self, key: str = "", **fields: object) -> str:
        """The finding text, with `{name}` placeholders filled from `fields`.

        A message is authored prose about the reader's page, so it lives with the rule rather than in
        the checker. The rendering is `str.format`, which fails on a field the template names and the
        call site did not pass - so every message is rendered by a fixture in `dev/tests/test_lint.py`
        rather than trusted, because a template error would otherwise surface on a real run.
        """
        if key not in self.messages:
            raise PolicyError(f"rule '{self.id}' has no message {key!r}; it defines "
                              f"{sorted(self.messages) or 'none'}")
        try:
            return self.messages[key].format(**fields)
        except (KeyError, IndexError) as exc:
            raise PolicyError(f"rule '{self.id}' message {key!r} names {exc}, which the checker did "
                              f"not supply") from None

    @property
    def strict(self) -> bool:
        """What most callers want. `reported` is kept whole beside it because collapsing three
        grades into a bool loses the difference between moderate and flexible, which the policy id
        has to cover."""
        return self.reported == "strict"

    def applies(self, project: str) -> bool:
        return "all" in self.scope or project in self.scope


@dataclass(frozen=True)
class Policy:
    rules: dict[str, Rule]
    values: dict[str, list | dict]
    exceptions: dict[str, dict[str, str]]
    project_urls: dict[str, str]
    policy_id: str
    sources: tuple[Path, ...]

    @property
    def path(self) -> Path:
        """The subskill file, which is what a message about a rule should name."""
        return self.sources[-1]

    # -- tables -----------------------------------------------------------------------------------

    def table(self, name: str) -> list | dict:
        if name not in self.values:
            raise PolicyError(f"no value table '{name}' in {' or '.join(map(str, self.sources))}")
        return self.values[name]

    def words(self, name: str) -> list[str]:
        """A list table, longest value first, which is the order a matcher wants."""
        values = self.table(name)
        if isinstance(values, dict):
            raise PolicyError(f"value table '{name}' is a map, not a list")
        return list(values)

    def mapping(self, name: str) -> dict[str, str]:
        values = self.table(name)
        if not isinstance(values, dict):
            raise PolicyError(f"value table '{name}' is a list, not a map")
        return dict(values)

    def exception(self, table: str, value: str) -> str | None:
        """The pattern that exempts `value` in `table`, or None when it has no exception."""
        return self.exceptions.get(table, {}).get(value)

    # -- rules ------------------------------------------------------------------------------------

    def rule(self, rule_id: str) -> Rule:
        if rule_id not in self.rules:
            raise PolicyError(f"{self.path}: no rule '{rule_id}'")
        return self.rules[rule_id]

    def strict(self, rule_id: str) -> bool:
        return self.rule(rule_id).strict

    def threshold(self, rule_id: str) -> int:
        value = self.rule(rule_id).threshold
        if value is None:
            raise PolicyError(f"{self.path}: rule '{rule_id}' carries no threshold")
        return value

    def projects(self) -> tuple[str, ...]:
        return tuple(sorted(self.project_urls))

    def require(self, rule_ids: set[str]) -> None:
        """Refuse unless every rule the caller can emit is defined.

        A rule deleted from the file while the checker still emits it would otherwise report under a
        severity read from nothing.
        """
        missing = sorted(rule_ids - set(self.rules))
        if missing:
            raise PolicyError(f"{self.path}: rules the checker emits are not in the policy: "
                              f"{', '.join(missing)}")


# ------------------------------------------------------------------------------------------------
# Reading


def _read(path: Path) -> dict:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PolicyError(f"no policy at {path}") from None
    except (OSError, UnicodeDecodeError) as exc:
        raise PolicyError(f"{path}: cannot be read ({exc})") from None
    except yaml.YAMLError as exc:
        raise PolicyError(f"{path}: not valid YAML ({exc})") from None
    if not isinstance(raw, dict):
        raise PolicyError(f"{path}: not a mapping; a policy file's top level is keys - 'schema', "
                          f"then 'tables' and/or 'rules'")
    if raw.get("schema") != SCHEMA_VERSION:
        raise PolicyError(f"{path}: schema {raw.get('schema')!r}, expected {SCHEMA_VERSION}")
    return raw


def _tables(raw: dict, path: Path) -> tuple[dict, dict]:
    """(values, exceptions) for one file, in the shape the checkers match on."""
    values: dict[str, list | dict] = {}
    exceptions: dict[str, dict[str, str]] = {}
    blocks = raw.get("tables") or {}
    if not isinstance(blocks, dict):
        raise PolicyError(f"{path}: 'tables' is not a mapping; write 'tables:' with one key per "
                          f"table")
    for name, block in blocks.items():
        if not isinstance(block, dict):
            raise PolicyError(f"{path}: table '{name}' is not a mapping; write 'why' plus exactly "
                              f"one of 'map', 'values' or 'ranges'")
        if not (block.get("why") or "").strip():
            raise PolicyError(f"{path}: table '{name}' has no 'why'; a list that decides a verdict "
                              f"says what it is for")
        shapes = [key for key in ("map", "values", "ranges") if key in block]
        if len(shapes) != 1:
            raise PolicyError(f"{path}: table '{name}' needs exactly one of 'map', 'values' or "
                              f"'ranges'")
        if shapes == ["ranges"]:
            values[name] = _ranges(block["ranges"], name, path)
            continue
        has_map = shapes == ["map"]
        entries = block["map"] if has_map else block["values"]
        if not entries:
            raise PolicyError(f"{path}: table '{name}' is empty; a rule reads it, so an empty list "
                              f"would silently disable a check - add entries, or delete the table "
                              f"and the rule that reads it")
        # Longest first is what a matcher needs - `in order to` has to be tried before `to`. It is
        # not what every table needs: one that is only ever a membership test, or that a message
        # reads out in order, wants the order it was written in. `ordered: true` says so, and the
        # case that found it is `callout_roles`, where sorting silently reordered a suggestion into
        # "tip, information, limitation" against the guide's own sequence.
        keep_order = bool(block.get("ordered"))
        longest_first = (lambda v: (0, 0)) if keep_order else (lambda v: (-len(v), v))
        if has_map:
            if not isinstance(entries, dict):
                raise PolicyError(f"{path}: table '{name}': 'map' is not a mapping; write "
                                  f"'wrong: right' pairs, with a null value for no replacement")
            values[name] = {key: entries[key] for key in sorted(entries, key=longest_first)}
        else:
            if not isinstance(entries, list):
                raise PolicyError(f"{path}: table '{name}': 'values' is not a list; write one "
                                  f"'- entry' per line")
            if len(set(entries)) != len(entries):
                duplicated = sorted({v for v in entries if entries.count(v) > 1})
                raise PolicyError(f"{path}: table '{name}' repeats {duplicated}; delete the extra "
                                  f"copy, each entry appears once")
            values[name] = sorted(entries, key=longest_first)
        for entry in (entries if isinstance(entries, list) else entries):
            if not isinstance(entry, str) or not entry.strip():
                raise PolicyError(f"{path}: table '{name}' has an empty or non-string value "
                                  f"{entry!r}; every entry is a non-empty string")
        exempt = block.get("exceptions") or {}
        if not isinstance(exempt, dict):
            raise PolicyError(f"{path}: table '{name}': 'exceptions' is not a mapping; write "
                              f"'value: pattern' pairs")
        for value in exempt:
            if value not in values[name]:
                raise PolicyError(f"{path}: table '{name}' exempts {value!r}, which it does not "
                                  f"contain; fix the spelling or add {value!r} to the table")
        if exempt:
            exceptions[name] = dict(exempt)
    return values, exceptions


def _ranges(entries: object, name: str, path: Path) -> tuple[tuple[int, int], ...]:
    """Inclusive codepoint ranges, written `[low, high]`.

    A third shape beside `map` and `values` because the Unicode tables are pairs of integers, and
    writing 900 codepoints out as strings to fit an existing shape would be worse than adding one.
    Each pair is checked for order: `[0x1f6cf, 0x1f6cb]` parses fine and matches nothing, which is a
    check that silently stops firing.
    """
    if not isinstance(entries, list) or not entries:
        raise PolicyError(f"{path}: table '{name}': 'ranges' is not a non-empty list; write one "
                          f"'- [low, high]' pair of codepoints per line")
    out = []
    for entry in entries:
        if (not isinstance(entry, list) or len(entry) != 2
                or not all(isinstance(x, int) and not isinstance(x, bool) for x in entry)):
            raise PolicyError(f"{path}: table '{name}': {entry!r} is not a [low, high] pair of "
                              f"integers; write two whole codepoints, e.g. [128000, 128019]")
        low, high = entry
        if low > high:
            raise PolicyError(f"{path}: table '{name}': range [{low:#x}, {high:#x}] runs backwards, "
                              f"so it can never match; swap the bounds")
        out.append((low, high))
    return tuple(out)


def _rules(raw: dict, path: Path, projects: tuple[str, ...]) -> dict[str, Rule]:
    out: dict[str, Rule] = {}
    rules = raw.get("rules") or {}
    if not isinstance(rules, dict):
        raise PolicyError(f"{path}: 'rules' is not a mapping; write 'rules:' with one key per rule "
                          f"id")
    for rule_id, row in rules.items():
        if not isinstance(row, dict):
            raise PolicyError(f"{path}: rule '{rule_id}' is not a mapping; write 'reported', "
                              f"'provenance' and 'message' under it")
        reported = row.get("reported")
        guide = row.get("guide") or reported
        for name, severity in (("reported", reported), ("guide", guide)):
            if severity not in SEVERITIES:
                raise PolicyError(f"{path}: rule '{rule_id}' has {name} severity {severity!r}; "
                                  f"expected one of {', '.join(SEVERITIES)}")
        if SEVERITIES.index(reported) < SEVERITIES.index(guide):
            raise PolicyError(f"{path}: rule '{rule_id}' reports {reported} but the guide grades it "
                              f"{guide}; a checker may lag its policy, never exceed it - lower "
                              f"'reported' or raise 'guide'")
        scope = tuple(row.get("scope") or ("all",))
        if "all" in scope and len(scope) > 1:
            raise PolicyError(f"{path}: rule '{rule_id}' is scoped 'all' and also {list(scope)}; "
                              f"'all' already covers them - keep 'all' or list only the projects")
        threshold = row.get("threshold")
        applies_to = row.get('applies_to', ['always'])
        if (not isinstance(applies_to, list) or not applies_to
                or any(c not in ('always', 'review', 'draft', 'new', 'touched') for c in applies_to)):
            raise PolicyError(f"{path}: rule '{rule_id}' has invalid applies_to contexts")
        if threshold is not None and (isinstance(threshold, bool) or not isinstance(threshold, int)):
            raise PolicyError(f"{path}: rule '{rule_id}' has a non-integer threshold "
                              f"{threshold!r}; write a whole number or delete the field")
        if not (row.get("provenance") or "").strip():
            raise PolicyError(f"{path}: rule '{rule_id}' has no provenance; every rule records what "
                              f"it mirrors or which Modern Treasury decision it enforces")
        out[rule_id] = Rule(
            id=rule_id,
            reported=reported,
            guide_severity=guide,
            scope=scope,
            threshold=threshold,
            provenance=row["provenance"],
            messages=_messages(row, rule_id, path),
            overrides=_overrides(row, rule_id, path, projects, scope, reported, guide),
            applies_to=tuple(applies_to),
        )
    return out


def _overrides(row: dict, rule_id: str, path: Path, projects: tuple[str, ...],
               scope: tuple[str, ...], reported: str, guide: str) -> dict[str, tuple[str, str]]:
    """Per-project severities, validated against the projects the parent actually defines.

    Three failure modes worth their own refusals, because each is a different mistake: naming a
    project that does not exist, naming one the rule does not apply to (dead policy that reads as
    live), and reporting stricter than that project's own guide grade.
    """
    block = row.get("overrides")
    if block is None:
        return {}
    if not isinstance(block, dict) or not block:
        raise PolicyError(f"{path}: rule '{rule_id}': 'overrides' is not a non-empty mapping of "
                          f"project -> severities; delete the field if the rule has none")
    out: dict[str, tuple[str, str]] = {}
    for project, entry in block.items():
        where = f"{path}: rule '{rule_id}' override for '{project}'"
        if project not in projects:
            raise PolicyError(f"{where}: no such project; the parent defines {', '.join(projects)}")
        if "all" not in scope and project not in scope:
            raise PolicyError(f"{where}: the rule is scoped to {list(scope)}, so this override can "
                              f"never apply; widen the scope or delete the override")
        if not isinstance(entry, dict):
            raise PolicyError(f"{where}: not a mapping; write reported and guide")
        over_reported = entry.get("reported", reported)
        over_guide = entry.get("guide", guide)
        for name, severity in (("reported", over_reported), ("guide", over_guide)):
            if severity not in SEVERITIES:
                raise PolicyError(f"{where}: {name} severity {severity!r}; expected one of "
                                  f"{', '.join(SEVERITIES)}")
        if SEVERITIES.index(over_reported) < SEVERITIES.index(over_guide):
            raise PolicyError(f"{where}: reports {over_reported} but grades {over_guide}; a checker "
                              f"may lag its policy, never exceed it - lower 'reported' or raise "
                              f"'guide'")
        out[project] = (over_reported, over_guide)
    return out


def _messages(row: dict, rule_id: str, path: Path) -> dict[str, str]:
    """`message:` for a rule that says one thing, `messages:` for one that says several."""
    single, several = row.get("message"), row.get("messages")
    if (single is None) == (several is None):
        raise PolicyError(f"{path}: rule '{rule_id}' needs exactly one of 'message' or 'messages'; "
                          f"a rule with nothing to say cannot report a finding")
    if single is not None:
        if not isinstance(single, str) or not single.strip():
            raise PolicyError(f"{path}: rule '{rule_id}': 'message' is empty; write the sentence a "
                              f"finding shows, or use 'messages' for several")
        return {"": single}
    if not isinstance(several, dict) or not several:
        raise PolicyError(f"{path}: rule '{rule_id}': 'messages' is not a non-empty mapping; write "
                          f"'key: text' per variant, or use 'message' for one")
    for key, text in several.items():
        if not isinstance(text, str) or not text.strip():
            raise PolicyError(f"{path}: rule '{rule_id}': message {key!r} is empty; write the "
                              f"sentence a finding shows, or delete the key")
    return dict(several)


def _projects(raw: dict, path: Path) -> dict[str, str]:
    """The projects the parent defines, as name -> url_prefix.

    Three refusals rather than one. The single "no 'projects'" this used to raise was true only for
    the missing case and misleading for the other two - it sent an author looking for a field that
    was sitting right there, wrongly shaped. Found by mutant 066 on the Nickel side, where the same
    three arms had to be split to be reachable at all.
    """
    projects = raw.get("projects")
    written = "write one key per project, each with 'repo' and 'url_prefix'"
    if projects is None:
        raise PolicyError(f"{path}: no 'projects'; {written}")
    if not isinstance(projects, dict):
        raise PolicyError(f"{path}: 'projects' is a {type(projects).__name__}, not a mapping; "
                          f"{written}")
    if not projects:
        raise PolicyError(f"{path}: 'projects' is empty; {written}")
    urls = {}
    for name, block in projects.items():
        if not isinstance(block, dict) or not (block.get("url_prefix") or "").strip():
            raise PolicyError(f"{path}: project '{name}' has no url_prefix; write "
                              f"url_prefix: /{name}/")
        urls[name] = block["url_prefix"]
    return urls


def identity(rules: dict[str, Rule], values: dict, exceptions: dict) -> str:
    """A short hash of everything a verdict depends on, stamped on every report.

    Deliberately not the git SHA: a run happens against a working tree, which may carry an edit that
    is not committed, and the stamp has to describe what actually decided the findings.
    """
    decisive = {
        rule_id: {"reported": rule.reported, "guide": rule.guide_severity,
                  "scope": list(rule.scope), "threshold": rule.threshold,
                  "applies_to": list(rule.applies_to)}
        for rule_id, rule in sorted(rules.items())
    }
    # Only when non-empty. An `overrides: {}` on every rule would change the hashed payload and
    # restamp every stored report for a capability nobody is using - the dormant-feature equivalent
    # of the documentation fields this projection exists to keep out.
    for rule_id, rule in rules.items():
        if rule.overrides:
            decisive[rule_id]["overrides"] = {
                project: list(pair) for project, pair in sorted(rule.overrides.items())
            }
    payload = {"rules": decisive, "values": values, "exceptions": exceptions}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


SUBSKILLS = ("docs-lint", "docs-content", "docs-maintain", "docs-test")


def load_all() -> Policy:
    """Every subskill's policy over the shared one: what the umbrella reports under.

    Rules used to be one list in one artifact, so their union was free. Splitting them per subskill
    buys a guard that could not exist before: two subskills claiming the same rule id is now a
    refusal rather than whichever row the compiler happened to write last.
    """
    merged_rules: dict[str, Rule] = {}
    owner: dict[str, str] = {}
    values: dict[str, list | dict] = {}
    exceptions: dict[str, dict[str, str]] = {}
    for subskill in SUBSKILLS:
        one = load(subskill)
        for rule_id, rule in one.rules.items():
            if rule_id in merged_rules:
                raise PolicyError(f"rule '{rule_id}' is defined by both {owner[rule_id]} and "
                                  f"{subskill}; one subskill owns a rule, or two checkers report "
                                  f"the same id under different severities")
            merged_rules[rule_id] = rule
            owner[rule_id] = subskill
        values.update(one.values)
        exceptions.update(one.exceptions)

    parent_raw = _read(PARENT)
    return Policy(rules=merged_rules, values=values, exceptions=exceptions,
                  project_urls=_projects(parent_raw, PARENT),
                  policy_id=identity(merged_rules, values, exceptions),
                  sources=(PARENT,))


def load(subskill: str) -> Policy:
    """The merged policy for one subskill, or a `PolicyError` naming why there is not one."""
    child = SKILLS / subskill / "config" / "rules.yaml"
    parent_raw, child_raw = _read(PARENT), _read(child)

    project_urls = _projects(parent_raw, PARENT)  # rules validate overrides against these
    parent_values, parent_exceptions = _tables(parent_raw, PARENT)
    child_values, child_exceptions = _tables(child_raw, child)

    # `includes:` names sibling files whose tables merge in. It exists so that 180 irregular
    # participles and 900 Unicode codepoints do not sit between two rules in the file a reader opens
    # to change a severity. They are still this subskill's tables and obey the same one-owner rule.
    for name in child_raw.get("includes") or []:
        if not isinstance(name, str) or "/" in name or not name.endswith(".yaml"):
            raise PolicyError(f"{child}: include {name!r} must be a sibling .yaml filename")
        extra_path = child.parent / name
        extra_values, extra_exceptions = _tables(_read(extra_path), extra_path)
        clash = sorted(set(child_values) & set(extra_values))
        if clash:
            raise PolicyError(f"table(s) {', '.join(clash)} defined in both {child} and "
                              f"{extra_path}; a table has one owner - delete whichever copy is "
                              f"not the one being maintained")
        child_values.update(extra_values)
        child_exceptions.update(extra_exceptions)

    both = sorted(set(parent_values) & set(child_values))
    if both:
        raise PolicyError(f"table(s) {', '.join(both)} defined in both {PARENT} and {child}; a "
                          f"table has one owner, or the two copies drift - delete the copy in "
                          f"whichever file is not the owner")

    values = {**parent_values, **child_values}
    exceptions = {**parent_exceptions, **child_exceptions}

    # `projects` is the authored form - a repo and a URL prefix per project - and the prefixes are
    # also a table the link rule matches against. Derived rather than written twice, and put in
    # `values` so the policy id covers it: the prefixes decide `link-absolute-internal`, and a stamp
    # that did not move when they changed would describe a policy that no longer applied.
    if "project_url_prefixes" in values:
        raise PolicyError(f"'project_url_prefixes' is derived from 'projects'; define it in one "
                          f"place, not both")
    values["project_url_prefixes"] = {
        name: project_urls[name] for name in sorted(project_urls, key=lambda n: (-len(n), n))
    }
    rules = _rules(child_raw, child, tuple(sorted(project_urls)))
    if parent_raw.get("rules"):
        raise PolicyError(f"{PARENT}: carries rules; rules belong to the subskill that emits them - "
                          f"move them to that subskill's config/rules.yaml")

    return Policy(rules=rules, values=values, exceptions=exceptions,
                  project_urls=project_urls,
                  policy_id=identity(rules, values, exceptions),
                  sources=(PARENT, child))
