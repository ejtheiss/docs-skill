---
name: docs-test
description: Verify that a Modern Treasury docs page's technical claims are true — request and response examples against the OpenAPI schema, endpoint paths, enum and constrained-string values, webhook event names, documented state transitions, and links. Reports nothing yet; needs the monorepo, the network, or an approved sandbox org.
---

# docs-test

The tier that needs something outside the docs repos: the monorepo spec, an HTTP request, or a
sandbox org. Everything here is a factual claim with an authority to check it against, which is why
these rules need no adjudication — a wrong field name is not a matter of taste.

Part of `docs-review`; runs as `docs-review --only test`. Excluded from a pre-commit run by default,
because it is the tier that can be slow or offline.

## Status: no rules

Loads its policy, accepts every flag, reports nothing. The probes exist in the development harness and
the defect classes are measured; none has been admitted as a shipped rule yet.

What the measurement found, and what each becomes:

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
python3 scripts/apicheck.py <path>           # a run that is honestly empty
python3 scripts/apicheck.py --list-rules     # empty table, with the policy hash
```

Flags match `docs-lint`. Exit status 0, because no strict rule can fail.
