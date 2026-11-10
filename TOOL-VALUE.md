# Tool value matrix: what earns its place in the style-guide system

Rule for inclusion: a tool stays only if it produces a deliverable nothing cheaper produces, and the
evidence for that is measured on the frozen pre-2026-03-13 corpus (667 docs; 312 guides, 344
`reference/**` pages). Anything that fails its test is dropped, not demoted to "nice to have".

| Tool | Unique deliverable | Measured evidence | Verdict |
|---|---|---|---|
| Conformance counting (`extract.py` + `stats.py`) | Turns every guideline into a rule with a real conformance rate and named conforming/violating docs | 32 candidate rules generated, each with counts and examples; surfaced 13 split practices the current guide gets wrong or omits | **Keep — core** |
| Vale | Enforces rules on every PR without a human reading the doc | 27 of 32 candidate rules are mechanically checkable (fence languages, callout set, vague link text, filler terms, `MT` shorthand, currency form, heading skips) | **Keep — core** |
| spaCy | Measures the voice rules the existing guide asserts but never quantified: passive voice, tense, person, imperative openings | Produced the passive 28% / imperative 5% / `will` 913 / second-person 2,239 vs first-person-plural 755 measurements the tense-and-person rules rest on | **Keep — supporting** |
| Burrows's Delta (unsupervised distance to corpus centroid) | Was intended to be the off-style detector | Delta AUC 0.471 vs `reference/**`, 0.322 vs post-cutoff machine-authored docs, 0.463 vs unrelated engineering markdown — at or below chance, and no better than a sentence-length baseline | **Drop** |
| Supervised function-word classifier | Same detection goal, strong form of the test (5-fold CV on 200-token windows) | AUC 0.917 separating our docs from unrelated engineering markdown, but 0.436 vs post-cutoff docs written for our own docs site | **Drop for detection; keep only as a "is this text even ours" tripwire** |
| Embeddings / LLM similarity | Not tested | No labeled set exists yet to test against | **Not adopted** |

## Why stylometric distance fails here, in plain terms

Function-word stylometry identifies *authors of long, freely written text*. Our corpus is the
opposite: short pages (median doc is a few hundred words of prose), heavily templated, and written
by many hands to a shared house voice. The supervised result is the useful one — the features can
tell our docs from someone else's engineering README (AUC 0.92), but they cannot tell a well-written
new page from an off-style one, because both use the same function words in the same proportions.

Two corrections were needed before this conclusion could be trusted, and both are in the script:

1. Score equal-length 200-token windows, not whole documents; otherwise Delta mostly measures page
   length.
2. Restrict features to function words. Using the top-150 words outright made the "detector" a topic
   classifier that scored off-topic text as *more* on-style than our own pages.

## What replaces the stylometry-based detector

Detection ("docs that don't fit our style") is delivered as a per-doc conformance scorecard: each doc
is scored against the measured rules, with the specific failing lines cited. That is more accurate
than any distance score we could produce here, and unlike a distance score, it tells the writer what
to fix. The three original goals still land:

1. **Author in the correct style** — genre style profiles plus a prompt pack, both generated from the
   measured corpus.
2. **Improve style** — split practices (13 of them) are the explicit improvement agenda; the report
   ranks them by how much of the corpus each decision would change.
3. **Detect off-style docs** — rule scorecard in CI via Vale, not stylometric distance.
