# Admission-gate stand-in

## Phase C

```sh
export DOCS_CORPUS_ROOT=/path/to/materialized-corpus
PYTHONDONTWRITEBYTECODE=1 python3 dev/gate/gate.py \
  --rule openapi-field-exists --rule reuse-undefined-block \
  --rule leak-names --rule leak-internal \
  --corpus-mode review --corpus-mode draft \
  --checker-arg=--names --checker-arg=dev/gate/fixtures/customer-names.txt \
  --checker-arg=--spec --checker-arg="$DOCS_CORPUS_ROOT/docs-readme-platform/reference/modern-treasury-api.json" \
  --out dev/gate/evidence/phase-c.md --jobs 8
PYTHONDONTWRITEBYTECODE=1 python3 dev/gate/phase_c.py dev/gate/evidence/phase-c.md
```

The supplement independently checks raw spec keys and enum arrays, measures empty
and fixture names lists, confirms undefined-block counts, and measures the
development-only adjacent-code-span candidate. It records the spec SHA256.
Both commands require an explicit corpus root. Ordinary pytest uses only
vendored fixtures and does not run these corpus-scale measurements.
Mutation mappings cover verdict functions; direct/integration tests cover the
extractors and inventory loaders. Neither oracle agreement nor the strict grade
establishes runtime API correctness or blind-adjudicated precision. A zero-rate
leak rule has no real corpus firing witness; its positives are fixture witnesses.
Fixture cases marked `isolated` replace run-level checker arguments so that
no-list/empty-list behavior remains testable during a names-enabled corpus run.

Self-contained development harness for PLAN-subskills §3 and PLAN-phases' rule gate.
The original `dev/tests`, adjudication and mutation harness was not pushed; this
uses only `dev/gate` and never becomes a shipped dependency. Python 3.12+, the
checker's dependencies, and `python3 -m pip install -r dev/requirements-gate.txt`
are required.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest dev/gate/tests -q -p no:cacheprovider
python3 dev/gate/gate.py --rule fence-language --rule filler --out dev/gate/evidence/existing.md
python3 dev/gate/gate.py --rule image-alt --rule body-h1 --corpus-mode review --corpus-mode draft --out dev/gate/evidence/contexts.md
```

Corpus evidence is opt-in: set `DOCS_CORPUS_ROOT` to a materialized corpus
directory (`DOCS_GATE_CORPUS` is an explicit compatibility alias). There is no
home-directory default. Keep the three repo names in
its paths for project inference; `reference/` is a fourth project, matching the
checker. The manifest is included in evidence. Add mode/names-file tokens using
`--checker-arg=--mode --checker-arg=value --checker-arg=--names-file --checker-arg=/path`.
Arguments reach corpus, fixture, mutant and survivor runs unchanged. Output-format
and findings-filter flags are refused. The current checker need not support future
options yet; unsupported arguments fail loudly.

Repeat `--corpus-mode` to measure review and draft separately in one report.
Without it, the passthrough mode (or review by default) is preserved. Draft
activates the `new` context on every corpus page. Fixture-local arguments override
passthrough arguments so review/no-base and draft boundaries remain testable in
the same run. `--jobs` (default 4) bounds parallel isolated mutant pytest runs.

Add rule/function mappings (or multiple source/function `targets`) and required boundary names in `rules.yaml`, then
positive/negative/boundary Markdown and `expectations.json` in `fixtures/<rule>/`.
Expectations assert target-rule lines and complete findings (without file paths),
including neighboring rules, so mutations to shared functions are not silently
ignored. Existing snapshots were captured from the real checker and inspected;
they are regression tests, **not independent confirmation**. There are no numeric
thresholds in the two initial rules; fixtures cover table aliases, canonical,
unknown and empty fence tags; case/info suffixes; every filler entry, replacement,
deletion, all `just` exception alternatives, word boundaries and code exclusions.

Mutations are single AST edits within mapped functions, including helpers. Context
unit tests run alongside rule fixtures, covering exact changed-line sets, span
boundaries, missing files, invalid bases, and draft/new behavior. Every
mutant runs the fixture pytest suite twice with bytecode disabled, against an
isolated skill copy (the source tree is never rewritten). All generated mutants
remain in the kill-rate denominator, including equivalent and neighboring-rule
mutants. Surviving mutants are compared on complete rule-specific corpus findings,
not just counts. Stable ids and both survivor sets are saved in JSON. Logs and
skill copies remain in ignored `evidence/run-*` directories for inspection.

Evidence includes rates, deterministic lexicographic witnesses, fixture counts,
mutation rates and corpus-silence. Exit 1 means base rate >50%, missing witness or
mutation rate <0.950; invalid configuration/checker/fixtures abort rather than
yielding evidence of success. Gates 5 (independent oracles) and 6 (blind labels)
are explicitly **not established**, so even exit 0 is not full rule admission.

A rule deliberately inactive in review/no-base has no firing witness in that
mode; the report says so rather than inventing one. At least one firing and one
non-firing witness must exist across the requested modes.

The isolation test rejects imports and executable references to `dev/`. Existing
shipped comments, docstrings and YAML provenance already mention the external
harness and are exempt; this does not assert their literal absence or edit them.
