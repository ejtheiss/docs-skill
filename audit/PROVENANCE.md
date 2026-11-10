# docs-lint audit — rule provenance

Audit of every rule in `skill/docs-lint/scripts/lint.py`. A rule stays only if it has a
source (an established implementation or an explicit Modern Treasury style decision), a fixture that
pins its behaviour, and a corpus count that is consistent with the docs actually being in that style.

Verification used three layers, in this order:

1. **Whiteboard invariants** — properties the checker must satisfy regardless of rule (below). Not in
   the checker; expressed as tests.
2. **Differential testing** against the tools each rule claims to mirror:
   `dev/tests/differential/differential.py` runs markdownlint 0.37, the `emoji-regex` package rdmd itself
   uses, and write-good 1.0.8 over the frozen 667-page corpus and fails on any disagreement that is
   not listed with a reason.
3. **Fixture regression** — `dev/tests/test_lint.py`, 189 cases: a positive and a negative fixture
   per rule, plus the parser edge cases that produced false positives during the audit.
4. **Mutation testing and survivor classification** (fifth and sixth audits): break the checker on
   purpose, then decide against the corpus whether each surviving mutant is an untested decision or a
   change with no observable behaviour.

Current state: 338/338 tests pass (189 lint fixtures), 0 unexplained differential disagreements,
mutation kill rate 0.955 on 177 mutants with every remaining survivor proven corpus-silent. Over the
head corpus: 682 pages, 5,038 findings (2,201 strict, 2,837 flexible).

Reproduce:

```bash
pip install markdown-it-py PyYAML
python3 -m unittest discover -s dev/tests
npm install --prefix dev/tests/differential
python3 dev/tests/differential/differential.py ~/style-corpus
python3 skill/docs-review/scripts/review.py ~/style-corpus --format json
```

## Invariants (whiteboarded, then written as tests)

| Invariant | Why it matters | Test |
|---|---|---|
| Code content never produces a prose finding | Fences and inline code contain `simply`, `in order to`, URLs | `test_code_content_never_produces_prose_findings` |
| A finding's line moves exactly with the text above it | Line numbers are the only thing a reviewer navigates by | `test_prepending_a_paragraph_shifts_every_line_by_the_same_amount` |
| Parsing is deterministic | A checker that reorders findings cannot gate anything | `test_parsing_is_deterministic` |
| Every finding's `strict` equals `RULES[rule][0]` | Severity cannot be decided at the call site | `test_every_finding_uses_a_registered_rule` |
| Every registered rule is reachable by a fixture | Dead rules are how invented rules survive | `test_every_registered_rule_is_reachable` |
| `--strict-only` output is a subset of full output | Otherwise the gate and the report disagree | `test_strict_only_is_a_subset`, `test_strict_only_hides_flexible_notes` |
| JSON and text report the same findings | Two renderers, one truth | `test_json_and_text_report_the_same_findings` |
| `--rule` filters, never mutates | Filtering must not change a message or line | `test_rule_filter_does_not_change_a_finding` |
| Overlapping inputs are counted once | `lint.py page.md dir/` must not double count | `test_duplicate_paths_are_counted_once` |
| Directory walk is markdown-only and sorted | Reproducible audits | `test_directory_traversal_is_markdown_only_and_ordered` |
| Unknown rule id and unresolvable project exit 2 | Silence about a bad invocation is worse than failing | `test_unknown_rule_id_is_a_usage_error`, `test_undetectable_project_is_a_usage_error` |

## Rules

`hits/pages` are over the frozen pre-2026-03-13 corpus (667 pages).

| Rule | Severity | Source | Oracle | hits/pages | Verdict |
|---|---|---|---|---|---|
| `frontmatter-title` | Strict | ReadMe: frontmatter `title` is the page h1 | — | 8/8 | Keep |
| `frontmatter-excerpt` | Strict | MT policy: excerpt is search/preview text | — | 496/496 | Keep, **but see backlog** |
| `body-h1` | Strict | markdownlint MD025 with `front_matter_title` | markdownlint, 0 disagreements | 431/134 | Keep, **open decision** |
| `heading-skip` | Strict | markdownlint MD001, title counted as h1 | markdownlint, 0 disagreements | 40/38 | Keep |
| `heading-formatting` | Strict | MT policy: no bold/italic/underline in headings | — | 19/7 | Keep |
| `heading-repeats-title` | Strict | MT policy: a heading may not restate the title | — | 6/6 | Keep |
| `fence-untagged` | Strict | markdownlint MD040 | markdownlint, 0 disagreements | 8/7 | Keep |
| `fence-language` | Strict | MT policy: one canonical tag per language (`bash`/`curl` → `shell`) | — | 121/46 | Keep |
| `fence-language-unknown` | Flexible | MT policy: prefer the listed tags | — | 2/1 | Keep as a note only — the tag list is a convention, not a closed set |
| `list-depth` | Strict | MT policy: at most three levels | — | 0/0 | Keep; quiet only after the HTML-table fix below |
| `link-anchor-empty` | Strict | markdownlint MD042 | markdownlint, 0 disagreements | 0/0 | Keep |
| `link-anchor-vague` | Strict | WCAG 2.4.4 (link purpose in context); Google devdocs link-text guidance | — | 59/44 | Keep |
| `link-bare-url` | Strict | markdownlint MD034 | markdownlint, 0 disagreements | 2/1 | Keep. An autolink (`<https://x>`) satisfies MD034 but not our anchor-text rule, so it is reported as `link-anchor-vague`, not here (`test_autolink_is_a_url_as_anchor_text`) |
| `link-absolute-internal` | Flexible | MT policy: relative links inside a repo | — | 140/62 | Keep flexible — cross-repo links must be absolute, and the checker cannot always tell which repo a URL belongs to |
| `image-alt` | Strict | markdownlint MD045 + WAI decorative-image exemption | markdownlint, 0 disagreements | 50/13 | Keep, **open decision** |
| `callout-emoji` | Strict | MT policy on top of rdmd's callout set | `emoji-regex`, 0 disagreements | 13/9 | Keep |
| `mt-shorthand` | Strict | MT policy: never abbreviate the company name | — | 69/14 | Keep |
| `object-shorthand` | Strict | MT policy: never abbreviate object names (`LT`, `LA`, `IPD`, …) | — | 218/29 | Keep; reads heading text as well as prose |
| `object-capitalization` | Strict | MT policy: objects are capitalised | — | 529/157 | Keep; ambiguous names (Transaction, Invoice, Return, Counterparty, Document, Event) are excluded by design; reads heading text as well as prose |
| `currency-mixed` | Strict | MT policy: one notation per page | — | 7/7 | Keep |
| `sentence-length` | Flexible | Vale `Microsoft.SentenceLength` (a suggestion there, 30 words) | — | 301/148 | Flexible — matches how the source tool ships it |
| `passive-voice` | Flexible | Vale `Google.Passive` / write-good passive, extended by the spaCy competition (fourth audit) | write-good; 175 documented extras and 10 documented misses, both explained in `differential.py` | 1789/366 | Flexible — the source tools ship it as a suggestion and the payments overlay deliberately uses passive for bank behaviour |
| `filler` | Flexible | Google devdocs word list, Vale `Microsoft.Adverbs`, proselint greylist | — | 229/142 | Flexible — every source treats these as suggestions |
| `filler-please` | Flexible | Google devdocs: no "please" when explaining product use | — | 89/70 | Flexible; "please contact" is exempt |
| `contractions` | Flexible (platform only) | MT policy for platform guides | spaCy tokenizer, 8023 sentences, 11 disagreements, all spaCy false positives on possessives | 33/17 | Keep |
| `acronym-undefined` | Flexible | MT policy: expand an industry acronym on first use | — | 116/82 | Flexible — first use may legitimately be in a title or a page the reader arrives from |
| `reference-no-shell` | Flexible (reference only) | MT policy: reference shows json bodies | — | 4/3 | Keep |
| `no-ordered-lists` | Flexible (reference only) | MT policy: reference is descriptive, not procedural | — | 0/0 | Keep — reference pages already contain no ordered lists, so the rule holds the line rather than reporting a backlog |
| `json-parse` | Strict | A reader copies the example: a body that parses in no JSON dialect is broken, and every field/type/schema check skips it silently | `dev/audit_methods/json_wellformed.py` (independent classification, itself cross-checked by Node `json5`); differential agreement 18 vs 18, 0 either-only | 18/18 on head | Keep — see the sixth audit |
| `url-query-separator` | Strict | A query string opening with `&` requests a different path | Confirmed against the running API: both instances return an HTML 404 in the sandbox | 2/1 on head | Keep — unique mechanical fix, so it ships one |

### Removed during the audit

| Removed | Reason |
|---|---|
| Ambiguous-object capitalization (`Transaction`, `Invoice`, `Return`, `Counterparty`, …) | Unfixable false-positive rate: the lowercase word is ordinary English. Moved to human review. |
| "Unsupported emoji" heuristic (`ord(ch) > 0x2000`) | Invented. Any non-ASCII lead character became an "emoji callout", including `—` and `"`. Replaced with rdmd's own rule. |
| Terminology rules skipped every heading | The prose channel excludes headings so that sentence length, passive voice and filler do not misfire on fragments; object and company naming was excluded with them, so `## In the MT App` passed. Headings are now scanned by `mt-shorthand`, `object-shorthand` and `object-capitalization` only (`test_shorthand_in_a_heading_is_flagged`, `test_headings_are_not_scanned_for_readability_or_filler`). |
| Title-suppression of `object-capitalization` | Tautological: a page titled "Ledger Accounts" got a free pass on the very rule it was most likely to break (272 suppressed occurrences). |
| Silent default of `--project` to `platform` | Produced overlay findings for a project the file was not in. Now exit 2 with a usage message. |
| Acronym "expanded anywhere on the page" | Passed pages that expanded an acronym *after* using it. Now the expansion must be in the first-use sentence, and a bare `(ACH)` no longer counts. |
| Hand-rolled markdown line scanner | Disagreed with markdown-it on 18 corpus pages (fences in HTML tables, headings inside list items, list continuation depth). Replaced by markdown-it-py. |

### Simplification pass (second audit)

Dead or unreachable code, then complexity that bought nothing. Behaviour is unchanged except for the
acronym rule, which lost 5 false positives (121 → 116 findings, 84 → 82 pages).

| Cut | Reason |
|---|---|
| `AMBIGUOUS_OBJECTS` constant | Never referenced — left behind when the ambiguous-object rule was removed. |
| `Page.body_start` field | Written once, never read; `parse_page` already passes the offset to `_walk_tokens` as a local. |
| `quote_depth` counter in the token walk | Only ever tested for truth alongside `pending_callout`, which is set on the same token. Nested, multi-paragraph and consecutive quotes now have fixtures. |
| Guarded `ordered_stack` pop/peek | markdown-it guarantees balanced `list_open`/`list_close`, so the guards could not fire. |
| `PROJECT_URL_PREFIX` tuples + `any(...)` | One prefix per project; a string and `in` say the same thing. |
| `shell`/`curl`/`bash` list in `reference-no-shell` | `FENCE_LANG_FIXES` already normalises the aliases; the rule now tests the normalised tag. |
| Acronym initials inference (`_spells`, `GLUE_WORDS`, `expanded_in`) | Wrong by construction: FX is not the initials of "foreign exchange", so correctly expanded pages were flagged. Replaced by an explicit expansion pattern per acronym, with a fixture per acronym in both directions. |
| Re-sorting the callout emoji by length on every call | Sorted once at module level. |

Kept after checking, with the reason it is not over-built:

| Kept | Reason |
|---|---|
| Custom sentence splitter | `pysbd` and `syntok` (rule-based segmenters, both on GitHub) split 76 of 6,752 prose blocks differently and each costs a third dependency; after the decimal-guard fix below the remaining disagreements are markdown artefacts, not English boundaries, so switching is a behaviour change rather than a simplification. |
| `link-anchor-empty`, `list-depth`, `no-ordered-lists` | Zero corpus hits is the point — they hold a line the corpus already respects. Each has a fixture, so "never runs" here does not mean untested. |

### Third audit: replacing invented logic with generated Unicode data

Two pieces of hand-written logic were checked against the sources the established tools derive theirs
from, and both were wrong. Strict findings are unchanged; flexible notes went 2617 → 2604.

| Was | Now | Evidence |
|---|---|---|
| `DECIMAL_TAIL_RE = \d\.$` — "a digit before the stop means a decimal" | `ENUMERATOR_TAIL_RE = ^\d{1,3}\.$` — only a hand-typed list number suppresses the boundary. A decimal never needs a guard: `3.14` has no whitespace after the point, so the boundary regex cannot match it. | The guard was the sole cause of 25 of 76 disagreements with `pysbd`, gluing real sentences together (`…is considered level 0. Up to 1 million Ledger Accounts…`). Removing it caused 3 new disagreements, all `1. API Testing` list numbers, which the narrower rule keeps. Corpus effect: 15 bogus `sentence-length` notes gone, 30 passive findings re-pinned from the glued pair to the right sentence. |
| `EMOJI_RANGES` — 15 hand-written blocks plus a modifier walk | `EMOJI_PRESENTATION_RANGES` / `EMOJI_TEXT_RANGES`, generated from Unicode `emoji-data.txt` by `dev/experiments/gen_emoji_ranges.py`, plus the UTS #51 sequence rules (flag pair, keycap, skin tone, tag sequence, ZWJ). This is how `emoji-regex`, the package rdmd uses, is built. | The hand-written ranges missed 291 of 3,781 Unicode emoji sequences (arrows with U+FE0F, keycaps, flags, skin tones on text-presentation bases) and claimed 2,270 code points that are not emoji at all (unassigned points inside `1F300–1FAFF`). The generated tables: 0 missed, 0 stray. |

The corpus could not catch either: it uses five callout emoji and no numeric sentence boundaries in
the affected shape. So the differential run now sweeps every fully-qualified sequence in the bundled
`emoji-test.txt` through both `starts_with_emoji` and rdmd's own regex — 3,781 strings, 0
disagreements, against 291 for the pre-change detector, which is what makes the sweep worth having.

### Fourth audit: does one dependency beat the regexes? (spaCy competition)

The question was whether adding a POS tagger and dependency parser would make the prose rules
materially better. It was decided by running both over the corpus rather than by argument. spaCy
3.8.7 with `en_core_web_sm` implements sentence splitting, passive voice and contractions in
`dev/compete/spacy_rules.py`; `dev/compete/compete.py` runs it against the checker over all 667 pages
(6,752 prose blocks, 8,023 sentences) and writes every disagreement to `disagreements.jsonl`;
`dev/compete/labels.py` adjudicates them by category, and `score.py` counts.

The first run went to spaCy on passive voice (26–107), which is what the extensions below were built
from: each one is a class of construction spaCy's parse caught and word shape did not. After folding
them in, the same comparison reverses.

| Detector | Checker right | spaCy right | Result |
|---|---|---|---|
| `passive-voice` | 30 | 9 | 39 disagreements out of 8,023 sentences. spaCy's 9 are inverted clauses ("Listed below is…", "Nested within your object are…"), participles outside write-good's lexicon (`borne`, `resent`, `undone`) and three or more words between auxiliary and participle. Its losses are copula-plus-complement ("is debit normal", "can be debit only"), fragments, table cells (`0h 25m 0s`) and get-idioms ("get started"), none of which have an actor to name. |
| `contractions` | 11 | 0 | spaCy's tagger marks a possessive `'s` on a proper noun ("Beta Corp's Ledger Account") as a clitic. The `AND'd`/`OR'd` case it did win is now fixed in the checker, so it wins nothing. |
| sentence splitting | — | — | 72 blocks differ. 44 of the boundaries only spaCy makes fall where there is no `.`, `!` or `?` at all, so they are provably wrong; 0 of the checker's do. The remaining 36 are candidates on both sides. |

Verdict: not adopted. ~55 MB of dependency and model, an import that dominates runtime, and no
network in the Claude.ai sandbox, in exchange for a detector that loses on every one of the three.
The measurable part of its advantage was portable, so it was ported:

| Extension | Example it now catches | Source |
|---|---|---|
| Up to two intervening words, not one adverb | "is **not** evaluated", "are **still broadly** used" | spaCy disagreement class |
| Negated and contracted be | "payments **aren't** sent", "**it's** advised" | spaCy disagreement class |
| Prefixed participle (`pre-`, `re-`, `auto-`, …) | "is **auto-ledgered**", "are **pre-populated**" | spaCy disagreement class; a noun compound ("user-defined", "bank-issued") is a compound adjective and stays excluded |
| The get-passive | "will **get increased**", "revenue **gets recognized**" | spaCy disagreement class; Vale's `Google.Passive` has no get-passive either |
| Predicate-adjective guard | "are interested in", "are unverified", "is related", "is unchecked" no longer flagged | spaCy disagreement class, in spaCy's favour |
| Get-idiom guard | "get started", "get set up", "getting connected" no longer flagged | rule intent: no actor to name |
| All-caps host is not a contraction | "conditions are AND'd together" no longer flagged | spaCy disagreement class, in spaCy's favour |

Corpus effect: strict findings unchanged at 2076, flexible notes 2604 → 2688 (`passive-voice`
1705 → 1789, `contractions` −3 false positives). Fixtures 133 → 140. The differential run against
write-good still passes, with both directions of divergence now stated in `EXPECTED`.

What is still not caught, stated rather than hidden: the 9 constructions above. Closing them needs a
parse, and the score says the parse costs more than it returns.

### Fifth audit: is the fixture suite adequate? (mutation testing)

133 fixtures passing says the tests run; it does not say they test. `dev/audit_methods/mutate.py`
answers that by breaking the checker on purpose: it walks the AST and mutates decision points inside
functions — comparison operators, boolean connectives, dropped `not`, numeric thresholds, boolean
constants, and the severity a rule assigns — applies each mutant to a copy in a temp tree, and runs the
fixture suite against it. A mutant that survives is a decision the suite executes but does not check.
Module-level constants are deliberately excluded: in this checker they are generated Unicode tables,
where a mutated code point measures nothing about the fixtures.

| Run | Mutants | Killed | Survived | Kill rate |
|---|---|---|---|---|
| Baseline | 145 | 121 | 24 | 0.834 |
| After the two boundary fixtures below | 145 | 124 | 21 | 0.855 |
| After `json-parse` and `url-query-separator` were added (new decision points) | 181 | 152 | 31 | 0.831 |
| After the JSON and URL fixtures | 181 | 164 | 17 | 0.906 |
| After the sixth audit's four fixtures (below) | 181 | 168 | 13 | 0.928 |
| After five more fixtures for survivors the corpus could not decide (below) | 181 | 172 | 9 | **0.950** |

The 0.928 row is lower than the 0.939 an earlier run reported, and the earlier number was wrong: the
harness wrote mutants to one path inside one second, and `.pyc` invalidation is mtime plus size, so a
mutant the same size as its predecessor ran the predecessor's bytecode. Two verdicts flipped per run.
With `PYTHONDONTWRITEBYTECODE=1` two consecutive runs now return byte-identical survivor sets — which
is the point: a validation harness whose own result is not reproducible cannot be evidence for
anything, and only running it twice showed that.

Two survivors were real gaps in what the suite claimed to cover, both off-by-one on a documented
threshold:

| Survived mutant | What it means | Fixture added |
|---|---|---|
| `words > MAX_SENTENCE_WORDS` → `>=` | The suite had a 40-word sentence and nothing at 30, so the published limit could be off by one and every test still passed | `test_sentence_length_boundary` |
| `len(sentence.split()) > 2` → `>=` | The 3-word floor that separates prose from a label was never tested at the boundary | `test_three_words_is_the_shortest_sentence_read` |

### Sixth audit: what does a surviving mutant actually mean?

"Mostly parser boundaries where both operators produce the same result" was, in the fifth audit, my
reading of the survivors — the same kind of claim as "verified by hand", and worth as little. A kill
rate cannot separate an untested decision from a decision with no observable behaviour, so
`dev/audit_methods/mutation_survivors.py` asks the corpus instead: re-apply each surviving mutant, run
all 682 head pages through it, and compare every field of all 5,038 findings against the baseline.

| Verdict | Meaning | First run of 15 survivors |
|---|---|---|
| `corpus-visible` | findings differ on a real page — a real gap, and that page is the fixture | 3 |
| `crashes` | the mutant raises, so the altered guard is load-bearing | 1 |
| `corpus-silent` | byte-identical findings over 682 pages | 11 |

My fifth-audit reading was wrong on 4 of 15. Each became a fixture, all in `Pointers`:

| Survived mutant | What it means | Fixture added |
|---|---|---|
| `end > len(text)` → `>=` in `clip_evidence` | A span ending exactly at the end of the evidence became unpinned: the finding still fires, so no rule-name test notices, but the caret disappears | `test_span_that_ends_the_evidence_is_still_pinned` |
| `start <= offset` → `<` in `Block.line_at` | A construction starting exactly at a wrapped line's first character was reported on the previous line | `test_construction_at_the_start_of_a_wrapped_line_reports_that_line` |
| `attrGet("src") or ""` → `and ""` | `image-alt` lost the filename from its evidence, leaving a finding with nothing to act on | `test_image_finding_names_the_source_file` |
| `type == "link_close" and link_stack` → `or` | Formatting inside anchor text (`[**here**](…)`) popped the link stack early and crashed the checker on a real page | `test_formatted_anchor_text_does_not_unbalance_the_link_stack` |

A harness bug came out of this too, and it is the reason the classification is trustworthy now:
survivors were originally re-applied by matching line number plus unparsed text, and
`depth, in_string, escaped = 0, False, False` holds two targets that unparse identically. The mutant
being classified was not always the mutant that survived. Mutants now carry their target index.

Five more were then killed by fixtures written for what the mutant would cost a reader, since
corpus-silence answers "does this change today's output" and not "is this decision load-bearing":

| Survived mutant | What it means | Fixture added |
|---|---|---|
| `open_at < 0` → `<= 0` in `json_balanced_object` | `-1` is the "no object here" sentinel; `<= 0` also discards an object at offset 0, which is where every `json` fence body starts | `test_body_that_opens_the_code_line_is_scanned` |
| `in_string` initialised `False` → `True` | The whole body reads as one string, so no object ever closes and every malformed body is skipped silently | `test_brace_inside_a_string_does_not_close_the_object` |
| `end <= start` → `<` in `clip_evidence` | A zero-width span renders a caret row with no caret in it | `test_zero_width_span_reads_as_unpinned` |
| `tag == "a" and self._open_link` → `or` in the HTML channel | Any closing tag ends the anchor, so `Click <b>here</b>` loses "here" and stops being a vague anchor | `test_formatting_inside_an_html_anchor_does_not_end_the_anchor` |
| `x.path == path` → `!=` in `render_text` | Every page's findings print under every other page's heading. No single-file fixture can see this | `test_each_page_is_reported_under_its_own_heading` |

The 9 remaining survivors, in `dev/audit_methods/mutation.json`, are all corpus-silent: defensive
guards (`text.split("\n")` never returns an empty list, so `not lines` is unreachable), presentation
details (`indent=2`, an 8-row report cap), and a JSON error line that normalization cannot push past
the end of the source body.
Corpus-silence is not proof of equivalence and is not claimed as one: it is the statement that 682
real pages cannot tell the two builds apart. The gate going forward: no rule is promoted while a
mutant of its own decision points survives *visibly*.

### Seventh audit: re-measured after the four-way split (Phase 2)

Re-homing the checker to `docs-lint` and moving every severity, threshold and word list into the
compiled policy artifact changed the mutable surface: module-level constants that were once literals
in the source are now read from `rules.yaml`, so 4 mutation targets disappeared with them and the run
discovers 177 mutants, not 181. Re-running the survivor classification on the migrated harness found
5 decision points the migrated suite no longer covered — two of them corpus-visible:

| Survived mutant | What it means | Fixture added |
|---|---|---|
| `e in CALLOUT_ROLES` → `not in` (twice, in `sanctioned_callouts`) | Every `callout-emoji` finding on the corpus offers a suggestion with the roles stripped or reordered, so the reader is told which emoji to use but not for what | `test_the_callout_suggestion_names_each_emojis_role` |
| `len(listed) > 1` → `>= 1` | With one sanctioned emoji the suggestion renders as ` or 📘` — invisible until Notion trims the table to one row | `test_one_sanctioned_callout_reads_as_one_item`, `test_a_sanctioned_callout_with_no_role_is_still_offered` |
| `'flexible'`/`'strict'` severity constants and `guide != reported` in `--list-rules` | The guide grade stops being printed, or is printed on every rule, so the one place the two severities are reconciled silently agrees with itself | `test_list_rules_annotates_a_rule_the_guide_grades_harder` |

Measuring only the checker after that move would be the one way to raise the rate by removing coverage:
`findings.py` and `policy.py` now carry the ordering, the report shape, the severity vocabulary and every
refusal. The harness therefore mutates all three shipped modules that decide something, and the three
empty subskills none, since they decide only whether the artifact loaded. That surfaced 4 further
uncovered decision points:

| Survived mutant | What it means | Fixture added |
|---|---|---|
| `ranked = rule_counts(shown)[:8]` → `[:9]` (`findings.py`) | The "Most frequent" line grows or shrinks without any rule test noticing | `test_most_frequent_shows_eight_rules_at_most` |
| `'moderate'` dropped from the accepted severities (`policy.py`) | The third grade the plan is built on becomes a load error, so no rule can ever carry it | `test_moderate_is_a_grade_the_loader_accepts` |
| `value_tables` never populated (`policy.py`) | `require()` stops reporting a table Notion dropped; the run instead dies later, mid-page, on a missing lookup — the earlier fixture passed on the *word* `currency_codes` appearing in either message | assertion tightened to the `require()` message |
| `rules` mapping allowed to be empty (`policy.py`) | An artifact with zero rules loads, and a checker with no policy reports a clean corpus | `test_an_artifact_with_no_rules_at_all_is_refused` |

Kill rate **0.959** over the three modules (217 mutants, 208 killed: `lint.py` 169/177,
`findings.py` 13/14, `policy.py` 26/26), identical survivor sets across two consecutive
bytecode-disabled runs, and all 9 survivors classified `corpus-silent` by
`dev/audit_methods/mutation_survivors.py`. The remaining `findings.py` survivor inverts the
`sys.path` guard, which every caller makes redundant by inserting the shared directory itself.

### Eighth audit: re-measured after Phase 4 narrowed two rules

Enforcing the agent exemption and inverting `frontmatter-excerpt` added decision points (the `by`-phrase
window, the non-agent head table, the gerund and shape guards), so the run discovers **221** mutants.
Kill rate **0.959** (212 killed: `lint.py` 173/181, `findings.py` 13/14, `policy.py` 26/26), the survivor
set identical across two consecutive bytecode-disabled runs, and all 9 classified `corpus-silent`
against the post-Phase-4 baseline of 4,601 findings
(`dev/audit_methods/mutation_survivors.py --mutation dev/audit_methods/mutation-phase4.json`). No mutant
of the new agent logic survived. `findings.py` reads 13/14 on its own, below the 0.950 module figure: its
one survivor is the `sys.path` guard inversion, which every caller makes redundant by inserting the
shared directory itself, so the criterion is stated over the three modules together rather than per file.

The change is measured as a differential, not as a new number: `dev/acceptance/phase4_delta.py` attributes
each of the 795 individual finding changes (5,038 → 4,601) to one of four Phase 4 causes, and
`dev/audit_methods/passive_agent_differential.py` scores the shipped `agent_span()` against spaCy's
`agent` dependency over the **pre-change** report — the post-change output no longer contains the findings
the change suppressed, so scoring it there measures the sample the change created. Agreement 0.9787 over
1,874 passives (90 both-named, 1,744 both-unnamed, 11 regex-only, 29 parser-only), and the window
sensitivity table (24…240 characters) moves agreement only between 0.9765 and 0.9797, so the 48-character
threshold is not load-bearing.

The audit's own finding is about the harness. The delta keyed findings on a `span` field the shared
format does not have — the columns are `col` and `end_col` — so 12 changes were invisible: suppressing a
sentence's first passive exposes a later construction that names nobody, and that finding differs from its
predecessor only in the caret. It cancelled, and the run reported every delta attributed over 771 of 795.
The columns are part of a finding's identity now, causes are judged against the construction the finding
reported rather than against the whole sentence, and `dev/tests/test_phase4_delta.py` fixtures the harness
itself. Independent corroboration of the 101 suppressions: the spaCy differential counts 90 + 11 named
agents in the pre-change set without reading the delta at all.

### Two rules added, each on executed evidence

| Rule | Evidence that promoted it | Independent check |
|---|---|---|
| `json-parse` (strict) | 18 bodies in the head corpus parse in no JSON dialect after the documented conventions (comments, trailing commas, elisions, placeholders, property fragments, field-name lists, alternative bodies) are normalized away. A reader copies these; every field, type and schema check silently skips them | `dev/audit_methods/json_rule_differential.py`: the shipped rule and the independent probe select **exactly the same 18 bodies**, 0 either-only. The probe's own classification is itself cross-checked by a Node `json5` parse, 0 disagreements over 565 bodies |
| `url-query-separator` (strict) | 2 documented URLs open their query string with `&`, so they request a different path. Found by endpoint normalization, then **confirmed against the running API**: both return an HTML 404 in the sandbox (`dev/audit_methods/execute_curl.py`) | Mechanical fix is unique (`&` → `?` at the first occurrence), so the rule ships a fix |

### False positives found and fixed (each now has a fixture)

| Symptom | Cause | Fixture |
|---|---|---|
| 372 "contractions" including `Account's balance` | `\w+'s` matched possessives | `test_possessive_is_not_a_contraction` |
| `👍`, `⚠️`, `❗️` reported as unsupported "unicode" | No model of rdmd's callout emoji | `test_unsanctioned_readme_callout_emoji`, `test_typography_at_start_of_quote_is_not_a_callout` |
| Untagged-fence findings inside `<table>` cells | Indented cell content read as a fence | `test_indented_block_in_an_html_table_cell_is_not_a_fence` |
| Deep-nesting findings from bullets in HTML tables | Table layout read as list nesting | `test_bullets_inside_html_table_are_not_a_list` |
| Only the first lowercase object per sentence reported | `break` in the loop | `test_object_capitalization_reports_each_object_in_a_sentence` |
| Sentences split at `e.g.`, `1.5`, `U.S.` | No abbreviation guard | `test_abbreviation_does_not_end_a_sentence`, `test_decimal_does_not_end_a_sentence` |
| `…level 0. Up to 1 million…` read as one 40-word sentence | Any digit before the stop suppressed the boundary | `test_a_number_before_the_stop_still_ends_a_sentence`, `test_a_hand_typed_list_number_does_not_end_a_sentence` |
| `↗️`, `1️⃣`, `🇺🇸`, `✌🏻` not seen as callout emoji; `🌢`, `🎔` (unassigned) seen as emoji | Hand-written code point blocks instead of Unicode property data | `test_emoji_forms_from_the_unicode_tables_are_callouts`, `test_non_emoji_leads_are_not_callouts`, plus the emoji-test.txt sweep in the differential run |
| 15 "empty link anchor" on `[`modern-treasury-js`](…)` | Anchor text inherited the prose channel, which blanks inline code | `test_inline_code_anchor_is_not_an_empty_anchor` |
| 19 "bare URL" on `[https://x](https://x)` | Anchor text scanned as prose | `test_url_as_anchor_text_is_vague_not_bare` (now reported as a vague anchor, which is what it is) |
| `currency-mixed` evidence read `USD` with no line | Page-level check with no location | `test_mixed_currency` (both notations, both lines) |
| 3 "contractions" on `conditions are AND'd together` | The suffix pattern took any host, including a code operator | `test_code_operator_is_not_a_contraction` |
| 10 "passive voice" on `are interested in`, `are unverified`, `is related` | A predicate adjective has the same word shape as a participle | `test_predicate_adjective_after_a_copula_is_not_passive` |
| "passive voice" on `to get started`, `get set up` | The get-passive pattern matched the idiom, which has no actor | `test_get_idiom_is_not_passive` |
| "passive voice" on `are user-defined`, `are bank-issued` | The prefixed-participle extension first accepted noun compounds too | `test_prefixed_participle_is_passive_but_a_noun_compound_is_not` |

## Runtime dependencies

The checker requires `markdown-it-py` (4.2.0 verified) and `PyYAML` (6.0.3 verified) instead of being
standard-library only. This was not a preference: the hand-rolled scanner disagreed with a real
CommonMark parser on 18 of 667 corpus pages, and every one of those disagreements was a false finding
in a construct the docs genuinely use — fences inside HTML table cells, headings inside list items,
list continuation depth, frontmatter whose nested `metadata.title` shadowed the real title. markdown-it
is the same parser family ReadMe's own rdmd is built on, so agreement with it is agreement with
rendering. Both packages are pure Python, install in one command, and are already used by the build
scaffolding.

## Open decisions (policy, not code)

1. ~~**`frontmatter-excerpt` is strict but 496 of 667 pages fail it**~~ Closed in Phase 4 by D7: Modern
   Treasury does not use excerpts, so the finding is a *present* excerpt and a page without one is
   correct. Flexible, 167 pages, listed once in `dev/inventory/excerpts.md` for deletion by hand.
2. **`body-h1`, 431 findings on 134 pages** — the existing high-level guide says "the highest sections
   in a doc should be Heading 1", ReadMe renders the frontmatter title as the h1, and markdownlint
   MD025 agrees with the checker. Confirm the guide text changes rather than the corpus.
3. **`image-alt`, 50 findings on 13 pages** — strict per WCAG, but it is a corpus-wide cleanup.

Nothing else in the checker is waiting on a decision.

## Severity reconciliation

`lint.py --list-rules` prints severity and source straight from the compiled policy artifact, and is the authority.
The guide and the skill were reconciled against it:

- `SKILL.md` lists the same strict and flexible sets, names the three project-scoped rules, and
  documents exit status 2 for a bad invocation.
- The Notion pages label a rule **Strict, checker flags it as a suggestion** wherever the style is
  strict for a reviewer but the checker reports it as flexible (`passive-voice`, `sentence-length`,
  `filler`, `filler-please`, `acronym-undefined`, `link-absolute-internal`, `contractions`,
  `reference-no-shell`, `no-ordered-lists`). Before this pass they read plain "Strict", which
  contradicted the checker's own output.
- The stale rule id `first-heading-h1` in the guide was replaced by the real one, `body-h1`, and the
  rule text now matches what the checker enforces: ReadMe renders the frontmatter title as the h1, so
  body headings start at h2.
