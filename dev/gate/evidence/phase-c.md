# Admission-gate evidence

Corpus: `/home/ubuntu/work/corpus-head`; policy e4db8909fade.
Checker arguments: `["--names", "dev/gate/fixtures/customer-names.txt"]`.
Mutations include neighboring decisions within mapped functions; all fixture findings are asserted.

## leak-internal

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
| payments | 0 / 179 | 0 | within base-rate limit |
| ledgers | 0 / 69 | 0 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 0 / 358 | 0 | within base-rate limit |
| total | 0 / 709 | 0 | — |

Firing witness: `none (inactive or corpus-silent)`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 2 boundary; real-checker pytest passed.
Mutation: 40/40 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## leak-names

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
| payments | 0 / 179 | 0 | within base-rate limit |
| ledgers | 0 / 69 | 0 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 0 / 358 | 0 | within base-rate limit |
| total | 0 / 709 | 0 | — |

Firing witness: `none (inactive or corpus-silent)`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 4 boundary; real-checker pytest passed.
Mutation: 12/12 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## openapi-field-exists

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 28 / 179 | 278 | within base-rate limit |
| ledgers | 19 / 69 | 62 | within base-rate limit |
| platform | 2 / 103 | 186 | within base-rate limit |
| reference | 28 / 358 | 288 | within base-rate limit |
| total | 77 / 709 | 814 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-tutorials/bill-payments-copy-1.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 28 / 179 | 278 | within base-rate limit |
| ledgers | 19 / 69 | 62 | within base-rate limit |
| platform | 2 / 103 | 186 | within base-rate limit |
| reference | 28 / 358 | 288 | within base-rate limit |
| total | 77 / 709 | 814 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-tutorials/bill-payments-copy-1.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 1 boundary; real-checker pytest passed.
Mutation: 23/23 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): see independent raw-key / enum-array confirmation below.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## reuse-undefined-block

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 0 / 179 | 0 | within base-rate limit |
| ledgers | 1 / 69 | 1 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 8 / 358 | 8 | within base-rate limit |
| total | 9 / 709 | 9 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-sandbox-overview.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 0 / 179 | 0 | within base-rate limit |
| ledgers | 1 / 69 | 1 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 8 / 358 | 8 | within base-rate limit |
| total | 9 / 709 | 9 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-sandbox-overview.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 2 boundary; real-checker pytest passed.
Mutation: 19/19 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): see independent raw-key / enum-array confirmation below.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## Corpus manifest

```text
docs-readme-payments 72421e2857f11bfa0d7b71819e59fbde65f6e54f (origin/v2.0)
docs-readme-ledgers 683c1df2c275bce4a1207b5c43b234f6948dec07 (origin/v2.0)
docs-readme-platform 5f5f385f3b5406e597774e2ce9122b6b7f8f599a (origin/v2.0)
```

## Independent OpenAPI confirmation

Spec: `/home/ubuntu/work/corpus-head/docs-readme-platform/reference/modern-treasury-api.json`; SHA256 `4d548c71bd296e21d511a256870802dc0b7c42b61d5fcbf98390aebfe7942225`.
Raw key / enum-array oracle: 814/814 agreement = 1.000.
Literal raw-text absence only: 0.835; enum strings in examples/prose are not enum declarations.
This confirms absence from this snapshot, NOT a documentation error or endpoint validity. No blind adjudication claim.

## OpenAPI top 10 diagnostic groups

| Kind | Value | Findings | Representative path:line |
|---|---|---:|---|
| field | `content_type` | 81 | /home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/index.md:393 |
| field | `source` | 81 | /home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/index.md:396 |
| field | `size` | 80 | /home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/index.md:391 |
| field | `document_details` | 80 | /home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/index.md:403 |
| enum | `posted` | 59 | /home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-tutorials/bill-payments-copy-1.md:189 |
| enum | `residential` | 52 | /home/ubuntu/work/corpus-head/docs-readme-payments/docs/Bring your own Bank/share-legal-entity-data-with-banks/index.md:106 |
| field | `regulators` | 48 | /home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/index.md:429 |
| field | `compliance_details` | 48 | /home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/index.md:465 |
| field | `industry_classifications` | 48 | /home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/index.md:474 |
| field | `third_party_verification` | 48 | /home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/index.md:475 |

Findings cluster in Ledgers and webhook event envelopes, consistent with snapshot gaps, but snapshot absence alone cannot distinguish gaps from stale or incorrect docs. In particular, `posted`, `residential`, file attributes and webhook `event` require contract verification, not automatic doc edits. MT curl literal JSON is supported; shell variables, non-JSON bodies and unanchored/third-party JSON are excluded. Metadata and schema-declared free-form maps are excluded by policy.

## Undefined component confirmation

{"EarlyAccess": 8, "SandboxDetails": 1}
Escaped angle-bracket placeholders and fenced/inline examples are not component uses.

## Customer-name measurements
Fixture names are test data, not a default customer list. Wyoming can be legitimate public content.
### empty-review
| Project | Pages fired / pages | Findings |
|---|---:|---:|
| payments | 0/179 | 0 |
| ledgers | 0/69 | 0 |
| platform | 0/103 | 0 |
| reference | 0/358 | 0 |
### empty-draft
| Project | Pages fired / pages | Findings |
|---|---:|---:|
| payments | 0/179 | 0 |
| ledgers | 0/69 | 0 |
| platform | 0/103 | 0 |
| reference | 0/358 | 0 |
### fixture-review
| Project | Pages fired / pages | Findings |
|---|---:|---:|
| payments | 0/179 | 0 |
| ledgers | 0/69 | 0 |
| platform | 0/103 | 0 |
| reference | 0/358 | 0 |
### fixture-draft
| Project | Pages fired / pages | Findings |
|---|---:|---:|
| payments | 0/179 | 0 |
| ledgers | 0/69 | 0 |
| platform | 0/103 | 0 |
| reference | 0/358 | 0 |

## code-span-adjacent: measurement-only candidate
NOT ADMITTED: measurement only; independent semantic oracle and adjudicated precision absent. Adjacent enum/options spans are not inherently errors.
Definition: lexical single-backtick spans separated only by whitespace or nothing, within one prose/table block; fences, frontmatter and comments excluded. The raw `` `a``b` `` spelling is counted lexically even though CommonMark can parse it as one span.
| Project | Pages fired / pages | Pairs |
|---|---:|---:|
| payments | 1/179 | 8 |
| ledgers | 0/69 | 0 |
| platform | 0/103 | 0 |
| reference | 3/358 | 4 |
Firing witness: /home/ubuntu/work/corpus-head/docs-readme-payments/docs/Bring your own Bank/share-legal-entity-data-with-banks/legal-entities-at-cross-river-bank.md
Non-firing witness: /home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md
`business_registeredprimary` caught: False. It is one span, not adjacent spans.
Real corpus cell witnesses: [{'path': '/home/ubuntu/work/corpus-head/docs-readme-payments/docs/Customer Onboarding/onboard-a-business/required-fields-for-businesses.md', 'line': 136, 'text': 'Array of [Addresses](https://docs.moderntreasury.com/platform/reference/address-object) - P.O. boxes are not accepted with `address_type` of `business_registeredprimary` marked as `false`', 'caught': False}]
No shipped rule id, mutation threshold or admission claimed for this measurement-only candidate. Concatenated-identifiers candidate was not implemented.

## Gate scope and admission qualifications
Mutations target the mapped verdict functions; extraction, schema traversal and repository discovery are covered by integration fixtures and direct tests, not claimed as mutation-covered.
Corpus leak-internal and leak-names rates are zero: no real firing witness exists; positive fixtures provide firing examples. Neither names list is a universal ban.
The independent oracle confirms snapshot absence only; no blind human adjudication or runtime API confirmation was performed. The four requested checks ship as strict inventory/leak checks, not as proofs that the documentation is factually wrong.
