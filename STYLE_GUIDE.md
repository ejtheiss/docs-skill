# Modern Treasury Documentation Style Guide

Derived from the documentation as it stood before 2026-03-13 (667 pages: 312 guides, 344 API
reference pages), so every rule below is what our own writers already did, not an outside opinion.
Each rule carries the share of the corpus that follows it, plus real examples pulled from named
pages. Rules marked **Decision needed** are places where the corpus genuinely disagrees with itself;
they are recorded rather than invented so they can be settled deliberately.

The guide has two layers:

- **Base style** — rules every project already follows. Applies everywhere, no exceptions.
- **Project overlays** — Ledgers, Payments, Platform guides and API reference differ measurably in
  voice and formatting. Each overlay records only where that project departs from base.

When authoring or reviewing a page, read the base style plus the one overlay for the page's repo.

---

# Part 1 — Base style

## 1.1 Prose

### Write in the present tense for anything happening in Modern Treasury

Reserve `will` for outcomes that happen later or outside the platform.

> Create a Ledger Transaction to record that Jane Doe has deposited $100 in her user wallet account.

> The metadata fields in the received Transaction object will be filled by your bank.

`will` appears 9.7–13.7 times per 1,000 words across projects, concentrated in bank- and
network-dependent outcomes, which is the pattern to keep. Rewrite platform-side `will`:

| Instead of | Write |
|---|---|
| Selecting a transaction and clicking on the Reconcile button will allow you to create a Ledger Transaction… (`ledgers/docs/Accounts/account-reconciliation/index.md`) | Select a transaction and click **Reconcile** to create a Ledger Transaction and matching Expected Payment. |
| When creating a transaction, Ledgers will request that you ensure debits equal credits within each currency. (`ledgers/docs/Accounts/currencies/use-multiple-currencies.md`) | Ledgers requires debits to equal credits within each currency. |

### Use the imperative for product functionality

Steps and API instructions open with a verb. Real examples, both conforming:

> Create a Ledger using the [Create Ledger endpoint](https://docs.moderntreasury.com/platform/reference/create-ledger) (`POST /ledgers`).
> — `ledgers/docs/Get Started/ledgers-tutorials/bill-payments-tutorial.md`

> Use the `POST /ledger_transactions` endpoint to post Ledger Entries onto your Ledger Accounts.

Imperative openings run 4% (API reference) to 15% (platform guides) of sentences. That is a floor,
not a ceiling: procedural sections should be close to 100% imperative.

### Address the reader as "you" for their decisions, "we" for a shared walkthrough

Both are in the corpus and both are correct in their place — `you` for what the reader must decide or
do outside Modern Treasury, `we` for walking through a worked example together.

> You can perform account reconciliation in Modern Treasury to resolve the variance between a balance in your ledger and a balance reported by a bank or vendor.
> — `ledgers/docs/Accounts/account-reconciliation/index.md`

> We can use the [add Ledger Account to Category](https://docs.moderntreasury.com/reference/add-ledger-account) endpoint to add an account to a Category.
> — `ledgers/docs/Categories/ledger-account-categories-overview/add-a-ledger-account-to-a-ledger-category.md`

Do not switch between them inside a single section. Mixing across a whole page is common (52% of
pages contain both), so this is a section-level rule, not a page-level one.

### Keep sentences under ~30 words

Median sentence: 15–18 words; 90th percentile: 26–33. Sentences past 30 words are where the corpus
starts failing, usually by chaining two facts with a comma:

> When a Virtual Account is debited a `debit` IPD is created, the Virtual Account's Ledger Account will be debited the amount of the outbound payment and the internal account's ledger account will be credited the amount of the outbound payment.
> — `ledgers/docs/Accounts/link-ledger-accounts-to-payment-objects/link-a-ledger-account-to-a-virtual-account.md`

Rewrite as: *Debiting a Virtual Account creates a `debit` Incoming Payment Detail. Modern Treasury
debits the Virtual Account's Ledger Account and credits the Internal Account's Ledger Account for the
outbound payment amount.*

### Prefer active voice; use passive only when the actor is the bank or is genuinely unknown

Passive voice is 23–28% of sentences today. Most of it is avoidable:

| Passive, from the corpus | Active rewrite |
|---|---|
| The bank balance within a row is populated from the bank Balance Report. (`ledgers/docs/Accounts/account-reconciliation/balances-used-in-account-reconciliation.md`) | Each row's bank balance comes from the bank Balance Report. |
| The posted balance is used as it represents the reconciled funds in the ledger. (same page) | Reconciliation uses the posted balance because it represents reconciled funds. |

Passive is acceptable when the bank or network is the actor and naming it adds nothing: *A `debit`
Incoming Payment Detail is created when the Virtual Account is debited.*

### Cut filler and hedging

Banned outright: `simply`, `just` (as a minimizer), `easily`, `obviously`, `of course`.
Replace `in order to` with `to`. Drop `please` except in a direct request for contact. Replace
`Note that X` with `X`, or a 📘 callout if it deserves emphasis.

| Corpus sentence | Rewrite |
|---|---|
| For this, we simply need the ids of both the parent Category and the Ledger Account… | We need the IDs of the parent Category and the Ledger Account. |
| You can link Internal Accounts or External Accounts to Ledger Accounts in order to automatically ledger payments… | Link Internal or External Accounts to Ledger Accounts to ledger payments automatically. |
| This enables you to easily "roll up" balances that comprise many Ledger Accounts… | Roll up balances across many Ledger Accounts. |
| Note that the transaction is created in a `pending` state. | The transaction starts in a `pending` state. |

Current density is 2.6–3.0 filler terms per 1,000 words; the top offenders across guides are `please`
(79), `note that` (58), `in order to` (53) and `simply`/`just`/`easily` (71).

## 1.2 Terminology

### Capitalize Modern Treasury objects

Ledger Account, Ledger Transaction, Ledger Entry, Payment Order, Internal Account, External Account,
Virtual Account, Expected Payment, Legal Entity, Incoming Payment Detail. Lowercase the same words
when you mean the everyday concept, and use inline code for the API field or object name.

> When an Incoming Payment Detail is received for an Internal Account with both ledger accounts configured, Modern Treasury automatically creates a Ledger Transaction…
> — `ledgers/docs/Accounts/link-ledger-accounts-to-payment-objects/auto-ledgering-incoming-payment-details-guide.md` (the lowercase "ledger accounts" here should be capitalized)

Four words are ambiguous on purpose and need judgment rather than a substitution rule: Transaction,
Invoice, Return, Counterparty. Capitalize only when referring to the Modern Treasury object; if the
sentence reads ambiguously either way, name it explicitly (*a bank-reported transaction*, *the
Transaction object*).

### Spell out "Modern Treasury"

Never `MT` in prose (91% conformance overall; platform guides are the outlier at 76%).

> That calculation was made externally from MT… → *…outside Modern Treasury.*
> — `ledgers/docs/Get Started/ledgers-tutorials/lending-tutorial.md`

### Never use object shorthand

`LA`, `LT`, `EP`, `PO`, `LAS`, `IPD` appear 148 times in guides and are banned in prose. Write the
full object name every time; abbreviating collides with other objects.

> The LAS and the EP are now linked together through a common Ledger Transaction.
> — `ledgers/docs/Settlements/linking-ledger-account-settlements-to-payment-objects/link-a-ledger-account-settlement-and-expected-payment.md`
> → *The Ledger Account Settlement and the Expected Payment are now linked through a common Ledger Transaction.*

### Define industry acronyms on first use per page

Applies to ACH, RTP, EFT, FX, KYC, SDK, IAT: *Real-Time Payments (RTP)*. `API` needs no expansion.

### Wrap endpoints, fields and values in inline code

All 51 endpoint references in guides are already inline code: `` `POST /ledger_transactions` ``.
Same for field names (`normal_balance`) and enum values (`pending`).

## 1.3 Structure

### Headings never skip a level

h1 → h2 → h3, no jumps (96% conformance). No bold, italics or underline in heading text.

### No heading repeats the page title

98% conformance. An `Overview` section must add information the title does not.

### Lists nest at most three levels

100% conformance — treat as a hard limit. Use a numbered list only for a sequence the reader performs
in order or a definite count; bullets otherwise.

### Every code fence declares a language

99% conformance. Untagged fences are a bug.

### Links carry descriptive anchor text

The anchor names the destination (100% conformance for having text at all; 96% for avoiding vague
anchors). Banned anchors: `here`, `this page`, `click here`, `read more`, `learn more`.

> Read more about this [here](https://docs.moderntreasury.com/ledgers/docs/handle-concurrency#locking-on-category-balance).
> — `ledgers/docs/Categories/ledger-account-categories-overview/index.md`
> → *Read more about [locking on Category balance](…).*

### Callouts use the sanctioned emoji set

📘 for information, 🚧 for early access or limitations, 💡 for tips in tutorials and quickstarts
(125 of 136 guide callouts, 92%). ❗️, 👍 and ⚠️ appear 11 times in guides and are not sanctioned — map
them to 📘 or 🚧. 💡 is carried over from the existing guide but appears zero times in the corpus; it is
allowed, not established.

### Frontmatter carries `title` and `excerpt`

`title` is present on 100% of pages. `excerpt` is on 96% of reference pages but only 51% of
guides — write one for every new page; it is the search and social description.

## 1.4 Images and accessibility

**Decision needed.** Only 3 of 53 images in the corpus have alt text (6%), so this cannot be stated
as an existing convention — it is a documented gap. Recommendation: require alt text on all new
images, and backfill in a dedicated pass. Alt text describes what the reader would learn from the
image, not the file: `![Reconciliation rule matching two values](…)`.

---

# Part 2 — Project overlays

Voice fingerprints, measured. Use them as the target when writing for that project.

| Metric | Ledgers | Payments | Platform guides | API reference |
|---|---|---|---|---|
| Median sentence words | 18 | 16 | 15 | 16 |
| Passive share | 28% | 28% | 23% | 27% |
| Imperative openings | 5% | 7% | 15% | 4% |
| `you`/`your` per 1k words | 20.5 | 33.3 | 29.9 | 23.8 |
| `we`/`our` per 1k words | 16.6 | 5.8 | 5.3 | 7.6 |
| Contractions per 1k words | 4.0 | 4.8 | 2.5 | 3.6 |
| Ordered-list share | 16% | 31% | 67% | 0% |
| Callouts per page | 0.03 | 0.35 | 0.86 | 0.15 |
| Code fences per page | 2.83 | 1.44 | 0.57 | 0.62 |

## 2.1 Ledgers (`docs-readme-ledgers`)

Teaching voice: longest sentences, heaviest use of `we`, densest code, almost no callouts.

- **Walk through worked examples in first person plural.** `we`/`our` is 3× the rate of any other
  project and is the house voice for tutorials. Keep `you` for what the reader decides.
- **Lead pages with h1.** 83% of Ledgers pages start at h1 — the strongest signal in the corpus, and
  the reason the base rule for first-heading level is Ledgers' convention rather than a corpus-wide
  average.
- **Shell fences are tagged `shell`.** `shell` 117, `curl` 37, `bash` 14 today; standardize on
  `shell` and convert the rest.
- **Explain double-entry consequences explicitly.** Every balance change names the account and the
  direction: *This account will get deducted (debited) by $1,200 in USD when the transfer is posted.*
- Callouts are effectively unused (2 in 72 pages). Do not add them to match other projects; use them
  only for genuine warnings.

## 2.2 Payments (`docs-readme-payments`)

Operational voice: shortest procedures, strongest second person, JSON-first examples.

- **Address the reader directly.** `you`/`your` at 33.3 per 1k words is the highest in the corpus;
  `we` is rare and should stay rare.
- **JSON before shell.** `json` 87 vs `curl` 68 vs `shell` 19 — show the payload, then the request.
  Standardize the request fences on `shell`.
- **Bank- and network-dependent outcomes take future tense and may take passive voice**, because the
  actor is the bank: *The metadata fields in the received Transaction object will be filled by your
  bank.*
- **Deep nesting is the norm here** (35% of pages sit 3+ levels below `docs/`, e.g.
  `docs/Money Movement/making-payments/ach/ach-return-codes.md`). **Decision needed:** either accept
  3 levels for rail-specific pages in Payments, or flatten. Recommendation: accept 3 levels where the
  third level is a payment rail, and cap there.

## 2.3 Platform guides (`docs-readme-platform/docs`)

Task voice: most imperative, most numbered, most callouts, least code.

- **Numbered steps by default.** 67% of lists are ordered — dashboard and configuration procedures
  are sequences. Number them and open each step with a verb (imperative openings are 15% here,
  triple any other project).
- **Callouts carry prerequisites and limits.** 0.86 per page, mostly 🚧.
- **Avoid contractions.** 2.5 per 1k words, the lowest in the corpus; this is a more formal register.
- **`MT` shorthand is a known problem here** (76% conformance vs 97–98% elsewhere). Spell it out.
- SQL examples are tagged `sql` (20 fences) — the only project where SQL appears.

## 2.4 API reference (`docs-readme-platform/reference`)

Spec-derived reference voice: terse, no procedures, no ordered lists.

- **No ordered lists** (0 of 19 lists) and almost no prose beyond object and field description.
- **`json` is the fence language** (184 of 214). Only 4 shell fences exist; keep shell out of
  reference pages and link to guides for workflows.
- **Object names in reference prose are often lowercase field names, not objects** (47%
  "capitalization conformance" is mostly correct usage of `ledger_account` as a field). Capitalize
  the object, inline-code the field.
- **`excerpt` is mandatory** — 96% of reference pages have one.
- Every page starts h1 or h2 with the object name; sections are `Working with X`, `Initiating X`.

---

# Part 3 — Open decisions

Each is a place where the corpus does not agree with itself. Recommendation given; none is settled.

| # | Decision | Evidence | Recommendation |
|---|---|---|---|
| 1 | First heading level: h1 or h2? | Ledgers 83% h1; Payments 43%; Platform 44%; reference 36% | Require h1 everywhere; it is the majority within the project that most consistently applies a rule, and ReadMe renders the page title separately. |
| 2 | Shell fence tag: `shell`, `curl`, or `bash`? | `shell` 153, `curl` 105, `bash` 14 | `shell`, and drop `bash` entirely. |
| 3 | Internal links: relative paths or absolute `docs.moderntreasury.com` URLs? | Guides 39% relative (Ledgers 17%, Payments 60%, Platform 29%); reference 71% relative | Relative paths inside a repo, absolute only when crossing repos. Cross-repo links are the reason absolute URLs dominate guides. |
| 4 | Guide nesting depth | Payments 65% within 2 levels; others ~100% | Allow a third level only for payment rails. |
| 5 | Alt text | 6% of images | Require on new images; backfill separately. |
| 6 | Currency format | `$` 176 uses vs 12 ISO-code amounts in guides; mixed on 5 pages | `$` when USD is the only currency on the page, ISO code (`1,200 USD`) when more than one appears — matching the existing guide, which the corpus mostly follows. |
| 7 | Ambiguous object names (Transaction, Invoice, Return, Counterparty) | 17–54% capitalized | Capitalize only for the object; add a disambiguating word when ambiguous. |
| 8 | `we` vs `you` scope | Both on 52% of pages | Enforce per section, not per page. |

---

# Part 4 — How this guide was built

Measurement pipeline, kept out-of-band and rebuilt ad hoc when a rule needs re-measuring: extract
each page into typed channels (headings, prose, lists, fences, callouts, links, images, frontmatter),
count conformance per project, and quote real examples. A rule is base style only when every project
conforms at ≥90%; it lands in an overlay when projects disagree by ≥25 points; otherwise it is an
open decision above.

Stylometric authorship methods (Burrows's Delta and a function-word classifier) were tested for
detecting off-style pages and rejected: Delta scored at chance (AUC 0.32–0.47), and a supervised
classifier separated our docs from unrelated engineering markdown at AUC 0.92 but only 0.44 from
other pages written for our own docs site. Off-style detection therefore runs on the rules above, not
on stylometric distance.
