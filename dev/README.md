# Development checks

The target runtime is Python 3.10. Keep installed skills and development checks
compatible with 3.10; also verify under Python 3.12.

Install the dependencies in `requirements-gate.txt`, then run
`python3 -m pytest -q -p no:cacheprovider` from the repository root.
Corpus-dependent gate evidence requires an explicit `DOCS_CORPUS_ROOT`.
