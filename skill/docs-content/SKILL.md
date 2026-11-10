---
name: docs-content
description: Judge a Modern Treasury docs page against what the rest of the corpus does — continuity of a worked example across a guide sequence, page structure against pages of its kind, concepts taught before use, coverage of a documented surface. Reports nothing yet; the thresholds are gated on adjudicated labels.
---

# docs-content

The tier that needs the corpus. Continuity, consistency of teaching pattern, and coverage are not
properties of a file: they are properties of a file relative to the norms the other pages establish.

Part of `docs-review`; runs as `docs-review --only content`.

## Status: no rules

This subskill loads its policy, accepts every flag the others do, and reports nothing. That is
deliberate, and it is not a stub for missing effort.

Each candidate here has a measured base rate and no threshold. 261 verbatim-repeated prose groups and
121 near-duplicates at Jaccard ≥0.6 describe what the corpus looks like; they do not say what a page
should look like. A rule fired at those rates would flag the majority of pages, which is a description
of the corpus wearing a finding's clothes — the shipped `passive-voice` (87% of payments pages) is the
standing example of what that costs a reader.

Thresholds come from blind adjudicated labels, per Phase 3 of the plan, and no rule is admitted here
without a measured base rate, witnesses that fire and do not fire, boundary fixtures, and a mutation
kill rate matching the rest of the skill. Until then an empty run is the honest one.

## Run

```bash
python3 scripts/content.py <path>            # a run that is honestly empty
python3 scripts/content.py --list-rules      # empty table, with the policy hash
```

Flags match `docs-lint`: `--project`, `--strict-only`, `--format`, `--rule`, `--list-rules`. Exit
status 0, because no strict rule can fail.

## Where the rules will come from

`config/rules.yaml` beside this checker, merged over `../docs-review/config/policy.yaml` — the same shape every subskill uses.
A candidate becomes real by getting a row there with a severity and a threshold, and by passing the
admission gate — not by being coded.
