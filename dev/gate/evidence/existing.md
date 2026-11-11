# Admission-gate evidence

Corpus: `/home/ubuntu/work/corpus-head`; policy 8601df99863b.
Checker arguments: `[]`.
Mutations include neighboring decisions within mapped functions; all fixture findings are asserted.

## fence-language

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 36 / 179 | 81 | within base-rate limit |
| ledgers | 14 / 69 | 51 | within base-rate limit |
| platform | 1 / 103 | 1 | within base-rate limit |
| reference | 0 / 358 | 0 | within base-rate limit |
| total | 51 / 709 | 133 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/currencies/use-multiple-currencies.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 1 boundary; real-checker pytest passed.
Mutation: 27/27 killed = 1.000; bar ≥0.950: PASS
Two bytecode-disabled runs: identical survivor sets.

Survivors:
- None.

Gate 5 (independent oracle): NOT ESTABLISHED by this harness.
Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.

## filler

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 56 / 179 | 83 | within base-rate limit |
| ledgers | 35 / 69 | 67 | REJECT/DEMOTE (>50%) |
| platform | 28 / 103 | 41 | within base-rate limit |
| reference | 25 / 358 | 35 | within base-rate limit |
| total | 144 / 709 | 226 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Accounts/account-reconciliation/balances-used-in-account-reconciliation.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/custom_pages/support.md`

Fixtures: 1 positive, 1 negative, 1 boundary; real-checker pytest passed.
Mutation: 23/23 killed = 1.000; bar ≥0.950: PASS
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
