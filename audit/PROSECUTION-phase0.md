# Prosecution — Phase 0 (Notion rule tables)

Method: shell + Notion MCP read-only queries. No fixes applied (see §"Remedies not applied").
Code under audit: `skill/docs-style-review/scripts/stylecheck.py` (1221 lines).
Row data: `collection://ce42afb4-f477-42c3-8636-5f5120fda9b0` (30 rows),
`collection://10238de1-ce37-45e9-a46c-1c79e1fad729` (87 rows, 86 active). Both counts verified.

---

## 1. BLOCKING — Drift case 1 is factually false: the shipped checker *does* report `just`

`PLAN-phases.md:45-46` asserts "`just` banned in the guide but not in `BANNED_FILLER`, 35 occurrences
on 27 pages unreported". The premise is wrong. `BANNED_FILLER` does not contain `just`, but
`stylecheck.py:1016-1018` hard-codes a second, separate `just` check that emits the same rule id:

```
1016	    just = re.search(r"\bjust\b", sentence, re.IGNORECASE)
1017	    if just and not re.search(r"\bjust (as|like|in time)\b", sentence, re.IGNORECASE):
1018	        add(lineno, "filler", "Cut 'just'.", sentence, fix="delete the word", span=just.span())
```

Executed proof, fixture `/tmp/pros/f1.md`:

```
$ python3 scripts/stylecheck.py f1.md --project ledgers
  flex        6  filler                   Cut 'just'.
                        > You just need three fields to create a Ledger Transaction.
                              ^^^^
                        fix: delete the word
```

("Configure it just as expected." on line 8 was correctly *not* reported — the `just as|like|in time`
exclusion works.) At corpus scale, on one repo only:

```
$ cd /home/ubuntu/repos/docs-readme-ledgers
$ python3 .../stylecheck.py . --project ledgers --rule filler | grep -c "Cut 'just'"
14
```

Consequences, all three of which Phase 0 shipped:

- `PLAN-phases.md:45-46` and `PLAN-subskills.md:164-166` ("35 occurrences across 27 corpus pages go
  unreported") are unsupported. The occurrences are reported.
- The Notion `filler_words` row `just` carries `Active = __NO__` with the note "Drift case 1: the guide
  bans just as a minimizer, the checker…". A compiled artifact honouring `Active=false` would
  **remove** a check the code performs today, silently deleting ≥14 real findings on ledgers alone.
  This breaks `PLAN-phases.md:102-104` (Phase 1 exit: "the compiled artifact reproduces today's
  constants exactly except for the three intentional drift fixes") — this would be a fourth,
  unintentional behaviour change.
- The new base-style prose is false to readers. `01 — Base Style`, filler section: "Of these the
  checker reports all but `just`, which is policy a reviewer applies". The checker reports `just`.

Phase 0 was justified as drift reduction; on this rule it authored new drift and told readers the
opposite of what the tool does.

**Remedy.** Either (a) delete `stylecheck.py:1016-1018` and keep `Active=__NO__`, which is a code
change and therefore Phase 1/2 work, not Phase 0 — in which case say so on the row; or (b) fold `just`
into `BANNED_FILLER` with the exclusion list as a row column and set `Active=__YES__`. Until one is
chosen, revert the base-style sentence and set the row note to "code reports this today via a
hard-coded branch outside `BANNED_FILLER`; `Active` state is aspirational, not current".

## 2. BLOCKING — the D7 excerpt inversion moved the drift instead of removing it

Prose was inverted now; `RULES["frontmatter-excerpt"] = (True, …)` (`stylecheck.py:114`) was not. The
guide and the checker now contradict each other in the *opposite* direction, and a writer who follows
the new prose fails the build.

`01 — Base Style` now reads: "### Frontmatter has `title`, and no `excerpt` — **Strict** … We do not
use excerpts. An `excerpt` key in frontmatter is reported so it can be removed; do not add one to a new
page."

Executed proof — `/tmp/pros/f2.md`, frontmatter with `title` and no `excerpt`, i.e. a page written
exactly as the guide now instructs:

```
$ python3 scripts/stylecheck.py f2.md --project ledgers
  STRICT      1  frontmatter-excerpt      Page has no excerpt; it is the search and preview text.
FAIL: 1 page(s), 1 strict failure(s)
```

And `/tmp/pros/f1.md`, which *has* an excerpt (the thing the guide now says is reported for removal),
produced **no** `frontmatter-excerpt` finding at all.

The Notion row is also self-contradictory as a compilation input: `Severity = strict`,
`Active = __YES__`, `Value table = null`, and a Note saying the behaviour inverts in Phase 4. A sync
compiling this row today produces exactly today's wrong behaviour while the guide asserts the inverse,
and nothing in the artifact tells a reader which one is live. `PLAN-subskills.md:402-404` explicitly
called this out as "the Notion page has to change with the rule" — the page changed, the rule did not.

**Remedy.** Revert the base-style excerpt section to the pre-D7 wording until Phase 4 lands, or ship
D7's code change now. If the prose must lead, add an explicit "not yet enforced; the checker still
requires an excerpt" sentence in the prose itself, not only in a Notion row note a reader never sees.

## 3. BLOCKING — the shipped SKILL.md declares the *code* authoritative, contradicting the whole premise

`skill/docs-style-review/SKILL.md:97`:

> `--list-rules` prints this table from the code, **which is the authority if the two ever drift.**

The index page section Phase 0 added says the opposite: "the checker's severities, thresholds, word
lists and code tables compile from these rows, so changing a rule's list or grade is an edit here
rather than a code change." `PLAN-subskills.md:90-94` makes Notion the source of truth.

So the shipped skill now instructs a reader to resolve any Notion/code disagreement in favour of code,
which nullifies items 1, 2 and 4 for anyone actually using the skill. `SKILL.md` mtime is
`2026-09-02 20:01:27`, i.e. it *was* touched during this phase, and `PLAN-phases.md:83-86` ("Built")
does not declare any SKILL.md change — see §12.

**Remedy.** Change SKILL.md:97 to name Notion (or, once Phase 1 ships, the compiled artifact hash) as
the authority, and declare the edit in Phase 0's "Built" paragraph.

## 4. BLOCKING — `filler-please` is marked table-driven but has zero backing rows

Phase 0's own Exit line (`PLAN-phases.md:78`) is "Every table-driven rule has rows".
`PLAN-subskills.md:119` lists `filler-please` (90 findings) under "Filler words + replacements".

The Notion row for `filler-please` sets `Value table = filler_words`. The seven `filler_words` rows
are `easily, in order to, just, note that, obviously, of course, simply`. Neither `please` nor
`please note` is a row. The rule's actual policy is hard-coded:

```
1019	    please = re.search(r"\bplease\b", sentence, re.IGNORECASE)
1020	    if please and "contact" not in sentence.lower():
```

A sync following the `Value table` pointer compiles `filler-please` against a list that contains
nothing it looks for. Worse, `stylecheck.py:66-68` cites external provenance for tokens that exist in
neither the code list nor Notion: "`just`, `please`, `please note` and `in order to` come from the
Google developer documentation style guide word list" — `please note` is nowhere.

**Remedy.** Either add `please` / `please note` rows in a `filler_please` table (with the `contact`
exemption as a column or a row note), or set `Value table = null` for `filler-please` and record on the
row that its token and exemption are code-resident.

## 5. SHOULD-FIX — `mt-shorthand` and `reference-no-shell` are table-driven in the plan, un-tabled in Notion

`PLAN-subskills.md:118` puts `mt-shorthand` (68 findings) under the "Object shorthand" table;
`PLAN-subskills.md:127` puts `reference-no-shell` (5) under overlay scoping but its trigger literal is
a fence language.

Notion `Value table` is `null` for both. The literals stay in code:

- `stylecheck.py:987` — `re.search(r"\bMT\b", sentence)`; the string `MT` is not a Values row.
- `stylecheck.py:800` — `if FENCE_LANG_FIXES.get(lang, lang) == "shell":` — the target token `shell`
  is a bare literal, so retiring or renaming the `shell` fence tag in Notion silently decouples
  `reference-no-shell` from `fence_language_fixes`.

**Remedy.** Add an `mt_shorthand` value row (`MT` → `Modern Treasury`), and either add a
`reference_no_shell_langs` table or a row note stating the coupling is code-resident.

## 6. SHOULD-FIX — the severity vocabulary the plan promises cannot be expressed, and is not populated

`PLAN-subskills.md:206-212` defines three grades with distinct gates: strict ≥0.95 precision,
moderate ≥0.80, flexible no floor. The `Severity` select offers `strict/moderate/flexible`. Measured
distribution over all 30 rows:

```
severity distribution: Counter({'strict': 20, 'flexible': 10})
rows with moderate: []
```

Severity was mechanically derived from the code's boolean (`RULES: dict[str, tuple[bool, str]]`,
`stylecheck.py:112`) — I verified `Severity == 'strict'` iff `RULES[id][0] is True` for all 30 rows,
zero mismatches. So the column carries no information the boolean did not, and the middle grade the
plan's gate is built around has no instance. Two knock-ons:

- The index page's own new prose defines only two labels ("Strict … Flexible"), with no `moderate` row
  in its table. The guide a human reads therefore cannot express the grade Phase 4 is expected to
  assign `passive-voice` (`PLAN-phases.md:143-145`, "demotion or narrowing is the likely outcome").
- The base-style page encodes a *second*, divergent severity per rule in prose that has no column at
  all: "Sentences stay under about 30 words — **Strict** (`sentence-length` is reported as flexible,
  judged in review)", likewise for `passive-voice` and `acronym-undefined`. A single `Severity` column
  cannot round-trip "strict as guidance, flexible as reported", so the compiled artifact will drop the
  distinction the prose depends on.

**Remedy.** Add a `Guide severity` column distinct from `Reported severity`, and add the `moderate`
definition to the index page's label table so Phase 4 has somewhere to land.

## 7. SHOULD-FIX — `callout_emoji` rows describe the wrong set, and the set the rule actually needs is absent

The rule needs two sets: what ReadMe *recognises* as a callout (12 entries in
`README_CALLOUT_EMOJI`, `stylecheck.py:259-271`, plus the generic emoji ranges) and what Modern
Treasury *sanctions* (3 entries, `SANCTIONED_CALLOUTS`, `stylecheck.py:64`).

Notion holds 3 rows (📘/note, 🚧/warning, 💡/tip) — the sanctioned set — but each carries the note
"ReadMe callout themes map; anything outside this set is a finding." That is the recognised set's
description attached to the sanctioned set's rows. It is wrong twice: the ReadMe themes map has 12
entries, and "anything outside this set" is not a finding — only emoji that ReadMe recognises *or* that
match the generic ranges reach `page.callouts` at all (`stylecheck.py:405-409`).

Diff: `code=3 notion=3 code_only=[] notion_only=[]` against `SANCTIONED_CALLOUTS` — the values are
right, only the semantics recorded on them are wrong. `README_CALLOUT_EMOJI`: 12 in code, 0 in Notion.

**Remedy.** Correct the note to "Modern Treasury's sanctioned callout emoji; a recognised ReadMe
callout emoji outside this set is a finding." Leave `README_CALLOUT_EMOJI` in code (it is mechanism —
it mirrors rdmd's themes map, not an MT decision — consistent with `PLAN-subskills.md:135-137`), but
say so on the rows so the omission reads as deliberate.

## 8. SHOULD-FIX — three concrete non-round-trippable columns block "reproduces today's constants exactly"

Phase 1 exit (`PLAN-phases.md:102-103`) requires byte-exact reproduction. Three measured obstacles:

**(a) `FILLER_REPLACEMENTS` empty-string value is indistinguishable from an absent key.**
`stylecheck.py:244` — `FILLER_REPLACEMENTS = {"in order to": "to", "note that": ""}`. Diff output:

```
[FILLER_REPLACEMENTS vs filler_words] code=2 notion=7 notion_only=['easily','just','obviously','of course','simply']
    MISMATCH 'note that': code='' notion=None
```

`note that`'s `Maps to` is empty, identical to the five words that have no replacement. A sync yields a
2-key dict missing `note that`, or a 7-key dict, neither equal to the constant. (Behaviourally inert
today — `stylecheck.py:1013` treats `""` as falsy — so this is should-fix, not blocking, but the
byte-exactness test will trip on it.)

**(b) `object_shorthand.Maps to` holds data the code does not have.** Diff:

```
[SHORTHAND->obj vs object_shorthand] code=7 notion=7 code_only=[] notion_only=[]
    MISMATCH 'EP': code=None notion='Expected Payment'   (and 6 more)
```

`SHORTHAND` (`stylecheck.py:59`) is a bare list of strings; the code never resolves a shorthand to its
object name (`stylecheck.py:990-993` prints only the shorthand). The column is either dead weight the
sync must be told to ignore, or an intended enhancement — the rows do not say which.

**(c) Markdown in text columns does not survive.** One provenance string of 30 lost its formatting:

```
provenance mismatches: [('url-query-separator',
  'A documented URL whose query string opens with `&` requests a different path; …',
  'A documented URL whose query string opens with & requests a different path; …')]
```

The backticks around `&` are gone. All 29 others matched exactly. `acronym_expansions.Maps to`
stores regexes as text (`bankers.{0,2} automated clearing (system|services)`,
`real[- ]?time payments`) — I verified all 10 match the code strings byte for byte and all 10 compile,
so that column is currently clean, but it is one stray Notion auto-format away from the same class of
loss and has no schema guard.

**Remedy.** Give the sync's schema an explicit "empty means absent" vs "empty means empty string"
convention per table; mark `object_shorthand.Maps to` as documentation-only or wire it up; store
regex/provenance columns as Notion code-formatted text and add a round-trip assertion to Phase 1's
guards.

## 9. SHOULD-FIX — `Active` semantics do not hold water as written

Index page: "**`Active` is the gate, not a preference.** A value or rule whose `Active` box is
unchecked is compiled but not enforced. **New entries start unchecked**, because a rule's precision was
measured against a specific list."

Measured against the rows:

- `rules with Active unchecked: []` — all 30 rule rows are active. The rule-level checkbox has no
  instance and no test.
- 86 of 87 value rows are active. The single exception, `just`, is the one case where the code
  contradicts the checkbox (§1) — so the only exercise of the mechanism is also its counterexample.
- "New entries start unchecked" is contradicted by the phase's own work: `LAC` is new to the guide and
  was created `Active = __YES__` (defensible — the code already enforced it — but then the stated
  invariant is not an invariant).

The deeper hole the brief asks about: yes, `Active` creates a state where the guide and the enforced
artifact disagree with **no reader-visible signal**. `Active` lives in a database column; the prose
pages a writer actually reads carry no marker. Today's `just` row is exactly this: the guide's filler
section lists `just` as banned, the row says not enforced, and the code enforces it. Three states, one
reader, no way to tell.

**Remedy.** Require every inactive row to have a non-empty `Note`, and require the sync to emit the
inactive set into the refreshed `style/*.md` as an explicit "authored, not enforced" list so the
divergence is visible in the prose a writer reads. Add one deliberately inactive rule row plus a guard
test, or drop the rule-level checkbox until Phase 1 can exercise it.

## 10. SHOULD-FIX — Phase 0 traded code↔Notion drift for Notion↔shipped-guide drift; net drift went up

The four base-style prose edits did not propagate to the shipped local copies, which `SKILL.md:30-31`
tells readers to trust ("Local copies are in `style/`… If they disagree with Notion, Notion wins —
refresh the local copies rather than editing them in place"). mtimes: `style/01-base-style.md` and
`style/00-index.md` both `2026-08-26`, untouched.

| Phase 0 edit | Notion (edited) | `style/01-base-style.md` (shipped, stale) |
|---|---|---|
| LAC added | "`LA`, `LT`, `LAS`, `EP`, `PO`, `IPD`, `LAC` are banned" | `:129` "`LA`, `LT`, `LAS`, `EP`, `PO`, `IPD` are banned" |
| filler-except-`just` | "the checker reports all but `just`" | `:87` "Banned: `simply`, `just` (as a minimizer), …" — no clause |
| `body-h1` rename | "**Strict** (`body-h1`, `heading-skip`)" | `:148` "**Strict** (`first-heading-h1`, `heading-skip`)" |
| D7 excerpt inversion | "Frontmatter has `title`, and no `excerpt`" | `:179-181` "Frontmatter has `title` and `excerpt`… Write one; do not leave it empty" |

`style/00-index.md` also has no "The rule tables" section (grep for `rule table|Active|Docs Style
Rules` → no matches). Phase 1 refreshes these, so this is deferred rather than wrong — but the
justification for doing Phase 0 first (`PLAN-phases.md:45-48`, "Every later phase that touches a table
would otherwise deepen the drift") is undercut: before Phase 0 there were 3 drift cases; after it there
are 3 code↔prose cases (§1, §2, and `body-h1` now fixed) plus 4 new Notion↔shipped-copy cases.

**Remedy.** State in Phase 0's text that the shipped `style/*.md` copies are knowingly stale until
Phase 1, or refresh the four sections by hand now.

## 11. NIT — policy the checker decides that is in neither database

Verified absent from both data sources. My classification, argued:

*Should become rows (policy, an MT decision, retunable without code):*
- The `just` exclusion list `just (as|like|in time)` — `stylecheck.py:1017`.
- The `filler-please` exemption `"contact" not in sentence.lower()` — `stylecheck.py:1020`.
- `GET_IDIOM_RE` idioms `started|set up|connected|going|stuck` — `stylecheck.py:227`. An
  editorial list of acceptable `get` idioms, indistinguishable in kind from `vague_anchors`.
- `NOT_JSON_BODY_RE` command prefixes `curl|npm|yarn|python|ruby|node|$|#|GET|POST|PATCH|PUT|DELETE`
  — `stylecheck.py:171`. Decides which fences `json-parse` even looks at, i.e. it gates a strict rule.
- `JSON_FENCE_LANGS = {"json","json5"}` — `stylecheck.py:159`. Overlaps `fence_languages` and will
  drift from it.

*Legitimately stays in code (mechanism, matches `PLAN-subskills.md:135-137`):*
- `EMOJI_PRESENTATION_RANGES` / `EMOJI_TEXT_RANGES` / `REGIONAL_INDICATORS` / `SKIN_TONES` /
  `TAG_CHARACTERS` (`stylecheck.py:278-338`) — generated from Unicode data, not an MT decision.
- `IRREGULAR_PARTICIPLES` (`:177`), `PARTICIPLE` (`:191`), `CONTRACTED_S_HOSTS` (`:195`),
  `INTERVENING` (`:201`), `ABBREVIATIONS` (`:240`) — English morphology.
- `README_CALLOUT_EMOJI` (`:259`) — mirrors rdmd's themes map. See §7 on recording the omission.
- `DECORATIVE` (`:246`), `EVIDENCE_LIMIT = 200` (`:418`), every `*_RE` — implementation.
- `PROJECTS` tuple (`:95`) — duplicated by the `Scope` multi-select's options and the
  `project_url_prefixes` rows; harmless, but a third place the project list is written down.

## 12. NIT — `PLAN-phases.md` does not declare that `SKILL.md` was modified

`PLAN-phases.md:83-86` ("Built") declares: two databases, an index-page section, and base-style prose
"edited in four places". mtimes show a third workspace artifact changed inside the phase window:

```
2026-09-02 20:26:11  PLAN-phases.md
2026-09-02 20:14:00  PLAN-subskills.md
2026-09-02 20:01:27  skill/docs-style-review/SKILL.md
```

`/home/ubuntu/docs-style` is not a git repo (`fatal: not a git repository`) and no backup exists, so I
could not diff SKILL.md to establish what changed or whether it was material. This is exactly the
`SKILL.md:97` file that now contradicts the phase's premise (§3). `PLAN-subskills.md` was also edited
and is likewise undeclared.

**Remedy.** Declare both edits in Phase 0's "Built" paragraph, and put `/home/ubuntu/docs-style` under
git so the next phase's blast radius is auditable rather than inferred from mtimes.

---

## Claims verified as true (§7 of the brief)

Not everything failed. Verified by measurement:

- **30 rows / 87 rows / 86 active** — all three exact. `code rules 30 notion rows 30 code_only []
  notion_only []`.
- **"each of the 30 rules has a severity, a scope and a provenance"** — `null severity/scope/
  provenance: []`. Provenance matches `RULES[id][1]` on 29 of 30 (see §8c for the one).
- **Severity mapping** — `severity mismatches: []` against the code boolean.
- **Scope** — `scope mismatches: []`. All 30 match `OVERLAY_RULES` exactly: `contractions`→platform,
  `no-ordered-lists`/`reference-no-shell`→reference, the other 27 →all.
- **Thresholds** — `sentence-length` 30 = `MAX_SENTENCE_WORDS`; `list-depth` 3 = `MAX_LIST_DEPTH`.
- **Value lists match code element-for-element**, zero code-only and zero Notion-only values, for
  `object_names` (14), `vague_anchors` (7), `fence_languages` (16), `currency_codes` (14),
  `callout_emoji` (3), `object_shorthand` (7), `fence_language_fixes` (5), `acronym_expansions` (10),
  `project_url_prefixes` (4), and `filler_words` against the *active* subset (6/6 both ways). This is
  the phase's genuine achievement and it is solid.
- **"four places" in base-style prose** — all four edits confirmed present in the live page: LAC in
  the shorthand list, the "all but `just`" clause, `body-h1` in the structure heading, and the
  inverted excerpt section. (Three of the four are wrong for other reasons — §1, §2, §10 — but the
  count is honest.)
- **`body-h1` drift case is cleanly resolved.** Row has `Guide alias = first-heading-h1`, prose adopts
  `body-h1`, code reports `body-h1`. No defect found.
- **`LAC` drift case is cleanly resolved.** Row active with an explanatory note, prose lists it, code
  enforces it (`SHORTHAND`, `stylecheck.py:59`). No defect found.

## Hypotheses I tried to prove and could not (recorded so they are not re-litigated)

- **List-order dependence.** I expected `OBJECTS` order to be load-bearing (longest-prefix matching)
  and Notion to lose it. It is not. `check_object_capitalization` (`stylecheck.py:996-1006`) `break`s
  per object, not globally, so "Ledger Account" and "Ledger Account Category" both fire independently.
  I re-ran the checker with `OBJECTS` replaced by its alphabetical sort on a fixture containing
  "ledger account category" and got byte-identical findings, because `report` sorts by
  `(r.line, r.rule, r.message)` (`stylecheck.py:1127`). Same for `SHORTHAND` and `CURRENCY_CODES`
  (all 3-char, no prefix relations, so alternation order is immaterial at `:252`).
  `CALLOUT_EMOJI_BY_LENGTH` derives its order in code via `sorted(..., key=len, reverse=True)`
  (`:272`), so Notion never needs to carry it. **No ordering column is needed.**
- **`reference`→`/platform/` prefix collision.** Not a defect. `PROJECT_URL_PREFIX` is keyed by
  project, and the Values rows key on the project name (`Value`) with the prefix in `Maps to`, so two
  projects sharing `/platform/` compiles unambiguously. Diff clean, 4/4.
- **Fence-fix-before-unknown ordering.** `stylecheck.py:795-798` consults `FENCE_LANG_FIXES` then
  `STANDARD_FENCE_LANGS` in an `if/elif`. That ordering is code control flow, not data, so no row
  ordering is required. The `Value table` pointers (`fence-language`→`fence_language_fixes`,
  `fence-language-unknown`→`fence_languages`) are correct.
- **Tuple vs set vs list.** Real (`CURRENCY_CODES` tuple, `STANDARD_FENCE_LANGS` set, `OBJECTS` list)
  and not recorded anywhere in Notion, but no behaviour depends on the container type; a sync can pick
  per-table in the schema. Nit at most, folded into §8.

## Blast radius — clean (§6 of the brief)

```
$ git -C /home/ubuntu/repos/<repo> status --porcelain     # docs-readme-payments, -platform, -ledgers, monorepo
(no output for all four)
```

No new branches: newest branch in each repo predates today (`docs-readme-platform` HEAD
`cf7203a9`, 2026-09-01; `monorepo` `master` 2026-08-27; `docs-readme-payments` 2026-08-26;
`docs-readme-ledgers` 2026-05-18). No new commits. `find / -xdev -newermt "2026-09-02 19:30" -type f`
outside the workspace returned only `/opt/.devin/*` and `/etc/*` session infrastructure and one
user-uploaded attachment (`/home/ubuntu/attachments/…/reusable-content-proposal.md`) — nothing
authored by this phase. Inside the workspace, only the three files in §12.
The Notion writes are the intended ones. `dev/` and `audit/` remain unshipped and no shipped file
references them. **No finding.**

## Judgement on whether Phase 1 is buildable from this

Yes, with §1, §2, §4 and §8 fixed first. The value tables are element-exact against the code, which is
the hard part and it is done. What Phase 1 cannot do today: satisfy its own exit criterion
("reproduces today's constants exactly except for the three intentional drift fixes"), because §1 makes
a fourth, unintended change mandatory under the `Active` rule, §4 compiles a rule against the wrong
list, and §8 makes byte-exactness impossible for two dicts and one provenance string. The "checker
never reads Notion at runtime" constraint is not violated by anything Phase 0 built — no shipped file
gained a network call.

## Remedies not applied

I changed nothing. The brief permitted me to correct pure documentation inaccuracies in
`PLAN-phases.md`, but every inaccuracy I found (§1, §2) requires a policy decision about which
direction to resolve, so correcting the text would presuppose the answer. Exact replacement text for
`PLAN-phases.md:45-46`, for whoever takes the decision:

> Three tables already disagree with the shipped code (`just` is reported by a hard-coded branch in
> `check_filler` outside `BANNED_FILLER`, so the guide's list and the code's list disagree even though
> the finding fires; `LAC` enforced by code and absent from the guide; `first-heading-h1` in the guide
> reported as `body-h1` by 434 findings).

and for `PLAN-phases.md:69-71`, delete "because it is filler only in the minimizer sense and the
checker cannot yet separate that from *just three fields*" — `stylecheck.py:1017` implements exactly
that separation.

## Severity counts

blocking 4 (§1, §2, §3, §4) · should-fix 6 (§5, §6, §7, §8, §9, §10) · nit 2 (§11, §12)
