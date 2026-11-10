---
name: docs-review
description: Use when writing, editing or reviewing a docs page; answering "is X documented" or "where do the docs say"; or handling any docs-readme-* path or docs.moderntreasury.com URL.
---

# Modern Treasury documentation

Choose **review**, **locate**, **draft** or **sweep**. Commands are relative to
this skill directory. Existing dependencies are `markdown-it-py` and `PyYAML`.
Git is needed for ref-based modes; `gh` and network access are optional for locate.

The three documentation repositories remain read-only during evidence gathering.
Locate, small-edit validation and sweep use refs, never checkout, branch, commit
or push in them. Draft writes only to its explicit output directory. Temporary
snapshots and validation copies do not change source repositories.

## Project and style references

| Destination | Project |
|---|---|
| `docs-readme-ledgers/docs/**` | `ledgers` |
| `docs-readme-payments/docs/**` | `payments` |
| `docs-readme-platform/docs/**` | `platform` |
| `reference/**` | `reference` |

Read the base and one overlay. An overlay wins where it differs. The guide, not
a corpus majority, decides person: Ledgers walkthroughs use `we`; Payments and
platform tasks address `you`.

| Reference | Purpose |
|---|---|
| [00 — Index](style/00-index.md) | Grades, policy ownership, projects |
| [01 — Base style](style/01-base-style.md) | Voice, terminology, formatting, links, images |
| [02 — Ledgers](style/02-overlay-ledgers.md) | Worked accounting examples |
| [03 — Payments](style/03-overlay-payments.md) | Operational workflows and failure paths |
| [04 — Platform](style/04-overlay-platform-guides.md) | Setup and UI labels |
| [05 — API reference](style/05-overlay-api-reference.md) | Spec-derived descriptions |
| [06 — Flexibility](style/06-flexible-conventions.md) | Latitude and no-backfill decisions |
| [07 — Review](style/07-review-and-correction.md) | Correction scope and order |
| [08 — ReadMe conventions](style/08-readme-conventions.md) | Corpus-cited components, frontmatter, tabs and links |

## Review mode

```shell
python3 scripts/review.py <path>
python3 scripts/review.py <path> --base <git-ref>
python3 scripts/review.py <path> --mode draft --project payments
python3 scripts/review.py <path> --format json
python3 scripts/review.py <path> --strict-only
python3 scripts/review.py <path> --only lint
python3 scripts/review.py --list-rules
```

1. Identify the project and read its guide pages.
2. Fix mechanical strict findings in scope. Weigh flexible notes individually.
3. Apply **reviewer judgment** to tense, person, imperative steps, accuracy and
   the [rubric](references/rubric.md). These judgments are never rule findings.
4. Verify claims against cited contracts/specs, not model memory. A clean score
   does not establish product correctness.
5. Report mechanical findings separately from reviewer judgment, with evidence
   and any unresolved gaps. Never enforce an unwritten preference.

Review is default. Without `--base`, `body-h1` and `image-alt` are inactive. With
a base, absent files are new and added/replaced lines are touched. New pages
require their first body heading to be h1; existing pages are not backfilled.
Alt text applies to new/touched images. Draft treats every file as new.
`heading-skip` stays active independently.

Reported flexible: `sentence-length`, `passive-voice`, `filler`, `filler-please`,
`fence-language-unknown`, `link-absolute-internal`, `acronym-undefined`,
`contractions`, `reference-no-shell`, `no-ordered-lists`, `frontmatter-excerpt`,
`em-dash`. Guide grades may be stricter. Requests use `curl`, with ReadMe labels
allowed; `shell` is for non-request commands. Use page 08's Callout/Image syntax.

Four tiers share findings and a policy stamp. docs-lint has 31 rules;
docs-content, docs-maintain and docs-test currently report none. `--only` selects
tiers. Review exits 0 with no strict findings, 1 with strict findings, 2 for bad input.

## Runtime: getting sources

No local documentation clones or GitHub CLI authentication are required. Fetch
only task-required pages and the spec, never the whole corpus. First use the
GitHub MCP connector's `get_file_contents` on
`Modern-Treasury/docs-readme-<project>`, ref `v2.0`; record the returned file SHA.
Otherwise fetch `https://docs.moderntreasury.com/<project>/docs/<slug>.md` and
record SHA `live`. Do not invent a SHA or treat live content as a pinned revision.
The spec is `docs-readme-platform`, path `reference/modern-treasury-api.json`.

Save pages under `SNAPSHOT/<repo>/<path>` and create `SNAPSHOT/manifest.json`
with this exact shape (one entry per fetched file):

```json
{"entries": [{"repo": "docs-readme-payments", "path": "docs/example.md", "sha": "live", "url": "https://docs.moderntreasury.com/payments/docs/example.md"}]}
```

`repo` is a repository basename, `path` is repository-relative, `sha` is the
connector's Git SHA or `live`, and `url` is the HTTPS source URL (the connector's
`html_url` or the fetched public URL). List only fetched files. Missing files,
duplicate entries, unsafe paths and invalid fields are input errors. Reports
retain each file's provenance; a task-scoped snapshot is not corpus coverage.

For PRs use connector `search_pull_requests` / `list_pull_requests` (and fetch
patches as needed). Save `prs.json` as an array, or `{"items": [...]}`, of:

```json
[{"number": 123, "title": "Example", "body": "Description", "state": "open", "merged_at": null, "html_url": "https://github.com/Modern-Treasury/docs-readme-payments/pull/123", "repo": "Modern-Treasury/docs-readme-payments", "patch": "+ optional patch text"}]
```

Use `open`/`closed` state and ISO timestamps for `merged_at` (or null). `body`
may be null; `patch` is optional. Repository basenames and GitHub
`repository_url` are also accepted. Supply all relevant open/recently merged
PRs: the script cannot establish connector search completeness or recover
missing patch text. No input and unavailable `gh` means **PR search not run**.

## Locate mode

Use for generalized questions and documentation discovery. **The model judges
whether the quote answers the question: reviewer judgment.** Term coverage is
not an answer or a product guarantee.

```shell
python3 scripts/locate.py "Which identification types are supported for a legal entity?" --snapshot SNAPSHOT --prs prs.json
python3 scripts/locate.py "registered agent address" --snapshot SNAPSHOT --no-web --no-prs --json
python3 scripts/locate.py "external_account" --repos /path/to/docs-readme-payments --ref origin/v2.0 --top 5 --days 90
```

Use `--snapshot DIR` for runtime; explicit `--repos DIR... --ref origin/v2.0`
is the development-only Git path. Neither mode changes source files. Search
removes stopwords, preserves code tokens/quoted phrases and expands synonyms
from `config/locate.yaml`. Git grep reads resolved refs, not working trees.
Passages rank by term coverage with title/heading coverage bonuses, then stable
path/line tie-breaks; one passage per page is returned. Quotes include
path, heading, line range, SHA and public URL. URLs use explicit frontmatter
`slug`, otherwise filename (parent for `index.md`), under shared project prefixes.
Confirm inferred URLs; a weak hit does not establish the requested behavior.

Optional web checks fetch candidate `<url>.md` and project `llms.txt` indexes with
bounded timeouts. `ok` means the exact quote is present, not that it answers the
question. Mismatch/unreachable and empty/incomplete indexes are recorded. Index
completeness is checked against candidate URLs only, not the entire corpus.

PR search examines titles, bodies and changed patches of open PRs and PRs merged
within `--days`, from `--prs FILE`, or optionally via `gh api`. It reports bounded-search truncation and access
errors. Missing gh or offline sources do not erase local results. Always report
the `searched:` list: repositories/SHAs, terms, URLs, PR queries and unavailable
sources. "Not found" means no local candidate, not that a feature is unsupported.

## Draft mode

The model writes prose. The script only scaffolds templates and validates.

| Destination | Template |
|---|---|
| Small edit | [Quote, replacement, path, heading](references/templates/small-edit.md) |
| Docs page | [Page](references/templates/docs-page.md) |
| Integration | [Phases and webhook gate](references/templates/integration-guide.md) |
| API reference | [Spec-change handoff](references/templates/api-reference-change.md) |
| Topics page | [Concepts and constraints](references/templates/topics-page.md) |

```yaml
question: Is registered-agent address behavior documented?
destination: small-edit
project: payments
evidence:
  - claim: The cited source does not specify registered-agent address support.
    source: repo path, ref SHA and passage verified by the reviewer
    verified: true
target:
  repo: docs-readme-payments
  path: docs/Customer Onboarding/onboard-a-business/required-fields-for-businesses.md
  heading: Required Fields for Businesses
```

This is a schema example, not verified evidence. Replace it with actually checked
claims and sources. Each evidence item needs `claim`, `source`, `verified: true`.
The flag is reviewer testimony, not script verification. Optional `fields` maps
placeholder names to model-authored strings; missing fields remain placeholders.
Only small edits require target repo/path/heading; other destinations require
question, verified evidence, destination and project.

```shell
python3 scripts/draft.py brief.yaml --snapshot SNAPSHOT --out /path/to/draft --max-iterations 5
python3 scripts/draft.py validate /path/to/draft
```

The snapshot choice is saved in the draft brief; validation may also receive
`--snapshot DIR`. Small-edit quotes must occur verbatim under the target heading
in a manifest-listed file. Results carry its SHA/`live` and source URL. For Git
development mode instead use an explicit local `target.repo` and `target.ref`.

Model loop:

1. Locate and verify evidence. Do not draft beyond it.
2. Scaffold into an empty directory; author `candidate.md` in the selected shape.
3. Validate, read iteration count/findings, edit, repeat until zero strict.
4. Stop at the configured iteration cap (`config/draft.yaml`), reporting the blocker; do
   not silently reset state. `--max-iterations` sets the initial cap. Validate can
   lower it, never extend it. Changed briefs require new evidence-bound drafts.
5. Apply reviewer judgment and rubric even after mechanical validation succeeds.

Small edits remain quote/replacement/path/heading, not a whole page. Validation
requires one verbatim quote under the target heading at its Git ref. It applies
the replacement in a temporary copy, runs `review --mode draft` on that page and
counts findings on added/replaced lines only; unrelated existing failures are
excluded. The docs repository is never edited.

API reference drafts contain template-derived `instructions.md` and
`candidate.json`, never generated endpoint Markdown. The envelope is
`{"target":"reference/modern-treasury-api.json","patch":[...]}` with nonempty
JSON Patch operations. Validation checks structure only, not applicability to
the actual spec; correct pointers/fields/product behavior are reviewer judgment.
Other page destinations receive whole-page draft review.

`state.json` records counts; each validation attempt consumes an iteration,
including rejected candidates. `validation.json` records the latest result.
Exit 1 means editing/cap reached; exit 2 means invalid setup or input.

## Sweep mode: scaffold only

```shell
python3 scripts/sweep.py --snapshot SNAPSHOT --top 10
python3 scripts/sweep.py --repos /path/to/docs-readme-payments --ref origin/v2.0 --top 5
```

Sweep reviews only manifest-listed pages in snapshot mode; Git development mode
snapshots refs into temporary copies and runs corpus-wide review. Ranking
is strict severity first (all strict), pages affected, then rule id. Page traffic
is explicitly unknown, a placeholder with no ranking weight. This is not a
traffic integration or permission for bulk edits. It prints sources and policy
stamp and never edits docs.

## Reviewer labels and policy maintenance

The [rubric](references/rubric.md) defines eight candidate ids and the Phase 3
JSONL schema. Label accept/reject decisions separately:

```shell
python3 scripts/rubric_label.py label.json --out phase-3-labels.jsonl
```

These are not reported rules. Preserve reviewed inputs/evidence for hash checks.
The helper validates shape, not evidence truth or reviewer identity.

Policy lives in YAML: shared vocabulary/projects in `config/policy.yaml`, and
severities, scopes, contexts, thresholds, tables/exemptions in subskills'
`config/rules.yaml`. Hashes cover deciding fields, not explanatory prose. Change
the guide and matching policy together; reopen the relevant admission gate.
Do not change a checker merely to silence a finding. Locate synonyms and draft
iteration defaults are separate mode configuration, not lint policy inputs.

No shipped script imports development code. Corpus probes, fixtures, mutation
tooling and adjudication infrastructure stay outside the skill.
