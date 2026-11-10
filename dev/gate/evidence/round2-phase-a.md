# Admission-gate evidence

Corpus: `/home/ubuntu/work/corpus-head`; policy 96408a85051c.
Checker arguments: `[]`.
Mutations include neighboring decisions within mapped functions; all fixture findings are asserted.

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

Fixtures: 2 positive, 2 negative, 2 boundary; real-checker pytest passed.
Mutation: 8/8 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## filler

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 56 / 179 | 83 | within base-rate limit |
| ledgers | 35 / 69 | 67 | REJECT/DEMOTE (>50%) |
| platform | 28 / 103 | 41 | within base-rate limit |
| reference | 26 / 358 | 36 | within base-rate limit |
| total | 145 / 709 | 227 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/account-reconciliation/balances-used-in-account-reconciliation.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 56 / 179 | 83 | within base-rate limit |
| ledgers | 35 / 69 | 67 | REJECT/DEMOTE (>50%) |
| platform | 28 / 103 | 41 | within base-rate limit |
| reference | 26 / 358 | 36 | within base-rate limit |
| total | 145 / 709 | 227 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/account-reconciliation/balances-used-in-account-reconciliation.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 1 boundary; real-checker pytest passed.
Mutation: 27/27 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## marketing-words

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 3 / 179 | 3 | within base-rate limit |
| ledgers | 3 / 69 | 4 | within base-rate limit |
| platform | 3 / 103 | 4 | within base-rate limit |
| reference | 1 / 358 | 2 | within base-rate limit |
| total | 10 / 709 | 13 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-tutorials/digital-wallet-event-handler.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 3 / 179 | 3 | within base-rate limit |
| ledgers | 3 / 69 | 4 | within base-rate limit |
| platform | 3 / 103 | 4 | within base-rate limit |
| reference | 1 / 358 | 2 | within base-rate limit |
| total | 10 / 709 | 13 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-tutorials/digital-wallet-event-handler.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 2 positive, 2 negative, 2 boundary; real-checker pytest passed.
Mutation: 18/18 killed = 1.000; bar ≥0.950: PASS
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
