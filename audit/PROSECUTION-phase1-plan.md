# Prosecution — Phase 1, findings about the *plan* rather than the code

Companion to `PROSECUTION-phase1.md`. That report prosecutes the build; this one prosecutes the spec it
was built against. Same evidence base; the commands are in the code report and are cited by section.

The two deviations I was asked to judge are P1 (`revision: content-hash`) and P2 (the D7 deferral). My
verdict on both is that the *decision* is right and the *plan text* is wrong — it still asserts the
thing that was not done, which is how a deviation becomes an undocumented defect.

---

## P1. `revision: content-hash` instead of `last_edited_at` — accept the deviation, change the plan, but replace the capability that was lost

**Plan text, Phase 1 Do:** "The artifact records `synced_at`, each page's Notion `last_edited_at`, and a
content hash." **Delivered:** `source.revision: content-hash`, no `last_edited_at` (code report SERIOUS 4).

The implementation's justification (`notion_sync.py:350-353`) is that "the question a revision id answers
here is 'did this change', which a hash answers without a timestamp." For the *policy*, that is not just
acceptable, it is better: a content hash is content-addressed, so it does not move when someone reflows a
paragraph, and §C8 shows the `content_hash` / `style_hash` split isolating policy edits from prose edits
exactly as intended. A `last_edited_at` would have been noisier for the purpose the plan actually needs
it for.

But the plan asked for a timestamp for a second reason it never states, and that reason is unserved:

- **Staleness cannot be detected cheaply.** `--check` compares the artifact against a snapshot you must
  already have fetched. So "has Notion moved since we last compiled?" requires a full re-fetch. A
  per-page `last_edited_at` answers it with one cheap query. This is the capability that was silently
  dropped, and it is the one a scheduled freshness check in a later phase will want.
- **Artifacts cannot be ordered in time.** `synced_at` is when the sync ran, not when the policy changed.
  Two artifacts with equal `content_hash` and different `synced_at` say nothing about which reflects
  newer Notion state — and §H1 shows that difference is nonetheless visible in every report.
- **The one Notion-describing timestamp is unverifiable.** `snapshot_fetched_at` is copied from the
  snapshot, which `SNAPSHOT_SPEC` asks a human to fill in. The artifact presents an operator-supplied
  string as provenance.

**Plan change I recommend.** Rewrite the Do sentence to: "The artifact records `synced_at`, a policy
content hash, a prose `style_hash`, and per-page content hashes; where the Notion client exposes it, each
page's `last_edited_at` as well." Then add an item for the dropped capability: "a `--stale` mode that
answers 'has Notion changed since this artifact' without a full compile" — and note that it needs
`last_edited_at` or an equivalent, which is the real argument for capturing it at snapshot time rather
than as a formula in Notion. The formula failing is not a reason to drop the field; the snapshot step is a
Notion API call and the API returns `last_edited_time` on every object.

**Do not** leave the plan asserting a field the artifact lacks. That is the worst outcome here, because a
future phase will read the plan and assume the field is there.

---

## P2. The D7 deferral is coherent and should stay — but the plan must own its cost and its exit

**Plan text:** the deferral is now explicit ("`frontmatter-excerpt` — prose inverted per D7 now; the
rule's behaviour inverts in Phase 4") and defended: "Inverting it in Phase 2 is not an option — Phase 2's
exit is a byte-identical report, which is the only proof that re-homing 30 rules changed no verdict."

**That argument is correct and I could not break it.** Inverting the rule in Phase 2 would change
verdicts on 515 pages, which destroys the only evidence that re-homing was safe. Phase 4 is the right
home. Phase 0's prosecution called this defect "moved, not removed"; Phase 1 has made it *disclosed*,
which is the meaningful improvement: `style/01-base-style.md:109` now tells the reader the checker still
reports the superseded sense and to ignore that finding, and the rule's artifact note records the
inversion. A writer is no longer asked to trust a verdict the guide disowns.

Three things the plan still does not say, and should:

1. **The cost, quantified.** For phases 1-3 the strict gate contains 515 findings the guide instructs
   writers to ignore, and `frontmatter-excerpt` is a strict rule whose stated policy is the inverse of
   its behaviour. The plan calls the 515 a "cleanup inventory" but never says that the strict gate is,
   for three phases, not a gate anyone can be held to. If any intervening phase wants "zero strict
   failures" as a criterion, it cannot have it.
2. **The disclaimer needs an owner.** `style/01-base-style.md:107-109` is a temporary paragraph in a
   generated file whose source is Notion. Nothing ties its removal to the Phase 4 change. Add to Phase
   4's exit: "the base-style excerpt disclaimer is removed and the page states only the new policy."
   Otherwise it outlives the bug and the guide starts lying in the other direction.
3. **It weakens Phase 1's own exit criterion 2 into a tautology.** See P3.

---

## P3. Exit criterion 2 is unmeetable as written and currently passes for the wrong reason

**Plan text, Phase 1 Exit:** "a corpus run against it differs from the current 5,038 findings only by
those fixes, each explained".

Two problems.

- **"against it" is not possible in Phase 1.** The checker decides from hard-coded constants; the
  artifact supplies only a stamp (code report BLOCKING 3, proven by sabotaging the artifact and getting
  identical findings). A corpus run "against the artifact" is a Phase 2 capability. As written, the
  criterion describes work this phase deliberately does not do.
- **The difference is zero, and had to be.** All three drift resolutions adopted behaviour the code
  already had (`LAC` was already enforced, `body-h1` was already the rule id, `just` was already
  reported). So "differs only by the intentional drift fixes" is satisfied by differing by nothing at
  all. §A2 confirms 682 pages / 5,038 findings exactly. The criterion has no discriminating power in
  Phase 1 — it cannot fail.

This matters because it reads, in the plan and in any summary of it, as strong evidence that the sync is
faithful. It is not evidence of that at all; it is evidence that Phase 0's drift resolutions were chosen
to be behaviour-preserving, which was itself a good decision.

**Plan change.** Split the criterion. Phase 1 keeps the honest, checkable half: "a corpus run is
unchanged at 5,038 findings, confirming the drift resolutions were behaviour-preserving, and every report
carries the policy hash." Move "a corpus run *driven by* the artifact differs from the baseline only by
explained fixes" to Phase 2, where consumption makes it a real test.

---

## P4. The plan does not say what "byte-identical" means, and Phase 1 just made that ambiguity load-bearing

Phase 2's exit rests on a byte-identical report. Phase 1 put a wall-clock timestamp inside the compared
payload (`stylecheck.py:1106` -> `policy_stamp()` -> `synced_at`). §H1 proves a re-sync of the *same*
snapshot, with `content_hash` unchanged, changes the JSON report:

```
<  "policy": "policy 2b8215e292ca synced 2026-09-02T20:48:40+00:00"
>  "policy": "policy 2b8215e292ca synced 2026-09-02T21:04:44+00:00"
```

Nothing in Phase 1 or Phase 2 acknowledges this. It is a genuine plan defect found by test, and the kind
that surfaces as a mysterious Phase 2 failure at the worst moment. Note the irony: Phase 1's **Do not**
paragraph justifies keeping Notion out of the checker partly because "two runs on the same commit can
disagree" — and Phase 1 introduced a way for exactly that to happen.

**Plan change.** State the rule in Phase 2's entry: the byte comparison is over the report with the
`synced_at` component of the stamp masked (or the artifact pinned for the duration of the comparison),
while `content_hash` is compared. Better, change the product so the report carries `content_hash` as a
structured field and `synced_at` separately, so a consumer can compare one without the other.

---

## P5. The plan's own record of what it built is wrong: 104 vs 109 rows

**Plan text, Phase 0 Built:** "`Docs Style Rule Values` (104 rows across 15 tables)". Live Notion, the
snapshot and the artifact all say **109**, and agree with each other on every one of the 15 tables (code
report NOTED 4). I did not fix it, per instruction.

Small, but this is the second consecutive phase where the plan's "Built" paragraph contained a number
nobody had measured — Phase 0's prosecution found the same class of error in "35 occurrences unreported".
The pattern is the finding: **the plan states counts from memory and they are wrong a substantial
fraction of the time.** Every number in a "Built" paragraph should be produced by a command whose output
is pasted, or not stated at all.

---

## P6. Phase 1 is mislabelled as delivering the Notion-backed policy, when it delivers half of it

`PLAN-subskills.md:149` promises "The checkers read only the artifact, offline, and print the hash in
every report". `PLAN-subskills.md:93` frames the whole point as moving policy "to the *data* the checkers
read". Phase 1 delivers the compile side and the stamp; the read side is Phase 2. That phasing is
sensible.

The problem is that nothing in Phase 1's text says the read side is absent, and the *shipped product*
asserts the opposite in four places (`config/rules.yaml:2`, `notion_sync.py:2,6,402` — code report
BLOCKING 3). A reader of the plan plus the artifact would reasonably conclude the architecture is live.
It is not, and the sabotage test shows a user editing `rules.yaml` changes nothing and gets no warning.

**Plan change.** Add one sentence to Phase 1's **Do**: "The checkers do not yet read policy from the
artifact — they stamp its hash; consumption is Phase 2. The differential is what keeps artifact and
constants equal until then." And make Phase 2's entry criterion cite the differential's completeness,
which is currently the unstated assumption the whole re-homing safety argument rests on.

---

## P7. The plan requires "every guard has a test that trips it" but gives no way to enforce it

The criterion was missed 9 times out of 34 (code report BLOCKING 1) and the phase still reported done,
because "every guard has a test" is checked by human recollection. The suite passes 244 tests, which
reads as thorough and is unrelated to whether the criterion holds.

**Plan change.** Make the criterion mechanical wherever it appears: "the suite asserts that every `raise`
in the sync executes at least once during the suite." That converts a promise into a test — the same move
the plan already makes elsewhere ("verified by an element-by-element diff against the constants rather
than by eye"). Apply the same reasoning to the differential: require that every field the artifact carries
is either compared or explicitly listed as deliberately uncompared, since four fields are silently
uncompared today.

---

## P8. The `Active` gate mechanism has no live instance, and its only description is false

Phase 0's plan text says: "Every row is active today, so the mechanism has no live instance — Phase 1
exercises it with synthetic rows in the guard tests, not by parking a real rule in it." That is honest,
the guard tests do exercise it (`test_inactive_row_is_reported_not_dropped_silently`), and the generated
`00-index.md` header surfaces it truthfully ("nothing — every row is active"), which closes Phase 0 §9's
reader-visibility complaint.

But the one row that *describes* an inactive entry describes one that does not exist: the `filler` rule's
Note, live in Notion and compiled into `config/rules.yaml:139`, says "just is authored in the values table
but inactive; see its row" while `just` is `Active = __YES__` (code report SERIOUS 5). Phase 0's blocking
finding was a false claim about `just` in the plan; the fix corrected the value row beautifully and left
an equally false claim about `just` one table over.

**Plan change.** Two: (a) require the differential to compare `note` and `guide_alias`, so prose fields in
the source of truth cannot contradict the rows they describe without something failing; (b) add to the
admission-gate section that a row's `Note` may not assert an activation state — `Active` is the only place
activation is recorded, and notes restating it will drift. The generated header already does this job
correctly and mechanically.

---

## P9. `Reported severity` is described as "capped by the rule's measured precision" when no precision has been measured

Phase 0's plan text introduces the two-grade split as: "a rule has a `Guide severity` (what a reviewer
applies) and a `Reported severity` (what a run prints, capped by the rule's measured precision)". But
`PLAN-subskills.md:205-216` is explicit that gate 6 has passed nothing: "Today there are zero adjudicated
labels, which is why `docs-content` and `docs-maintain` cannot ship a single rule at any grade above
flexible right now."

So today's `Reported severity` values — 20 strict — are not capped by any measured precision; they are the
code's pre-existing boolean, renamed. The split is a good design and I am not arguing against it (it
captures a distinction the prose genuinely carried). But the plan describes a mechanism that is not yet
operating, in the same breath as the column it describes, and nothing in the artifact records that the cap
is notional. Combined with the fact that **nothing compares `guide_severity` at all** (code report
BLOCKING 2c — it accepts `banana`), the two-grade design is currently unverified in both directions.

**Plan change.** Say that `Reported severity` today mirrors the shipped boolean and becomes
precision-capped when gate 6 produces labels; and add a `precision` (or `measured_at`) field to the rule
rows so the difference between "graded by measurement" and "graded by inheritance" is data rather than
prose. Phase 3's measurement work then has somewhere to write its result, and the gate has something to
check.

---

## Whole-plan coherence: does Phase 1 pre-commit anything Phases 2-8 must undo?

Mostly no, and this is the part of Phase 1 I would defend. Three specific checks:

- **Phase 2 (byte-identical re-homing) remains achievable.** The constants are untouched, the corpus is
  bit-for-bit reproducible (§F2: two JSON runs identical at 528,222 bytes), and the artifact is
  element-exact against the constants for everything the differential actually compares. The two threats
  are P4 (the `synced_at` in the payload) and the differential's blind spots — both fixable before Phase
  2 starts, and neither requires undoing anything built in Phase 1.
- **The schema is additive.** `schema: 1`, `inactive`, `exceptions` and the two severity columns are new
  fields rather than reinterpretations. `exceptions` in particular is the right shape for Phase 4's rule
  inversions. The five new value tables (`mt_shorthand`, `filler_please`, `get_idioms`,
  `json_fence_languages`, `non_json_fence_prefixes`) are compiled but unread, which is harmless and is
  exactly what Phase 2 needs waiting for it.
- **One thing is worth watching.** `compile_values` sorts every table by `(-len(value), value)`
  (`notion_sync.py:234`), which is deterministic and defensible — Phase 0's prosecution established that
  `OBJECTS` order is *not* load-bearing for output, so this is safe today. But it is a compile-time
  decision that silently discards Notion's authored order. If a later phase adds a rule where list order
  *is* semantic (a first-match-wins substitution list, say), the sync will reorder it and the differential
  will not notice, because it compares tables as sets. Worth a line in the plan: "table order in the
  artifact is normalised by length; a rule that needs authored order must say so, and the sync must be
  extended before it is added."

---

## Summary of recommended plan edits

| # | Edit | Why |
|---|---|---|
| P1 | Rewrite the `last_edited_at` sentence to match what is recorded; add a `--stale` capability item | The plan asserts a field the artifact lacks |
| P2 | Add the D7 cost to the plan; tie disclaimer removal to Phase 4's exit | The deferral is right; its cost and its end are unrecorded |
| P3 | Split exit criterion 2; move "run driven by the artifact" to Phase 2 | As written it cannot fail in Phase 1 |
| P4 | Define "byte-identical" in Phase 2's entry (mask `synced_at`) | Phase 1 made a no-op re-sync change the report |
| P5 | 104 -> 109; require counts in "Built" to come from pasted command output | Second consecutive phase with an unmeasured number |
| P6 | State in Phase 1 that consumption is Phase 2; fix the four shipped "checkers read" lines | Phase 1 is mislabelled as delivering the read side |
| P7 | Make "every guard has a test" a mechanical assertion; require every artifact field to be compared or declared uncompared | The criterion was missed 9/34 and nothing caught it |
| P8 | Require `note`/`guide_alias` in the differential; forbid notes asserting activation state | A false `Active` claim shipped in the artifact |
| P9 | Say `Reported severity` is inherited until gate 6 measures it; add a `precision` field | The plan describes a cap that does not yet exist |
| — | Note that artifact table order is normalised, and order-sensitive rules need an extension first | Prevents a silent trap in a later phase |

None of these require undoing Phase 1 work. P4 and P7 should land before Phase 2 begins; the rest are text.
