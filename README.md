# docs-style: evidence pipeline for the Modern Treasury docs style guide

Measures the documentation style that existed *before* machine-authored contributions began
(2026-03-13), so style rules can be stated with a conformance rate and real examples instead of
opinion.

Frozen corpus revisions (last commit on or before 2026-03-12):

| Repo | Revision |
|---|---|
| docs-readme-payments | `1f275577d8bcb9704ae211b3adaa8528b921fd7e` |
| docs-readme-ledgers | `e6fbd1280d3dbea3851fc9d22c0541e84fee15ce` |
| docs-readme-platform | `f5453f0cd6aebee27a20fc2506e514c51af62b` |

## Usage

```shell
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm

# materialize each repo at its frozen revision into <corpus>/<repo>/
git -C /path/to/docs-readme-payments archive <rev> | tar -x -C corpus/docs-readme-payments

.venv/bin/python extract.py --corpus corpus --out corpus.jsonl
.venv/bin/python stats.py --corpus corpus.jsonl --out report.md
.venv/bin/python stylometry.py --corpus corpus.jsonl --out stylometry.md
```

## Deliverables

- `skill/` — the guide and the tooling that applies it, and nothing else. `docs-review/` is the
  umbrella runner, the shared findings and reporting, the policy loader, the shared
  `config/policy.yaml`, and `style/` — the style guide itself, one page per file, which is the source
  of truth for the prose. The four subskills `docs-lint/`, `docs-content/`, `docs-maintain/` and
  `docs-test/` each carry their own `SKILL.md` and their own `config/rules.yaml`. Copy this directory
  as-is to install the skill.
- `dev/` — everything that verifies the checker but must not ship with it: `tests/` (fixtures plus the
  differential harness against markdownlint, emoji-regex and write-good), `build-notes/` (the
  measurements, stylometry go/no-go and tool-value record that produced the rules — kept out of the
  shipped skill on purpose), and the invariants a new rule has to keep. See `dev/README.md`.

## Files

- `extract.py` — markdown-it based extraction to one JSON record per doc: headings, paragraphs, list
  prose, fences, callouts, links, images, tables, frontmatter, genre.
- `stats.py` — descriptive statistics plus candidate rules, each with conformance rate, conforming
  and violating examples, and whether it is mechanically enforceable. Writes `report.md`.
- `stylometry.py` — go/no-go test for stylometric methods. Writes `stylometry.md`.
- `TOOL-VALUE.md` — which tools earn their place, with the measurement that decided it.
