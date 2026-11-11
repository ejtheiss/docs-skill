# Reviewer judgment rubric

These candidate-rule ids are **reviewer judgment**, NOT reported rules. They do
not appear in `rules.yaml`, checker findings or strict/flexible scores. A reviewer
must inspect the evidence and log each accept/reject decision as one JSONL label
line for the Phase 3 adjudication set. Missing evidence is a reject pending
verification, not permission to invent product behavior.

| Candidate rubric id | One-line test | Deciding evidence |
|---|---|---|
| `guarantee-scoped-to-evidence` | Does each guarantee name its scope and exceptions? | Product contract, bank/rail limitations and linked source supporting the exact claim |
| `step-actor-marked` | Does each step identify customer API call, Modern Treasury transition, or bank-driven work? | Endpoint caller, documented state machine and bank/network responsibility |
| `ledger-entries-balance` | Do debits and credits balance within each currency and name the affected accounts? | Complete entry amounts, currencies and account directions, not a net total across currencies |
| `psp-byob-scoped` | Does the claim distinguish PSP from bring-your-own-bank behavior? | Product configuration, supported bank capabilities and applicability documentation |
| `no-invented-fields` | Does every field, enum and event exist in the relevant contract? | Exact schema pointer, current spec or verified event documentation |
| `webhook-per-async-transition` | Does each asynchronous dependency have a documented event gate before the next step? | Event name, correlation field, resulting state and documented ordering; verified polling alternative where no event exists |
| `idempotency-where-retry-moves-money` | Is retry behavior safe wherever repeating the action can move money? | Endpoint idempotency contract, key scope/lifetime and failure/retry semantics |
| `money-losing-mistake` | Could following the page lose, duplicate or misroute money: yes or no? | Amounts, account direction, authorization, retry and failure-path trace; yes means reject, no means accept with rationale |

For the other candidates, accept means the test is satisfied by evidence; reject
means a violation or an evidence gap. The label does not claim the whole page is
correct. Never mark accept merely because a checker is silent.

## JSONL label schema

One JSON object per line. All fields below are required; unknown fields are
rejected. Hash exact UTF-8 input bytes with SHA-256. A case is the complete review
input (page, proposed change and evidence bundle); page_hash identifies the page
version independently of that case.

| Field | Type and constraint |
|---|---|
| `case_hash` | 64 lowercase hexadecimal SHA-256 characters |
| `page_hash` | 64 lowercase hexadecimal SHA-256 characters |
| `rubric_id` | One candidate id in the table above |
| `decision` | `accept` or `reject` |
| `rationale` | Nonempty string explaining the evidence and decision; money-losing-mistake records yes/no here |
| `reviewer` | Nonempty reviewer identifier, identifying the actual human or model |
| `timestamp` | ISO 8601 datetime with a timezone, for example `2026-11-10T12:00:00Z` |
| `policy_id` | 12 lowercase hexadecimal characters from the review's policy stamp, without the `policy ` prefix |

The helper validates shape, not the truth of the evidence, the hashes' provenance
or reviewer identity. Preserve the reviewed inputs separately. Historical policy
ids are allowed so labels remain usable after policy changes.

```shell
python3 scripts/rubric_label.py label.json --out phase-3-labels.jsonl
```

Use `-` instead of `label.json` to read one label from standard input. The output
directory must already exist. Invalid input is rejected before the log is opened.
The helper appends a label; it never edits a documentation page or adds a rule to
the checker.
