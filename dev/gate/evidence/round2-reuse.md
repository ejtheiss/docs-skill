# Admission-gate evidence

Corpus: `/home/ubuntu/work/corpus-head`; policy 72ec529aacde.
Checker arguments: `[]`.
Mutations include neighboring decisions within mapped functions; all fixture findings are asserted.

## reuse-undefined-block

### review

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 0 / 179 | 0 | within base-rate limit |
| ledgers | 1 / 69 | 1 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 0 / 358 | 0 | within base-rate limit |
| total | 1 / 709 | 1 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-sandbox-overview.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-platform/reference/Payments/reconciliation-rule-object/create-reconciliation-rule.md`

### draft

| Project | Pages fired / pages | Findings | Gate 1 |
|---|---:|---:|---|
| payments | 0 / 179 | 0 | within base-rate limit |
| ledgers | 1 / 69 | 1 | within base-rate limit |
| platform | 0 / 103 | 0 | within base-rate limit |
| reference | 0 / 358 | 0 | within base-rate limit |
| total | 1 / 709 | 1 | — |

Firing witness: `/home/ubuntu/work/corpus-head/docs-readme-ledgers/docs/Get Started/ledgers-sandbox-overview.md`
Non-firing witness: `/home/ubuntu/work/corpus-head/docs-readme-platform/reference/Payments/reconciliation-rule-object/create-reconciliation-rule.md`

Fixtures: 1 positive, 1 negative, 2 boundary; real-checker pytest passed.
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

## Original nine page paths

- `docs-readme-ledgers/docs/Get Started/ledgers-sandbox-overview.md`: SandboxDetails
- `docs-readme-platform/reference/Payments/reconciliation-rule-object/create-reconciliation-rule.md`: EarlyAccess
- `docs-readme-platform/reference/Payments/reconciliation-rule-object/delete-reconciliation-rule.md`: EarlyAccess
- `docs-readme-platform/reference/Payments/reconciliation-rule-object/get-reconciliation-rule.md`: EarlyAccess
- `docs-readme-platform/reference/Payments/reconciliation-rule-object/index.md`: EarlyAccess
- `docs-readme-platform/reference/Payments/reconciliation-rule-object/list-reconciliation-rules.md`: EarlyAccess
- `docs-readme-platform/reference/Payments/reconciliation-rule-object/move-reconciliation-rule.md`: EarlyAccess
- `docs-readme-platform/reference/Payments/reconciliation-rule-object/update-reconciliation-rule.md`: EarlyAccess
- `docs-readme-platform/reference/Topics/webhooks/bulk-result-webhooks.md`: EarlyAccess

Hosted-block confirmation: Eric supplied the 2026-11-10 browser DOM and .md export observation; not independently repeated in this run.
