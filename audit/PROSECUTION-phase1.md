# Prosecution — Phase 1 (the sync and the artifact)

Adversarial verification by shell, in `/home/ubuntu/docs-style`, plus read-only Notion MCP. No servers,
no browser. Nothing fixed, nothing committed. Method: read the product and harness first, then try to
break each claim with an executed command. Every finding below carries the command and its output.

**Counts: BLOCKING 3 · SERIOUS 5 · NOTED 6.**

What held up, stated first because it is most of the work: compilation is genuinely deterministic and
reproducible (§C0/§C8), 25 of 34 guards are real and trip on hostile input (§C), the offline constraint
is proven under blocked sockets (§F1), the shipped skill runs standalone with `dev/` unreachable (§G1),
the refreshed style copies do carry all four Phase 0 prose edits (§A4), the corpus reproduces 682 pages
and 5,038 findings exactly (§A2), and all 15 tables match live Notion row-for-row (§E1). The findings
below are about the things that are *asserted* rather than demonstrated.

---

## BLOCKING

### 1. Exit criterion "every guard has a test that trips it" is unmet: 25 of 34

The Phase 1 **Exit** says, verbatim:

> every guard has a test that trips it

There are 34 `raise SyncError` sites. The suite passes 244 tests and never executes 9 of them. Measured
by tracing every line of `notion_sync.py` executed during the whole suite (no `coverage` in the
environment, so `sys.settrace` over `ast`-located `Raise` nodes — script at `/tmp/pros1/guardcov.py`):

```
$ PYTHONDONTWRITEBYTECODE=1 python3 /tmp/pros1/guardcov.py
suite: ran 244 tests, failures=0, errors=0
raise SyncError sites: 34
tripped by a test: 25   never executed: 9

GUARDS NO TEST EVER TRIPS:
  notion_sync.py:131  raise SyncError(f"{path} is not a snapshot object")
  notion_sync.py:156  raise SyncError(f"{where}: '{column}' is {type(value).__name__}, expected text")
  notion_sync.py:176  raise SyncError(f"{where}: no '{column}' column (schema changed in Notion?)")
  notion_sync.py:188  raise SyncError(f"{where}: '{column}' is {text!r}, which is neither a list nor text")
  notion_sync.py:190  raise SyncError(f"{where}: '{column}' is {text!r}, expected a list")
  notion_sync.py:195  raise SyncError(f"{where}: '{column}' repeats a value ({', '.join(out)})")
  notion_sync.py:213  raise SyncError(f"{where}: empty Value")
  notion_sync.py:261  raise SyncError(f"{where}: empty Rule ID")
  notion_sync.py:392  raise SyncError(f"{ARTIFACT} is not a rules artifact")
```

To be fair to the implementation I then tried to trip all nine by hand. **Eight are real and working** —
the gap is test coverage, not broken guards:

```
:131 snapshot is a JSON list not an object           GUARD TRIPPED (exit 1) ... is not a snapshot object
:156 via Value = a dict (Notion rich-text shape)     GUARD TRIPPED (exit 1) 'Value' is dict, expected text
:156 via 'Maps to' = a list of rich-text objects     GUARD TRIPPED (exit 1) 'Maps to' is list, expected text
:176 rule row missing the Scope column               GUARD TRIPPED (exit 1) no 'Scope' column (schema changed in Notion?)
:188 Scope = '[all' (bad JSON list)                  GUARD TRIPPED (exit 1) which is neither a list nor text
:195 Scope = 'all,all' (repeat)                      GUARD TRIPPED (exit 1) 'Scope' repeats a value (all, all)
:261 empty Rule ID                                   GUARD TRIPPED (exit 1) rules row 2: empty Rule ID
:392 previous artifact is valid YAML, wrong shape     GUARD TRIPPED (exit 1) ... is not a rules artifact
```

Note `:213` ("empty Value") is also reachable — I tripped it in §C5a below — so it too is untested
rather than broken. The ninth, `:190`, is unreachable dead code (see NOTED 2).

**Why blocking rather than a nit:** the exit criterion is not "the guards work", it is "every guard has
a test that trips it", because a guard with no test is a guard that silently rots. Nine of them,
including the two schema-change detectors (`:176`, `:156`) that are the *entire* defence against Notion
renaming a column, rest on my ad-hoc mutation rather than on anything the suite will re-run.

**Remedy.** Add one test per uncovered guard, using the mutations above verbatim. Delete `:190`. Then
make the criterion self-policing: assert in the suite that every `ast` `Raise` node in `notion_sync.py`
is executed by the suite, so a new guard cannot be added without a test.

---

### 2. The differential — the only proof of "element-exact" — is vacuous in three load-bearing places

`dev/verify/artifact_differential.py` prints:

```
$ python3 dev/verify/artifact_differential.py
artifact 2b8215e292ca  30 rules  109 values
  element-exact: every table, rule, severity, scope, threshold and exemption agrees
exit=0
```

That sentence is doing all the work behind the Phase 1 exit criterion "the compiled artifact reproduces
today's constants exactly". Three parts of it cannot fail.

**(a) The `<delete>` distinction is invisible — the very thing it was added to preserve.**

Phase 0's prosecution found `FILLER_REPLACEMENTS` could not round-trip because `note that`'s replacement
*is* the empty string. Phase 1 added the `<delete>` token for exactly this, and the plan says so:

> the literal `<delete>` means "replacement is the empty string" — without that distinction
> `FILLER_REPLACEMENTS` cannot round-trip

The sync compiles it correctly. The differential cannot see it degrade, in **either** direction, because
`artifact_differential.py:94` compares `(want[key] or "") != (got_map[key] or "")`, which collapses
`None` and `""`:

```
$ python3 ... # degrade 'note that' from '' (delete) to None (no replacement)
code FILLER_REPLACEMENTS: {'in order to': 'to', 'note that': ''}
--- degrade 'note that' from '' (delete) to None ---
differential output: *** NOTHING REPORTED ***
--- and the reverse: promote 'simply' from None to '' ---
differential output: *** NOTHING REPORTED ***
--- sanity: a real replacement change IS caught ---
differential output: ["values.filler_words.in order to: code 'to' != artifact 'so as to'"]
```

And the sync will happily produce that degradation from a plausible Notion edit — someone clearing the
`Maps to` cell, or typing spaces into it:

```
C7a 'note that' Maps to <delete> -> empty/None       COMPILED (exit 0)
    'note that' compiled to: None
C7b 'note that' Maps to = '   ' (whitespace)         COMPILED (exit 0)
    'note that' compiled to: None
```

So the Phase 0 remedy is implemented but unverified: the round-trip it exists to guarantee can break
silently and the differential will still say "element-exact".

**(b) Three table expectations are hand-typed literals, not derived from the code.**

`artifact_differential.py:50-70` derives twelve tables from `stylecheck` constants (`set(sc.OBJECTS)`,
`dict(sc.FENCE_LANG_FIXES)`, and `get_idioms`/`non_json_fence_prefixes` genuinely parsed out of the
regexes). But three are typed by hand, and the code has no constant behind them at all:

```
  "mt_shorthand": {"MT": "Modern Treasury"},
  "filler_words": {word: sc.FILLER_REPLACEMENTS.get(word) for word in sc.BANNED_FILLER}
                  | {"just": None},
  "filler_please": {"please"},

$ python3 ...
  sc.MT_SHORTHAND: <absent>    sc.FILLER_PLEASE: <absent>    sc.JUST: <absent>
  'just' in sc.BANNED_FILLER: False
```

Those three policies live in the checker as inline regex literals (`stylecheck.py:991-993` `\bMT\b` ->
`"Modern Treasury"`, `:1023-1024` `\bplease\b`/`"contact"`, and the `just` branch). Because the
differential retypes the expected values instead of extracting them, it cannot detect the code changing.
Proof — mutate the checker's expansion and re-run the differential:

```
$ sed -i 's|"Modern Treasury", sentence|"MT Incorporated", sentence|' skill/.../stylecheck.py
993:            fix=re.sub(r"\bMT\b", "MT Incorporated", sentence), span=match.span())
$ python3 dev/verify/artifact_differential.py
artifact 2b8215e292ca  30 rules  109 values
  element-exact: every table, rule, severity, scope, threshold and exemption agrees
exit=0
```

The checker now tells writers to expand MT to "MT Incorporated" and the differential certifies agreement.
The file already contains the right technique — `code_exceptions()` at `:73-80` extracts the `just` and
`please` exemptions from the source text with a regex — it simply was not applied to these three.

**(c) Four rule fields are compared by nothing.** Mutating each field of a loaded artifact one at a time:

```
  CAUGHT    reported_severity: strict -> flexible          rules.body-h1.severity: code strict=True, artifact flexible
  UNCAUGHT  guide_severity: strict -> flexible             (no output)
  UNCAUGHT  guide_severity: -> nonsense 'banana'           (no output)
  CAUGHT    scope: [platform] -> [all]                     rules.contractions.scope: ...
  UNCAUGHT  value_tables: wiped to []                      (no output)
  UNCAUGHT  value_tables: -> ['currency_codes']            (no output)
  CAUGHT    threshold: 30 -> 29 (sentence-length)          rules.sentence-length.threshold: code 30 != artifact 29
  UNCAUGHT  guide_alias: first-heading-h1 -> junk          (no output)
  UNCAUGHT  guide_alias: -> None                           (no output)
  CAUGHT    provenance: replaced entirely                  rules.body-h1.provenance: ...
  CAUGHT    provenance: punctuation-only change            rules.body-h1.provenance: ...
  UNCAUGHT  note: replaced with a false statement          (no output)
```

`guide_severity` is the more serious of these: it is the new column the two-grade design rests on and
the value the admission gate raises a rule *into*, and it can be set to `banana` in the artifact with
nothing objecting. (`compile_rules` validates it at sync time, so Notion cannot introduce it — but
nothing detects the artifact and the code disagreeing about it, which is what the differential is for.)
`value_tables` being uncompared is how a rule could silently stop being backed by rows — the exact
Phase 0 §4 defect. `note` being uncompared is how BLOCKING/SERIOUS 2 below survived.

Also `compare_exceptions:148` has a substring escape hatch (`found not in pattern`) that accepts
truncated garbage:

```
  exception 'just' := 'as'                       -> UNCAUGHT
  exception 'just' := 'as|like'                  -> UNCAUGHT
  exception 'just' := 'j'                        -> UNCAUGHT
  exception 'please' := 'c'                      -> UNCAUGHT
  exception 'please' := 'cont'                   -> UNCAUGHT
  exception 'just' := 'contact the mothership'   -> CAUGHT
```

**Remedy.** (a) compare maps with a sentinel so `None` and `""` are distinct. (b) extract `MT`,
`please` and `just` from the source the way `code_exceptions()` already does, or hoist them into real
constants in `stylecheck.py` (they are policy, and Phase 2 has to hoist them anyway). (c) compare
`guide_severity`, `value_tables`, `guide_alias` and `note`; drop the substring clause and normalise both
sides instead. Then extend `TestDifferentialDetectsDrift` with one case per newly compared field — its
current 8 cases hit only `currency_codes` ±, one `filler_words` replacement, `reported_severity`,
`threshold`, `scope` and one exemption drop.

---

### 3. The shipped artifact tells the reader something false: "this file is what the checkers read"

`config/rules.yaml:2` ships this line to users, and `notion_sync.py` repeats it three times:

```
$ grep -n "checkers read" skill/docs-style-review/config/rules.yaml skill/docs-style-review/scripts/notion_sync.py PLAN-subskills.md
config/rules.yaml:2:# Notion is the source of truth for the policy; this file is what the checkers read.
scripts/notion_sync.py:2:"""Compile the Notion style-guide policy into the local artifact the checkers read.
scripts/notion_sync.py:6:`config/rules.yaml` (what the checkers read) and refreshed copies of `style/*.md`
scripts/notion_sync.py:402:# Notion is the source of truth for the policy; this file is what the checkers read.
PLAN-subskills.md:149:3. The checkers read only the artifact, offline, and print the hash in every report
```

The checker reads the artifact for the stamp and nothing else. Proof: sabotage the policy in a copied
skill tree — flip `body-h1` to flexible, empty `currency_codes`, corrupt the hash — and the verdict does
not move:

```
$ # BASELINE (untouched artifact)
  STRICT      6  body-h1   Body heading is h1; ReadMe renders the frontmatter title as h1.
FAIL: 1 page(s), 1 strict failure(s), ...
policy 2b8215e292ca synced 2026-09-02T20:48:40+00:00

$ # AFTER SABOTAGE  (body-h1 reported: flexible | currency_codes: [] | hash: DEADBEEFDEAD)
  STRICT      6  body-h1   Body heading is h1; ReadMe renders the frontmatter title as h1.
FAIL: 1 page(s), 1 strict failure(s), ...
policy DEADBEEFDEAD synced 2026-09-02T20:48:40+00:00
```

Identical findings; only the stamp changed. And with the artifact deleted entirely the checker is
unaffected:

```
$ rm sk/config/rules.yaml && python3 sk/scripts/stylecheck.py f.md --project ledgers
FAIL: 1 page(s), 1 strict failure(s), ...
policy not synced (no config/rules.yaki)      # graceful, as designed
```

The architectural plan is fine — `artifact_differential.py:5` is explicit that "the checker still
carries the constants it was written with (Phase 2 re-homes them)", and Phase 2 is where consumption
lands. The defect is that **the shipped product states the end-state as present fact.** A user who
edits `config/rules.yaml` because its own header told them it is what the checkers read will change
nothing and get no warning. Worse, the run advertises `policy DEADBEEFDEAD` — the stamp is a provenance
claim about a file that does not govern the verdict, so today it cannot be relied on for the purpose
`policy_stamp()`'s own docstring gives it ("so a verdict can be reproduced against the exact rule tables
that produced it").

**Remedy.** Reword the four shipped lines to state what is true today, e.g. "Notion is the source of
truth for the policy; the checkers stamp this file's hash in every report and will read their rule data
from it in Phase 2." Leave `PLAN-subskills.md:149` alone — it is the target architecture — but have
Phase 1's own record say plainly that consumption is not yet wired, which the plan currently does not.

---

## SERIOUS

### 4. Exit "the artifact records ... each page's Notion `last_edited_at`" is unmet by substitution

The Phase 1 **Do** paragraph says:

> The artifact records `synced_at`, each page's Notion `last_edited_at`, and a content hash.

```
$ python3 -c "...; print(a['source']['revision']); print('has last_edited_at?', 'last_edited_at' in str(a['source']))"
content-hash
has last_edited_at? False
```

The stated reason (`notion_sync.py:350-353`) is that the client does not expose `last_edited_time`, and
that "the question a revision id answers here is 'did this change', which a hash answers without a
timestamp." Judged harshly, that is two-thirds right and the missing third matters:

- **A hash does answer "did it change"**, and does it better than a timestamp for the policy itself —
  it is content-addressed, so a formatting-only Notion edit does not move it. §C8 confirms the
  separation works exactly as designed.
- **It cannot answer "is my artifact stale"** without re-fetching the whole snapshot. `last_edited_at`
  is cheap to poll; a content hash requires the full fetch you were trying to avoid. `--check` only
  works if you already produced a fresh snapshot, i.e. it validates the compile step, not the freshness
  of Notion.
- **It cannot order two artifacts in time, and `synced_at` is not a substitute** — that is when the
  sync ran, not when the policy changed. Two artifacts with the same `content_hash` and different
  `synced_at` say nothing about which reflects newer Notion state.
- **`snapshot_fetched_at` is self-reported** by a hand-produced snapshot (`SNAPSHOT_SPEC` asks the
  operator for it), so the one timestamp claiming to describe Notion is unverifiable.

**Remedy.** Either record `last_edited_time` per page and per row (it is on the Notion API objects even
if this client's convenience wrapper omits it — the snapshot step is where to capture it), or amend the
plan to drop the requirement and say why, and add the freshness story the timestamp was providing. Do
not leave the plan asserting a field the artifact does not have.

### 5. A false statement about `Active` shipped in the artifact, in the same class as the Phase 0 `just` finding

`config/rules.yaml:139`, compiled straight from Notion:

```
  filler:
    note: just is authored in the values table but inactive; see its row.
```

But `just` is active, and the artifact says so two ways:

```
config/rules.yaml:37-39   inactive: {rules: [], values: []}
config/rules.yaml:399     filler_words: {..., just: null}
```

Confirmed live, read-only, so this is a source-of-truth defect and not a sync artefact:

```
$ notion-query-data-sources (values db, filler_words)
{"Value":"just","Table":"filler_words","Maps to":null,"Active":"__YES__",
 "Exceptions":"just (as|like|in time)",
 "Note":"Filler only as a minimizer. ... Earlier plan text claimed the checker did not report just at
  all; that was wrong (stylecheck.py:1016-1018)."}

$ notion-query-data-sources (rules db, 'filler')
{"Rule ID":"filler","Reported severity":"flexible","Guide severity":"flexible","Active":"__YES__",
 "Note":"just is authored in the values table but inactive; see its row."}
```

The value row was corrected properly and its note is exemplary. The *rule* row's note was left behind
and now contradicts it. This is precisely the failure mode Phase 0's §1 was about — a prose assertion in
the guide that the rows disprove — reintroduced by the fix for it, and it reached the shipped artifact
because the differential does not compare `note` (BLOCKING 2c). It is SERIOUS rather than BLOCKING only
because it changes no behaviour: nothing reads `note`.

Also worth recording, since the generated header is the reader-visible half of the `Active` mechanism and
it is now telling the truth: `style/00-index.md:4` reads
`<!-- Authored but not enforced: nothing — every row is active. -->`. That closes Phase 0 §9's
"no reader-visible signal" complaint — and it is what makes the stale note above self-evidently wrong.

**Remedy.** Fix the `filler` rule's `Note` in Notion, re-sync, and compare `note` in the differential so
the next one cannot ship.

### 6. Malformed rows compile silently into policy that can never match

The Phase 1 **Do** paragraph promises:

> Guards: fail on a missing or malformed table rather than falling back to parsing prose

`cell()` only `.strip()`s. Unicode variants and Notion rich-text markup are neither rejected nor
normalised — they become new policy values:

```
C3a 'USD ' trailing space                     COMPILED (exit 0)   USD in artifact: True        <- stripped, fine
C3b 'US<ZWSP>D' zero-width space              COMPILED (exit 0)   USD present: False | compiled: 'US\u200bD'
C3c 'Ledger<NBSP>Account'                     COMPILED (exit 0)   'Ledger Account' present: False | 'Ledger\xa0Account'
C4a Value = '`USD`' (inline code)             COMPILED (exit 0)   compiled: ['`USD`']
C4b Value = '**USD**' (bold)                  COMPILED (exit 0)   compiled: ['**USD**']
```

A writer who bolds or code-formats a value in Notion — the single most likely thing to happen to a
word in a Notion table — silently removes it from enforcement and substitutes a literal that cannot
match prose. `**USD**` is a malformed row and the sync accepts it. The plan even anticipates the
mechanism ("Notion stores rich text, so inline code formatting in `Provenance` does not survive the
round trip") but applies the reasoning only to `Provenance`, where it is harmless, and not to `Value`,
where it is not. The dev-only differential would flag these as "in Notion, not in code" for the twelve
derived tables, but that is a harness run someone has to remember, not a guard, and it is blind for the
three hand-typed tables in BLOCKING 2b.

**Remedy.** In `cell()`, NFKC-normalise, reject or strip zero-width and non-breaking characters, and
reject `` ` ``/`*`/`_` markup in `Value` and `Maps to` (a style guide never bans a word containing a
backtick). Add the three mutations above as guard tests.

### 7. A no-op re-sync changes the report bytes, which endangers Phase 2's exit criterion

Phase 2's exit is a byte-identical report before and after re-homing. `stylecheck.py:1106` puts
`policy_stamp()` — which includes the wall-clock `synced_at` — inside the compared payload. Re-syncing
the *same* snapshot leaves the policy identical and still moves the report:

```
$ python3 sk/scripts/stylecheck.py <corpus> --format json > before.json
$ sleep 1 && python3 sk/scripts/notion_sync.py --snapshot snapshot.json
  content_hash unchanged: 2b8215e292ca
  new synced_at: 2026-09-02T21:04:44+00:00
$ python3 sk/scripts/stylecheck.py <corpus> --format json > after.json
$ cmp before.json after.json
  *** REPORTS DIFFER ***
30c30
<         "policy": "policy 2b8215e292ca synced 2026-09-02T20:48:40+00:00"
---
>         "policy": "policy 2b8215e292ca synced 2026-09-02T21:04:44+00:00"
```

Phase 1 has made Phase 2's acceptance test dependent on when the artifact was last synced, and nothing
in either phase's text acknowledges it. Two runs on the same commit can now disagree — which is the
precise harm the Phase 1 **Do not** paragraph invokes to justify keeping Notion out of the checker.

**Remedy.** Split the stamp: keep `content_hash` in the report (it is the reproducibility claim) and
either exclude `synced_at` from the JSON payload or have Phase 2 compare with it masked. Say which in
the plan.

### 8. D7: a page written exactly as the refreshed guide instructs still strict-fails

Unchanged from Phase 0 §2, deliberately, per the plan's "deferred to Phase 4". Verified against the
shipped Phase 1 tree:

```
$ cat no_excerpt.md   # title only — exactly what the refreshed guide asks for
$ python3 stylecheck.py no_excerpt.md --project ledgers --rule frontmatter-excerpt
  STRICT      1  frontmatter-excerpt      Page has no excerpt; it is the search and preview text.
FAIL: 1 page(s), 1 strict failure(s)

$ python3 stylecheck.py with_excerpt.md --project ledgers --rule frontmatter-excerpt
PASS: 1 page(s), 0 strict failure(s)
```

The mitigation is real and I want to credit it: `style/01-base-style.md:107-109` now warns the reader
explicitly ("The checker has not caught up with this yet: today it still reports a *missing* excerpt,
which is the superseded rule. Ignore that finding."), and the rule's artifact note records the Phase 4
inversion. That is honest, and much better than Phase 0. What remains is the cost, which the plan does
not quantify: for three phases the strict gate contains 515 findings the guide instructs writers to
ignore, and a rule whose stated policy is the inverse of its behaviour. Judged against the exit
criterion, this is also *why* criterion 2 passes trivially (SERIOUS-adjacent, see the verdict list): a
corpus run "differs only by the intentional drift fixes" partly because no drift fix changed behaviour
at all.

**Remedy.** Keep the deferral — inverting now would break Phase 2's byte-identical exit, and the plan is
right about that. Add to Phase 4's exit that the base-style disclaimer paragraph is removed in the same
change, or it will outlive the bug.

---

## NOTED

1. **The shrink floor is per-table and lets a 29% policy loss through.** As specified ("fail when a list
   shrinks by more than a third"), implemented correctly, but the practical effect on small tables is
   worth stating: dropping 4 of 14 currency codes compiles clean.
   ```
   C1a drop 1 of 14 currency codes (7%)    COMPILED (exit 0)   currency_codes now: 13
   C1b drop 4 of 14 currency codes (29%)   COMPILED (exit 0)   currency_codes now: 10
   C1c drop 5 of 14 currency codes (36%)   GUARD TRIPPED (exit 1) refusing a sync that drops more than
                                             a third of a list (table:currency_codes: 14 -> 9)
   ```
   The `inactive` list in the artifact and the generated `00-index.md` header do surface deactivations,
   which is the main mitigation. Consider also failing when a rule's backing table shrinks at all
   without `--force`.
2. **`notion_sync.py:190` is dead code.** It fires when text starting with `[` parses as JSON to a
   non-list, which cannot happen: `json.loads` of anything starting with `[` yields a list. This is the
   one guard from BLOCKING 1 that no test *can* trip. Delete it.
3. **`test_boundary.py`'s path check is evadable by string concatenation.** It inspects only
   `ast.Constant` literals (`:30-32`, `:68-75`), so a shipped file can reach the harness without holding
   a literal harness path:
   ```
   HARNESS = ROOT / ("d"+"ev") / "notion" / "snapshot.json"
     literals found by test_boundary.literals(): ['snapshot.json', 'notion', 'd', 'ev']
     -> flagged by test_no_harness_path_is_opened? False
     -> flagged by test_no_harness_import? False
   ```
   No shipped file does this today — §G1 shows the copied tree runs standalone — so this is
   defence-in-depth, not a live defect. A stronger check: run the shipped tree with the workspace
   renamed and assert nothing raises.
4. **`PLAN-phases.md` "Built" undercounts the values database: 104 vs 109.** All three sources agree on
   109 and disagree with the plan:
   ```
   table                       live  snapshot  artifact  match     ... (all 15 rows 'yes')
   TOTALS  live=109 snapshot=109 artifact=109
   PLAN-phases.md 'Built' claims: 104 rows across 15 tables
     -> actual is 109 rows across 15 tables
   ```
   A pure documentation inaccuracy in the plan's own record of what it built. I did not fix it.
5. **One no-op git operation touched a source repo during the Phase 1 window.**
   `docs-readme-ledgers` reflog shows `2b2ae79 HEAD@{2026-09-02 20:53:02}: checkout: moving from v2.0 to
   v2.0` — same SHA, no content change, tree clean. Recording it only because the constraint was "no
   writes to `/home/ubuntu/repos/*`"; nothing was modified, committed, branched or stashed.
6. **Hypotheses from the brief I could not substantiate**, recorded so they are not re-litigated:
   - *Provenance is not compared.* It is, and more strictly than expected — even a punctuation-only
     change is caught. Only backticks and whitespace runs are normalised away, which `plain()` documents
     and the plan explicitly sanctions.
   - *Row reordering or formatting-only edits move the hashes.* They do not; the separation is exact
     (§C8 below).
   - *Something in the runtime path reaches the network.* Nothing does (§F1).
   - *Sandbox keys or tokens were written to a file.* None. The only regex hits in the workspace are
     third-party `node_modules` noise; `dev/notion/snapshot.json` and `config/rules.yaml` contain zero
     matches for `authorization|api_key|bearer|secret`.
   - *A source repo was modified.* All four are clean with no new branches, commits or stashes.

---

## Evidence for the things that held up

**§C0 / §C8 — determinism and reproducibility are exemplary.** Compiling the real snapshot in an
isolated tree reproduces the shipped hash exactly, and all six determinism properties hold:

```
C0 control: unmutated snapshot   COMPILED (exit 0)   hash: 2b8215e292ca (real is 2b8215e292ca)

run 1: ('2b8215e292ca', 'c4612b4f499c')
run 2 (same snapshot):           ('2b8215e292ca', 'c4612b4f499c') -> IDENTICAL
run 3 (rows+pages shuffled):     ('2b8215e292ca', 'c4612b4f499c') -> IDENTICAL
run 4 (prose edit):              ('2b8215e292ca', '0b455f68f81d') -> content same | style MOVED
run 5 (value edit):              ('de35ba0b0dd0', 'c4612b4f499c') -> content MOVED | style same
run 6 (fetched_at only):         ('2b8215e292ca', 'c4612b4f499c') -> both unchanged
```

**§C — 25 guards are real.** Beyond the eight I tripped by hand in BLOCKING 1:

```
C2  rename table currency_codes->currency_code   GUARD TRIPPED  unknown table 'currency_code'; known tables are ...
C5a Active row with empty Value                  GUARD TRIPPED  values row 102: empty Value
C5b Active row with whitespace-only Value        GUARD TRIPPED  values row 102: empty Value
C5c whole table deactivated (callout_emoji)      GUARD TRIPPED  table 'callout_emoji' has no active rows; a rule
                                                                reads it, so an empty list would silently disable a check
C6a duplicate rule id, different severity        GUARD TRIPPED  rules row 31: rule 'body-h1' appears twice
C6b duplicate rule, first copy inactive          GUARD TRIPPED  rules row 3: rule 'body-h1' appears twice
C6c duplicate value in the same table            GUARD TRIPPED  values row 110: 'USD' appears twice in currency_codes
```

Notably C6a is last-wins-proof and C5c refuses to silently disable a check — both good.

**§A2 — the corpus reproduces exactly.** The canonical 682-page snapshot is
`/home/ubuntu/style-corpus-head` (not the live repos, which drift; those give 5,036 over 676 pages):

```
ledgers    docs-readme-ledgers  pages=76  findings=1132
payments   docs-readme-payments pages=169 findings=1897
platform   docs                 pages=94  findings=1078
platform   custom_pages         pages=1   findings=2
platform   custom_blocks        pages=8   findings=20
reference  reference            pages=334 findings=909
TOTAL pages 682 findings 5038
```

**§A4 — the refreshed style copies carry all four Phase 0 prose edits.**

```
style/01-base-style.md:81   `LA`, `LT`, `LAS`, `EP`, `PO`, `IPD`, `LAC` are banned in prose.
style/01-base-style.md:89   ### First heading is h1, and levels never skip — **Strict** (`body-h1`, `heading-skip`)
style/01-base-style.md:107  ### Frontmatter has `title`, and no `excerpt` — **Strict** (...)
style/01-base-style.md:108  We do not use excerpts. Do not add one to a new page, and delete the one you find ...
style/00-index.md:26        <td>**Moderate**</td>          # the grade the gate needs, now defined
style/00-index.md:36        ## The rule tables
```

**§E1 — snapshot, artifact and live Notion agree on every table.** All 15 rows matched (table above,
NOTED 4). Rule severities live: 20 strict/strict, 4 flexible/strict (the two-grade split), 6
flexible/flexible, all 30 active, zero `moderate` — consistent with the plan's account.

**§F1 — offline is proven, not asserted.** Whole corpus and a full compile under a `sitecustomize` that
raises on any socket call:

```
$ PYTHONPATH=/tmp/noNet python3 stylecheck.py <corpus>/docs-readme-ledgers --project ledgers --format json
  ran clean, findings = 1132 | policy = policy 2b8215e292ca synced 2026-09-02T20:48:40+00:00
$ PYTHONPATH=/tmp/noNet python3 scripts/notion_sync.py --snapshot snap.json
  policy 2b8215e292ca  style c4612b4f499c  (policy unchanged)
```

**§F2 — repeat runs agree.** Suite identical across two runs bar timing (`Ran 244 tests in 1.941s` vs
`1.985s`); two JSON corpus runs byte-identical at 528,222 bytes.

**§G1 — the shipped skill stands alone.** Copied `skill/docs-style-review` to `/tmp/g1/sk` with `dev/`
and `audit/` unreachable: a page check, `--list-rules` and `--snapshot-spec` all work, and
`notion_sync.py --check` gives a clean usage error rather than reaching for a harness default (which
`test_boundary.py:77-83` also asserts).

**§I — blast radius clean.** All four repos: 0 porcelain lines, single expected branch, 0 stashes, no
commits in the Phase 1 window. `find /home/ubuntu -xdev -newermt "2026-09-02 20:30"` outside the
workspace: 0 files.

---

## Verdict: Phase 1 exit criteria

| # | Criterion (quoted) | Verdict |
|---|---|---|
| 1 | "The compiled artifact reproduces today's constants exactly except for the intentional drift fixes" | **Met, weakly proven.** True as far as I can independently confirm — all 15 tables match live Notion and the twelve derived comparisons are genuine — but the mechanism that certifies it is vacuous for the `<delete>` distinction, three tables and four rule fields (BLOCKING 2). `guide_severity`, `value_tables`, `guide_alias` and `note` are verified by nothing at all. |
| 2 | "a corpus run against it differs from the current 5,038 findings only by those fixes, each explained" | **Met numerically, vacuous in substance.** Exactly 682 pages / 5,038 findings. But the run is not "against it" — the artifact does not drive any decision (BLOCKING 3) — and the difference is zero because all three drift resolutions adopted behaviour the code already had. This criterion cannot fail until Phase 2. |
| 3 | "every guard has a test that trips it" | **Unmet.** 25 of 34 (BLOCKING 1). |
| 4 | "the refreshed `style/*.md` carry the Phase 0 prose edits" | **Met.** All four edits present, plus an honest D7 disclaimer and the `Moderate` grade the gate needs. |
| 5 | Do: "The artifact records `synced_at`, each page's Notion `last_edited_at`, and a content hash" | **Partially unmet.** `synced_at` and both hashes present; `last_edited_at` absent by substitution (SERIOUS 4). |
| 6 | Do not: "Let any checker read Notion at run time" | **Met**, proven under blocked sockets (§F1). |
| 7 | Side: product/harness separation | **Met.** Shipped tree runs with `dev/` unreachable; the boundary *test* is evadable but nothing evades it (NOTED 3). |

**Recommendation.** BLOCKING 1 and 2 are a day's work and both are test-side, not design-side: the sync
itself is the strongest part of this phase. BLOCKING 3 is four lines of prose. I would not start Phase 2
before BLOCKING 2 is closed, because Phase 2's whole safety argument is "the differential proves
re-homing changed nothing", and today the differential cannot see changes to `guide_severity`,
`value_tables`, the `<delete>` semantics, or the three tables it hand-types — which is exactly the
surface Phase 2 moves. SERIOUS 7 should be settled before Phase 2 starts too, since it decides what
"byte-identical" means.
