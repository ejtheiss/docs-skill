# Admission-gate stand-in

Self-contained development harness for PLAN-subskills §3 and PLAN-phases' rule gate.
The original `dev/tests`, adjudication and mutation harness was not pushed; this
uses only `dev/gate` and never becomes a shipped dependency. Python 3.12+, the
checker's dependencies, and `python3 -m pip install -r dev/requirements-gate.txt`
are required.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest dev/gate/tests -q -p no:cacheprovider
python3 dev/gate/gate.py --rule fence-language --rule filler --out dev/gate/evidence/existing.md
```

`DOCS_GATE_CORPUS` defaults to `~/work/corpus-head`. Keep the three repo names in
its paths for project inference; `reference/` is a fourth project, matching the
checker. The manifest is included in evidence. Add mode/names-file tokens using
`--checker-arg=--mode --checker-arg=value --checker-arg=--names-file --checker-arg=/path`.
Arguments reach corpus, fixture, mutant and survivor runs unchanged. Output-format
and findings-filter flags are refused. The current checker need not support future
options yet; unsupported arguments fail loudly.

Add rule/function mappings and required boundary names in `rules.yaml`, then
positive/negative/boundary Markdown and `expectations.json` in `fixtures/<rule>/`.
Expectations assert target-rule lines and complete findings (without file paths),
including neighboring rules, so mutations to shared functions are not silently
ignored. Existing snapshots were captured from the real checker and inspected;
they are regression tests, **not independent confirmation**. There are no numeric
thresholds in the two initial rules; fixtures cover table aliases, canonical,
unknown and empty fence tags; case/info suffixes; every filler entry, replacement,
deletion, all `just` exception alternatives, word boundaries and code exclusions.

Mutations are single AST edits within mapped functions, including helpers. Every
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

The isolation test rejects imports and executable references to `dev/`. Existing
shipped comments, docstrings and YAML provenance already mention the external
harness and are exempt; this does not assert their literal absence or edit them.
