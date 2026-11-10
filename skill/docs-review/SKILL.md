---
name: docs-review
description: Review Modern Treasury documentation against the docs style guide (base style plus per-project overlays for ledgers, payments, platform guides and API reference). Runs four subskills as one log — docs-lint, docs-content, docs-maintain, docs-test. Use when writing a new docs page, reviewing or editing pages in docs-readme-ledgers / docs-readme-payments / docs-readme-platform, or auditing a set of pages.
---

# Modern Treasury docs review

Applies the Modern Treasury documentation style guide to markdown pages in the three ReadMe repos:
`docs-readme-ledgers`, `docs-readme-payments`, `docs-readme-platform` (guides in `docs/**`, API
reference in `reference/**`).

The style guide lives in `style/`, and those files are the source of truth. This skill carries the
guide, the procedure, and runnable checkers for the rules that can be checked mechanically.

## The four subskills

They split by dependency tier, not topic — which is why the seam holds, and why each is separately
runnable:

| Subskill | Needs | Decides | Status |
|---|---|---|---|
| `docs-lint` | the file only | frontmatter, headings, fences, JSON bodies, links, object names, currency, prose mechanics | 31 rules |
| `docs-content` | corpus norms | continuity, teaching pattern, structure, coverage | no rules yet |
| `docs-maintain` | all three repos | reuse, duplication, block references, wording drift | no rules yet |
| `docs-test` | monorepo, network or sandbox | schemas, enums, endpoints, events, states, links | no rules yet |

An empty subskill loads its policy and reports nothing. That is the honest state: a candidate rule
there has a measured base rate but no threshold, and a rule fired without one describes the corpus
rather than diagnosing a page. Each subskill's `SKILL.md` says what it measured and what it is waiting
on.

They report as one log: one findings format, one severity vocabulary, one scorecard, one policy stamp.

## Style guide pages

Read the base style plus the ONE overlay for the project you are working in.

| Page | What it covers |
|---|---|
| `style/00-index.md` | How to use the guide, and what the two grades mean |
| `style/01-base-style.md` | Voice, tense, terminology, structure, formatting, links, callouts, images |
| `style/02-overlay-ledgers.md` | Teaching voice for ledger guides and tutorials |
| `style/03-overlay-payments.md` | Operational voice for rails, returns and reconciliation |
| `style/04-overlay-platform-guides.md` | Task voice for dashboard and configuration procedures |
| `style/05-overlay-api-reference.md` | Conventions for spec-derived reference pages |
| `style/06-flexible-conventions.md` | Where we allow variation on purpose |
| `style/07-review-and-correction.md` | How to validate, verify and correct a page |
| `style/08-readme-conventions.md` | Corpus-backed ReadMe frontmatter, components, code tabs and links |

These were rendered from Notion until 2026-09-03 and are now edited directly. A rule change is an
edit here plus the matching edit to a policy file, in one change: the prose explains the rule and the
policy compiles it, and a reviewer applying one while a run applies the other is the drift this skill
exists to prevent.


## Procedure

### 1. Identify the project

| Path | Project | Checker value |
|---|---|---|
| `docs-readme-ledgers/**` | Ledgers | `ledgers` |
| `docs-readme-payments/**` | Payments | `payments` |
| `docs-readme-platform/docs/**` | Platform guides | `platform` |
| `docs-readme-platform/reference/**` | API reference | `reference` |

Inferred from the path; pass `--project` when running outside a repo checkout.

### 2. Run

```bash
pip install markdown-it-py PyYAML                       # once
python3 scripts/review.py <path>                        # all four subskills, one log
python3 scripts/review.py <path> --only lint            # one tier (pre-commit path)
python3 scripts/review.py <path> --only lint --only test
python3 scripts/review.py <path> --strict-only          # only what must be fixed
python3 scripts/review.py <path> --format json          # machine-readable
python3 scripts/review.py <path> --mode draft           # every file is new
python3 scripts/review.py <path> --base <git-ref>        # review new files and touched images
python3 scripts/review.py <path> --rule filler --rule mt-shorthand
python3 scripts/review.py --list-rules                  # every rule, severity, source, policy hash
```

Default is all four, because a reviewer who has to remember which tier catches which defect has been
handed the tool's problem. `--only` is repeatable; the JSON scorecard names the subskills that ran.
Review is the default mode. Without `--base`, review does not infer new/touched content: `body-h1` and `image-alt` do not fire. Draft checks the first body heading and every image. Existing pages do not require an h1 backfill.

Exit status: 1 when a strict rule fails (so it can gate a commit), 2 for a bad invocation — an unknown
`--rule`, or a path whose project cannot be inferred with no `--project` given.

Each subskill is also directly runnable (`../docs-lint/scripts/lint.py` and so on) with the same flags
minus `--only`; findings are identical either way.

### 3. Fix every strict finding

Strict findings are not preferences. Correct them in the change you are making. Common ones and their
fixes are in **07 — Review & Correction**.

### 4. Judge the flexible findings

`sentence-length`, `passive-voice`, `filler`, `filler-please`, `fence-language-unknown`,
`link-absolute-internal`, `acronym-undefined`, `contractions`, `reference-no-shell`,
`no-ordered-lists`, `frontmatter-excerpt`, `em-dash` are reported for a human to decide. Fix when the alternative reads better; leave
otherwise. Do not bulk-apply.

### 5. Review what no checker sees

- **Tense**: present for what happens in Modern Treasury, future for what happens at the bank or
  outside the platform.
- **Person**: `we` versus `you` per the project overlay, consistent within each section.
- **Imperative**: procedural steps open with a verb, one action per step.

Use `references/templates/` for the destination's response shape. Fill every placeholder and run the page templates in draft mode with an explicit project when needed. `small-edit.md` is a patch handoff, not a publishable page. Requests use `curl`, with ReadMe labels allowed; non-request commands use `shell`.
Apply `references/rubric.md` as **reviewer judgment**, not reported rules. Log each accept/reject decision with `scripts/rubric_label.py` for the Phase 3 adjudication set.

Then check accuracy — endpoints, field names, enum values, screenshots — against the current product.

### 6. Report

Group findings by rule, not by line, and quote the rule name from the guide. For an audit of many
pages use `--format json` and summarize with the `scorecard` object (`strict_failures`,
`pages_clean`, `by_rule`, `subskills`).

## Where policy lives

No checker carries a policy decision. Every severity, threshold, word list, scope and exemption is
read at import from two YAML files, and each has one owner:

- **`config/policy.yaml`** (this skill) — the vocabulary and the Modern Treasury domain facts:
  the three severities, the four projects and their URL prefixes, object names and shorthand, `MT`,
  acronym expansions, currency codes. Shared, because a fact about what our objects are called is as
  useful to `docs-content` as to `docs-lint`.
- **`<subskill>/config/rules.yaml`** — the rules that subskill emits, plus the tables only it reads.
  For `docs-lint` that is 31 rules plus policy tables of prose mechanics: filler words, vague
  anchors, fence tags, callout emoji, the grammar lists behind `passive-voice`.

A table defined in both files is a refusal, and so is one rule id claimed by two subskills. Every
report and `--list-rules` stamps a policy id, so a finding can be traced to the policy that decided
it. The id is computed from the files on every run and never quoted from one, so an edit cannot be
reported under an id that predates it.

The id covers what decides a verdict — reported and guide severity, scope, threshold, the tables and
the exemptions and applicability contexts — and nothing else. Provenance and each table's `why` ride in the files and outside
the id, because `--list-rules` prints them and no rule reads them. So the stamp answers "would this
policy have decided my findings differently?" rather than "has anyone touched the guide", and
rewording an explanation does not re-open the admission gate for 31 rules.

Until 2026-09-03 the policy came from Notion through an 832-line sync, with a snapshot captured out
of band, staleness and tamper detection around the seam. That machinery existed because a database
cell is untrustworthy input. A reviewed file is not, so it is gone — along with the `Active` gate
(delete the rule), the `<delete>` sentinel (write `""`), and the separate `exceptions` block (an
exemption sits beside the value it exempts).

Consequences worth knowing:

- A wrong severity or a missing word is an edit to a policy file, reviewed like any other change.
  Do not edit a checker to change a verdict; there is nothing there to edit.
- A run reads two local files and opens no socket. A verdict behind a network call cannot be pinned
  or mutation-tested, and two runs on one commit could disagree.
- A missing, unreadable, malformed or incomplete policy makes a subskill refuse to run rather than
  fall back to a default, because a guessed threshold reports a number nobody chose.
- A table change re-opens the admission gate for the rules that read it.

`--list-rules` prints the authoritative rule table. Judgment rules with no check, enforced in review:
ambiguous object capitalization (Transaction, Invoice, Return, Counterparty, Document, Event), tense,
person consistency, imperative steps, UI-label formatting, failure-path coverage, one-sentence field
descriptions.

## Changing a checker

Do not edit a checker from a review. The fixtures, the differential against markdownlint /
write-good / emoji-regex, the snapshot-to-runtime differential, the mutation harness and the corpus
the rules were measured on live in the docs-style repo outside this skill; a rule changed without them
is unverified. Make the change there, run its suites, and copy the result back.

What ships is this directory: `SKILL.md`, `scripts/`, `config/`, `style/` and the umbrella's `references/`. What proves
it — corpus snapshots, probes, oracles, fixtures, mutation tooling, adjudication — never ships, and no
shipped file imports from it.

## Notes

- The checkers are deliberately disposable. They encode the guide; the guide does not depend on them.
- The checkers read and report; nothing writes to a page. The rubric helper appends only to an explicitly chosen JSONL label log.
- Never rewrite a page wholesale to satisfy a checker. Fix findings in what you touch.
- Corpus-wide cleanups go one rule per change, so the diff stays reviewable.
