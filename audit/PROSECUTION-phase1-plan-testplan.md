# Prosecution plan — Phase 1 (the sync and the artifact)

Shell + Notion MCP read-only. No servers, no browser, no recording. Nothing is fixed; findings only.

Evidence already gathered in setup (file:line), used to design the cases below:
- `notion_sync.py:57-73` 15 tables; `:88` `SHRINK_FLOOR = 2/3`; `:203-251` compile_values;
  `:234` sort `(-len, value)`; `:248` `<delete>` -> `""`; `:254-301` compile_rules; `:304-306` digest;
  `:341-342` content_hash over policy only, style_hash over page sha256s; `:353` `revision: content-hash`;
  `:371-381` check_shrink; `:412-423` style_note.
- `stylecheck.py:94` ARTIFACT path; `:1110-1122` policy_stamp; `:1106` scorecard `policy` key;
  `:1188` `--list-rules` prints the stamp. No other artifact read → constants still decide.
- `artifact_differential.py:50-70` constants(); `:56` `mt_shorthand` hard-coded literal; `:57-58`
  `filler_words` with `| {"just": None}` hard-coded; `:59` `filler_please` literal; `:94-96` map
  comparison; `:109-135` compare_rules; `:138-150` compare_exceptions (`:148` substring clause).
- `test_notion_sync.py:346-398` TestDifferentialDetectsDrift, 8 injected cases.
- `rules.yaml:37-39` `inactive: {rules: [], values: []}`; `:139` `filler` note says just is "inactive";
  `:399` `filler_words.just: null`; `:493` exception `just (as|like|in time)`.

## A — Exit criteria, quoted, each met/unmet with executed evidence

Phase 1 **Exit** is four clauses. Each gets a command:

A1 "*The compiled artifact reproduces today's constants exactly except for the intentional drift
fixes*" → `python3 dev/verify/artifact_differential.py`; exit 0 and "element-exact" required. Then
independently re-derive the comparison myself (not using their differential) to check the differential
is not the thing under test. PASS iff my independent diff also finds zero.

A2 "*a corpus run against it differs from the current 5,038 findings only by those fixes, each
explained*" → run the checker over all three repos, total the findings, compare to 5,038.
Note the trap: since the checker does not read the artifact for decisions, "a corpus run **against
it**" is not literally possible. Judge whether the clause is met, unmeetable-as-written, or quietly
reinterpreted. FAIL if the count differs from 5,038 with no explanation on record.

A3 "*every guard has a test that trips it*" → enumerate every `raise SyncError` in notion_sync.py and
map each to a test that asserts it. Any `raise` with no test = unmet. Count must be exhaustive, not
sampled.

A4 "*the refreshed `style/*.md` carry the Phase 0 prose edits*" → grep all four edited sections in
`style/01-base-style.md` (LAC in the shorthand list; the `just` clause; `body-h1` not
`first-heading-h1`; the inverted excerpt section) and the rule-tables section in `style/00-index.md`.

A5 **Do**-clause: "*The artifact records `synced_at`, each page's Notion `last_edited_at`, and a content
hash*" → `last_edited_at` is absent by admission (`revision: content-hash`). Judge harshly: does a
content hash answer the same question? Specifically test whether it detects an *external* edit that
reverts to a previous state, and whether it can order two artifacts in time.

## B — Is the artifact consumed, or only stamped?

B1 Corrupt the policy in the artifact in a way that would change a verdict if it were read — set
`values.currency_codes` to `[]` and `rules.body-h1.reported_severity: flexible` — then re-run the
checker on a fixture that violates both.
- If the checker is reading the artifact: currency/body-h1 findings change.
- If it is only stamping: findings identical, only the hash line differs.
PASS = the delivered labelling matches whichever is observed. FAIL = plan/README/SKILL.md claim the
checker reads policy from the artifact when it does not.
B2 Delete the artifact entirely and re-run: the checker must still work and say
"policy not synced", proving the artifact is not load-bearing today.
B3 Grep the plan, README and SKILL.md for any sentence implying the checker's decisions come from the
artifact. Quote any overclaim verbatim.

## C — Guards: construct snapshots that are wrong but compile silently

Baseline: copy `dev/notion/snapshot.json`, mutate one thing, run the sync into a temp skill root, and
record exit status + stderr. A guard is real only if it exits 1. Cases:

C1 Drop a single row from a 14-row table (14→13, 7%) — expect silent success (shrink floor is 1/3).
   Then drop 4 (14→10, 29%) — still under a third. Assert both compile clean, and judge whether
   "fail when a list shrinks by more than a third" is a useful floor for a *policy* list.
C2 Rename a table in every row of one table (e.g. `currency_codes` → `currency_code`) — expect
   `unknown table` SyncError, not a silent empty list.
C3 Unicode/whitespace variants: replace `USD` with `USD ` (trailing space), `U​SD` (zero-width space),
   and `ﬀ`-style NFKC-foldable text; and `Ledger Account` with a non-breaking space. Expect either a
   guard or a differential "in Notion, not in code". A value that silently becomes a *different*
   policy value with no complaint is a finding.
C4 Rich-text markup: put `` `USD` `` and `**USD**` in a Value cell. Expect a complaint; if it compiles
   as a literal with backticks, the policy silently gains a value that can never match.
C5 A row that is Active with an empty Value → expect `empty Value`. And a table whose every row is
   deactivated → expect `has no active rows`.
C6 Duplicate rule id with a *different* severity → expect `appears twice` (not last-wins).
C7 `Maps to` three ways on a map table: `<delete>`, empty, `"   "` (whitespace only). Assert the
   compiled artifact distinguishes `""` from `null`, and that whitespace-only is treated as empty.
   Then assert the **differential** notices if `<delete>` is swapped for empty — `artifact_differential
   .py:94` collapses `None` and `""` via `(want[key] or "")`, so I expect this to be undetected. This
   is the single most important case in this plan: the `<delete>` convention was added *because* of my
   Phase 0 finding, and if the differential cannot see it, the fix is asserted rather than demonstrated.
C8 Determinism: run the sync twice on the same snapshot → identical `content_hash` and `style_hash`.
   Shuffle the row order → hashes unchanged. Change one prose page by one character → `style_hash`
   moves, `content_hash` does not. Change one value → `content_hash` moves, `style_hash` does not.

## D — Is the differential vacuous?

D1 Enumerate every field in the artifact's rule rows (`reported_severity`, `guide_severity`, `scope`,
`value_tables`, `threshold`, `guide_alias`, `provenance`, `note`) and, for each, mutate it in a loaded
artifact and check whether `compare_rules` reports it. Any field that can be changed with no output is
an uncovered field. Expect `guide_severity`, `guide_alias`, `value_tables` and `note` to be uncovered.
D2 Mutate the five *new* tables' code side rather than the artifact side: `constants()` hard-codes
`mt_shorthand`, `filler_please` and `just`, so the comparison for those cannot fail no matter what the
code says. Prove it: change `SANCTIONED_CALLOUTS` (derived → should be caught) versus the fact that
there is no code expression at all behind `{"MT": "Modern Treasury"}` (literal → cannot be caught).
D3 `compare_exceptions:148` has a substring clause `found not in pattern`. Set the artifact's exception
for `just` to a short substring like `as` and check whether it passes. If it does, the exemption
comparison accepts wrong values.
D4 `plain()` strips backticks and collapses whitespace. Change a provenance's punctuation only and see
whether it is reported.

## E — Snapshot vs live Notion (read-only MCP)

E1 Query both data sources live; compare row counts and per-table counts to `dev/notion/snapshot.json`
and to the artifact. Assert: live rules rows == 30 == artifact rules; live values rows == artifact
value count. **Known discrepancy to resolve:** PLAN-phases.md "Built" says "104 rows across 15 tables"
while the delivered artifact is reported as 109 values. Since `inactive.values` is `[]`, these must be
equal; one number is wrong.
E2 Assert all 15 table categories exist live and no column was dropped/renamed (`Reported severity`,
`Guide severity`, `Exceptions` must exist on the live rows).
E3 The Phase-0 `just` class of bug, restated: find any row live that is `Active = __NO__` while the
code still enforces it, and any row `Active = __YES__` that the code does not implement. Cross-check
`inactive` in the artifact against live checkbox state.
E4 Check the `filler` rule's `note` live: the artifact carries "just is authored in the values table
but inactive" while `just` is active and `inactive.values` is `[]`. Confirm the stale note is in Notion
(a source defect) rather than introduced by the sync.

## F — Offline and determinism

F1 Prove no runtime network path: grep shipped files for `socket`, `urllib`, `requests`, `http`,
`notion`, and run the checker with a `socket` guard that raises on any connection attempt
(monkeypatched via a `sitecustomize`-style harness, not by editing shipped code) over a real page.
F2 Run the full suite twice with `PYTHONDONTWRITEBYTECODE=1` and diff the outputs; assert 244 tests and
identical results. Then run the checker twice on one repo with `--format json` and diff (excluding the
`synced_at`/timestamp fields only if they legitimately vary — note if they do).

## G — Product/harness boundary

G1 `cp -r skill/ /tmp/shipped-only/`, delete nothing else, then run the checker and
`notion_sync.py --check` from the copy with `dev/` and `audit/` unreachable. Both must work.
G2 Stronger: run the copy with the *original* tree renamed away so no absolute path can reach `dev/`.
Assert `--list-rules`, a real page check, and `--format json` all succeed and print the same policy hash.
G3 Confirm `test_boundary.py`'s literal check would actually catch a harness path: it only inspects
`ast.Constant` strings (`test_boundary.py:30-32,68-75`), so a path built by concatenation or `parents[2]`
traversal would evade it. Judge whether the boundary is enforced or merely spot-checked.

## H — Whole-plan coherence

H1 Phase 2 requires a byte-identical JSON report before and after re-homing. The report now embeds
`policy <hash> synced <timestamp>` (`stylecheck.py:1106`). A wall-clock `synced_at` inside the compared
payload makes "byte-identical" depend on when the artifact was last synced. Test whether two artifacts
with identical policy but different `synced_at` produce different JSON reports — if so, Phase 1 has
made Phase 2's acceptance test harder and the plan should say how (pin, or exclude the field).
H2 D7: confirm `frontmatter-excerpt` is still strict-on-missing in both code and artifact while the
prose says the opposite, and judge whether the new "the prose states the policy *and* says the checker
still reports the superseded sense" is actually present in the refreshed `style/01-base-style.md`.
H3 Judge whether `guide_severity`/`reported_severity`, the 5 new tables, and `exceptions` pre-commit
anything Phase 3–8 must undo — in particular whether `reported_severity` "capped by measured precision"
is coherent when no precision has been measured yet (gate 6, `PLAN-subskills.md:205-216`).

## I — Blast radius

I1 `git -C /home/ubuntu/repos/<repo> status --porcelain` and `git branch -a` / `git reflog` for the
four repos; assert empty and no new refs since the Phase 0 audit.
I2 `find / -xdev -newermt` since Phase 1 started, excluding the workspace; assert only session
infrastructure.
I3 Secret hygiene: grep the whole workspace (including `dev/notion/snapshot.json`, the artifact and
every `style/*.md`) for the sandbox key prefix `test-`, `MT_SANDBOX_*` values, and any `secret`/`token`
literal. Assert no key material is written to any file. Phase 1 touches no sandbox, so any hit is a
finding.
I4 Confirm nothing was published to ReadMe and no Notion *writes* happened in Phase 1 beyond Phase 0's
intended policy-table edits — check whether the phase edited Notion (the `just` row activation and the
`Exceptions` column are Phase 0 work per the plan; if they happened during Phase 1 the plan mislabels
them).

## Deliverables

`audit/PROSECUTION-phase1.md` — BLOCKING / SERIOUS / NOTED, each with the exact command and output, plus
a remedy, and a verdict list of the Phase 1 exit criteria met/unmet.
`audit/PROSECUTION-phase1-plan.md` — findings about the plan rather than the code, including a judgement
on `revision: content-hash` and the D7 deferral.
