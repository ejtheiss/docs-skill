# Admission-gate evidence

Corpus: `/home/ubuntu/work/corpus-head`; policy cc311b98b5af.
Checker arguments: `[]`.
Mutations include neighboring decisions within mapped functions; all fixture findings are asserted.

## Phase A interpretation

Reproduction:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 dev/gate/gate.py \
  --rule fence-language --rule callout-emoji --rule link-absolute-internal \
  --rule filler --rule image-alt --rule em-dash --rule body-h1 \
  --rule reference-no-shell --corpus-mode review --corpus-mode draft \
  --out dev/gate/evidence/phase-a.md --jobs 6
```

All eight mutation rates clear 0.950; survivor sets are identical twice.
The command exits 1 because filler fires on 37/69 Ledgers pages (53.6%) in
both modes. It remains reported flexible, not promoted to strict or admitted.
Independent oracles and blind adjudication remain unestablished.

Review measurements have no base; body-h1 and image-alt are intentionally
inactive there, so firing witnesses exist only in draft. Draft activates new
on every file. Git-backed fixtures independently cover new, existing, touched
and untouched content; context tests cover exact line sets and error paths.

Policy choices:

- Only the first fence-info token is the language. Non-request shell commands
  are allowed solely through non_request_fences, pending Eric's decision.
- Approved component icon/theme pairs are measured independently of attribute
  order and quoting; fixtures include character entities and variation selectors.
- Platform guides and API reference are separate projects, matching the baseline.
  Relative file links use the current project's namespace. index.md suggestions
  use the parent slug; URL fragments are preserved.
- Markdown and HTML tables are excluded from em-dash prose. The HEAD card
  reference page has three table em dashes (reference/Payments/card/index.md,
  lines 22, 23, 68), including a stand-alone missing-value marker. Paragraphs,
  headings and component prose are checked; code and frontmatter are not.
- Leverage noun exemptions are lexical policy patterns, not a POS-model oracle.
  Mixed noun/verb fixtures ensure a noun exemption does not suppress a later verb.
- A heading-free page has no first body heading to violate body-h1; no synthetic
  missing-heading finding is emitted. heading-skip remains independently active.
- A multiline image is touched when any line of its syntax changes.

Survivor interpretation (all retained in the denominator):

- The shared context survivors change Git's --end-of-options token and enable
  SequenceMatcher autojunk. They are corpus-silent in both no-base measurements;
  this is not a claim of equivalence for arbitrary --base diffs or refs.
- The callout survivor changes selector normalization of the sanctioned YAML
  values, none of which currently contains a selector. It is corpus-silent in
  both modes. Component and blockquote input normalization mutants are killed.

## body-h1

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 0 / 179 | 0 | within base-rate limit |
| ledgers | 0 / 69 | 0 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 0 / 358 | 0 | within base-rate limit |
| total | 0 / 709 | 0 | — |

Firing witness: `none (inactive or corpus-silent)`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 86 / 179 | 86 | within base-rate limit |
| ledgers | 8 / 69 | 8 | within base-rate limit |
| platform | 38 / 103 | 38 | within base-rate limit |
| reference | 27 / 358 | 27 | within base-rate limit |
| total | 159 / 709 | 159 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/account-reconciliation/balances-used-in-account-reconciliation.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 4 boundary; real-checker pytest passed.
Mutation: 54/56 killed = 0.964; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- `string-L38-99fc7031ec24`: corpus-silent **True** ({'review': True, 'draft': True})
- `boolean-constant-L48-297642e1a8a5`: corpus-silent **True** ({'review': True, 'draft': True})

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## callout-emoji

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 8 / 179 | 10 | within base-rate limit |
| ledgers | 2 / 69 | 3 | within base-rate limit |
| platform | 7 / 103 | 12 | within base-rate limit |
| reference | 6 / 358 | 6 | within base-rate limit |
| total | 23 / 709 | 31 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-tutorials/marketplace-tutorial.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 8 / 179 | 10 | within base-rate limit |
| ledgers | 2 / 69 | 3 | within base-rate limit |
| platform | 7 / 103 | 12 | within base-rate limit |
| reference | 6 / 358 | 6 | within base-rate limit |
| total | 23 / 709 | 31 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-tutorials/marketplace-tutorial.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 2 boundary; real-checker pytest passed.
Mutation: 23/24 killed = 0.958; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- `string-L1004-731d6108c482`: corpus-silent **True** ({'review': True, 'draft': True})

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## em-dash

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 14 / 179 | 25 | within base-rate limit |
| ledgers | 0 / 69 | 0 | within base-rate limit |
| platform | 2 / 103 | 8 | within base-rate limit |
| reference | 5 / 358 | 8 | within base-rate limit |
| total | 21 / 709 | 41 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/index.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 14 / 179 | 25 | within base-rate limit |
| ledgers | 0 / 69 | 0 | within base-rate limit |
| platform | 2 / 103 | 8 | within base-rate limit |
| reference | 5 / 358 | 8 | within base-rate limit |
| total | 21 / 709 | 41 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/index.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 1 boundary; real-checker pytest passed.
Mutation: 8/8 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## fence-language

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 24 / 179 | 83 | within base-rate limit |
| ledgers | 13 / 69 | 78 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 3 / 358 | 4 | within base-rate limit |
| total | 40 / 709 | 165 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/currencies/index.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 24 / 179 | 83 | within base-rate limit |
| ledgers | 13 / 69 | 78 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 3 / 358 | 4 | within base-rate limit |
| total | 40 / 709 | 165 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/currencies/index.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 1 boundary; real-checker pytest passed.
Mutation: 39/39 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## filler

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 58 / 179 | 86 | within base-rate limit |
| ledgers | 37 / 69 | 71 | REJECT/DEMOTE (>50%) |
| platform | 29 / 103 | 45 | within base-rate limit |
| reference | 26 / 358 | 38 | within base-rate limit |
| total | 150 / 709 | 240 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/account-reconciliation/balances-used-in-account-reconciliation.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 58 / 179 | 86 | within base-rate limit |
| ledgers | 37 / 69 | 71 | REJECT/DEMOTE (>50%) |
| platform | 29 / 103 | 45 | within base-rate limit |
| reference | 26 / 358 | 38 | within base-rate limit |
| total | 150 / 709 | 240 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/account-reconciliation/balances-used-in-account-reconciliation.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 1 boundary; real-checker pytest passed.
Mutation: 27/27 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## image-alt

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 0 / 179 | 0 | within base-rate limit |
| ledgers | 0 / 69 | 0 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 0 / 358 | 0 | within base-rate limit |
| total | 0 / 709 | 0 | — |

Firing witness: `none (inactive or corpus-silent)`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 34 / 179 | 84 | within base-rate limit |
| ledgers | 7 / 69 | 9 | within base-rate limit |
| platform | 17 / 103 | 83 | within base-rate limit |
| reference | 1 / 358 | 1 | within base-rate limit |
| total | 59 / 709 | 177 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/account-reconciliation/balances-used-in-account-reconciliation.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 5 boundary; real-checker pytest passed.
Mutation: 51/53 killed = 0.962; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- `string-L38-99fc7031ec24`: corpus-silent **True** ({'review': True, 'draft': True})
- `boolean-constant-L48-297642e1a8a5`: corpus-silent **True** ({'review': True, 'draft': True})

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## link-absolute-internal

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 70 / 179 | 193 | within base-rate limit |
| ledgers | 28 / 69 | 52 | within base-rate limit |
| platform | 22 / 103 | 54 | within base-rate limit |
| reference | 17 / 358 | 33 | within base-rate limit |
| total | 137 / 709 | 332 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/account-reconciliation/index.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 70 / 179 | 193 | within base-rate limit |
| ledgers | 28 / 69 | 52 | within base-rate limit |
| platform | 22 / 103 | 54 | within base-rate limit |
| reference | 17 / 358 | 33 | within base-rate limit |
| total | 137 / 709 | 332 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/account-reconciliation/index.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 3 boundary; real-checker pytest passed.
Mutation: 16/16 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## reference-no-shell

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 0 / 179 | 0 | within base-rate limit |
| ledgers | 0 / 69 | 0 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 3 / 358 | 4 | within base-rate limit |
| total | 3 / 709 | 4 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-platform/reference/Payments/return-object/index.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 0 / 179 | 0 | within base-rate limit |
| ledgers | 0 / 69 | 0 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 3 / 358 | 4 | within base-rate limit |
| total | 3 / 709 | 4 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-platform/reference/Payments/return-object/index.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 2 boundary; real-checker pytest passed.
Mutation: 39/39 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## Corpus manifest

```text
docs-readme-payments 72421e2857f11bfa0d7b71819e59fbde65f6e54f (origin/v2.0)
docs-readme-ledgers 683c1df2c275bce4a1207b5c43b234f6948dec07 (origin/v2.0)
docs-readme-platform 5f5f385f3b5406e597774e2ce9122b6b7f8f599a (origin/v2.0)
```
