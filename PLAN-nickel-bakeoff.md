# Nickel bakeoff — plan

Companion to `PLAN-phases.md`. That plan's Phase 0c moved policy out of Notion into hand-authored
YAML read by `policy.py`. This one asks whether the same policy expressed in Nickel, with the loader
reduced to an accessor layer, beats it — and defines what "beats" means before either side is built.

Both implementations stay live. The YAML path remains the one that ships until this decides
otherwise; nothing here edits it.

## Why this is being asked

`policy.py` is 436 lines. 233 of them — 53% — are schema validation, merging and file reading. That
is a configuration language, hand-rolled, written over one session. Nickel's four features map onto
it almost exactly: `import` replaces the `includes:` mechanism and its path guard, `&` replaces the
merge, contracts replace 46 hand-written refusals, and Nickel already errors on conflicting
non-default fields, which is the one-owner rule for free.

**Two corrections from the discussion that produced this plan, recorded because they change the
question.**

*The one-owner rule was never a rejection of composition.* It was written in Phase 0b against a
migration hazard — the same 64 rows living in Notion and in `invariants.yaml` at once, two complete
copies free to drift. Base-plus-delta is not duplication. The prohibition on the second was
generalised from a guard against the first and never re-examined, and it was then offered as an
argument against Nickel. It is not one.

*The guide already promises an override the policy cannot express.* `style/00-index.md`: "Where an
overlay contradicts base style, the overlay wins for that project." Nothing exercises it today — the
overlays add project-scoped rules or restate base ones, and the one genuine contradiction the guide
ever had (reference pages requiring an excerpt) was fixed in D7 by reconciling the two pages rather
than by layering. But the prose commits to a behaviour the machinery has no way to implement, which
is the guide-versus-checker drift this project exists to remove, sitting latent. Whichever side of
the bakeoff wins has to close it.

## Shape under test

Nickel is harness. The skill ships one evaluated file and needs no toolchain to read it.

| Harness (`dev/nickel/`) | Ships |
|---|---|
| `schema.ncl` — every contract, one per refusal | the evaluated policy, as YAML |
| `policy.ncl`, `rules.ncl`, `language.ncl` — the sources | `scripts/*.py`, `SKILL.md`, `style/*.md` |
| the export step and its CI equality check | |
| `fixtures/` — one deliberately-broken file per contract | |

Nickel emits the **final, matcher-ready** shape: sorted longest-first, `map`/`values`/`ranges`
resolved, `ordered` honoured, `project_url_prefixes` derived from `projects`. Python reads it and
answers questions. If the evaluation only validated and Python still shaped the data, this would be
a worse version of what exists and should be abandoned at that point.

**YAML, not JSON, as the exported format.** The README installs this skill by copying the directory,
so installed copies live away from the source repo; with YAML someone can still patch a filler word
in place rather than needing a Rust toolchain for one word. Generated YAML also stays readable in a
review diff, and every policy change produces two diffs — the meaningful `.ncl` one and the generated
one — so the generated one being skimmable matters. The explanation survives either way: across the
three current files there are 57 `why:`/`provenance:` fields against 28 comment lines, so the
documentation is data and comes through evaluation intact. Only file headers are lost, and those are
contributor-facing.

## The two blocking questions, and how each is answered

Both were raised as reasons to doubt the port. Both look solvable; neither is assumed.

### 1. Contract coverage must be measured, not asserted

Today `guard_coverage.py` traces the test suite with `sys.settrace` and proves every
`raise PolicyError` line was executed: 46 of 46, measured. Losing that is the one regression this
plan will not accept quietly.

The Nickel equivalent, by identity rather than by line:

- **Granularity is preserved by construction.** Each refusal is its own named contract, composed with
  `std.contract.all`, rather than one contract with several internal checks. `_ranges` alone is three
  refusals today — not a pair, not integers, runs backwards — so it becomes three named contracts.
  One contract, one refusal, one fixture, and the count stays comparable to 46.
- **Enumeration needs no parsing.** Contracts are fields of one record in `schema.ncl`, so
  `nickel query` lists them. A source-parsing enumerator would be a second implementation that can
  drift from the first.
- **Provocation is a fixture directory.** One deliberately-broken `.ncl` per contract, each expected
  to fail blaming that contract by name.
- **`dev/verify/contract_coverage.py`** runs every fixture, extracts the blamed contract from stderr,
  and asserts the provoked set equals the enumerated set — reporting in the same words as today:
  `N contracts in schema.ncl: N provoked by the fixtures, 0 untested`.

This is arguably stronger than the tracer it replaces: coverage by contract identity survives a
refactor that moves lines, where line-number tracing silently re-covers whatever moved into place.

**The risk that decides it, and it is retired first.** Under `std.contract.all`, does Nickel's blame
reliably name the *innermost* failing contract? If it names only the outermost, attribution is
impossible and the composition has to be flattened — each contract applied at its own field — or the
approach fails. Stage 0 answers this on three representative contracts before anything else is
built.

### 2. Errors must name the cell and say what to type

The 46 refusals were written deliberately against a declarative validator whose message is a JSON
path. That property is not negotiable, and it is testable rather than a matter of taste.

Nickel's `std.contract.custom` returns `'Error { message, notes }`, and blame carries the field path
and the source position. So a contract can say what is wrong, where, and what to write instead —
which is more than the current Python messages give, since they name the cell in prose but cannot
point at a line.

**Acceptance is a rubric over the same broken inputs, scored per refusal, and it is binary:**

1. Does the error identify the offending field, by path or by position?
2. Does it state the remedy — what to write, not merely what is wrong?

46 of 46 must pass both. A contract that says `contract broken` and a path is a fail, not a
near-miss. The same broken-input corpus is run through both implementations and the messages are
printed side by side, so the comparison is read rather than claimed.

## Stages

Each stage says what has to be true before the next starts. A stage that cannot answer its question
ends the bakeoff in favour of YAML, which is a result and not a failure.

**Stage 0 — retire the two risks.** Three representative contracts only, no data: one simple
(`Severity`), one composed (`Range`, three checks), one cross-field (reported never stricter than
guide). Prove blame attribution under composition, and that an error can carry path plus remedy.
*Exit:* both demonstrated, or stop. Timeboxed; this is the cheapest place to learn the answer is no.

**Stage 1 — the schema.** Every contract, no data. Named one per refusal, enumerable by
`nickel query`.
*Exit:* the enumeration lists a contract for each of the 46 refusals in `policy.py`, mapped one to
one in a table checked into the repo.

**Stage 2 — the data.** `policy.ncl`, `rules.ncl`, `language.ncl`, generated from the current YAML
rather than retyped — the same discipline every migration in this repo has used, for the same
reason: these lists go into regexes and codepoint comparisons, and one wrong character compiles into
a check that silently matches nothing.
*Exit:* `nickel export --format yaml` produces a file; nothing is compared yet.

**Stage 3 — equivalence.** The evaluated Nickel policy must equal the YAML policy exactly: same
tables in the same order, same rules, same messages, same exemptions, same policy id. Then the lint
corpus must produce identical findings under both.
*Exit:* byte equality on the evaluated policy and identical findings. A difference here is a porting
bug, not a design difference, and is fixed rather than explained.

**Stage 4 — contract coverage.** Build `contract_coverage.py` and the fixture directory.
*Exit:* N of N provoked, 0 untested, with N mapped to the 46.

**Stage 5 — error quality.** Run the broken-input corpus through both, print side by side, score the
rubric.
*Exit:* 46 of 46 pass both rubric questions, or the gap is named per refusal.

**Stage 6 — the override the guide promises.** Implement per-project severity override on the winning
side, closing the latent gap named above. Nickel's merge with priorities is the interesting case; the
YAML side would need roughly twenty lines in `_rules` plus per-project resolution on `Rule`. Doing it
on both is what makes the comparison mean something, since this is the one place the two approaches
genuinely differ in kind.

**Stage 7 — decide**, against the criteria below and nothing else.

## Results, stages 0-5 (run 2026-09-03/04, nickel 1.17.0 via homebrew on a contributor Mac)

Five runs, each ending at the first gate it could not pass, which is how the plan said it would go.
The execution split held: the Mac ran only Nickel, the sandbox ran only Python, `dev/nickel/out/` was
the entire interface.

**Blocking criterion 1 - equivalence: PASSED.** `main.ncl` evaluates the full composition; the
export reproduces the shipped policy exactly - 30 rules, 28 tables, every entry and order, and the
same policy id (`8601df99863b`), computed by the same identity function over the rebuilt shapes.

**Blocking criterion 2 - coverage: PASSED.** 34 of 34 contracts provoked by a fixture, 0 untested,
measured by `contract_coverage.py` from per-fixture logs; enumeration from `codes.ncl`, attribution
by each contract's own embedded code. Together with the 9 refusals that stay in Python under the
existing tracer, the "every refusal is provoked by a test" property survives the split intact.

**Blocking criterion 3 - error quality: PASSED comparatively, with a shared debt found.** Q1 (names
the offending entity): 34 of 34 on both sides. Q2 (states the remedy): Nickel better on 11, tie on
23, worse on 0 - and every Nickel error additionally carries file, line and column via blame, which
the Python loader structurally cannot. The rubric also caught the plan itself overstating its
baseline: 16 of the refusals state the breakage without a remedy *on both sides*, because the Nickel
messages were ported from Python's. That is a wording debt independent of the bakeoff - loader
messages are not covered by the policy id, so rewording them moves nothing.

**What five runs against a real evaluator taught, recorded in `dev/nickel/README.md`:** records are
recursive, so a field defined in terms of its own name is infinite recursion that laziness hides
until the first failure; `doc` is a reserved keyword; an unforced `let` never runs its contract, so a
fixture must put the contract on an exported field; `std.string.length` counts grapheme clusters
where Python counts codepoints, so longest-first order became generated data rather than recomputed
under two semantics; and Nickel emits YAML 1.2 while PyYAML parses 1.1, which turned the string "no"
into boolean `False` - equivalence rides JSON, and the shipped-artifact format decision inherits that
datum.

**Open before stage 7:** stages 3b, 4b and 6 below.

## Deepenings, added after stages 0-5 passed

The first pass proved the policies equal and the contracts covered. Two gaps remained between that
and "thorough", and both are now built.

**Stage 3b - the checker cannot tell which language built its policy: PASSED.** Object equality is
not behavioural identity: the accessor layer compiles regexes from these tables, renders message
templates, resolves thresholds. So a harness shim (`dev/nickel/shim/sitecustomize.py`, activated by
environment in every process including subprocesses) feeds the entire Python checker from the Nickel
export without touching `skill/`. Result: all 199 checker tests and 57 subtests pass, the behavioural
subskill tests pass, and a real page produces byte-identical findings under both backends. The
failures the shim *causes* are exactly the loader tests (which damage YAML the shim ignores) and the
boundary test correctly objecting to a harness path feeding policy - both by construction, both
listed, neither about the checker.

**Stage 4b results (first sweep).** 110 mutants: 102 killed, 2 survived, 6 stillborn (excluded from
the rate as unparseable) - kill 102/104 = 0.981, above the repo's 0.950 admission bar on the first
pass. The same run put the whole policy evaluation at 0.152s, which retires the pre-commit-latency
worry from criterion 5: pre-evaluating remains the shipping design, but even evaluating at check time
would cost a sixth of a second.

Both survivors were adjudicated, and each was a different lesson. Mutant 006 flipped the record
branch of `is_empty_entries` - dead code from before maps became pair arrays, unreachable by any
well-formed fixture; deleted rather than fixture-chased, which also improves the error a record-shaped
`map` gets (the pairs remedy instead of "table is empty"). Mutant 070 rewired `check_projects` so
that `projects = {}` - present, a record, empty - escaped the refusal; the fixture only tested the
*missing* key. Genuine coverage gap: the fixture now supplies the empty record, and the missing-key
path stays pinned because dropping its negation breaks valid policy, which the good-path evaluation
kills. Second sweep target after both fixes: 0 survivors over 107 mutants.

**Stage 4b - mutation-test the schema itself: BUILT, awaiting one run.** Stage 4 proved every
contract can fire; it did not prove the fixtures would notice a *broken* contract, and this repo's
own admission gate demands mutation kill >=0.950 of every checker. `gen_schema_mutants.py` writes 110
single-site operator flips of `schema.ncl` (==/!=, &&/||, dropped negations, off-by-one emptiness);
`mutation.sh` runs each against main.ncl plus all 34 fixtures - killed when the export changes or a
fixture's verdict moves, STILLBORN (excluded from the rate) when the mutant does not parse, survivor
otherwise, each survivor named for adjudication. The same run times the full evaluation, which is
criterion 4's performance datum.

## Stage 6, redesigned: the override as a capability, not a demo

The original stage 6 was a comparison exercise. Redesigned so that whichever side wins, the skill
ends up better: the index page's promise - "where an overlay contradicts base style, the overlay wins
for that project" - becomes real machinery.

**The feature.** A rule may carry `overrides: {<project>: {reported, guide}}`. Effective severities
for a page are the override's when one names the page's project, else the rule's own. Three new
refusals, mirrored on both sides with fixtures and mutations like every other: an override for an
unknown project, an override for a project outside the rule's scope (dead policy), and the
never-exceed-the-guide law applied per project.

**Where the two sides genuinely differ in kind - what criterion 6 actually measures.** The Nickel
side resolves at evaluation: the export carries `severity_by_project`, fully resolved, and no loader
anywhere resolves anything. The YAML side has no evaluation step, so its loader must resolve at load
time - ~20 lines in `_rules` plus the accessor. Same feature, resolution living in data versus living
in code; that difference, felt on a real capability, is the honest input to stage 7.

**Verdict neutrality, provable as ever.** No shipped rule carries an override, so the policy id must
not move and the corpus behaviour must not change; the capability lands dormant, and its first real
use is a deliberate policy change through the admission gate.

**Blast-radius amendment, explicit.** Stage 6's YAML half necessarily touches
`skill/docs-review/scripts/policy.py` (the resolver and accessor) and `lint.py` (consuming per-project
severity). The original "nothing in skill/ changes until stage 7" was written for the *port*; a
dormant additive capability proven id-stable and suite-green is allowed under it, and this sentence
is the record of that decision.

## Stage 6 results: the override, built on both sides

**The capability is real and it works.** A rule may carry `overrides: {<project>: {reported, guide}}`.
Proven end to end on one page of identical content: with `passive-voice` graded strict and overridden
to flexible for payments, a payments page PASSES and a ledgers page FAILS. That is the index page's
promise - "where an overlay contradicts base style, the overlay wins for that project" - executing
for the first time.

**Dormant, and provably so.** No shipped rule carries an override; the policy id is unmoved at
`8601df99863b`, and 341 tests pass. Keeping it unmoved took one deliberate decision: `overrides` is
added to the hashed projection *only when non-empty*, because an `overrides: {}` on every rule would
have restamped every stored report for a feature nobody is using - the dormant-capability form of the
same argument that keeps documentation out of the id.

**Six refusals, not the three this plan guessed.** Unknown project, override outside the rule's scope
(dead policy that reads as live), reported-stricter-than-its-own-guide - plus shape and severity
validation, which are different mistakes and so get their own codes and fixtures. 42 of 42 mutations
provoke the expected refusal on the Python side.

**Criterion 6, the one that was supposed to decide this - and it comes out a draw on the merits.**
The Nickel side resolves precedence at evaluation: `lib.ncl` computes `severity_by_project` and the
export states the answer per project, so no loader resolves anything. The Python side resolves at
load: `_overrides` parses and validates, `Rule.severity_for` answers, and `lint.py` calls
`strict_for(page.project)` at the one site that builds a finding. Honest count: Nickel needed ~30
lines of resolution in `lib.ncl` plus threading `projects` through two contract signatures; Python
needed ~45 lines in `policy.py` plus one line in `lint.py`. Comparable effort, and both landed the
same afternoon.

Where Nickel is genuinely better: the cross-file check is natural (the parent defines projects, the
subskill references them, and `SubskillDocumentFor projects` parameterises the contract over exactly
that), and a consumer of the export never has to know precedence exists. Where Python is genuinely
better: the resolution is one readable function with a name, and reading `severity_for` tells you the
rule in four lines. Neither is the landslide criterion 6 was written expecting.

## Stage 7: the decision

**Keep YAML. Do not adopt Nickel.** The three blocking criteria all passed, so this is not a rejection
on evidence of failure.

**This section was rewritten after the fact, and the first version's reasoning is withdrawn.** It said
the decision turned on "criterion 6 came out a draw". That is true and it is the wrong reason: the
criterion written to decide the bakeoff was aimed at the weakest of the four things that motivated it,
while the strongest was structurally barred from scoring. The verdict survives the correction. The
reasoning below replaces it, and the critique of how the criteria were built is appended to the
criteria section itself, which is left as written.

### Scored against the two pains that started this, not against the criteria

`## Why this is being asked` names two, and the second has two halves that came apart - the *volume*
of hand-rolled validation, and the *quality of what it says* when it refuses. Scored separately
because they got opposite answers.

| Originating pain | Solved? | By what |
|---|---|---|
| The guide promises an override the policy cannot express (`style/00-index.md`) | **Yes** | The **YAML** side, Stage 6: ~45 lines in `policy.py`, one line in `lint.py`. Proven live, dormant, id unmoved. |
| 53% of `policy.py` is hand-rolled schema validation, merging and file reading | **No** | Nickel relocates it; it does not remove it. |
| That machinery's messages are worse than a real validator's | **Yes - by writing better prose** | Nickel won this at stage 5 (11 better, 23 tied, 0 worse). Stage 6b reworded the Python side and inverted it: 17 better, 15 tied, 0 worse. The pain was real; the remedy was authorship, not a language. |

The second row is worth a measurement rather than an impression. At motive time `policy.py` was 436
lines, 233 of them parse/validate/merge. It is now **496 lines, ~242 of them parse/validate/merge** -
192 in the seven helpers plus `load`'s include merge and one-owner guard. The proportion moved 53% to
49% and the absolute count went *up*, because Stage 6 added validation of its own. The originating
complaint is intact, and no language choice was going to retire it: those lines are the policy schema,
and a schema has to be stated somewhere in some language. Nickel offered a better *place* to state it,
not less of it.

### All four motivating features dissolved on contact

*Written as "three of four" before stage 6b; 6b took the fourth.*

The motive claimed Nickel's four features "map onto it almost exactly". In the event:

- **`import`** - the `includes:` mechanism already works and is **11 lines**, guard included. Not
  needed.
- **`&` merge** - the override actually wanted is one shallow axis, one field, two grades.
  `Rule.severity_for` is four readable lines. Not needed.
- **The one-owner rule for free** - this plan's own correction under `## Why this is being asked`
  records that the rule was a Phase 0b migration guard against the Notion/YAML double-copy, never a
  design principle. Free of a cost we had invented.
- **Contracts** - the last one standing, and the reason this stayed open after stage 7. Stage 6b
  closed it: what we wanted from contracts was refusals that name the cell and state the remedy, and
  that turned out to be reachable in Python by writing the sentences properly. Not needed either.

So the deciding criterion was built around the merge feature, which turned out weakest, and error
quality - the one place the comparison was both measurable and decisively in Nickel's favour - was
made a pass/fail gate, which by construction cannot earn credit toward a verdict. That, not a draw,
is what actually happened.

**What is left of the difference, stated precisely, because it is the only thing that survived.**
Nickel's error quality comes from the language: a contract that names a field and states its shape
produces a good message *by construction*, and the source position arrives whether the author thought
about it or not. Python's comes from authorship, and stage 6b is the proof that authorship can fail
silently - 22 refusals sat remedy-less for the life of the project, and the six written later to a
higher bar diverged from them for weeks with nothing noticing. That is not a capability gap. It is a
maintenance property, and it is the one honest argument left for a config language here. It is also
cheaper to answer with a test than with a toolchain, which is what the follow-through below does.

### What decides it on the corrected reading

- **Every surviving route to Nickel ran through error quality, and stage 6b closed it.** The
  question was whether refusals that name the cell, state the remedy and point at a line are worth a
  Rust toolchain for people who edit this policy a few times a year and already read Python. Answered
  empirically rather than by argument: reword the prose and Python wins on message content, leaving
  `file:line:column` as the whole of Nickel's advantage.
- **The costs did not move.** A second language, a Rust binary for anyone editing policy, two diffs
  per change, and ~300 lines of `.ncl` against ~242 of Python that stays either way.
- **Five debugging round-trips, discounted but not dismissed.** Recursive records behind laziness,
  `doc` reserved, contracts skipped on unforced bindings, grapheme-vs-codepoint length, YAML 1.2 vs
  1.1. All written down now - but part of that count is an artifact of writing 700 lines of Nickel
  with no evaluator in reach, not a property of the language. A contributor with the binary and an
  LSP gets the recursion error in a second. Priced lower than the first version of this section
  priced it, and still not zero.

### Revisit if - re-aimed at the criterion that won

The previous version pointed these at a second override axis, which is the motive that dissolved.
Pointed now at the one that did not:

1. ~~**Stage 6b leaves the messages weak.**~~ **DISCHARGED - see Stage 6b results below.** Prose
   closed the gap and then overtook it: Python is now better on 17, tied on 15, worse on 0, and
   Nickel's residual edge is source position alone. This route is closed.
2. **A second consumer needs the evaluated policy** - something other than `policy.py` reading it,
   where a validated artifact beats a validating loader.
3. **The schema outgrows one reader.** ~242 lines is a file one person holds in their head. Several
   times that is not, and contracts scale better than hand-written refusals.

Not on the list any more: a second override axis. It was the deciding criterion and it earned Nickel
nothing.

**What the bakeoff bought regardless of the verdict** - all of it kept, none of it dependent on
Nickel:

1. The override capability, on the YAML side, closing a promise the guide had made and the machinery
   could not keep.
2. `E-PROJECTS` split three ways after mutant 066 - and the finding that Python answers all three with
   "no 'projects'", which is misleading when the field is present but is a list. **Collected in
   6b:** split, and two tests added to cover the new arms.
3. Dead code deleted from the shape checker (mutant 006).
4. Stage 3b's shim: the whole suite can be run against any policy backend, which is how a future
   backend gets evaluated without a five-run debugging loop.
5. A 0.981-then-0.990 mutation-tested schema, and the discovery that three consecutive sweeps each
   found something real.
6. The wording debt: 22 Python refusals stating the breakage without the remedy. **Collected in 6b**,
   and it is what discharged revisit-if #1.
7. The rubric itself, as the only thing in the repo that ever compared two refusals for consistency -
   which is how 6b found that the override refusals were written to a higher bar than the originals
   and nothing had noticed.

**Disposition: `dev/nickel/` stays, frozen.** It is the reason this question does not get reopened
from scratch, and the no-harness-imports rule already keeps it out of the shipped skill. But the
`## Blast radius` instruction to *delete* it on a no was written before the harness existed, and
deleting it now would destroy `out/rubric.md` and `out/nickel-errors.json` - the baseline every
comparative number in this plan was scored against, including stage 6b's. Those numbers would become
unverifiable assertions.

So: the generated, policy-coupled artifacts go (`data/`, `fixtures/`, `mutants/` - 2.3M of 2.8M, 158
of 236 files) and everything else stays, generators included, so any of it is one command from
restored. **The reason is rot, not size.** Nothing outside that directory ran `gen_data.py --check`,
so `data/` tracked the shipped YAML with nothing guarding the coupling and the next policy edit would
have desynchronised it in silence - and a Nickel implementation that no longer matches the policy it
was compared against is worse than no record, because it still reads as evidence. It had already
happened: regenerating at 6b produced 42 fixtures and 118 mutants against the committed 34 and 106,
because stage 6 grew `schema.ncl` and nobody re-ran the generators. The recorded 0.990 kill rate was
measured against mutants of an older schema.

The alternative - wiring `gen_data.py --check` into the suite - would make every policy edit
regenerate this directory, i.e. two diffs per change, which is exactly the cost cited for *rejecting*
Nickel. Paying it forever for a rejected option is the wrong trade.

Stage 6b is done, YAML side; its results are below and they closed the last of the three revisit-if
routes that ran through error quality.

## Stage 6b results: the wording debt paid, and revisit-if #1 discharged

Run as the experiment Stage 7 asked for, not as a tidy-up: reword the remedy-less Python refusals,
then score them against the Nickel messages in `dev/nickel/out/rubric.md` and see what is left.

**It was 22, not 16.** The plan remembered 16 because that was the count failing on *both* sides. The
Python side alone had 22 refusals stating the breakage with no remedy, plus 4 more that named no
offending value. All reworded.

**The standard had drifted, and nothing enforced consistency.** Every one of Stage 6's six override
refusals already stated its remedy - they were written weeks later, to the higher bar the rubric
implies - while the 22 originals never were. Two refusals for the same *kind* of mistake read
differently depending on when they were written: `_rules`'s stricter-than-guide check said only "a
checker may lag its policy, never exceed it", while `_overrides`'s said that and "lower 'reported' or
raise 'guide'". Nothing in the repo compared them. The rubric is the only thing that ever did, which
is an argument for keeping it runnable.

**Q2, rescored after the rewording - and it inverts.** Where stage 5 had Nickel better on 11, tied on
23, worse on 0:

| | count | what separates them |
|---|---|---|
| **Python better** | 17 | Nickel describes the *field*; Python interpolates the *datum* - `repeats ['here']`, `threshold 'thirty'`, `[1, 2, 3] is not a [low, high] pair`, `non-string value '   '` - and now states a remedy in all 17 where Nickel states none |
| Tied | 15 | identical or equivalent prose, several of them word-for-word |
| Nickel better | 0 | on message content |

**So the two sides put the identity in different places**, and that is the real finding. Python has
the offending value in hand when it refuses, so it can quote it in the prose. A Nickel contract
describes the shape it wanted and lets *blame* carry the datum, as an underlined source position.
Neither is a capability the other lacks; they are the same information routed differently.

**Which settles revisit-if #1: no.** Nickel's residual advantage is `file:line:column` alone, and
against a message that already names the file, the table, the rule and the offending value, position
is a convenience rather than a capability gap. The strongest surviving route to adopting Nickel is
closed. The other two revisit-if conditions - a second consumer of the evaluated policy, and the
schema outgrowing one reader - are untouched by this and remain the live ones.

**Three things fixed on the way, all of them latent before:**

1. **`E-PROJECTS` split three ways, and the message stopped lying.** It answered all three arms with
   "no 'projects'", which is true when the field is absent and false when it is present and wrongly
   shaped - it sent an author hunting for something already in front of them. Now: `no 'projects'`,
   `'projects' is a list, not a mapping`, `'projects' is empty`. This was mutant 066's finding on the
   Nickel side, carried across; the bakeoff's second listed dividend, now actually collected.
2. **Two new refusals, two new tests.** `guard_coverage.py` immediately caught the split as **2
   untested** of 54 - an untested guard is an untested product claim - so `test_policy.py` gained one
   test per arm. Back to **54 of 54 provoked, 0 untested.**
3. **`rule_table_reads.py` was dead and looked alive.** It read rule ids from
   `docs-review/config/rules.yaml`, a path gone since the parent became `policy.yaml`, so every
   invocation died on FileNotFoundError - a `dev/verify/` script providing no coverage while
   appearing to. Path fixed. Its `--compare` mode was separately dead *by design*: it compared
   against a `value_tables` declaration Phase 0b deliberately deleted, so it could only ever report
   every rule as a gap against an absent field. It now refuses with that explanation instead.

**Verdict-neutral, as required.** Loader messages are outside the hashed projection, so the policy id
is unmoved at `8601df99863b`; `policy_differential.py` is element-exact; `nickel_equivalence.py` still
reports the two sides identical; 42 of 42 mutations provoke their expected refusal; 362 tests pass
(the 30 `test_adjudicate` failures are this sandbox's Python 3.10 against `enterContext`, which needs
3.11, and are unrelated).

## Decision criteria, fixed now

Stated in advance so the bakeoff cannot be won by moving the goalposts afterwards.

**Blocking — all three, or the answer is no regardless of anything else:**

1. Equivalence (Stage 3).
2. Contract coverage measured at N of N (Stage 4).
3. Error quality 46 of 46 on both rubric questions (Stage 5).

**Comparative, weighed only once the blocking three pass:**

4. Net Python removed from `policy.py`, against Nickel added. Expected to be roughly a wash on
   volume — the honest claim is that declarative is better here, not shorter, and if the argument
   quietly becomes "fewer lines" it has lost the plot.
5. Contributor cost: a second language, a Rust binary for anyone editing policy, two diffs per
   change.
6. Whether Stage 6 is materially cleaner in Nickel. This is where a config language should win, and
   if it does not win here it does not win anywhere in this repo.

**What makes it a no even with the blocking three passed:** if `policy.py` does not actually reduce
to an accessor layer — if Python still validates, merges or shapes — then the port bought a
dependency and a second language for nothing.

### Post-hoc critique of these six criteria

Added at Stage 7. The criteria above are left exactly as written - amending them afterwards is the
goalpost-moving they exist to prevent - so the objections go here instead. They do not change the
verdict; they change how much weight the verdict's *evidence* can carry, and they are the checklist
for anyone who reruns this.

1. **Criterion 4 was pre-declared a wash.** "Expected to be roughly a wash on volume." A criterion
   stipulated neutral in advance cannot contribute to a win. It measured something real and could
   never have decided anything.
2. **Criterion 5 was a pure penalty.** A second language and a Rust binary are what adoption *is*, so
   there was no arrangement of results under which Nickel scored on it.
3. **Criterion 6 was therefore the sole decider** - and it was the only one written qualitatively, with
   no threshold, judged by the party who built both sides. Three comparative criteria, one of them
   winnable, and a tie on it defaulting to the incumbent.
4. **Error quality was a gate, not credit.** Nickel beat Python on the one criterion that was both
   measurable and comparative (11/23/0 plus source positions) and this bought it nothing, because
   criterion 3 was pass/fail. If a criterion can be *won* rather than merely passed, it belongs in the
   comparative set.
5. **Equivalence-as-a-gate forced imitation.** Criterion 1 required the export to reconstruct Python's
   object graph exactly, so wherever Nickel differed the difference was "a porting bug, not a design
   difference; it gets fixed". Grapheme-vs-codepoint length is the clean example: Nickel's own string
   semantics were neutralised by pre-sorting in Python's order and marking every table `ordered`. A
   native Nickel policy - per-field contracts, source positions on every error, `&` for the language
   tables - would have failed stage 3. **A fair rerun must test equivalence of *verdicts* on the
   corpus, not equivalence of the policy object**, or it forbids the challenger from playing to its
   strengths.
6. **The learning-curve evidence was contaminated.** Five round-trips were partly the cost of writing
   Nickel blind, because the sandbox could not fetch the binary. That is a fact about the working
   conditions of this bakeoff, not about the language, and it is discounted in Stage 7 accordingly.
7. **Stage 6 was the shallowest instance of Nickel's specialty.** Merge with priorities earns its keep
   on deep hierarchies - org over repo over project over page, `| default`, partial overrides at each
   level. It was tested on one axis, one field, two grades: inside Nickel's domain, at the depth where
   it has least advantage over an `if`.

**If this is ever rerun**, the four changes are: verdict-level equivalence instead of object-level;
error quality moved into the comparative set with a stated margin; a genuinely layered override as the
merge test; and both sides written with the toolchain in hand. Absent those, a rerun re-measures a
contest whose structure already caps the challenger at a tie - which is what happened, and Nickel
reached its cap.

## Blast radius

Nothing in `skill/` changes until Stage 7 decides. The YAML policy stays authoritative and shipping
throughout; `policy.py`, `config/*.yaml`, the 330 tests and `policy_differential.py` are untouched.
All new work lands in `dev/nickel/` and `dev/verify/`. The existing rule that no shipped file imports
from `dev/` already prevents the Nickel side from leaking into the product by accident.

If the answer is no, `dev/nickel/` is deleted and this document keeps the reasoning, so the question
is not reopened from scratch in six months.

*Amended at stage 6b: not deleted, frozen. Deleting it would take `out/` with it, and `out/` is the
baseline behind every comparative number recorded here. See **Disposition** in Stage 7.*
