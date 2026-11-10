# Docs review skill — phased build plan

Companion to `PLAN-subskills.md` (what the four subskills are) and `PLAN-content-patterns.md` (what was
measured). This file is the order of work: what each phase produces, what has to be true before it starts,
and what has to be true before it is called done.

`PLAN-nickel-bakeoff.md` is a separate, parallel question: whether the policy Phase 0c moved into
hand-authored YAML is better expressed in Nickel with `policy.py` reduced to an accessor layer. It
does not block or alter any phase here — both implementations stay live until it decides, and the
YAML path is the one that ships meanwhile. It also inherits one item this plan should carry: the
index page promises "where an overlay contradicts base style, the overlay wins for that project", and
no policy model here can express that. Nothing exercises it today; whichever side wins closes it.

## Blast radius

Unchanged from the other plans. No PR to any docs repo, nothing published to ReadMe, no monorepo change,
no commits or branches in the source checkouts. Everything is written under `/home/ubuntu/docs-style`.
Live HTTP is limited to GETs on the public docs site plus sandbox requests against one approved org.
Phase 0 is the only phase whose output lands outside this workspace, and it lands in Notion, not in code.

## Product / harness line

Every phase below produces artifacts on exactly one side of this line. A phase that cannot say which side
its output is on is not specified yet.

| Ships in the skill | Never ships (dev/, harness) |
|---|---|
| `SKILL.md` per subskill | corpus snapshots and manifest |
| `scripts/*.py` checkers | probes, oracles, differential validators |
| `findings.py` | Hypothesis properties, mutation harness |
| `config.yaml` | fixtures, labeled sets, adjudication tooling |
| `config/rules.yaml` (compiled from Notion) | precision and base-rate measurements |
| `scripts/notion_sync.py` | the pinned-hash regression corpus |
| `style/*.md` local copies, `norms.json`, `blocks.json` | everything in `audit/` |

Enforced mechanically, not by intent: a test asserts no shipped file imports from `dev/`, and a test
asserts every shipped rule id appears in the provenance table with a measured base rate.

## The gate every rule passes (from §3 of PLAN-subskills)

Base rate on the head corpus; a firing and a non-firing witness by path; positive, negative and boundary
fixtures; mutation kill ≥0.950 with an identical survivor set on two consecutive runs and bytecode
disabled; independent second implementation for every factual claim; and ≥100 blind-adjudicated labels
for anything not decidable, at ≥0.95 precision for strict and ≥0.80 for moderate.

No phase below is complete while a rule it introduces is short of this. "Detected" is not "shipped".

---

## Phase 0 — Notion rule tables

**Why first.** Tables already disagree with the shipped code (`LAC` enforced by code and absent from the
guide; `first-heading-h1` in the guide reported as `body-h1` by 434 findings). Every later phase that
touches a table would otherwise deepen the drift.

**Correction to the earlier draft of this section.** It claimed a third drift case — `just` banned in the
guide, absent from `BANNED_FILLER`, 35 occurrences unreported. That was false, and the Phase 0 prosecutor
caught it: `stylecheck.py:1016-1018` carries a second `just` check outside the list, with an exemption for
`just as` / `just like` / `just in time`, and it fires 14 times on the ledgers repo alone. The claim came
from diffing the guide against `BANNED_FILLER` and stopping there. Acting on it would have been worse than
recording it: honouring `Active = false` on the `just` row would have *deleted* real findings. The row is
now active with the exemptions in an `Exceptions` column.

**Do.** Two Notion databases under the style-guide index rather than a table pasted onto each page — one
row per rule (`Docs Style Rules`: two severities, project scope, numeric threshold, which value tables it
reads, guide alias, provenance, note) and one row per value (`Docs Style Rule Values`: fifteen lists and
maps — object names, object shorthand, `MT`, filler words, the `please` exemption, `get` idioms, vague
anchors, fence languages, fence-language fixes, JSON fence tags, non-JSON fence prefixes, acronym
expansions, currency codes, callout emoji, per-project URL prefixes). Prose stays the human
explanation; the rows are the compilable projection of it. Reconcile the drift cases as part of this,
since the table forces a decision. Apply D7 here too: the base-style page's "write an excerpt" guidance
inverts to "excerpts are not used; remove them".

**Changed from the first draft, and why.** (a) *Databases, not inline tables per page.* Inline tables give
the sync one parser per page and no schema; a database has typed columns, so a malformed row is a Notion
validation error before the sync ever sees it, and the sync reads one shape instead of eight. The prose
pages keep their explanations and now name the rule ids the checker reports. (b) *An `Active` checkbox on
every rule and every value.* Without it, authoring is enforcement: adding a word to an active list changes
what the checker reports the moment someone types it, against a precision number measured on the old list.
`Active` unchecked means compiled but not enforced, which is what lets a policy decision be recorded in
the source of truth while its admission gate is still open. Every row is active today, so the mechanism
has no live instance — Phase 1 exercises it with synthetic rows in the guard tests, not by parking a real
rule in it. (c) *30 rules, not 29* — the earlier count was mine and was wrong; `RULES` has 30 entries.

**Drift resolutions, as recorded in the rows.** `just` — active, with `just (as|like|in time)` in
`Exceptions`, which is the code's own exemption made data. `LAC` — adopted, `Active` checked; the code has
enforced it since it shipped and the 14 occurrences on 2 pages are real, so the guide's list gains it.
`first-heading-h1` vs `body-h1` — resolved in favour of the rule id, because the id is what reports,
fixtures and labels carry; the prose adopts `body-h1` and the row keeps `first-heading-h1` as `Guide
alias`. `frontmatter-excerpt` — prose inverted per D7 now; the rule's behaviour inverts in Phase 4, and
the row says so, so the 515 findings read as a cleanup inventory rather than a gate condition.

**Two grades per rule, not one.** The prose already carried a distinction a single column cannot hold:
"Sentences stay under about 30 words — **Strict** (`sentence-length` is reported as flexible, judged in
review)", same for `passive-voice`, `acronym-undefined` and `link-absolute-internal`. So a rule has a
`Guide severity` (what a reviewer applies) and a `Reported severity` (what a run prints, capped by the
rule's measured precision). Without the split the sync would have dropped the distinction the prose
depends on, and the admission gate would have had nothing to raise a rule *into*. The index page's label
table now also defines `Moderate`, which the gate needs and the guide had never named.

`Moderate` is defined and unused: all 30 rows are strict or flexible, because a rule earns the middle
grade from a measured precision and there are no labels yet. That is the right emptiness — Phase 3 is what
fills it, and a grade assigned before the measurement would be the guess the two-severity split exists to
avoid. The sync accepts it today so no schema change is needed when the first rule qualifies.

**D7 is a policy change now and a behaviour change in Phase 4.** Inverting the prose without the code left
a page written exactly as the guide instructs failing `frontmatter-excerpt`. The prose now states the
policy *and* says the checker still reports the superseded sense, so a writer is not asked to trust a
verdict the guide disowns. Inverting it in Phase 2 is not an option — Phase 2's exit is a byte-identical
report, which is the only proof that re-homing 30 rules changed no verdict — so the inversion stays in
Phase 4 and is its first item.

Inverting it on the base-style page alone was not enough, which the Phase 1 prosecution caught: the
API-reference overlay still required an excerpt on every reference page and the review-and-correction
table still listed "excerpt missing" as a correction to make. A policy that reverses has to be chased
through every page that restates it, so D7 is three page edits, not one — and it is the case that argues
hardest for compiling the tables, since a value in one row cannot contradict itself in three places.

**Un-tabled policy, now tabled.** The prosecutor found policy the checker decides that lived only in code:
the `just` exemptions, the `filler-please` "contact" exemption, the `get` idiom list, the JSON fence tags,
and the command prefixes that decide which fences the JSON rules even look at (a strict rule gated by an
untracked list). Those are five new value tables. Left in code deliberately, and now said so on the rows:
the Unicode emoji ranges, English morphology (participles, contractions, abbreviations), and ReadMe's own
callout themes map — mechanism mirroring an external artifact, not a Modern Treasury decision.

**Known deferred — closed 2026-09-03.** The shipped `style/*.md` copies were stale against these Notion
edits until Phase 1's sync refreshed them. That made the refresh Phase 1's first real acceptance test
rather than a claim: the sync's output had to contain the four edited sections, or it did not work. Two of
the D7 edits — the API-reference overlay and the review table — were live in Notion but not in the local
snapshot, because the shared Notion credential expired between making them and re-capturing.

Both are now captured, and the re-capture corrected a mistake the deferral had hidden. The local copies
did not merely lack those two edits; `patch_phase4.py` had written *different* wording into the same two
sections, so the snapshot asserted prose Notion never carried. Notion's own words won, which is the whole
point of the arrangement, and the shipped copies now read `### **No **`excerpt`** — Flexible**` on the
overlay and "`excerpt` present in frontmatter → Delete it — we do not use excerpts" in the review table.
The lesson is narrower than "re-capture sooner": a local stand-in for a Notion edit should hold Notion's
text or refuse to guess, because a plausible paraphrase is indistinguishable from a capture once it is in
the file.

**Built.** `Docs Style Rules` (30 rows, two severity columns, scope, threshold, provenance)
https://app.notion.com/p/c3d7ff559aea4a2b9c2f5fc504ac7a9e and `Docs Style Rule Values` (109 rows across 15
tables) https://app.notion.com/p/400c96361a4240d8b60827c1b32f3044, both children of the style-guide index,
which now carries a section on how to edit them and what the two grades mean. Base-style prose edited for
the drift resolutions and D7. `SKILL.md` corrected: it said the code was authoritative on drift, which
contradicts the whole arrangement. Prosecution report: `audit/PROSECUTION-phase0.md`.

**Exit.** Every table-driven rule has rows, verified by an element-by-element diff against the constants
rather than by eye; each of the 30 rules has both severities, a scope and a provenance; each drift case is
resolved in one direction with the decision recorded on the row itself; every value the checker treats as
policy is either a row or a row-documented mechanism exemption.

**Side.** Notion (neither product nor harness — it is the source).

## Phase 0b — one owner per table

**Why it exists.** Phase 0 wrote down the test for what belongs in Notion — "mechanism mirroring an
external artifact, not a Modern Treasury decision" — and then did not apply it to five tables. The
result was 64 rows of English grammar and file-format mechanics sitting in a database, maintained by
hand, for no reader. `non_agent_by` alone is 39 of them, 26% of the value table, and Phase 4 did not
choose that list: it derived it from where `agent_span()` disagreed with spaCy across the frozen
corpus. Editing it is re-running a measurement, not making a decision.

**What the miss cost.** Nothing yet, which is the point of fixing it now. The exposure was that a
Notion edit to a grammar list changes what a strict rule reports, against a precision measured on the
old list, with no review step between typing and enforcement. `Active` guards a new row; it does not
guard an edit to an existing one.

**Do.** Each of the sixteen value tables gets exactly one owner. Notion keeps what a human might
change; `skill/docs-review/config/invariants.yaml` takes `non_agent_by`, `get_idioms`,
`non_json_fence_prefixes`, `fence_language_fixes` and `json_fence_languages`. Both compile into the
same `config/rules.yaml`, so no list becomes less visible: the artifact still holds all sixteen, its
hash still covers them, and every report still stamps it. What changes is where an edit goes — a
reviewed diff instead of a database cell. Each table in the file carries a `why`, and the sync
refuses one that does not, so a list living there has to argue that it is not an MT decision.

**Two classifications from the first pass did not survive checking, and the correction is the useful
part.** `fence_languages` looked derivable from ReadMe's supported set; its own provenance row says
"Modern Treasury policy: prefer the tags the guide lists", so 16 of ReadMe's hundreds is an allowlist
and stays in Notion. `currency_codes` looked like ISO 4217; it is a hand-picked 14 that no build note
justifies, and it is interpolated into `ISO_AMOUNT_RE`, so widening it to the standard would change
what the rule matches. It stays in Notion and is flagged as the one list here with no measurement
behind it. That leaves `object_names` as the only genuinely derivable table, and it is deferred
below rather than claimed.

**Exit.** The compiled policy is byte-identical across the move and `content_hash` does not shift —
provenance lives in `source`, which the hash does not cover, so re-homing a table cannot change a
verdict. That is asserted by a test, not by eye
(`test_moving_a_table_between_sources_does_not_move_the_policy_hash`). A table present in both
sources is refused; `--migrating` tolerates the duplicate only while the two agree exactly and names
the rows to delete, because a migration that silently prefers one source is how two sources of truth
start. Guard coverage 53 of 53, up from 42. `artifact_differential.py` reads both sources, so the
second-implementation property still covers every table.

**Migration closed 2026-09-03.** The 64 rows were deleted from Notion by hand — this MCP bundle has no
page-delete tool, so it was a filtered multi-select in the UI. Notion now holds 84 value rows across
the 11 tables it owns, the plain sync runs with no flag, and the policy hash did not move
(`718466089eff`), which is what proves the file had been deciding those tables all along. The
transitional scaffolding went with it: `--migrating`, its `_check_superseded` helper, the fixture that
pruned the duplicated rows, and `extract_invariants.py`, which cannot run again because its input no
longer exists. Guard coverage 51 of 51.

**Not done, and honestly open.** `object_names` (14 rows) should be derived from `swagger.yaml` minus the six names
the guide deliberately leaves unchecked as ordinary English — which would mean a new MT object gets
capitalization enforcement without anyone remembering to add a row. That needs the monorepo, which
only `docs-test` reaches today; deriving it at sync time rather than check time keeps the checker's
dependencies where they are. Not built.

**Side.** Product (the sync's second source, the invariants file), harness (ownership and migration
tests, the extractor, the differential's second reader).

### 0b.1 — the hash covers decisions, not prose

**The blocker this removes.** Every attempt to clear dead metadata out of Notion hit the same wall:
`content_hash` covered the whole compiled rule, including `note`, `guide_alias` and `value_tables` —
three fields no verdict reads. So correcting a typo in a note was indistinguishable from changing a
severity: both re-opened the admission gate for all thirty rules and stale-marked every stored report
stamp. The cleanup cost more than the mess, every time, which is how the mess had lasted.

**Do.** `content_hash` covers `DECISIVE` only — reported severity, guide severity, scope, threshold —
plus the values and exemptions. Provenance stays in the artifact and out of the hash: `--list-rules`
prints it, nothing decides on it. `guide_alias` and `value_tables` leave the artifact and Notion
entirely.

**Why those two go rather than shrink.** `guide_alias` held one value (`body-h1` → `first-heading-h1`)
that nothing read; Phase 0 had already settled that drift by rewriting the prose, so it recorded
history with no reader. `value_tables` was worse than unused — it was 14 hand-kept cells guarded by a
check that could not fail. `policy.require()` verified that every *declared* table exists, which
`compile_rules` already refuses at sync time; nothing verified that the tables a rule actually reads
were declared, which is the error the column looks like it prevents.

**The reverse check was attempted and does not work.** `dev/verify/rule_table_reads.py` derives
rule → tables statically from `lint.py` and is kept as the record of why. It still reports six gaps,
four plainly spurious — it claims `sentence-length` and `contractions` read `non_agent_by`, and
`fence-untagged` reads the fence tables. The cause is structural: the checker bundles several rules
per function and shares module constants, so function-level attribution cannot separate them. Doing
it properly needs either restructuring `lint.py` so each rule's reads are locally scoped, or a
dynamic experiment on the corpus — perturb a table, see whose findings move. Two bugs found while
building it are recorded in its docstring, because both produced confident wrong answers: a rule-id
filter that required a hyphen silently dropped `filler`, and folding rules up the call graph gave
`check_page` every rule and every table, printing a uniform, useless mapping that looked plausible.

**Exit.** Every decisive field, every value and every exemption is byte-identical across the change;
only the three documentation fields left the artifact and only the stamp moved
(`4e394b9f453a` → `718466089eff`). Eight tests pin the property in both directions: editing
provenance does not move the hash, and changing a reported severity, a guide severity, a threshold, a
scope or a value does. The recomputed-from-the-file hash uses the same projection as the sync, or
every freshly written artifact would report itself tampered. Proof that it worked: dropping two
columns from Notion and clearing 14 note cells immediately afterwards moved nothing — `policy
unchanged`.

**What this cost, stated plainly.** One deliberate gate re-run. No verdict changed, so the re-run is
satisfied by the unchanged corpus behaviour rather than by re-measuring, but any report stamped
`4e394b9f453a` now names a policy hash that no longer exists. That is the one-time price of making
every future documentation edit free.

**Side.** Product (the hash projection, the dropped fields), harness (the eight hash tests, the
static analyser kept as a record of a rejected approach).

## Phase 0c — policy is authored, not compiled

**What this ends.** Notion is out of the loop. Phase 0b split the tables by owner and 0b.1 narrowed
the hash so documentation could move without a gate re-run; both were repairs to a bridge whose cost
this phase removes instead. The style guide prose moves into `skill/docs-review/style/` as the source
of truth, and the policy into YAML beside the checkers that read it.

**The shape.** One parent, one file per subskill:

| File | Holds |
|---|---|
| `docs-review/config/policy.yaml` | severities, the four projects and their URL prefixes, and the Modern Treasury domain tables: object names and shorthand, `MT`, acronym expansions, currency codes |
| `docs-lint/config/rules.yaml` | 30 rules, and the ten tables only lint reads — filler words, vague anchors, fence tags, callout emoji, the grammar lists behind `passive-voice` |
| `docs-{content,maintain,test}/config/rules.yaml` | stubs; those subskills emit nothing until Phases 5-7 |

The split is by ownership, not by who reads a table today. `object_names` is a fact about the product
that `docs-content` will want as much as `docs-lint`; `filler_words` is how one checker decides one
rule. A table defined in both files is a refusal, and so is one rule id claimed by two subskills —
a guard that could not exist while every rule lived in one compiled artifact.

**What went, and why it was safe to lose.** Roughly 2,200 lines: `notion_sync.py` (832),
`test_notion_sync.py` (1,057) and `artifact_differential.py`. Most of that existed because a database
cell is untrustworthy input — it can carry rich text, invisible characters, a row added minutes ago,
or a list that lost half its entries in a bad fetch. So the snapshot loader, `--stale`, `--check`,
tamper detection, shrink guards, the `Active` gate, the markup and invisible-character guards and the
`<delete>` sentinel were all guarding the seam rather than the policy. A reviewed file needs none of
them: delete a rule instead of deactivating it, write `""` instead of a sentinel, and put an
exemption beside the value it exempts. What replaced them is 1,013 lines across the loader, its
tests and the differential.

**What was kept, deliberately.** The policy id and the report stamp: a run happens against a working
tree, which may carry an uncommitted edit, so a git SHA would describe the wrong thing. It is
recomputed from the files every run and never quoted from one, which is what the sync's tamper
detection used to buy and now comes free. The second-implementation property is kept too —
`dev/verify/policy_differential.py` reads the YAML with its own parser and pulls the checker's
assembled regexes back apart, because a table can load intact and still be lost when a pattern is
built from it.

**Exit.** The merged policy reproduces the last compiled artifact exactly: all 16 tables, both
exemption sets, every severity, scope, threshold and provenance identical, verified field by field
before the bridge was deleted. 307 tests pass, the differential is element-exact, guard coverage is
35 of 35 (every refusal in the loader is provoked by a test), and all five entry points run. The
policy id changed, because it is computed differently — that is the one visible break, and it is the
same one-time cost 0b.1 paid.

**Side.** Product (the policy files, the loader, the per-subskill split), harness (the loader's
tests, the differential's second reader, the guard tracer repointed).

### 0c.1 — the rest of the data out of the checker

**Do.** `docs-lint/config/language.yaml`, included by `rules.yaml`, takes the facts about English,
Unicode and ReadMe's renderer that were sitting in `lint.py`: 180 irregular participles, the
abbreviations the sentence splitter needs, the closed adverb and contraction-host classes, rdmd's
callout emoji and their roles, and ~900 lines' worth of Unicode codepoint ranges. Finding messages
move too — one `message:` per rule, `messages:` for the one rule that says two things.

**Where the line got drawn, and why it is not "everything".** Two things stayed in `lint.py`
deliberately:

*The 26 compiled regexes.* A regex in YAML is code in a string: escaping doubles up, a malformed one
fails on a real run rather than at parse, and it cannot carry the comment that makes it right. The
block above `BE_PASSIVE_RE` explains that `'ve` and `'ll` are excluded because they are *have* and
*will*, which take an active perfect or future. That comment is the reason the rule is correct and
YAML has nowhere to put it. The seam is: the word list is data, the pattern assembled from it is code.

*The `fix` strings.* A fix is not prose but a transformation of the page's own text — `re.sub` over a
heading, a slice of the object name, `url.replace("&", "?", 1)`. A template language able to express
those would be a worse programming language than the one already here.

**Two schema additions, each forced by real data.** `ranges:` beside `map:` and `values:`, because
Unicode tables are pairs of integers and writing 900 codepoints as strings to fit an existing shape
would be worse than adding one; a backwards pair is refused, since `[0x1f6cf, 0x1f6cb]` parses fine
and matches nothing, which is a check that silently stops firing. And `ordered: true`, which opts a
table out of longest-first sorting — found by a regression, not by design: sorting is what a matcher
needs, and applying it to `callout_roles` silently reordered a suggestion into "tip, information,
limitation" against the guide's own sequence.

**The risk this took on, and the guard that pays for it.** Templated messages fail at render time on
a field the checker did not pass, which without a guard means a broken message reaching a reader
mid-run. `dev/tests/test_lint.py::EveryMessageIsRendered` runs the rest of the file with `Finding`
instrumented and asserts all 30 rules were rendered — measured, not assumed, and it fails if a rule
ever loses its fixture.

**Exit.** `lint.py` 1,201 → 1,129 lines and carries no word list, no codepoint table and no message
text. 330 tests pass, the differential is element-exact, guard coverage 46 of 46. A page exercising
16 rules produces byte-identical findings, templated messages included.

**Side.** Product (`language.yaml`, the messages, the two schema shapes), harness (the render guard,
the range and message tests).

## Phase 1 — the sync and the artifact

**Entry.** Phase 0 exit.

**Do.** `scripts/notion_sync.py` (ships, run on demand, never at check time) compiles `config/rules.yaml`
plus refreshed `style/*.md` from a Notion snapshot, validating every row as it reads it. The artifact
records `synced_at`, `snapshot_fetched_at`, each page's Notion `last_edited_at`, and a content hash.
Guards: fail on a missing or malformed table rather than falling back to parsing prose; fail on an empty
list; fail when a list shrinks by more than a third without `--force`.

**Where the snapshot comes from, and why the script does not fetch it.** Notion is reachable through an
MCP client the script cannot call: MCP tools run in the agent's harness, not in a subprocess on a
contributor's machine. So the snapshot — the two databases' rows plus the eight style pages, with their
edit times — is captured out of band into one JSON file and handed to `--snapshot`. That is a real
limitation, not a design flourish: a contributor with only the shipped tree can run the checker and read
the stamp, but re-syncing requires an agent (or any Notion client) to capture a snapshot first, and
`--check`/`--stale` need one to compare against. It buys the property the checkers depend on, which is
that compiling a policy is a pure function of a file. The validation is imperative row-by-row rather than
a declarative schema document, because the refusals have to name the cell and say what to type instead;
a schema validator's message is a JSON path.

**Conventions the sync needs, from the Phase 0 prosecution.** An empty `Maps to` means "no replacement";
the literal `<delete>` means "replacement is the empty string" — without that distinction
`FILLER_REPLACEMENTS` cannot round-trip, since `note that`'s replacement *is* empty. `Exceptions` columns
compile to the rule's exemption pattern, not to another banned value. `object_shorthand` carries its object
name in `Note`, not `Maps to`, because the checker never substitutes it — a map column there would compile
into a dict the code has no use for. Notion stores rich text, so inline code formatting in `Provenance`
does not survive the round trip; the artifact holds the plain form and the differ compares plain forms.

**Do not.** Let any checker read Notion at run time. A verdict behind a network call cannot be
mutation-tested, the harness cannot pin the inputs a precision number was measured against, and two runs
on the same commit can disagree.

**What Phase 1 does not do.** The artifact is compiled and stamped, not consumed: the checker still
decides with its own constants and reads `config/rules.yaml` only to name the policy a report ran under.
Editing a value in the artifact therefore changes the stamp and no finding. Phase 2 is what makes a
verdict artifact-backed, and until it lands the differential below is the only thing keeping the two in
agreement. The shipped artifact header and `SKILL.md` say this in the same words, so nobody reads the
file as authoritative before it is.

**Exit.** The compiled artifact reproduces today's constants exactly, element by element — all three
drift cases were resolved *toward the code*, with the reason recorded on the row (`just` is checked by its
own rule rather than the filler sweep, `LAC` is real and the guide was short a row, `body-h1` keeps its
reported name and the guide's `first-heading-h1` becomes an alias), so Phase 1 changes no verdict at all
and the byte-identical acceptance in Phase 2 has nothing to except. Every artifact field is either
compared against the code or carries a
declared invariant in its place (`dev/verify/artifact_differential.py`, and a field in neither set fails
it); the three tables the checker holds as inline literals are parsed out of its source rather than typed
into the differ; a corpus run still reproduces 5,038 findings exactly (2,201 strict, 2,837 flexible over
682 pages) — in Phase 1 that is a no-change check, not a drift check, because the checker does not read
the artifact yet, so "the corpus differs only by the intentional fixes" is a Phase 2 exit and is stated
there; every refusal in the sync is provoked by a test, proved by tracing the suite rather than counted by hand
(`dev/verify/guard_coverage.py`: 42 of 42); re-syncing the same snapshot rewrites no byte, and re-syncing
a freshly captured snapshot of unchanged policy rewrites only `snapshot_fetched_at` — the capture time is
the one field that is about the fetch rather than about the policy, and `synced_at`, both hashes and every
report stamp are unmoved; the refreshed `style/*.md` carry the Phase 0 prose edits.

**The artifact verifies itself.** A hash read out of the file it describes proves nothing: change a
severity, leave `content_hash:` alone, and every comparison agrees with itself while reports name a policy
the file no longer contains. So both hashes are recomputed from the artifact's own body before use —
`--check` and `--stale` refuse a file whose hashes do not describe it, a report stamp says `EDITED BY HAND`
rather than quoting the stale hash, and a sync repairs it but says on stderr that it did.

The same hole exists one level out, and `style_hash` cannot close it: it hashes the Notion pages, not the
files on disk, so a `style/*.md` copy edited in place leaves every hash agreeing while a reviewer reads a
guide nobody approved — and the guide is what a human applies when the checker has no rule. So `--check`
re-renders each copy from the snapshot and compares it, reporting an edited or deleted copy by name.

**Staleness, and why the revision is a content hash.** Notion exposes no row-level edit time through the
client (its formula language rejected every `lastEditedTime()` form tried), so the artifact's revision is
the hash of the policy it compiled — reproducible, and enough to answer "is this the artifact that
produced that report?". Page edit times *are* exposed, so the artifact records one per style page and
`notion_sync.py --stale` answers "has Notion moved since this was compiled?" against a fresh snapshot
without recompiling. A row edited without any page being touched is still invisible; a re-sync is what
detects it, and the hash is what proves it.

**Side.** Product (sync + artifact), harness (guard tests, guard-coverage tracer, the differ that compares
artifact to constants).

## Phase 2 — the split, no new rules

**Entry.** Phase 1 exit.

**Do.** Extract `findings.py`; move today's `stylecheck.py` to `docs-lint/scripts/lint.py` reading the
artifact instead of module constants; create `docs-review` umbrella with `--only <subskill>` selection and
all-four default; create the three empty subskills with their `SKILL.md`. Print the artifact hash in every
report and in `--list-rules`.

**Exit.** Byte-identical JSON report on the head corpus before and after the split — "byte-identical"
with the provenance stamp masked, since `synced_at` and the run's own duration are wall-clock fields that
cannot be equal across two runs and prove nothing about a verdict; the stamp is compared separately and
exactly. Then: every fixture green;
differential clean against markdownlint / write-good / emoji-regex; mutation ≥0.950 with identical
survivor sets twice; the no-`dev`-import test passes.

**What the mutation number had to become, and why.** The exit criterion was written as "0.950 on 181
mutants" against a single-file checker. The split makes the count meaningless as a target: `findings.py`
and `policy.py` took 17 decision points out of the linter, so a checker-only run reports a *higher* rate
over a *smaller* surface — the one way this criterion could be met by deleting coverage. The criterion is
therefore the rate over every shipped module that decides something (`lint.py`, `findings.py`,
`policy.py`), whatever the count comes to, with each survivor classified against the corpus. Mutating the
three empty subskills adds nothing: they decide only whether the artifact loaded, which `policy.py`
already carries.

**What the no-`dev`-import test does and does not prove.** It walks each shipped file's AST and fails on
an import that resolves into `dev/`, which catches the mistake anyone actually makes — reaching for a
harness helper while writing a checker. It does not resist evasion: a path assembled at run time, or a
`__import__` of a computed name, passes it. Making it airtight means running each shipped script with
`dev/` removed from the tree, which Phase 2 does once as the acceptance run; the AST test is the cheap
version that runs every time.

**Side.** Product (all four packages), harness (the before/after report equality test).

## Phase 3 — adjudication infrastructure

**Entry.** Phase 2 exit. This is the gate on every phase after it, and it produces no shipped code, so it
will look like nothing is happening. It is the difference between a checker that has been run and one that
has been tested.

**Do.** Blind label sets: findings shuffled, rule ids and severities stripped, stable content hashes so a
label survives a re-run, sampled across all three repos, with per-rule and per-severity precision computed
from the returned labels. Reviewer disagreement with my labels is the most useful signal available, so the
tooling must accept labels from more than one adjudicator and report where they diverge.

**Exit.** ≥100 labels returned for `passive-voice`; precision computed per rule and per severity; the
disagreement rate between adjudicators reported.

**Side.** Harness only.

**What the prosecution changed.** Two things, both about what a label is worth rather than how many
there are.

*Precision is reported per adjudicator, never pooled.* The first run pooled them and printed 0.79 for
`passive-voice` — the average of 0.62 and 0.96, describing a corpus neither adjudicator saw. Where two
adjudicators overlap, the run now prints the two bounds their disagreement admits (the rate over items
they agreed on, and the rate with every split item counted against the rule) because a single number
is a decision about the disputed items dressed as a measurement.

*The second adjudicator is a dependency parser, and it decides a different question than I do.* A
second pass by the model that wrote the rule is not independent, so the second adjudicator is spaCy's
parse deciding "is this an agentless passive" (`nsubjpass`/`auxpass` with no `agent` child). It cannot
decide "should this be rewritten", which means the disagreement between us is not noise: it separates
detection from actionability. On the 120-item set that separation is the whole result — 120/120 of the
reported lines are passive by the parse, 5 already name their agent, and 75 of the remaining 115 are
worth changing. So `passive-voice` has a detection precision of 0.96 [0.91, 0.98] and an actionability
floor of 0.62 [0.54, 0.71], and Phase 4 grades it on the floor. The 0.96 is deterministic; the 0.62 is
my inference until a writer labels the same set, which the harness scores as a third label file with
no code change.

Two defects in the harness itself, recorded rather than fixed: controls drawn from silent pages cannot
distinguish a generous adjudicator from a checker miss (5 of 20 contain agentless passives the checker
never reported, which is a recall result mis-filed as a control alarm), and drawing controls only from
lines the parser also calls clean is the fix. Phase 4 also inherits a measured rule change: the
exemption the rule's own message states ("unless it is the bank") is described but not enforced, and an
`agent`-dependency check removes those 5 findings deterministically.

## Phase 4 — settle the two lint rules that fail gate 1

**Entry.** Phase 3 exit.

**Do.** Grade `passive-voice` on its measured precision — now measured: detection 0.96 [0.91, 0.98] by an
independent parse, actionability floor 0.62 [0.54, 0.71], so it stays advisory and narrows rather than being
promoted. Narrowing has a deterministic part the labels identified: enforce the exemption the message already
states by dropping passives that name their agent (5 of 120 sampled findings), which raises precision without
any judgement call. Invert `frontmatter-excerpt` per D7 and emit the removal inventory as a one-time
list, not a gate condition — 167 pages, not the 515 the pre-inversion rule reported: the old finding was a
*missing* excerpt on almost every page, and the inverted one is a *present* excerpt on the minority that
carry it, which is the whole point of the inversion.

**Exit.** Both rules have a measured precision and a grade justified by it; the base-style page and the
rule table agree with the shipped behaviour. Four exit criteria were added by the build and its
prosecution, because the obvious way to check either change is biased:

- **Every individual finding change is attributed**, not just the totals. Corpus counts can net out —
  a rule that stopped firing where it should and started firing where it should not shows the expected
  delta. `dev/acceptance/phase4_delta.py` maps all 795 changes (5,038 → 4,601) to one of four named
  causes and fails on one unattributed row.
- **A finding's identity includes the columns it underlines, and a cause is judged per construction.**
  Added by the Phase 4 prosecution, which found the attribution silently incomplete: the first version
  keyed on a `span` field the findings format does not have (the columns are `col`/`end_col`), so 12
  changes cancelled against their own predecessors and the run reported success over a set it never
  examined. Suppressing a sentence's first passive can expose a second one that names nobody — same
  page, line, rule, message and evidence, different caret — so the caret is identity, and asking
  "is the *sentence* clean now?" wrongly refuses those legitimate suppressions. The cause functions ask
  `agent_span` about the construction the finding reported. Phase 7 inherits both requirements, being
  the next phase that changes verdicts on purpose.
- **The harness's own decisions carry fixtures** (`dev/tests/test_phase4_delta.py`). The checker fails
  loudly, as findings; an acceptance script fails silently, as green.
- **The agent detector is scored against the pre-change report**, never the shipped output. Once
  suppression ships the checker no longer reports what it suppressed, so the post-change output is the
  sample the change created. `--baseline` is the unbiased set of 1,874 passives.

**Result.** 616 findings removed and 179 added: 515 excerpt-absent retired, 167 excerpt-present raised,
101 passives suppressed for naming their actor, 12 passive carets moved within their sentence.
`passive-voice` 1,874 → 1,785, `frontmatter-excerpt` 515 → 167, no other rule's count moved. The 101 is
corroborated by the differential, which counts 90 + 11 named agents in the pre-change set without
reading the delta. `agent_span()` vs spaCy's `agent` dependency: 0.9787 agreement, 11 regex-only and 29
parser-only, each printed with its sentence; agreement varies only 0.9765–0.9797 across windows of 24 to
240 characters, so the threshold is not load-bearing. The 29 parser-only cases are residual false
positives by the rule's own message (1.6% of what still fires); they stay because the alternative is a
parser dependency in a shipped checker, and they are the first narrowing if the rule is ever promoted
above `flexible`. Mutation 0.959 over 221 mutants with no survivor in the new logic.

**Notion debt — paid 2026-09-03.** The `non_agent_by` table and the two changed gradings were written
into the local snapshot by `dev/notion/patch_phase4.py`, so `artifact_differential.py` proved the artifact
matched the snapshot — not that the snapshot matched Notion, and no Phase 4 claim could be read as "Notion
says so". The replay has now happened: `non_agent_by` is a 16th option on the Values `Table` property
carrying all 39 rows Active, and both rules hold their Phase 4 gradings, provenance and notes in Notion.

What makes the claim checkable rather than asserted is that the replay was verified in the direction that
can fail. Every compiled field of all 30 rule rows and all 148 value rows was read back out of Notion and
compared element by element against the snapshot (`dev/notion/capture/rules_fp.py`, `values_fp.py`): both
MATCH, so the artifact differential's subject and Notion are now the same object. The compiled policy hash
did not move (`4e394b9f453a`), which is the expected result and worth stating: the rows were already right
locally, so paying the debt changed the guide's provenance, not a single verdict. `patch_phase4.py` is
retired — `--check` still reads its rows as a regression test, and running it now refuses rather than
reverting the two pages Notion has since reworded.

**One thing this session could not verify.** The 4,601-finding corpus reproduction is not re-run here: the
frozen corpus lives at `/home/ubuntu/style-corpus-head`, outside this workspace. The claim rests on the
Phase 4 acceptance run, unchanged, and the unmoved policy hash is the reason that is sound — a sync that
compiles the same policy cannot move a finding. `dev/tests/test_adjudicate.py` also fails here on
`enterContext`, which is Python 3.11+ and the sandbox is 3.10.12; the other 376 tests pass, and
`guard_coverage.py` still traces 42 of 42 refusals once that one file is excluded.

**Side.** Product (both rule changes), harness (the labels behind them, the delta attribution, the
differential, the inventory).

## Phase 5 — `docs-maintain`, incremental mode

**Entry.** Phase 2 exit (does not wait on Phase 3 — both rules here are decidable).

**Do.** `blocks.json` inventory per repo (defined, referenced, orphaned). Then `reuse-undefined-block`
(strict: `EarlyAccess` ×8 in platform, `SandboxDetails` ×1 in ledgers) and `example-identity-collision`
(strict for `us_ssn`, which the sandbox proves 422s a reader; advisory for `us_ein` until the enforcement
asymmetry is answered by engineering). Then near-miss block names as moderate (`BYOBDislcaimer` vs the
`BYOBDisclaimer2` that 8 pages use). Incremental mode answers "does this content already exist" for the
pages in a change; exact-match needs no threshold, which is why it ships before the sweep.

**Exit.** Three rules through the full gate; the blocks inventory regenerates deterministically; the
incremental mode runs on a changed-page set in seconds.

**Side.** Product (rules + inventory), harness (fixtures, mutation, the second block-graph implementation).

## Phase 6 — `docs-test`

**Entry.** Phase 2 exit, plus the credential predicate from D9 in place before any request is issued
(`app.moderntreasury.com` only, key begins `test-`, `demo.` refused, abort on live mode, key never written
to a report).

**Do.** In value order, highest first:
1. **String fields the code constrains but the spec leaves open** — the class that caught
   `proof_of_addres`, which no schema check can reach because swagger types the field as a bare nullable
   string. Not built, and the highest-value unbuilt check in the plan.
2. Response-example validation against the schemas.
3. Typed differential made conclusive: placeholder syntax excluded, `minProperties` resolved, every
   finding adjudicated so the precision is measured rather than estimated (task #10).
4. Link resolution, live only — offline resolution measured 0.23 precision and stays killed.
5. Documented-request execution, with the attribution rule: a 4xx naming a missing org-level prerequisite
   is environment-dependent, not a docs defect.

Report "not verifiable in sandbox" as an outcome distinct from "verified" — Cases have no simulation path,
so a checker that silently skips what it cannot reach is worse than one that fails.

**Exit.** Each check has an independent second implementation agreeing on the corpus; the typed
differential's precision is a measured number; no execution finding is reported without attribution.

**Side.** Product (checks), harness (oracles, sandbox fixtures, the adjudicated differential findings).

## Phase 7 — `docs-content`

**Entry.** Phase 3 exit — this family has base rates and no thresholds, so it cannot ship above flexible
before adjudication exists.

**Do.** Truncation convention first: it is writable today (bare `...` line approved, `"..."` as a value
rejected, 0 of 76 request payloads omit a required field so no partial-example marker is needed). Then the
extractors, each behind Hypothesis properties before any rule reads their output — an extractor that
over-collapses makes everything look conformant, which is what the endpoint-normalizer properties were
written to catch. Then continuity and coverage as moderate/flexible only.

**Exit.** Every rule has a threshold derived from the frozen corpus and a precision from Phase 3 labels;
`norms.json` is generated, committed, and never hand-edited.

**Side.** Product (rules + norms), harness (extractor properties, thresholds, labels).

## Phase 8 — `docs-maintain`, sweep mode

**Entry.** Phase 5 and Phase 3 exits.

**Do.** The corpus-wide duplication sweep, ranked by `(occurrences − 1) × length`: 261 exact repeated prose
groups, 121 near-duplicate pairs at Jaccard ≥0.6, wording drift where one claim appears in five places in
four wordings, repeated payloads, duplicate pages and `copy-of-*` slugs. Suggest a block boundary where one
is computable.

**Do not.** Decide blockify vs merge vs trim. The reusable-content proposal's own verdicts differ per group
(merge D, trim-then-blockify E1, adopt B despite trivial savings) because they turn on SEO, product intent
and editorial taste. The checker ranks and points; the human decides.

**Exit.** Sweep output reproduces the proposal's block candidates or explains each divergence; every rule
in it is moderate or flexible, none strict.

**Side.** Product (sweep), harness (thresholds, labels).

## Phase 9 — hand-off

**Do.** Take the skill to the Devin eng team for blessing (D6: on request, and optionally on push). Hand
engineering the two open questions (EIN/SSN uniqueness asymmetry; the simulation 422 that does not say the
org lacks a Flow connection) and the swagger publishability gate — 22 operations cannot be published
because dereferencing them does not serialize, which is a property of `swagger.yaml` and belongs in the
monorepo as a PR gate, not in a docs subskill.

---

## Ordering constraints, stated once

- Phase 0 → 1 → 2 is a hard chain. Nothing else starts before Phase 2.
- Phase 3 gates 4, 7, 8. Phases 5 and 6 do not need it (their rules are decidable).
- Phase 5 before 8: the inventory and the exact-match case are what the sweep's ranking is built on.
- A Notion table change at any point re-runs the gate for the affected rules only, and re-pins the hash.

## Effort

Roughly one session per phase, with three exceptions: Phase 2 is closer to two because the byte-identical
acceptance test will find real behaviour differences in the extraction; Phase 3 is two to three because
adjudication is slow and should not be rushed by me alone; Phase 6 is two because item 1 is a new check
class and item 3 is an open research task. Phase 0 is hours, not a session. The long poles are external:
adjudicator availability, engineering's answers, and the eng blessing in Phase 9.

## What is still not decided

- Who adjudicates besides me. Phase 3's value depends on it.
- Whether the Notion tables live on the existing pages or in a `Rule tables` database. Either compiles;
  the database is easier to validate, the inline tables are easier to keep next to their prose.
- Whether the incremental mode's changed-page set comes from `git diff` or is passed in.
