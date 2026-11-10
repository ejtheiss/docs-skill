---
name: docs-maintain
description: Find duplication and reuse debt across the Modern Treasury docs repos — repeated regions that should be a link or a ReadMe reusable block, undefined or orphaned block references, duplicate pages, and the same claim published in several wordings. Reports nothing yet; the exact-match checks are the next admitted rules.
---

# docs-maintain

The tier that needs all three repos at once. Whether a paragraph should be a reusable block, whether a
block reference resolves, and whether the same statement has drifted into four wordings are questions
about the corpus as a whole, so no single-file run can decide them.

Part of `docs-review`; runs as `docs-review --only maintain`.

## Status: no rules

Loads its policy, accepts every flag, reports nothing. What is measured but not yet admitted:

- **Undefined block references** — `EarlyAccess` (×8, platform) and `SandboxDetails` (×1, ledgers) are
  referenced and never defined. Decidable, no threshold needed, first in line.
- **Orphaned blocks** — 10 defined and unused, one of them (`BYOBDislcaimer`) a typo of the block 8
  pages actually use, which is why near-miss names are reported next to orphans rather than separately.
- **Duplicate pages and `copy-of-*` slugs** — decidable.
- **Repeated regions** — 261 verbatim groups, one on 14 pages; ranked by `(occurrences − 1) × length`.
- **Near-duplicates** — 121 at Jaccard ≥0.6; needs a threshold, so needs labels.
- **Wording drift** — the same claim in several wordings. Blocks do not resolve across repos, so this
  is the only thing keeping cross-repo statements aligned.

Two modes, per the plan's D8: a one-time corpus-wide sweep, then an incremental check of the changed
pages against the existing block inventory before a docs commit. The incremental exact-match case
needs no thresholds, so it can ship ahead of the near-duplicate work.

What this subskill will never decide is the remedy. Merge, trim and blockify depend on SEO, product
intent and editorial taste, and the reusable-content proposal's own verdicts differ per group. The
checker reports duplication ranked by cost and suggests a block boundary where one is computable; a
human picks the remedy.

## Run

```bash
python3 scripts/maintain.py <path>           # a run that is honestly empty
python3 scripts/maintain.py --list-rules     # empty table, with the policy hash
```

Flags match `docs-lint`. Exit status 0, because no strict rule can fail.

## Not in this subskill

OpenAPI publishability is not a docs question. The 22 operations whose dereferenced spec does not
serialize are a property of `platform/swagger/v1/swagger.yaml`, and belong to a monorepo PR gate: a
docs-side checker would see the damage after it shipped rather than the cause. Validating a page's
example against the schema is `docs-test`, not here — it is per-page verification.
