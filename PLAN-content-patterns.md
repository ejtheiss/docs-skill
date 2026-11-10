# Plan: content patterns, continuity, maintainability, and technical truth

Status: research and planning. Nothing in this plan is implemented in the shipped skill yet.

## Blast radius: none

This work is sandboxed to the skill workspace (`/home/ubuntu/docs-style`) and stays there. While this
plan is being researched, built, or validated:

- **No pull request to any docs repo** — not `docs-readme-payments`, `docs-readme-ledgers` or
  `docs-readme-platform` — and nothing published to ReadMe.
- **No change to the monorepo**, including the swagger, the rswag schemas, the event registry and the
  models. Every source artifact is opened read-only. The §4.4 predicate is a *recommendation* for the
  monorepo, not a change I make there.
- **No commits, no pushes, no branches** in any repository, and no writes anywhere outside the skill
  workspace. Repository checkouts stay clean; `git status` is the check.
- **No side-effecting API calls.** Live HTTP is limited to `GET` requests against the public docs site
  for link verification (§5) and to replaying documented examples against the Modern Treasury
  **sandbox** organization with sandbox credentials (§4.7). Writes are opt-in behind `--writes`, the
  executor is harness-only, and no production credential is ever used.
- Demonstrations of what the checker *would* change (as with the stablecoin on-ramp page earlier) are
  produced on scratch copies outside the repos and delivered as a diff, never applied.

The only deliverable is the skill itself. Fixing the defects this research found — the 4 rejected
request fields, the 2 missing required fields, the 3 invalid event names, the 9 broken links, the 22
divergent operations — is separate work that needs its own approval, and the plan does not assume it.

Revision 6. Revision 1 proposed rule families from inspection. Revision 2 replaced every asserted
pattern with a measured base rate taken from a rehydrated corpus, dropped the candidates the
measurements killed, and added the severity model, the maintainability family, the truth-verification
layer, and the validation harness that has to prove the whole thing is not theater. Revision 3 closes
decisions D1–D5, retracts one revision-2 claim that further measurement showed to be wrong (§4.2), and
adds spec divergence as a check in its own right (§4.3). Revision 4 removes the phrase "verified by
hand" from this plan entirely: every number below is now re-derived by `dev/verify/verify_claims.py`
using a method independent of the probe that produced it, and three numbers changed as a result (§4.6).
It also settles §4.4 by running ReadMe's own OpenAPI tooling instead of arguing from a correlation.
Revision 5 turns the same scepticism on the harness itself: every validation method is executed and
judged by what it produced (§7.0), which cut TLA+/Alloy model checking, downgraded the schema
differential, and produced two findings about the *shipped* checker — a 0.834 mutation kill rate and
seven rule/area pairs that fire on more than half their pages. Revision 6 reinstates the sandbox
executor that revision 5 cut, because credentials were provided: it is built, executed against 272
documented requests, and reported in §4.7, and its yield is stated after the failure categories are
separated rather than before. Revision 6 also closes the mutation finding — kill rate **0.939**, and
every surviving mutant now proven silent across the whole corpus (§7.1) — and promotes the two rules
that execution and corpus measurement made conclusive, `json-parse` and `url-query-separator`.

**Nothing here is asserted on my reading of a file.** Each claim carries an ID; running
`dev/verify/verify_claims.py` recomputes it from source and exits non-zero if any claim disagrees with
what this plan says. Where two independent implementations are available they must both agree
(`jsonschema` and `ajv` for schema claims), and a disagreement fails the claim rather than being
adjudicated in favour of the nicer number.

---

## 0. What ships and what does not

This line is the same one the style checker already respects, restated because this plan adds
network access, monorepo access, and an AI-assisted reviewer — three things that must never leak into
the deliverable.

**Shipped product** — `skill/docs-style-review/`, portable, no corpus, no network required to load:

| Artifact | Status |
| --- | --- |
| `SKILL.md` | ships (extended with the new review order and the AI review instructions) |
| `style/00-07*.md` | ships (extended with derived content and continuity conventions) |
| `scripts/stylecheck.py` | ships (extended with graded severity) |
| `scripts/contentcheck.py` | ships, new — structure, continuity, maintainability |
| `scripts/apicheck.py` | ships, new — deterministic truth against a spec index |
| `scripts/linkcheck.py` | ships, new — link resolution, live confirmation |

No generated spec index ships. D1 closed: the checkers read the monorepo swagger and the published spec
directly, so there is exactly one source of truth per question and no cache to go stale.

**Validation harness** — `dev/`, never shipped, never imported by a shipped file:

| Artifact | Purpose |
| --- | --- |
| `dev/corpus/hydrate.py` | reproducible frozen and head snapshots plus manifest |
| `dev/corpus/probe_*.py` | detectability probes; every number in this plan comes from these |
| `dev/corpus/measurements/` | recorded probe output, the provenance for each base rate |
| `dev/mine/` | pattern mining that proposes candidate rules |
| `dev/tests/` | fixtures, property tests, differential oracles, mutation runs |
| `dev/verify/` | the claim oracle: re-derives every number in this plan and fails if the plan is stale (§4.6) |
| `dev/readme_limit/` | runs ReadMe's own OpenAPI tooling to decide §4.4 by execution |
| `dev/formal/` | TLA+/Alloy encodings, vacuity and independence checks |
| `dev/ab/` | blind A/B protocol, labels, adjudication, scoring |

Enforced mechanically: a test asserts no file under `skill/` imports from `dev/`, and that every
shipped checker runs against a fixture directory with the corpus absent and the network disabled.

What the shipped checkers do to a repository once approved: **read it and report**. They open the docs
pages, the swagger, the rswag schemas, the event registry and the published spec read-only, print
diagnostics, and set an exit code. No checker edits a page, applies a fix, calls a write API, or touches
git — a proposed correction is output for a human or for Devin to apply under review, which is the same
contract `stylecheck.py` already honours.

---

## 1. Corpus, rehydrated

`dev/corpus/hydrate.py` materializes two snapshots by `git archive`, and writes
`corpus-manifest.json` with a per-repo revision, commit timestamp, file count, and a content hash so
any number in this plan can be recomputed exactly.

| Snapshot | Revisions | Pages | Purpose |
| --- | --- | --- | --- |
| frozen | payments `f9528fdb`, ledgers `89697156`, platform `f5453f0c` | 667 | derive norms from human-authored docs only (committer time < 2026-03-13Z) |
| head | payments `3734502e`, ledgers `2b2ae79d`, platform `3989d2a2` | 682 | measure drift, evaluate checks on pages reviewers actually see |

Two corrections to the previous corpus:

- The old cutoff was applied in local time, which pinned payments and ledgers to commits already past
  the UTC boundary. `hydrate.py` states the cutoff as `committer timestamp < 2026-03-13T00:00:00Z` and
  derives revisions from it, so the pin cannot drift again.
- Frozen platform has 441 markdown files, head has 437: reference pages were removed, not only added.
  Drift is bidirectional, so "new pages only" evaluation would miss deletions.

Norms are derived on **frozen**. Precision is measured on **head**. A rule tuned and evaluated on the
same snapshot proves nothing.

### 1.1 Area, not archetype

Revision 1 proposed clustering pages into archetypes. The measurement says a cluster step is not
needed and would be circular: repo plus top-level directory already separates the corpus into four
families with sharply different structure. `reference/` in platform is the API reference; everything
else splits by repo.

| Area | Pages (frozen) | Median words | Pages with fences | Prose before first example | Numbered walkthrough (3+ steps) | Tables | Callouts | Has any H2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| api-reference | 338 | 2 | 0.32 | 0.20 | 0.00 | 0.06 | 0.11 | 0.07 |
| payments-guide | 150 | 286 | 0.33 | 0.70 | 0.17 | 0.20 | 0.27 | 0.46 |
| ledgers-guide | 76 | 297 | 0.45 | 0.74 | 0.09 | 0.30 | 0.03 | 0.37 |
| platform-guide | 103 | 212 | 0.19 | 0.80 | 0.36 | 0.11 | 0.40 | 0.45 |

The median api-reference page has **2 words of prose**: it is frontmatter plus generated attribute
tables. Any prose or structure rule applied there fires on nothing or fires on noise. So the plan
scopes all structural rules to the three guide areas and leaves api-reference to the API-truth
checks, which is the inverse of where revision 1 put its attention.

---

## 2. Severity model

Three grades, defined by what a reviewer is expected to do, each with a precision floor that gates
promotion. Precision is measured by blind A/B adjudication (§6) on head pages, not asserted.

| Grade | Reviewer contract | Precision floor | Exit code | Promotion evidence |
| --- | --- | --- | --- | --- |
| strict | must fix before merge | ≥ 0.98 | non-zero | deterministic check against a machine-readable source, or ≥ 0.99 corpus conformance with named counterexamples |
| moderate | must look, may decline with a reason | ≥ 0.85 | zero | area conformance ≥ 0.80 in frozen and discriminating (< 0.40 in at least one other area) |
| flexible | advisory, no action required | ≥ 0.60 | zero | measurable pattern, no established norm |

Rules that cannot reach their floor are demoted, not deleted; a rule that cannot reach 0.60 is cut.
Every finding carries `severity`, `rule`, `line`, `col`, `end_col`, evidence, and the caret already
implemented in `stylecheck.py`. No finding carries a suggested rewrite except where the fix is
mechanical and unique (fence tag, capitalization, link form) — the existing `fix:` field.

Two output modes: `--mode report` (always exit 0, everything) and `--mode gate` (exit non-zero on
strict only). Gate mode is what CI uses; report mode is what a reviewer reads.

---

## 3. Content-pattern rules, derived

Every candidate below carries the frozen base rate, the discrimination against other areas, and the
proposed grade. Candidates that failed measurement are listed in §3.4 so the plan records what was
killed and why.

### 3.1 Structure

| Candidate | Measured | Proposed grade | Notes |
| --- | --- | --- | --- |
| Guide pages introduce an example with prose before the first fence | 0.70 payments / 0.74 ledgers / 0.80 platform, 0.20 api-reference | moderate, guides only | strongest discriminator found |
| Step headings follow one form per project | payments uses `3. Create a Payment Order`; platform uses `Step 3: Add your destination` | moderate, per-project | cross-project drift is real: both forms exist for the same task shape |
| Platform how-to opens with `Prerequisites` | 17 of 103 platform pages, first H2; near-zero elsewhere | flexible | frequent but not dominant |
| Payments overview page opens with `Overview` | 17 of 150 payments pages, first H2 | flexible | same |
| Walkthroughs are numbered when 3+ sequential actions exist | 0.36 platform / 0.17 payments / 0.09 ledgers | flexible | too low to be a norm anywhere |
| Fence language matches area convention | reference json 184; payments json 87 / curl 67; ledgers shell 117 / curl 37; platform sql 20 / shell 17 | already strict in `stylecheck.py` | `curl` and `bash` tags are the drift |

### 3.2 Continuity and consistency of examples

The cast of characters in examples is shared, which makes continuity checkable. On head, across 160
pages with examples: 319 distinct UUIDs, 121 of them used on more than one page, one used on 30
pages; 118 distinct entity names; 66 distinct amounts, dominated by `1000` (63), `10000` (48),
`5000` (36).

| Candidate | Measured | Proposed grade |
| --- | --- | --- |
| An identifier introduced on a page is reused consistently within that page (no silent substitution between request and response) | continuity graph is buildable; per-page violation rate to be measured in phase 2 | strict if precision holds, else moderate |
| A shared entity name is spelled one way | `Kenner, Bach and Ledeen` (15) vs `Kenner, Bach & Ledeen` (9) — a real inconsistency in a shared cast member | moderate |
| New pages reuse the existing cast rather than inventing a new persona | 121 of 319 identifiers already cross-page; single-use personas are the tail | flexible |
| Amounts follow the established magnitudes | 6 values cover the majority of 66 | flexible |

### 3.3 Maintainability

Restatement is measurable once table markup is excluded. Reference pages repeat attribute-table rows
by design (one row string appears on 37 pages); that is generation, not restatement. Prose-only, on
head: 2,414 long paragraphs, **261 exact repeat groups**, 13 of them crossing repos, and **121
near-duplicate pairs** at Jaccard ≥ 0.6 over 5-word shingles.

Concrete instances, all from the corpus:

- The warehouse-destination setup paragraph appears on 14 platform pages verbatim.
- "Create a ledger using the Create Ledger endpoint …" appears on 11 pages.
- Two ledger tutorials share a balance-locking paragraph at 0.93 similarity.
- The API-keys instruction is duplicated between `account-collection-pre-built-ui.md` and
  `embed-payment-flow.md` at 0.94.

| Candidate | Measured | Proposed grade |
| --- | --- | --- |
| Paragraph repeated verbatim on N+ pages should be a reusable block | 261 groups; threshold N to be set so the flag count is reviewable, not exhaustive | moderate |
| Near-duplicate explanation (Jaccard ≥ 0.9, prose only) is drift between copies | 121 pairs at ≥ 0.6; the ≥ 0.9 tail is where copies have diverged | moderate |
| Restated concept that another page owns should be a link | needs an ownership model (which page is canonical); candidate generation works, the recommendation half does not yet | flexible, phase 3 |
| Referenced custom block does not exist | ledgers `<SandboxDetails />`, platform `<EarlyAccess />` — both referenced, neither defined | **strict**, deterministic |
| Defined custom block is never used | payments 5 unused of 8 (incl. `PaymentOrderStateMachine`), platform 5 unused of 8 | flexible, repo-level not page-level |

Reuse is barely adopted today — 16 defined blocks, 26 total usages across 682 pages — which is the
argument for the recommendation, and also the reason the recommendation must be advisory.

### 3.4 Candidates killed by measurement

- **"A request example is followed by its response."** 269 fences contain `curl`; only 81 are followed
  by a JSON fence. Not a norm. Would have been a high-volume false-positive generator.
- **Page archetype clustering.** Superseded by area (§1.1); clustering would have learned the same
  four groups plus a label the checker cannot verify.
- **Structure and prose rules on api-reference pages.** Median 2 words of prose.
- **Offline link resolution as a gate.** See §5.1: precision 0.23.
- **The claim that the published spec is unusable for field checks.** Retracted; see §4.2.

---

## 4. Technical truth, deterministic

Sources of truth, all machine-readable, all in the monorepo except the first:

| Source | Location | What it can decide |
| --- | --- | --- |
| Published ReadMe OpenAPI | `docs-readme-platform/reference/modern-treasury-api.json` | path and method existence; inlined request and response schemas (§4.2) |
| Monorepo swagger | `platform/swagger/v1/swagger.yaml` | request body fields, required fields, types, enums, response shapes |
| rswag schemas | `platform/spec/rswag/schemas/` | same, at finer grain |
| Event registry | `platform/config/events/registry.yml` | 147 valid `resource.name` webhook events |
| AASM models | e.g. `platform/app/models/payment_order.rb` | 13 states, 39 transitions, terminal states |

Measured on head, with the normalizer in `dev/corpus/probe_api_truth.py`:

| Check | Measurement | Proposed grade |
| --- | --- | --- |
| Endpoint exists | 59 distinct references / 330 occurrences; 319 matched; 8 unmatched, every one explainable: env-var placeholders (`<ORG_USDC_INTERNAL_ACCOUNT_ID>`), a literal `<endpoint>`, `/ping`, and two URLs joining query params with `&` instead of `?` — the last two are real defects | strict |
| Request body field exists | 186 docs payloads match an operation with a request schema; **4 fields the schema rejects** (`currency` on `POST /ledgers` ×3 — the schema accepts only `name`, `description`, `metadata`; `include_payment_flow` on `PATCH /invoices/{id}`). Claims `api.unknown_fields`, `api.unknown_field_names`: closed-schema validation under `jsonschema`, cross-checked by `ajv`, both agreeing | strict |
| Required field present | 58 operations publish a `required` list; **2 payloads omit one** (`currency` on `POST /ledger_accounts`, two ledgers tutorials). Claim `api.missing_required` — revision 3 said 0, which was an extractor artifact (§4.6) | strict, no marker needed |
| Enum value valid | swagger has 331 enums; not yet measured against docs literals | strict, phase 2 |
| Webhook event name valid | naive dotted-token matching: 223 candidates, 18 valid — unusable. Code-span-only: 48 candidates, 18 valid — precision 0.375. **Code span + registry resource prefix + event word in the same sentence: 3 flagged** (`payment_order.auto_ledgered`, `ledger_account_settlement.finished_processing` ×2 — the registry name is `finish_processing`). Claim `events.invalid_in_docs`, re-derived from a markdown-it token walk. That setting alone flags a fourth, `external_account.verification_status`, which is a *field*; the rule therefore also has to subtract the resource's own schema properties (§4.6) | strict at the contextual setting, field names subtracted |
| Object state name valid | 13 AASM states; states referenced on 32 pages | strict |
| State narrative consistent with the machine | 39 transitions; the only terminal state is `cancelled`. `completed` is **not** terminal (`reverse`, `mark_as_returned`, `uncomplete`, `mark_as_failed` all leave it) — so any page calling `completed` final is provably wrong | strict, via §7.3 |

The normalizer is the load-bearing piece: before it, 0 of 330 endpoint references matched, because the
published spec is rooted at `/` while the monorepo swagger prefixes `/api`. That is exactly the class
of error that makes a checker look impressive and be wrong, so it gets its own property tests (§7.1).

### 4.1 Execution, not just comparison

Comparison cannot catch a body that the schema accepts and the API rejects, and it cannot tell which
of two disagreeing source artifacts is right. The harness in `dev/audit_methods/execute_curl.py` does
both by replaying documented examples against a sandbox organization; §4.7 is the executed result.
This stays **harness-only**: the shipped checker never makes API calls, because it would need
credentials and would turn a docs review into a side-effecting operation. What ships from this work is
the recorded expectation, not the executor.

### 4.2 Retraction: the published spec does carry schemas

Revision 2 claimed the published spec could only decide path existence, because
`components.schemas` is empty. That was wrong, and it was wrong in the direction that matters — it
would have made monorepo access a hard prerequisite for checks that do not need it.
`dev/corpus/probe_spec_divergence.py` measures what each source can actually answer:

| Source | Operations | With a request body schema |
| --- | ---: | ---: |
| Monorepo swagger | 183 | 69 |
| Published spec | 206 | 79 |
| Either | — | 87 |
| Both | — | 61 |

The published spec has no components because it is fully **inlined**, not because it has no schemas.
Monorepo access is still the right default — it is generated from the code, so it cannot drift — but
the published spec is a usable fallback for the 26 operations the swagger cannot answer, and it is the
only source that covers the 45 published operations absent from the swagger.

### 4.3 Spec divergence is itself a finding

Of the 61 operations both sources describe, **22 disagree** on the accepted top-level fields: 17 where
the published spec omits a field the code accepts, 8 where it claims a field the code does not. Worst
case is `POST /expected_payments`, missing 17 fields including `direction`, `currency` and
`counterparty_id`. `PATCH /external_accounts/{id}` documents `external_id` and `ledger_account_id`,
which the code does not accept.

This needs no docs page to trigger and no judgment to adjudicate: two artifacts in the repo contradict
each other. Grade strict, reported against the published spec file, and it is the cheapest real value
in this plan.

### 4.4 The ReadMe limitation, decided by execution

The published spec is hand-maintained because some endpoints break ReadMe, and the ask is to detect
that before a monorepo PR lands rather than after the docs diverge. The evidence points at reference
cycles: an inliner cannot terminate on a cyclic schema, and the published file is fully inlined.

`dev/corpus/probe_readme_limit.py` detects cycles properly — on the current reference path, not
"this `$ref` appeared already", since a schema reusing `address` twice is not recursive. 5 of 151
component schemas are cyclic: `child_legal_entity`, `child_legal_entity_create`,
`legal_entity_association`, `legal_entity_association_inline_create_request`, `return`.

| Operation reaches a cyclic schema | Sources disagree | Sources agree | Disagreement rate |
| --- | ---: | ---: | ---: |
| yes | 6 | 2 | **0.75** |
| no | 16 | 37 | 0.30 |

Every cyclic disagreeing operation is a legal-entity, payment-order or return write — the exact
endpoints Eric named. But that is correlation over 8 operations, so revision 3 planned the check rather
than asserting it.

**Now executed.** `dev/readme_limit/probe.js` runs ReadMe's own tooling over the generated swagger and
records a verdict per step (`dev/readme_limit/verdict.json`):

| Step | Verdict |
| --- | --- |
| `rdme openapi validate` | **passes** — "is a valid OpenAPI API definition" |
| `oas-normalize.validate` | passes |
| `oas-normalize.bundle` | passes, 109 paths |
| `oas-normalize.dereference` | passes, 109 paths — the cycle survives as a JS object graph |
| serialize the dereferenced document to JSON | **fails**: `Converting circular structure to JSON … property 'items' closes the circle` |

So the limitation is not a validity failure, which is why "just publish the generated spec" looks like
it should work and doesn't. Validation, bundling and dereferencing all succeed; what fails is writing
the dereferenced document out — and the published file is precisely a fully inlined JSON document. The
failure is per-operation and enumerable: **22 operations cannot be serialized after dereferencing**,
every one a legal-entity, counterparty, invoice, payment-order, return or bulk-result operation, and 21
of the 22 exist in the hand-maintained published spec (`DELETE /legal_entity_associations/{id}` is the
one absent altogether).

Re-bucketing §4.3's divergence by that executed predicate instead of by my own cycle detector:

| Operation fails serialization | Sources disagree | Sources agree | Disagreement rate |
| --- | ---: | ---: | ---: |
| yes | 8 | 3 | **0.73** |
| no | 14 | 36 | 0.28 |

Two consequences, both now grounded:

1. The check is **decidable and belongs in the monorepo**, not in the docs skill: dereference the
   generated swagger and attempt serialization; any operation that throws will not publish and its
   reference page must stay hand-maintained. The diagnostic can name the closing property, which is
   what a schema author needs.
2. The migration path is real. The 87 operations that serialize cleanly can move to the generated spec;
   the 22 that don't stay hand-written until the cycles are broken (bounded depth, or a `$ref`-preserving
   published spec, which ReadMe supports and the current file does not use).

Both tables are reproducible: `dev/readme_limit/probe.js` writes the verdict, `rate.py` re-buckets
§4.3's divergence by it, and claims `readme.deref_succeeds`, `readme.serialization_fails` and
`readme.serialization_failures` re-run the whole thing inside the oracle. Note the second claim expects
a *failure* — if a future oas-normalize serializes cleanly, the claim goes unconfirmed and this section
is wrong rather than quietly stale.

Still not established: that ReadMe's hosted pipeline fails at the same step as its published libraries.
That needs an upload attempt against a ReadMe project, which needs an API key.

### 4.5 Partial examples: measured, not decided in the abstract

D2 asked for a marker for deliberately incomplete examples, because a required-field check cannot tell
a trimmed illustration from a defect. `dev/corpus/probe_partial_examples.py` measures both halves.

**Request payloads almost never omit a required field**: of 184 payloads matched to an operation with
a `required` list, 2 are missing one — `currency` on `POST /ledger_accounts`, in
`quickstart-for-card-products.md` and `quickstart-for-investment-platforms.md` (15 more could not be
matched to an operation and are excluded). Omission rate 0.011. So the request-side check is buildable
today at strict grade, and the marker is not on its critical path.

Revision 3 reported 0 omissions from 76 payloads. Both numbers were wrong for the same reason, and it
is the reason this section is worth reading: see §4.6.

**There is no existing convention**, and the shape of the evidence says the problem lives in
*responses*, not requests:

| Form in use | Occurrences | Example |
| --- | ---: | --- |
| comment naming omitted fields | 15 | `// Target amount is specified; base amount is omitted` |
| prose ("abridged", "truncated") | 4 | `close-an-internal-account.md` |
| bare `...` line in JSON | 3 | `reference/Topics/webhooks/payment-orders.md` |
| `"..."` as a value | 3 | `mount-embeddable-flow.md` |

25 usages across 682 pages, in four mutually incompatible forms, all of them in response or webhook
payloads. So this is a convention to *establish* on the style page rather than a norm to derive, and
the recommendation is the form that is already most idiomatic in a JSON body — a bare `...` line, which
also reads as invalid JSON to any tool that tries to parse it, making the truncation impossible to
miss. `"..."` as a value is the form to rule out: it parses, so a checker silently reads it as a real
string value.

Approved uses, to be stated as rules with examples: omitting optional fields to keep the illustration
focused (no marker needed, this is the common case); truncating a long collection or a nested object in
a *response* (marker required); showing one variant of a polymorphic body (marker not needed, but the
variant must be named in the prose). Not approved: omitting a required field from a request example, or
truncating anything the surrounding prose then refers to.

---

### 4.6 What the independent oracle changed

`dev/verify/verify_claims.py` recomputes each claim by a route the probe does not use: corpus counts
from `git ls-tree` at the manifest revision rather than the extracted tree; field and required-field
decisions by JSON Schema validation under `jsonschema` **and** `ajv` rather than a property-name set
difference; the state count from swagger's `payment_order.status` enum, an artifact the AASM parser
never reads; event names from a markdown-it token walk rather than a regex over raw text; divergence
by per-field accept/reject rather than set comparison; links by live HTTP over every link rather than
over the prefilter's candidates. `dev/verify/properties.py` adds the Hypothesis properties for the two
functions able to fake a good result.

Current state: **16 of 16 claims confirmed**, after three of them were corrected. The corrections are
the point of the exercise, and none of them were visible to inspection:

| Claim | Revision 3 said | Independently derived | Cause |
| --- | --- | --- | --- |
| `api.missing_required` | 0 omissions / 76 payloads | **2 omissions / 184 payloads** | the payload extractor required a bare language token after the opening fence, so every ReadMe fence with a title (```` ```shell Create a ledger ````) was skipped — 110 of 186 payloads, and the two real defects among them |
| `events.invalid_in_docs` | 3 flagged, precision 1.0 | **3 flagged, after subtracting schema fields** | the contextual rule as stated also flags `external_account.verification_status`, a field of the object discussed in a sentence that legitimately mentions webhooks; the discriminator is the resource's own property list in swagger |
| `links.broken` | 7, prefilter recall high | **9, prefilter recall 0.78** | recall was estimated from a 40-link sample instead of measured; sweeping all links live found 2 more 404s that resolve offline |

One further defect came out of the injectivity property rather than any probe: the published spec
declares two endpoints twice under different parameter names
(`/ledger_transactions/{id}/versions` and `/ledger_transactions/{ledger_account_statement_id}/versions`;
`/invoices/{id}/...` and `/invoices/{invoice_id}/...`). Claim `spec.published_duplicate_paths`. It is a
contradiction inside one file, so it grades strict alongside §4.3.

What the oracle does **not** yet decide, and must not be read as confirming: enum literals, response
bodies, ReadMe's *hosted* pipeline (§4.4 executes the published libraries only), and every precision number for the content and
maintainability families. The closed schemas it builds are top-level-only, so "the schema rejects this
field" is verified while "the value has the right type" is not.

### 4.7 Sandbox execution, run

Revision 5 cut this on cost. Sandbox credentials were then provided, so it is built
(`dev/audit_methods/execute_curl.py`) and run: every documented request in the head corpus is replayed
against the Modern Treasury **sandbox** organization, reads only unless `--writes` is passed, with no
production credential and no destructive verb outside that flag.

The first run reported 9 findings that schema comparison could not see. That number was wrong, and
what made it wrong is the finding worth recording: a non-success response is not evidence of a
documentation defect. Four separate causes had to be split out of it before the yield meant anything.

| Verdict | Count | What it means |
| --- | --- | --- |
| `ok` | 61 | request accepted by the sandbox |
| `reference_missing_in_sandbox` | 87 | structured API error naming an object this sandbox does not hold — a fixture gap, not a docs defect |
| `not_executable_placeholder` | 98 | `<internal_account_id>`, `ORGANIZATION_ID`, `YOUR_KEY`: nothing to send |
| `not_executable_unparseable_body` | 19 | the body does not parse in any JSON dialect, so there is nothing to execute (this is what `json-parse` reports statically) |
| `not_executable_multipart` | 5 | `-F` form uploads; replaying them as JSON invents required-field errors |
| `route_missing` | 2 | HTML 404, i.e. no route matched at all |

Three execution bugs of my own were producing "defects" before the split: a non-greedy regex truncated
nested payloads at the first `}`; placeholder URLs lost their closing `>`, so the path was malformed;
and structured API errors were read as missing routes. The classifier now distinguishes a structured
API error from an HTML 404, and the body extractor is a string-aware brace scanner.

**Unique yield after the split: 2**, plus 3 in the reverse direction.

- `POST /payment_orders` sent without `type` — the schema comparison is field-name-only, so an omission
  is invisible to it.
- `GET /ledger_transactions/{id}/versions&created_at[gte]=…` — the query string opens with `&`, so the
  request is for a different path entirely; both instances 404. This is the second of the two defects
  §4 already found by normalization, now confirmed against the running API, and it is the evidence
  behind the shipped `url-query-separator` rule.
- Reverse direction, and the more interesting one: 3 examples the schema check calls
  `unknown_fields:currency` on `POST /ledgers` are **accepted** by the running API. The ledgers
  controller permits `currency`; the swagger component omits it. That is source/spec drift, and no
  amount of schema comparison could have told me which side was wrong.

So execution earns its place, but not as a rule the skill ships: it decides which *static* checks are
worth shipping, and it is the only method here that can adjudicate the spec against the code. The
shipped checker still makes no API calls.

---

## 5. Link truth

### 5.1 Offline resolution is a prefilter, not an oracle

762 internal links, 289 external, 16 anchors on head. Resolving internal targets against page slugs
offline (with `foo/index.md` publishing as `foo` — omitting that alone made 300+ good links look
dangling) leaves 30 unresolved. Checking all 30 over HTTP: **7 are genuinely 404, 23 return 200**.
Precision 0.23.

Recall is worse than revision 3 claimed. That number came from a control *sample* of 40
offline-resolvable links, none of which 404'd. Claim `links.broken` drops the prefilter entirely and
resolves **every** distinct internal link live: **9 are 404**, so the prefilter misses 2 of 9 and its
recall is 0.78, not 1.0. Both misses resolve offline and 404 live — `/docs/stablecoin-on-ramp` (the
link omits the `payments` project prefix) and `/platform/reference/create-a-counterparty` (a slug that
exists in git under a different published path). A slug existing in the repo does not mean the URL the
page links to exists.

Design that follows: the prefilter is an ordering heuristic, not a filter. Check flagged candidates
first, then sweep the remainder; report only confirmed 404s either way. The docs site rate-limits, so
the client needs backoff — a 429 must never be reported as a broken link.

Confirmed broken links on head today: `send-a-payout-over-local-rails`, `create-an-internal-account`,
`create-entity-link`, `delete-entity-link`, `list-entity-links`, `reversal-object`,
`create-user-onboarding`, `docs/stablecoin-on-ramp`, `platform/reference/create-a-counterparty`.

Grade: strict when the network is available, skipped with an explicit "unverified" line when not.
Never inferred from the offline result alone.

---

## 6. AI-assisted checks

Two things only, both because no machine-readable source can decide them:

1. **Claim verification.** A prose claim that contradicts the source (a stated default, an ordering, a
   limit). Input: the claim plus the authoritative snippet. Output: one line, pointer, verdict.
2. **Topic-level coverage.** Whether a page omits an operation or lifecycle topic its family
   establishes. Grounding, so this is not invention: the spec resource-to-operation map (50 resources,
   22 with any curl example on head) and sibling pages in the same directory. The warning names the
   missing topic and nothing else.

Output contract, enforced by the harness and by SKILL.md: severity `moderate` at most, one line per
finding, a pointer, no prose rewriting, no generated documentation, no more than N findings per page.
A finding that cannot name a concrete missing operation or a contradicted source snippet is dropped.

Evaluation is the same as for deterministic rules: blind adjudication against a labeled set, with a
precision floor. AI findings that cannot hold 0.85 are demoted to flexible or removed from the
prompt.

---

## 7. Validation harness

This section is the answer to "prove it isn't theater". None of it ships.

### 7.0 Which methods earn their weight

A harness can be theater too, so each method was run and judged on what it produced rather than on
how rigorous it sounds. Every row below is an executed result, in `dev/audit_methods/`; two methods
are cut and one is downgraded.

| Method | Executed evidence | Verdict |
| --- | --- | --- |
| Claim oracle (`dev/verify/verify_claims.py`) | corrected 3 of 16 claims: payloads 76 → 186, required-field omissions 0 → 2, broken links 7 → 9 | **earns it.** Only method that has caught a wrong number in the plan |
| Executed ReadMe predicate (`dev/readme_limit/`) | reversed the conclusion: the swagger *is* valid and dereferences; serialization is what fails, 22 operations enumerated | **earns it.** Correlation had the mechanism backwards |
| Hypothesis properties (`dev/verify/properties.py`) | 8 properties; injectivity found the two duplicate published paths and the titled-fence extractor bug class | **earns it, narrowly.** Covers the normalizer and extractors only — no property yet touches a rule's verdict |
| Mutation testing (`dev/audit_methods/mutate.py`) | 145 mutants of the checker's own decision points: 121 killed, 24 survived, kill rate **0.834**. Survivors included an untested boundary on `MAX_SENTENCE_WORDS` and on the 3-word prose floor. Successive fixtures took it to **0.950** on 181 mutants (§7.1) | **earns it.** The fixture suite was executing rules it did not test, and this is the only thing that showed it |
| Vacuity / non-universality / independence (`dev/audit_methods/guards.py`) | over 4,794 findings on 667 frozen pages: 4 rules never fire (`reference-no-shell` was not on the known-guard list), **7 rule/area pairs fire on more than half the pages** — `passive-voice` on 0.87 of payments and 0.76 of ledgers, `frontmatter-excerpt` on 0.71–0.89 — and 3 rule pairs coincide on the same line (`frontmatter-excerpt`/`frontmatter-title` at 1.00, `passive-voice`/`sentence-length` at 0.54) | **earns it, and it bites.** A rule firing on 87% of an area is a corpus description; that is a severity finding about the *shipped* checker, obtained for one cheap run |
| Differential jsonschema vs ajv, at current scope | 0 disagreements over the 199 extracted payloads (186 of which match an operation carrying a schema) — because both validators see schemas reduced to property names plus `required`. Agreement on a question this easy is not evidence | **downgraded.** Keep as regression insurance, invest nothing further at this scope |
| Extending the differential to types/enums/nesting (`dev/audit_methods/schema_scope.py`) | typed schemas raise violations 6 → 30 and surface 8 the current scope cannot see. Adjudicated: **1 true defect** (`amount: "499"` as a string on `POST /payment_flows`), 2 placeholder artifacts (`'<ISO currency code ie. USD>'` against the `currency` enum), 5 caused by the swagger's own `minProperties: 9`/`10` constraints, which contradict partial examples | **conditional.** Worth doing only after placeholder syntax is excluded and `minProperties` is dropped; otherwise precision is ~0.13 |
| TLA+ / Alloy model checking of state narratives | machine is 13 states, 39 transitions; every question the plan asks it (edge exists, path exists, state is terminal) is decided by a transitive closure in milliseconds, 0 temporal or fairness questions, and AASM guards are not extracted so there is nothing a temporal logic could see. Worse, the *binding* constraint is extraction: 15 candidate narratives in 682 pages, of which ~2 are genuine ordered claims (the rest are enumerations — "one of `pending`, `completed`, `returned`"), and the naive unknown-state-token check runs 1 true defect in 20 hits | **cut.** Replaced by (a) a differential parse — the regexes and `aasm_prism.rb`, which walks Ruby's own AST, agree exactly on 13 states and 39 transitions — and (b) a per-object state-name spelling check, whose one real find is `canceled` for `cancelled` in a ledgers page. Model checking would have been machinery around a question no page asks |
| Survivor classification against the corpus (`dev/audit_methods/mutation_survivors.py`) | each surviving mutant re-applied and run over all 682 pages, diffed against the baseline 5,038 findings: 4 of 15 changed what the checker reports on a real page (one of them by crashing), and each became a fixture. **All 9 remaining survivors are corpus-silent** | **earns it, with a limit.** It separates "untested decision" from "decision with no observable behaviour", which a kill rate cannot — but corpus-silence is not a reason to stop: 5 further survivors were killed by asking what the mutant would cost a reader instead (§7.1) |
| Sandbox `curl` execution (§4.7) | run, once credentials were provided: 272 documented requests, 150 executed, unique yield **2** after four confounded failure categories were split out of an initial 9 — plus 3 cases where the running API accepts a field the swagger rejects | **reinstated, and it earns it.** It is the only method that can adjudicate the swagger against the code, and it is what promoted `url-query-separator` |
| Blind A/B adjudication | not run | **still required.** It is the only source of the precision floors in §2, and the guards above just gave it its first concrete target: whether `passive-voice` at 0.87 page coverage is a diagnostic or wallpaper |
| difflib cross-check of duplication | not run; the duplication rule does not exist yet | **deferred**, decided when the rule exists |

The pattern in the cuts: the deterministic engines were never the weak link. Extraction is. Every
method that failed to earn its place failed because the claim it would decide cannot yet be extracted
from a page with acceptable precision, and no amount of proof machinery downstream fixes that.

### 7.1 Property tests (Hypothesis)

- Extractor: segment offsets are monotonic; every reported line exists in the source; resolved text
  never contains fence content.
- Endpoint normalizer: idempotent (`n(n(x)) == n(x)`); well-formed output; segment count and literal
  segments preserved, so nothing but an identifier can become `{id}`; injective on the spec paths **up
  to parameter renaming** — collapsing `{invoice_line_item_id}` onto `{id}` is intended, collapsing two
  paths whose literal segments differ is the failure that would make every API claim look true.
- Payload extractor: recovers the payload whatever title the fence carries, and is stable under JSON
  key reordering. Both written after the titled-fence bug in §4.6, which is exactly the class of defect
  a generated title strategy catches and an example-based test does not.

Status: implemented in `dev/verify/properties.py`, 8 properties passing. The remaining items below are
not yet written.
- Continuity graph: identifier extraction is stable under reformatting (whitespace, key order in
  JSON); the graph is acyclic where the docs express a creation order.
- Duplication metric: Jaccard is symmetric, 1.0 on identical input, and monotone under appending
  unrelated text.

### 7.2 Vacuity, non-universality, independence

Every rule ships with two witnesses in the fixture suite: a page it fires on and a page it must not
fire on. Plus two corpus-level guards:

- **Non-vacuous**: fires at least once on the frozen corpus, or is explicitly marked as a
  never-observed guard rule (the existing `link-anchor-empty` case).
- **Non-universal**: does not fire on more than a stated share of pages in its area. A rule that fires
  everywhere is a corpus description, not a diagnostic.
- **Independent**: pairwise finding overlap below a threshold, so two rules are not selling the same
  observation twice.

Implemented and run against the shipped checker (`dev/audit_methods/guards.py`, 4,794 findings over
667 frozen pages), and it does not come back empty:

| Guard | Threshold | Flagged today |
| --- | --- | --- |
| vacuity | never fires | `link-anchor-empty`, `list-depth`, `no-ordered-lists`, `reference-no-shell` — the first three are declared guard rules, the fourth was not |
| non-universality | > 0.5 of pages in an area | 7 pairs: `passive-voice` (payments 0.87, ledgers 0.76), `frontmatter-excerpt` (payments 0.89, platform 0.71, ledgers 0.67), `sentence-length` (ledgers 0.53), `body-h1` (ledgers 0.51) |
| independence | > 0.5 co-occurrence on a line | `frontmatter-excerpt`/`frontmatter-title` 1.00 (8 cases), `body-h1`/`heading-repeats-title` 0.67, `passive-voice`/`sentence-length` 0.54 |

Two consequences, both about rules that already ship. `frontmatter-excerpt` firing on 0.89 of payments
is not a diagnostic about a page, it is the backlog item Eric has not ruled on, and it should be
reported once per run rather than once per page. And `passive-voice` at 0.87 page coverage is the first
rule blind A/B has to adjudicate: at that base rate it either carries real precision or it is
wallpaper, and no amount of regex refinement answers which.

### 7.3 State narratives: closure, not model checking

Cut, and replaced by two cheaper things. Executed evidence in `dev/audit_methods/state_reach.py`:

- **Differential extraction instead of a model.** The machine is parsed twice — by the probe's regexes
  and by `aasm_prism.rb` walking Ruby's own AST — and the two agree exactly (13 states, 39
  transitions). That is what the state claims actually rest on.
- **Exhaustive closure instead of temporal logic.** 13 states is not a state space that needs
  checking: the closure gives terminals (`cancelled` only), reachability from `pending` (every state),
  and `completed`'s out-edges (`failed`, `held`, `returned`, `reversed`, `sent`, so "final" is false)
  by enumeration.
- **The real blocker is extraction, not decision.** Only 15 sentences in 682 pages contain two or more
  state words, and reading them shows ~2 are ordered claims; the rest are enumerations, and the
  "adjacent transition" verdict on them is coincidence. A naive unknown-state check is 1 true defect
  (`canceled` for `cancelled`) in 20 hits.

So the shipped check is a state-name spelling check scoped per object, at flexible grade, and the
sequence check is not built until an extractor can tell an ordered claim from a list.

### 7.4 Differential validation

- Schema decisions cross-checked between Python `jsonschema` and Node `ajv`; disagreement fails the
  harness. Implemented in `dev/verify/verify_claims.py` and `dev/verify/ajv_check.js`. Downgraded by
  §7.0: the two agree on every payload, but they are agreeing about property names, which is not a
  question two conforming validators can differ on. It stays as regression insurance and gets no
  further investment at this scope. Extending it to types, enums and nesting is worth one session
  *only* with placeholder syntax excluded and the swagger's `minProperties` artifacts dropped
  (`dev/audit_methods/schema_scope.py`), which is what takes that yield from ~0.13 precision to
  something promotable.
- Markdown structure cross-checked against markdownlint, as today.
- Duplication cross-checked against an independent implementation (`difflib` ratio) — different
  algorithm, same verdict required at the extremes.

### 7.5 Blind A/B

Protocol: sample findings from both the current checker and the candidate, strip rule names and
severities, shuffle, present as bare pointer plus evidence, and adjudicate "would a reviewer act on
this?" without knowing the source. Label store keyed by content hash so labels survive re-runs.
Scored as precision per rule and per grade, against the floors in §2. Sample size set for a ±0.1
interval at the floor, which is ~100 labels per grade.

### 7.6 Differential regression

The existing differential runner extends to the new checkers: every finding on the full corpus is
snapshotted; a change that alters any finding must either be explained in the disagreement table or
it fails.

Mutation testing is now run rather than planned, and it is a purpose-built mutator
(`dev/audit_methods/mutate.py`) rather than `mutmut`: it mutates only decision points inside
functions — comparisons, boolean connectives, dropped negations, thresholds, and the severity a rule
assigns — because module-level constants in this checker are generated Unicode tables, where a mutant
measures nothing. Baseline 0.834 on 145 mutants, now **0.950 on 181** (the new rules added decision
points), survivors listed in `dev/audit_methods/mutation.json`.

The harness had to be fixed before its output was evidence at all. Mutants are written to one path
inside one second, and `.pyc` invalidation is mtime plus size, so a mutant the same size as its
predecessor ran the predecessor's bytecode: two verdicts flipped per run, and an earlier 0.939 was an
artifact. Bytecode is now off and two consecutive runs return byte-identical survivor sets.

A kill rate on its own cannot say whether a survivor is an untested decision or a change with no
observable behaviour, so survivors are classified rather than argued about:
`dev/audit_methods/mutation_survivors.py` re-applies each one and runs the whole head corpus through
it, comparing every field of all 5,038 findings against the unmutated baseline.

| Verdict | Meaning | Count |
| --- | --- | --- |
| `corpus-visible` | findings differ on a real page — a genuine test gap, and that page is the fixture to write | 3, all now fixtured |
| `crashes` | the mutant raises, so the guard it altered is load-bearing | 1, now fixtured |
| `corpus-silent` | byte-identical findings over 682 pages | 9 |

Corpus-silence is not proof of equivalence and is not treated as permission to stop: five silent
survivors were killed anyway, by asking what the mutant would cost a reader rather than what it costs
today's corpus. An object at offset 0 discarded as "absent" (every `json` fence body starts there); the
string flag initialised true, which skips every malformed body silently; a zero-width span that renders
a caret row with no caret; any closing HTML tag ending an anchor, so `Click <b>here</b>` stops reading
as vague; and per-page grouping in the text report, which no single-file fixture can see.

The 9 that remain are defensive guards and presentation: `text.split("\n")` never returns an empty
list, so `not lines` is unreachable; `indent=2` in the JSON writer; the 8-row "most frequent" cap; a
JSON error line that normalization cannot push past the end of the body.

The gate: **no rule is promoted while a mutant of its own decision points survives visibly.**

---

## 8. Open decisions

All five are closed.

| # | Decision | Resolution |
| --- | --- | --- |
| D1 | Source of truth for API checks | The checkers read `platform/swagger/v1/swagger.yaml`, `spec/rswag/schemas/` and the published spec directly. No committed index, no cache, no second source of truth. The runtime is Devin in a session with both repos checked out, so "portable without the monorepo" was a constraint that does not exist. Divergence between the two specs becomes a finding rather than something to reconcile silently (§4.3), and §4.4 is now an executed answer rather than a hypothesis: 22 operations cannot be inlined, the other 87 can move to the generated spec, and the predicate belongs in the monorepo |
| D2 | Partial examples | No marker gates the request-side check: 2 of 184 matched payloads omit a required field, and both are real defects (§4.6). For responses, the convention is established rather than derived — a bare `...` line, with approved and unapproved uses stated as rules in the style pages (§4.5) |
| D3 | Gate or report | Written as a gate with `--mode gate`, invoked when Devin checks in a docs change, not as a GitHub required check. Default stays `report` until engineering approves the gate, so the same artifact serves both without a rewrite |
| D4 | Canonical-page ownership | Derived from the docs: directory position plus inbound internal links (762 available) elect the canonical page for a repeated topic. Flexible grade until the election is measured against the 261 repeat groups |
| D5 | Network for link checking | Assumed available, since this runs in a Devin session. Live confirmation is required for a 404 verdict; a 429 or a network failure reports "unverified", never "broken" |

---

## 9. Phases

1. **Corpus and measurement** (done): hydration, manifest, five probes, recorded measurements.
2. **Mining and thresholds**: continuity violation rate per page, duplication thresholds, enum
   coverage; set every threshold from data and record it.
3. **Harness first**: property tests, witnesses, vacuity/independence guards, A/B protocol and the
   first labeled set — before any shipped rule is written. Partly done: the claim oracle and the
   normalizer/extractor properties exist (§4.6, §7.1). Outstanding and the real gate on phase 4: the
   labeled sets and the blind adjudication, which is where every precision floor in §2 comes from.
4. **Deterministic checkers**: `apicheck.py` and `linkcheck.py` reading the specs directly, promoted
   rule by rule as each clears its floor. Spec divergence (§4.3) leads, since it needs no docs page and
   no adjudication.
5. **Content checker**: `contentcheck.py` for structure, continuity, maintainability, moderate-first.
6. **AI review step**: claim verification and coverage warnings, held to the output contract in §6.
7. **Style pages**: fold the derived conventions into `style/`, rules and examples only, no data.
