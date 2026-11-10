# Plan: split `docs-style-review` into four subskills

Status: plan only. Nothing in this document has been built.

## Blast radius: none

No PR to any docs repo, nothing published to ReadMe, no monorepo change, no commit or branch in any
source repo. All work lands under `/home/ubuntu/docs-style`. Sources stay read-only. Live HTTP is
limited to `GET` on the public docs site plus documented requests against a **sandbox** organization
with test-mode credentials. Fixes this work discovers are reported, never applied.

## Why four, and what the seam actually is

The four names line up with the four *dependency tiers*, which is why the split holds. Each tier is
the set of things a checker needs before it can decide anything, and each tier is a different
deployment story.

| Subskill | Needs | Verdict latency | Can run in a docs PR with no setup |
|---|---|---|---|
| `docs-lint` | the file | ms | yes |
| `docs-content` | the file + corpus norms | ms (norms precomputed) | yes, with a committed norms artifact |
| `docs-maintain` | all three docs repos at once | seconds | yes |
| `docs-test` | monorepo read + network + sandbox credentials | seconds to minutes | no |

Two corrections to the grouping as proposed:

1. **Schema conformance of a documented example is `docs-test`, not `docs-maintain`.** It needs the
   monorepo but not the network, and it answers "is this page true", which is the docs-test question.
   `docs-maintain` answers "is this page's *content* duplicated, stale, or better expressed as a
   link/reusable block".
2. **OpenAPI publishability is not a docs subskill at all.** The executed finding
   (`dev/readme_limit/verdict.json`) is that 22 operations cannot be published because dereferencing
   them does not serialize — a property of `platform/swagger/v1/swagger.yaml`. A docs-side checker sees
   the damage after it ships. That check belongs in the monorepo as a PR gate, and this plan carries it
   only as a spec to hand to engineering (§7).

## 1. Product vs harness, restated per subskill

Shipped, for every subskill: `SKILL.md`, `scripts/`, `style/`. Nothing else.

Not shipped, ever: the corpus, the probes, the property tests, the mutation harness, the differential
oracles, the adjudication labels, the sandbox execution scripts, and every measurement that justified a
rule. `docs-test` makes this line easy to blur — it is the one subskill whose shipped code touches the
network — so the rule is stated concretely: **the shipped `docs-test` executes only requests that
appear in the page under review, and it never writes a fixture, seeds an org, or freshens an
identifier.** Fixture generation is harness work. A shipped checker that invents a payload is no
longer verifying the docs.

Enforced mechanically (a test in the harness, not a convention): no shipped file imports from `dev/`,
and no shipped file reads a path outside the page set, the config file, and the artifacts the config
names.

## 2. Target layout

```
skill/
├── docs-review/                      # umbrella: routes a page set to the subskills, one report
│   ├── SKILL.md
│   ├── config.yaml                   # committed; sandbox org + key, monorepo path, artifact paths
│   └── scripts/
│       ├── findings.py               # Finding, severity, report/JSON emitters, per-rule config
│       └── review.py                 # runner: selects subskills by available dependencies
├── docs-lint/
│   ├── SKILL.md
│   ├── scripts/lint.py               # today's stylecheck.py, minus the report plumbing
│   └── style/{00-index,01-base-style,02-overlay-*,06-flexible-conventions,07-review}.md
├── docs-content/
│   ├── SKILL.md
│   ├── scripts/content.py
│   ├── norms.json                    # generated from the frozen corpus, committed, never hand-edited
│   └── style/…
├── docs-maintain/
│   ├── SKILL.md
│   ├── blocks.json                   # block inventory per repo; regenerated, read by the incremental mode
│   └── scripts/maintain.py
└── docs-test/
    ├── SKILL.md
    └── scripts/test.py
```

`findings.py` is the load-bearing piece. Four subskills that each print their own findings is four
tools; the requirement is one compiler log, so severity, rule ids, provenance strings, the caret
pointer, `--strict-only`, `--rule`, and the JSON shape live in one module that all four import.

Config, per your call, is a committed `config.yaml` rather than `.env`, holding the sandbox org id and
test key inline. `docs-test` refuses any host other than `app.moderntreasury.com` (explicitly including
`demo.moderntreasury.com`), refuses a key that does not start `test-`, and aborts on any response showing
live mode.

## 2.1 Notion as the source of truth for content and tables

The guide already lives in Notion and the skill already defers to it. This extends that pattern from
prose to the *data* the checkers read, so that changing a rule's word list, threshold or severity is a
Notion edit rather than a code change.

The eight guide pages, resolved (SKILL.md currently ships `<notion-url>` placeholders for 01–07):

| Page | URL |
|---|---|
| 00 — Index | `.../p/3c8d6bfc2683805a9d6ffa77cef00542` |
| 01 — Base Style | `.../p/3c8d6bfc268380708abad5c9b3cb2f4c` |
| 02 — Ledgers | `.../p/3c8d6bfc268380beb423e6cce5948e8d` |
| 03 — Payments | `.../p/3c8d6bfc268380cbac39fda788c7e4b0` |
| 04 — Platform guides | `.../p/3c8d6bfc26838075bcabe168ff4563d1` |
| 05 — API reference | `.../p/3c8d6bfc268380f2b548f4b2a934973f` |
| 06 — Flexible Conventions | `.../p/3c8d6bfc26838011a16ccf4511c8a0c7` |
| 07 — Review & Correction | `.../p/3c8d6bfc26838079bbe1f3ef57ef817a` |

### What moves

Of the 28 rules that fire on the head corpus, **16 are pure table lookups** — their behaviour is fully
determined by a list, map or number, with no code change needed to alter them. Those 16 account for
**2,049 of 5,038 findings (41%)**:

| Table | Rules it decides |
|---|---|
| Object names | `object-capitalization` (574) |
| Object shorthand | `object-shorthand` (221), `mt-shorthand` (68) |
| Filler words + replacements | `filler` (226), `filler-please` (90) |
| Vague anchor list | `link-anchor-vague` (58) |
| Canonical fence tags + fixes | `fence-language` (146), `fence-language-unknown` (3) |
| Acronym expansions | `acronym-undefined` (136) |
| Sentence-word ceiling (30) | `sentence-length` (302) |
| List-depth ceiling (3) | `list-depth` |
| Currency codes | `currency-mixed` (7) |
| Per-repo URL prefixes | `link-absolute-internal` (167) |
| Overlay scoping | `contractions` (31), `reference-no-shell` (5), `no-ordered-lists` (3) |
| Sanctioned callout emoji | `callout-emoji` (12) |

Plus the severity grade of *every* rule (`strict`/`moderate`/`flexible`), which is the single most
likely thing to be retuned and today requires editing `RULES` in `stylecheck.py`.

### What does not move

Mechanism, not policy: every regex, the emoji code-point ranges (generated from the Unicode data files,
not a Modern Treasury decision), the irregular-participle list, the JSON dialect handling, the
markdown-it parse. And Notion is never a source of truth for API facts — `docs-test` reads
`swagger.yaml`, the rswag schemas and the event registry, never a Notion table.

### Why the checker must not read Notion at runtime

A verdict that depends on a network call is not reproducible: it cannot be mutation-tested, the harness
cannot pin the inputs a precision number was measured against, and two runs on the same commit can
disagree. So:

1. `scripts/notion_sync.py` (shipped, run on demand) compiles `config/rules.yaml` plus refreshed
   `style/*.md` from a Notion snapshot captured out of band — the script itself makes no network
   call, because MCP tools run in the agent's harness rather than in a subprocess.
2. The artifact records `synced_at`, the snapshot's capture time, each page's Notion
   `last_edited_at`, and a content hash recomputed from its own body before any use.
3. The checkers read only the artifact, offline, and print the hash in every report and in
   `--list-rules`. As shipped today only the second half of that is true: Phase 1 compiles and stamps
   the artifact, Phase 2 is what re-homes the decisions into it. Until then the checker decides with its
   own constants, an edit to `config/rules.yaml` moves the stamp and no finding, and an element-by-element
   differential against the constants is what keeps the two honest.
4. The harness pins the hash. Fixtures and mutation runs assert against one artifact revision; a sync
   that changes a table re-opens the admission gate for the affected rules only.

The hazard externalising data introduces is silent emptiness: a renamed table header or a cell rewritten
as prose yields an empty word list, and the rule stops firing while every test still passes. Two guards,
both cheap: the sync validates each table against a schema and fails loudly, and it refuses an artifact
where any list is empty or has shrunk by more than a third without `--force`. Mutation testing is the
backstop — a rule whose table went empty kills no mutants.

### Evidence this is worth doing: the tables have already drifted

Comparing four Notion tables against the shipped constants, three disagree:

- `filler`: the guide bans `just` as a minimizer; `BANNED_FILLER` does not contain it (and the code
  comment cites provenance for `just`, so it was dropped after the provenance was written). 35
  occurrences across 27 corpus pages go unreported.
- `object-shorthand`: the guide lists six shorthands, the code enforces seven — `LAC` is code-only
  policy, 14 occurrences on 2 pages.
- Rule id: the guide calls it `first-heading-h1`, the checker reports `body-h1`, so its 434 findings
  cite a rule id that does not appear in the guide.

All three are exactly what compiling from one source removes.

### One thing the Notion side needs first

Most of these values are currently *prose* in Notion, not tables: "Banned: `simply`, `just` (as a
minimizer), `easily`…" reads well and parses badly — compiling it means regexing English, which is the
failure mode this whole exercise exists to avoid. The fix is small and improves the page for humans too:
a `Rule tables` database (or one table per rule section) with columns `rule id | value | note`, kept next
to the prose that explains it. The prose stays authoritative for humans; the table is the compilable
projection of it, and the sync fails if a rule's table is missing rather than guessing from prose.

## 3. The admission gate (hard requirement)

No rule ships in any subskill until all six hold. This is the whole point of the exercise, so it is
written as a checklist the harness evaluates, not as an intention.

1. **Corpus base rate**, measured on the head corpus (682 pages): what fraction of pages the rule fires
   on. A rule firing on >50% of a project's pages describes the corpus rather than diagnosing a page
   and is rejected or demoted — this is what the guards caught for `passive-voice` (87%) and
   `frontmatter-excerpt` (89%, since resolved by inverting the rule — D7).
2. **Non-vacuity and non-universality witnesses**: a real corpus page the rule fires on, and a real
   corpus page it does not, both recorded by path.
3. **Fixtures**: at least one positive and one negative in the harness, plus a boundary fixture for
   every numeric threshold the rule uses.
4. **Mutation kill**: every decision point in the rule's implementation must be killed by the fixtures,
   or the survivor must be proven corpus-silent *and* argued harmless to a reader. Current bar is 0.950
   over 181 mutants; a new rule may not lower it. Runs use `PYTHONDONTWRITEBYTECODE=1` and must produce
   an identical survivor set twice, because the first version of this harness reported 0.939 off stale
   bytecode.
5. **Independent confirmation for any factual claim**: a second implementation must agree — reference
   tools for mechanics (markdownlint, emoji-regex, write-good), `json5` for JSON, `jsonschema` vs `ajv`
   for schemas, a Prism AST walk for Ruby state machines, HTTP status for links. Disagreement fails the
   claim; it does not get adjudicated away.
6. **Adjudicated precision** for anything that is not decidable: ≥100 blind-labeled findings, rule
   names and severities stripped, sampled across projects, with precision per severity meeting the
   grade's target. Strict ≥0.95, moderate ≥0.80, flexible reported without a floor but with the number
   published.

Grade semantics, so the gate has meaning: **strict** = a reader is provably harmed (does not parse,
does not resolve, contradicts the source of truth); **moderate** = deviates from a measured convention
with a named counterexample rate; **flexible** = reviewer judgment, never a gate failure.

Gate 6 is the one nothing has passed yet. Today there are zero adjudicated labels, which is why
`docs-content` and `docs-maintain` cannot ship a single rule at any grade above flexible right now,
regardless of how good the detection looks.

## 4. `docs-lint` — exists, needs re-homing not rebuilding

29 rules, 185 fixtures, 0.950 mutation, differential-checked against markdownlint/emoji-regex/write-good.
All 29 move as-is; the split is mechanical (extract `findings.py`, keep the rest).

Two open questions that the split does not create but does make visible:

- `passive-voice` (flexible, 87% of payments pages) fails gate 1 as written and is the first thing
  adjudication has to settle. `frontmatter-excerpt` no longer applies at all: excerpts are not used, so
  the rule inverts into "a present excerpt is removable" (D7), which is why its 89% base rate stops
  being a gate problem and becomes a one-time cleanup list of 515 pages.
- `url-query-separator` and `json-parse` look like docs-test rules (both were found by things 404ing or
  failing to parse) but are statically decidable, so they stay in lint. The test for whether a rule
  belongs in lint is "does it need anything besides the file", not "how was it discovered".

Work: extract shared module, re-run all three harness suites, confirm identical findings on the head
corpus before and after the split (a byte-identical JSON report is the acceptance test).

## 5. `docs-content` — the measurement exists, the thresholds do not

Candidate rules, each with what has already been measured and what gate 1/6 still needs:

| Candidate | Measured | Missing |
|---|---|---|
| Request example not followed by its response | 269 curl fences, 81 followed by JSON | nothing — this **fails** as a norm at 30%, and stays killed |
| Page archetype conformance | repo+directory already separates the corpus; median reference page has 2 words of prose | a defensible archetype definition; clustering added nothing |
| Walkthrough step shape (numbered, names an actor, shows a result) | not measured | extractor + base rate per project |
| Example introduction convention (how a snippet is framed before it appears) | not measured | extractor + base rate |
| Truncation convention in responses | 25 usages, 4 incompatible forms, 0 of 76 request payloads omit a required field | rule is writable now: bare `...` line approved, `"..."` as a value rejected |
| Callout placement and type | not measured | base rate; likely flexible only |

`norms.json` is generated from the **frozen** corpus (667 pages) and precision is measured on the head
corpus (682), so a norm is never validated against the pages that defined it.

Honest read: only the truncation rule is close. The rest need an extractor first, and an extractor that
over-collapses makes everything look conformant — which is exactly the failure mode the endpoint
normalizer property tests were written to catch, so the same treatment applies here (gate 5 via
Hypothesis properties on the extractor before any rule reads its output).

## 6. `docs-maintain` — the strongest unbuilt signal

Two modes, per D8. **Sweep**: all three repos, every duplication class, ranked — run once as a cleanup
project, then rarely. **Incremental**: for the pages in a change, does this content already exist in the
block inventory or on another page. Incremental is the one that runs on a push, needs no thresholds for
the exact-match case, and is therefore the first part of this family that can ship.

Measured on the head corpus already:

- 261 exact repeated prose groups, one paragraph on 14 pages.
- 121 near-duplicate pairs at Jaccard ≥ 0.6.
- 2 ReadMe custom blocks referenced but never defined — a hard defect, strict-eligible, and the only
  reuse finding that needs no threshold at all.
- 121 of 319 UUIDs reused across pages; 118 distinct example names; 66 distinct amounts.
- 3 identification numbers reused across distinct identities, one of which the sandbox proves breaks a
  reader (`us_ssn 111222333` on three pages for three people → `422`).

Candidate rules:

1. `reuse-undefined-block` — referenced custom block that no page defines. Strict. Decidable. Ships
   first because it needs no adjudication.
2. `example-identity-collision` — one `(id_type, id_number)` bound to multiple identities. Strict for
   `us_ssn`, advisory for `us_ein` until the enforcement asymmetry engineering question is settled.
3. `restatement-should-link` — repeated prose where one page is the canonical owner. Needs canonical
   ownership derived from the docs (your D4), a length floor, and adjudication. Moderate at best.
4. `reuse-candidate` — a paragraph repeated ≥N times, suggesting a reusable block. Flexible, suggestion
   only. N comes from the distribution, not from taste.
5. `example-continuity` — the same entity described inconsistently across payments/ledgers/platform.
   Needs an entity-identity notion before it needs a threshold.

### 6.1 Mapped against the reusable-content proposal

Re-run against all three repos with block names normalised (`name: Organization Change Approvals
Required Callout` is referenced as `<OrganizationChangeApprovalsRequiredCallout />`, so naive matching
reports two false undefined refs in platform):

- **Undefined**: `EarlyAccess` ×8 in platform, `SandboxDetails` ×1 in ledgers.
- **Orphaned**: 5 blocks in payments (`1099Disclaimer`, `Form1099Disclaimer`, `CreatingAnAccountForALE`,
  `PaymentOrderStateMachine`, `BlockchainNetworkSelection`), 5 in platform including `BYOBDislcaimer`,
  a typo of the block that 8 pages actually use.
- **No cross-repo references**: blocks do not resolve across repos, so a shared statement must be
  duplicated per repo — which makes wording-drift detection (below) the only way to keep them aligned.

What the proposal does that `docs-maintain` can decide mechanically:

| Detection | Grade | Why decidable |
|---|---|---|
| Undefined block reference | strict | renders broken; name normalisation is the only subtlety |
| Orphaned block definition | moderate | dead file, or a lost reference — both worth reporting |
| Near-miss block name (`BYOBDislcaimer` vs `BYOBDisclaimer2`) | moderate | edit distance against defined names |
| Duplicate page (same title, high similarity) | strict | `Closing Accounts` ×2, `copy-of-*` slugs |
| Near-identical slugs with unrelated content | moderate | `virtual-account-testing` / `-1` |
| Within-page repeated block (3 payloads 98.8% identical) | moderate | pairwise similarity inside one file |
| Cross-page duplicated region + line count | moderate | already measured: 261 exact groups, 121 near-dup pairs |
| **Wording drift across a repeated statement** | moderate | the same claim in 5 places with 4 wordings, or 3 link forms — highest correctness value in the whole proposal |
| Maximal shared prefix of a candidate block | n/a (input to a suggestion) | blocks are not parameterisable, so the block must be cut above the first differing line |

What it cannot decide, and should not pretend to: **blockify vs merge vs trim**. The proposal's own
verdicts show why — Group D is "don't blockify, merge the pages", E1 is "trim first, then blockify",
Group B is "tiny line count, adopt anyway for correctness". Those are editorial calls that depend on
search/SEO, product intent, and whether a shared example shape is acceptable. Same for block naming,
phase assignment, and picking the canonical wording among variants.

So the shipped shape is: report the duplication with its size, occurrence count, variant count and
location, ranked by `(occurrences − 1) × length`; suggest a block boundary where one is computable; and
stop short of the recommendation. The proposal is the human layer on top of that output, and it stays a
human layer.

The trap here, and the reason this family cannot be rushed: repetition is often correct. A paragraph
appearing on 14 pages may be 14 pages that each need it. Rules 3–5 are only meaningful once "the same
content, and one of these places should own it" is separated from "the same content, deliberately",
which is an adjudication question with no shortcut.

## 7. `docs-test` — the probes exist, none of them ship

| Check | Needs | State |
|---|---|---|
| Link resolution | network | live sweep works; offline detection measured at 0.23 precision and rejected as a gate |
| Endpoint exists | monorepo | works; ReadMe `api.operationId` frontmatter resolution needs improving |
| Request body fields | monorepo | works; found 4 rejected fields |
| Types, enums, nested fields | monorepo | 8 findings, 1 true defect; blocked on placeholder exclusion and `minProperties` |
| Response examples | monorepo | not built |
| Webhook event names | event registry | works; found 3 unregistered names |
| Object states vs AASM | monorepo | works; differential Prism parse agrees 13/39 |
| String fields the code constrains but the spec does not | monorepo | **not built, highest value** — this is the class that caught `proof_of_addres`, which no schema check can reach because swagger types it as a bare string |
| Documented request execution | sandbox + network | works; found the SSN collision |

Two rules the sandbox work forces into the design:

- **One org, plus attribution (D9).** A single sandbox produced a false defect ("the documented
  status-transition flow is unfollowable"), which was an artifact of that org lacking a Flow vendor
  connection. The fix is not a second org — it is attribution: an execution finding must reproduce after
  the fixture is freshened, and a 4xx whose message names a missing org-level prerequisite is reported as
  environment-dependent rather than as a docs defect. The credential predicate (`app.moderntreasury.com`,
  key begins `test-`, no `demo.`, abort on live mode) is enforced before the first request.
- **Per-org compliance config is not a docs claim.** `phone_numbers` required in one org and not another;
  `us_ssn` required for individuals in one org. Required-field claims must be checked against the
  code/spec, never against a sandbox response.

Also unverifiable by design and worth stating: Cases have no sandbox simulation path (only
`/simulations/incoming_payment_details/create_async` and
`/simulations/legal_entities/{id}/update_status` exist), so no Case page can be execution-verified.
`docs-test` must report "not verifiable in sandbox" as a distinct outcome from "verified" — a checker
that silently skips what it cannot reach is worse than one that fails.

## 8. Sequencing

Each step gated on the previous. No step ships a rule that has not cleared §3.

1. **Split, no new rules.** Extract `findings.py`, four subskills, umbrella runner, `config.yaml`.
   Acceptance: byte-identical JSON report on the head corpus, all 185 fixtures, differential clean,
   mutation ≥0.950, plus the new no-`dev`-import test.
2. **Adjudication infrastructure.** Blind label sets: shuffled findings, rule names and severities
   stripped, stable hashes, per-rule and per-severity precision. This is the gate on everything below,
   and it is where you or a docs reviewer disagreeing with my labels is the most useful signal
   available.
3. **Adjudicate `passive-voice`** and settle its grade; invert `frontmatter-excerpt` per D7 and emit the
   removal inventory.
4. **`docs-maintain` rules 1–2** (undefined block, identity collision). Both decidable, no adjudication
   needed, so these are the first genuinely new shipped rules.
5. **`docs-test` string-domain check** (fields the code constrains but the spec leaves open), then
   response-example validation, then typed differential with placeholders excluded and `minProperties`
   resolved.
6. **`docs-content` truncation rule**, then extractors with property tests, then the rest of the family
   behind adjudication.
7. **`docs-maintain` rules 3–5** last, since they are the most judgment-heavy in the plan.

Hand-off, not in this sequence: the swagger publishability gate (§ opening) as a spec for engineering,
and the two open engineering questions (EIN/SSN uniqueness asymmetry; simulation endpoint 422 that does
not say the org lacks a Flow connection).

## 9. Decisions (closed)

**D6 — invocation.** All four subskills run inside Devin, each individually addressable, and the normal
case is all of them. Invoked on request, and optionally on a push to GitHub. Consequences: the umbrella
runner takes an explicit subskill selection (`--only docs-test`) as well as the all-four default; each
subskill has to be usable standalone, which is what forces `findings.py` to be a shared import rather
than four copies; and the pre-push mode must be scoped to changed pages, since a corpus-wide run on
every push is both slow and dominated by inherited findings. Shipping this to the Devin eng team for
blessing is the last step of sequencing, not the first.

**D7 — `frontmatter-excerpt` inverts.** Excerpts are not used, so the rule is not "excerpt missing =
strict failure" but the opposite: report a present excerpt as removable. This is the cleanest resolution
of the 89% base rate — the 515 findings become a one-time cleanup inventory rather than a gate that
fails nearly every PR on inherited debt, and the strict rule that remains (`frontmatter-title`, 26
findings) has a base rate a gate can live with. `01 — Base Style` currently says "The excerpt is the
search and preview text. Write one; do not leave it empty", so the Notion page has to change with the
rule; this is a worked example of why the rule tables and the guide should compile from one source.

**D8 — reuse runs in two modes.** One-time corpus-wide sweep first (all three repos, every duplication
class in §6.1, ranked), which is where the existing 5,127 duplicated lines and 43 candidate blocks get
resolved as a project. After that the standing check is incremental: for the pages in a change, does
this content already exist in the block inventory or on another page — i.e. "are we recreating something
that exists", not "is the corpus optimal". Two implications: the block inventory (defined, referenced,
orphaned, per repo) becomes a committed artifact the incremental mode reads, and the incremental mode
needs no thresholds for the exact-match case, which lets it ship before the near-duplicate work.

**D9 — one sandbox org, no two-org rule.** The earlier two-org requirement was an artifact of the first
org being the wrong one, and is removed. `docs-test` prompts for an org id and API key and enforces a
credential predicate before issuing any request:

1. host must be `app.moderntreasury.com`; `demo.moderntreasury.com` is refused;
2. the key must begin `test-`; anything else is refused without prompting for confirmation;
3. any response showing live mode aborts the run;
4. the key is read from the skill's `config.yaml` and never written to a report or log.

The consequence for the harness is that an execution finding no longer needs corroboration in a second
org — but it does need the failure to be attributable to the documented request rather than to org
configuration, which is what the first org's missing Flow connection actually was. So the rule that
replaces it: an execution finding must reproduce after the fixture is freshened, and a 4xx whose message
names a missing org-level prerequisite is reported as environment-dependent, not as a docs defect.
