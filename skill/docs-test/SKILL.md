---
name: docs-test
description: Check Modern Treasury JSON examples against a supplied offline OpenAPI field and enum inventory. Snapshot absence is not proof of a documentation error; endpoint validity, runtime behavior and other technical claims need independent verification.
---

# docs-test

The tier that needs something outside the docs repos: the monorepo spec, an HTTP request, or a
sandbox org. Everything here is a factual claim with an authority to check it against, which is why
these rules need no adjudication — a wrong field name is not a matter of taste.

Part of `docs-review`; runs as `docs-review --only test`. Excluded from a pre-commit run by default,
because it is the tier that can be slow or offline.

## Offline snapshot

`openapi-field-exists` compares scoped MT JSON examples with an offline inventory.
Supply `--spec PATH` or `DOCS_REVIEW_SPEC` (the flag wins). No snapshot or a missing
file reports `not run: no spec snapshot` in the log and scorecard, without
blocking other review rules. Malformed supplied JSON is an input error. There
is no default path, network fetch, clone or authentication requirement.

Other probes remain future work. What the measurement found:

- **Constrained strings the spec leaves free** — `"document_type": "proof_of_addres"` is published and
  the API returns 422, while swagger types the field as a bare nullable string. The real domain is a
  Ruby constant, so this rule reads the code, not only the spec. Provably undetectable by typed schema
  validation, which makes it the highest-value rule in this tier.
- **Example against schema, typed and nested** — beyond property names: types, enums, nesting.
  `amount: "499"` as a string on `POST /payment_flows` is the true positive; `<ISO currency code ie.
  USD>` placeholders and the spec's own `minProperties` constraints are the false positives to exclude
  before it ships, or precision is ~0.13.
- **Identity collisions between guides** — `us_ssn 111222333` published for three different people, so
  the second guide a reader follows 422s. Only execution produces this.
- **Enum, event-name and endpoint existence** — set differences against the spec and the registry.
- **Documented state transitions** against the AASM machine (13 states, 39 transitions).
- **Links** — offline resolution measured 0.23 precision, so the shipped form is the live HTTP sweep.

## Sandbox credentials

Execution is opt-in and constrained (the plan's D9). One org, configured in this skill's config file —
not `.env`, and never written into a report:

- The instance must be `app.moderntreasury.com`. `demo.moderntreasury.com` is refused.
- The key must begin `test-`. A live key is refused, and a response indicating live mode aborts the run.
- A 4xx naming a missing org-level prerequisite is reported as environment-dependent, not as a docs
  defect. That distinction, not a second org, is what separates a real finding from a misconfigured
  sandbox — it is the reason an earlier "the documented flow is unfollowable" finding was retracted.

## Run

```bash
python3 scripts/apicheck.py <path> --spec snapshot.json
python3 scripts/apicheck.py --list-rules
```

Flags match `docs-review`. Exit 0 with no strict findings, 1 with strict findings,
2 for invalid input. This inventory does not validate examples against individual endpoints.
