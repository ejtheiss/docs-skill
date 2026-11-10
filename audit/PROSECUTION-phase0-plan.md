# Prosecution plan — Phase 0

Shell + Notion MCP only. No dev server, no browser, no recording.

## P1 — Drift case 1 (`just`) is falsifiable by execution
`stylecheck.py:1016-1018` hard-codes a `just` check that emits rule id `filler`, outside `BANNED_FILLER`.
Run the shipped checker on a fixture containing "You just need three fields." and "just as expected".
- PASS (plan correct): no `filler` finding for `just`.
- FAIL (plan wrong): a `filler` finding on `just` → PLAN-phases.md:45-46, the Notion `just` row
  (`Active=__NO__`), and the new base-style sentence "the checker reports all but `just`" are all false.

## P2 — Excerpt direction after D7 prose inversion
Fixture A: frontmatter with `title` only. Fixture B: frontmatter with `title` + `excerpt`.
Code: `RULES["frontmatter-excerpt"] = (True, ...)`.
- Expected if guide and code agree: B is reported, A is clean.
- Expected if drift was moved not removed: A is reported strict, B is clean → prose now contradicts code
  in the opposite direction.

## P3 — Element-by-element constant↔row diff
Script: import `stylecheck` as a module, dump OBJECTS, SHORTHAND, SANCTIONED_CALLOUTS, BANNED_FILLER,
FILLER_REPLACEMENTS, VAGUE_ANCHORS, STANDARD_FENCE_LANGS, FENCE_LANG_FIXES, ACRONYM_EXPANSIONS,
MAX_SENTENCE_WORDS, MAX_LIST_DEPTH, CURRENCY_CODES, PROJECT_URL_PREFIX, OVERLAY_RULES, RULES,
README_CALLOUT_EMOJI, JSON_FENCE_LANGS. Compare set-wise and mapping-wise against the two data sources.
Assertions: zero code-only values; zero Notion-only values; every `Maps to` equals the code's value; every
regex in `acronym_expansions.Maps to` compiles and equals the code string byte for byte.

## P4 — Every table-driven rule is backed by rows
For each rule PLAN-subskills §2.1 calls a pure table lookup, assert its Notion row names a value table and
that table's rows are non-empty. Specifically check `filler-please` (needs `please`, `please note`),
`mt-shorthand` (needs `MT`), `reference-no-shell` (uses `FENCE_LANG_FIXES` + the literal `shell`).
FAIL = rule has no backing rows, contradicting Phase 0's own Exit line.

## P5 — Severity / scope / provenance completeness and vocabulary
Assert all 30 rows have non-null Severity, Scope, Provenance. Assert `Severity=='strict'` iff
`RULES[id][0] is True`. Assert Provenance string equals `RULES[id][1]`. Record how many rows use
`moderate`. Cross-check against PLAN-subskills:210-212 (three grades, precision floors) and the index
page's own Strict/Flexible-only table.

## P6 — Compilability
Name every place a deterministic sync cannot decide the Python value from the rows alone:
list order where the code's order is load-bearing (`OBJECTS` longest-prefix), tuple vs set vs list,
`FILLER_REPLACEMENTS` empty-string value vs absent key, single-valued `Value table` for a rule reading two
tables, the `reference`/`platform` shared prefix, and the emoji rows vs `README_CALLOUT_EMOJI`.
Demonstrate the `OBJECTS` case concretely: reorder the list alphabetically (Notion's default order) and
re-run the checker on a fixture with "ledger account category" — a different finding proves order matters.

## P7 — Un-tabled policy inventory
grep for every literal the checker decides on that appears in neither database; classify each as
mechanism (stays in code, argued) or policy (should be a row).

## P8 — Blast radius
`git status --porcelain` and `git branch -a` for the four repos; `find / -xdev -newermt` outside
`/home/ubuntu/docs-style`; mtimes of shipped files. Assert no repo change, no new branch, and identify any
workspace file changed that Phase 0's "Built" paragraph does not declare.

## P9 — Claim-by-claim honesty audit of PLAN-phases.md
Verify each assertion in the Phase 0 "Built", "Drift resolutions" and "Exit" paragraphs against measured
values: 30 rows, 87 rows, 86 active, "four places" in base-style prose, "each of the 30 rules has a
severity, a scope and a provenance", and the three drift-case resolutions.
