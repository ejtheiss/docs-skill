---
name: docs-lint
description: Lint one Modern Treasury docs page against the style guide's mechanical rules — frontmatter, headings, code fences, JSON bodies, links, object names, currency notation, prose mechanics. Use when writing or editing a page in docs-readme-ledgers / docs-readme-payments / docs-readme-platform, or when a pre-commit check needs the fast tier that reads nothing but the changed files.
---

# docs-lint

The tier that needs nothing but the file. Every rule here is decidable from the page's own bytes, so
a run costs one read per file and can gate a commit.

Part of `docs-review`; run it directly for the fast path, or `docs-review --only lint` for the same
findings inside the umbrella's log.

## Run

```bash
pip install markdown-it-py PyYAML                        # once
python3 scripts/lint.py <path-to-page-or-dir>            # everything
python3 scripts/lint.py <path> --strict-only             # only what must be fixed
python3 scripts/lint.py <path> --format json             # machine-readable
python3 scripts/lint.py <path> --rule filler --rule mt-shorthand
python3 scripts/lint.py --list-rules                     # every rule, severity, source, policy hash
```

Exit status: 1 when a strict rule fails, 2 for a bad invocation — an unknown `--rule`, or a path whose
project cannot be inferred with no `--project` given.

`--project` takes `ledgers`, `payments`, `platform` or `reference`; the checker infers it from the
path, so pass it only outside a repo checkout. Three rules are project-scoped: `contractions`
(platform guides), `reference-no-shell` and `no-ordered-lists` (API reference).

## Where the rules come from

Nothing in `scripts/lint.py` decides policy. Every severity, threshold, word list and scope is read
at import from `config/rules.yaml` beside this checker and `config/language.yaml` it includes, merged
over `../docs-review/config/policy.yaml`. `language.yaml` holds the facts about English, Unicode and
ReadMe's renderer — participles, abbreviations, emoji codepoints — which are not Modern Treasury
decisions and would otherwise be 100 lines of tables inside the checker. Finding messages live with
their rules; only the `fix` stays in code, because a fix transforms the page's own text.
Each report and `--list-rules` stamps the resulting policy id, so a
finding can be traced to the policy it was decided under.

A wrong severity or a missing word is an edit to `config/rules.yaml`, never a code edit. The checker
refuses to run — rather than falling back to a default — when the artifact is missing, unreadable,
malformed, or missing a rule or table a rule needs: a linter that guesses a threshold reports a number
nobody chose.

Markdown is parsed with `markdown-it-py` and frontmatter with `PyYAML`, not with regexes over lines.
Do not "simplify" that away: a line scanner disagreed with a real CommonMark parser on 18 of 667
corpus pages, every disagreement a false finding (fences in HTML table cells, headings inside list
items, list continuation depth, nested `metadata.title` shadowing the page title).

## Rules

`--list-rules` prints the authoritative table with the artifact hash. In summary:

Strict: `frontmatter-title`, `body-h1`, `heading-skip`, `heading-formatting`,
`heading-repeats-title`, `fence-untagged`, `fence-language`, `list-depth`, `link-anchor-empty`,
`link-anchor-vague`, `link-bare-url`, `image-alt`, `callout-emoji`, `mt-shorthand`,
`object-shorthand`, `object-capitalization`, `currency-mixed`, `json-parse`, `url-query-separator`.

Flexible: `fence-language-unknown`, `frontmatter-excerpt`, `link-absolute-internal`,
`sentence-length`, `passive-voice`, `filler`, `filler-please`, `contractions`, `acronym-undefined`,
`reference-no-shell`, `no-ordered-lists`.

`frontmatter-excerpt` reports an excerpt that is *present*: Modern Treasury does not use them, so the
finding is the field to delete, and a page without one is correct. 167 corpus pages still carry one,
which is a cleanup list rather than a gate. `passive-voice` skips a passive that names its actor —
"initiated by the bank" is what the finding asks for — and stays flexible because only 62% [54, 71]
of the passives it reports were judged worth a writer's time.

`json-parse` reads every JSON fence and every `curl` body after removing the conventions the docs use
deliberately — `//` comments, trailing commas, `<placeholder>` values, a bare `...` line, an inline
`{ ... }`, a property fragment without its braces, a field-name list, two alternative bodies in one
fence. What remains is a body a reader cannot copy. `url-query-separator` fires on a documented URL
whose query string opens with `&`, which requests a different path.

## Fixing findings

Strict findings are not preferences: correct them in the change you are making. Flexible findings are
for a human to decide — fix when the alternative reads better, leave otherwise, and never bulk-apply.
Corpus-wide cleanups go one rule per change so the diff stays reviewable.

Nothing here rewrites a page. The checker reads and reports.
