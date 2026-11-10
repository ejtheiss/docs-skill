Applies to every page in every repo. Read this plus the one overlay for your project.
Each rule is **Strict** (corrected on sight) or **Flexible** (your call, then be consistent). The rule ID in brackets is what the checker reports.
---
## Voice and tense
### Present tense for anything happening in Modern Treasury — **Strict**
Reserve `will` for what happens later or outside the platform: at the bank, on the network, in the reader's own system.
**Do**
> Create a Ledger Transaction to record that Jane Doe has deposited \$100 in her user wallet account.
> The metadata fields in the received Transaction object will be filled by your bank.
**Don't**
> Selecting a transaction and clicking on the Reconcile button will allow you to create a Ledger Transaction.<br>→ Select a transaction and click **Reconcile** to create a Ledger Transaction.
> When creating a transaction, Ledgers will request that you ensure debits equal credits.<br>→ Ledgers requires debits to equal credits within each currency.
### Imperative for product functionality — **Strict**
Anything the reader does opens with a verb.
**Do**
> Use the `POST /ledger_transactions` endpoint to post Ledger Entries onto your Ledger Accounts.
> Create a Ledger using the [Create Ledger endpoint](https://docs.moderntreasury.com/platform/reference/create-ledger) (`POST /ledgers`).
**Don't**
> The next thing that needs to happen is the creation of a Ledger Transaction.<br>→ Create a Ledger Transaction.
### Active voice — **Flexible** (`passive-voice`)
Name the actor. Passive is acceptable only when the actor is the bank, the network or the counterparty, and naming it adds nothing.
A sentence that already names its actor in a `by` phrase satisfies this, and the checker no longer reports it. Of the findings that remain, an editorial pass judged roughly two in three worth rewriting — which is why this is advice a writer weighs, not a gate.
**Do**
> Each row's bank balance comes from the bank Balance Report.
> A `debit` Incoming Payment Detail is created when the Virtual Account is debited. *(bank-side; passive is fine)*
**Don't**
> The bank balance within a row is populated from the bank Balance Report.
> The posted balance is used as it represents the reconciled funds in the ledger.<br>→ Reconciliation uses the posted balance because it represents reconciled funds.
### Person follows the project overlay — **Strict**, reviewer judgment
`you` is what the reader decides or does outside Modern Treasury. `we` is a worked example we walk through together, and its default differs by project (see overlays). Never switch inside a section.
The guide and overlay decide the person, not a corpus majority. Ledgers walkthroughs use `we`; Payments and platform tasks address `you`.
> You will need to calculate total interest due to the loan provider outside of Modern Treasury.
> We will use Ledger Account Categories to track the overall balance across all our users' wallets.
### Sentences stay under about 30 words — **Strict** (`sentence-length` is reported as flexible, judged in review)
Long sentences are almost always two facts joined by a comma. Split them.
**Don't**
> When a Virtual Account is debited a `debit` IPD is created, the Virtual Account's Ledger Account will be debited the amount of the outbound payment and the internal account's ledger account will be credited the amount of the outbound payment.
**Do**
> Debiting a Virtual Account creates a `debit` Incoming Payment Detail. Modern Treasury debits the Virtual Account's Ledger Account and credits the Internal Account's Ledger Account for the outbound payment amount.
### No filler, no hedging — **Flexible** (`filler`, `filler-please`)
Banned: `simply`, `just` (as a minimizer), `easily`, `obviously`, `of course`. Both filler rules are reported flexible. `just` is exempt in the senses that are not minimizers: `just as`, `just like`, `just in time`.

| Banned wording | Correction |
|---|---|
| `seamlessly`, `powerful`, `robust` | State the specific capability, or delete |
| `best-in-class`, `battle-tested` | Supply a supported fact, or delete |
| `leverage` as a verb | `use`; noun uses such as `leverage ratio`, `the leverage`, `financial leverage` are exempt |
| `our SE team` | Name the responsible team or contact |
Write `to`, not `in order to`.
Delete `Note that` — state the fact, or make it a 📘 callout.
`please` only in a direct request to contact someone.
<table header-row="true">
<tr>
<td>Don't</td>
<td>Do</td>
</tr>
<tr>
<td>For this, we simply need the ids of both the parent Category and the Ledger Account.</td>
<td>We need the IDs of the parent Category and the Ledger Account.</td>
</tr>
<tr>
<td>Link Internal Accounts to Ledger Accounts in order to automatically ledger payments.</td>
<td>Link Internal Accounts to Ledger Accounts to ledger payments automatically.</td>
</tr>
<tr>
<td>This enables you to easily "roll up" balances that comprise many Ledger Accounts.</td>
<td>Roll up balances across many Ledger Accounts.</td>
</tr>
<tr>
<td>Note that the transaction is created in a `pending` state.</td>
<td>The transaction starts in a `pending` state.</td>
</tr>
</table>
---
## Terminology
### Capitalize Modern Treasury objects — **Strict** (`object-capitalization`)
Ledger, Ledger Account, Ledger Account Category, Ledger Account Settlement, Ledger Transaction, Ledger Entry, Ledger Event Handler, Payment Order, Internal Account, External Account, Virtual Account, Expected Payment, Incoming Payment Detail, Legal Entity, Balance Report.
Lowercase the everyday concept, capitalize the object, inline-code the API field.
> A Balance Report is a collection of balances at a specific point in time for an internal account.<br>→ …for an Internal Account.
> Each ledger account object can record transactions and balances in a single currency.<br>→ Each Ledger Account can record transactions and balances in a single currency.
**Transaction, Invoice, Return, Counterparty, Document and Event** are ordinary English words too.
Capitalize only when you mean the object, and disambiguate when the sentence reads either way: *a bank-reported transaction*, *the Transaction object*.
Not checked automatically — this one is on the reviewer.
### Write "Modern Treasury" — **Strict** (`mt-shorthand`)
Never `MT` in prose.
> That calculation was made externally from MT. → …outside Modern Treasury.
### No object shorthand — **Strict** (`object-shorthand`)
`LA`, `LT`, `LAS`, `EP`, `PO`, `IPD`, `LAC` are banned in prose. They collide across objects, which is the confusion capitalization exists to prevent.
> The LAS and the EP are now linked together through a common Ledger Transaction.<br>→ The Ledger Account Settlement and the Expected Payment are now linked together through a common Ledger Transaction.
### Expand industry acronyms on first use per page — **Strict** (`acronym-undefined` is reported as flexible, judged in review)
ACH, RTP, EFT, FX, KYC, SDK, IAT, SEPA, BACS, NACHA: *Real-Time Payments (RTP)*, then RTP for the rest of the page. `API` needs no expansion.
### Endpoints, fields, events and values are inline code — **Strict**, reviewer judgment
Write `POST /ledger_transactions`, `normal_balance`, `pending` and the exact event name in inline code. Never use bold, quotes or backslash escapes in place of inline code.

### No em dashes in prose — **Strict** (`em-dash`, reported flexible)
Use a comma, colon or separate sentence. Paragraphs, headings and component prose count; frontmatter, code and Markdown or HTML tables do not.
---
## Structure
### First heading is h1 on new pages; levels never skip — **Strict** (`body-h1`, `heading-skip`)
The first body heading is h1 in draft mode and on new files. Existing pages are not backfilled, even when edited. Review without a Git base does not infer new files. `heading-skip` remains active on pages opening at h1 or h2.
h1 → h2 → h3. A subtopic of a heading is one level deeper, never two.
```text
# Use Cases
## Use Case 1
### Use Case 1 Set-Up
```
### Headings carry no formatting — **Strict** (`heading-formatting`)
ReadMe's heading format only. No bold, italics or underline inside a heading.
> **Example Ledger → ### Example Ledger**
### No heading restates the page title — **Strict** (`heading-repeats-title`)
An `Overview` section says something the title does not, or it is deleted.
### Lists nest at most three levels — **Strict** (`list-depth`)
Numbered list for a sequence the reader performs in order, or a definite count. Bullets otherwise.
Which dominates is project-specific.
### Every code fence declares a language — **Strict** (`fence-untagged`, `fence-language`)
`curl` for curl requests, `json` for payloads and responses, `sql` for queries, then the language name for SDK snippets. Use `shell` only for non-request commands such as `npm install`, not `bash` or `sh`.
ReadMe tab labels follow the language: fence info such as `curl cURL` and `json Response` is allowed. Only the first token is the language; consecutive fences form code tabs.
### Frontmatter has `title` — **Strict** (`frontmatter-title`); and no `excerpt` — **Flexible** (`frontmatter-excerpt`)
We do not use excerpts. Do not add one to a new page, and delete the one you find on a page you are already editing.
The checker reports a *present* excerpt as a deletion, so the pages still carrying one are a cleanup list rather than a wall of failures. Flexible: a page is not wrong to ship while it still has one.
Templates include only frontmatter fields the page uses. Do not copy empty `metadata` or `next` blocks. See **08 — ReadMe Conventions** for examples.
---
## Links, callouts, images
### Anchor text names the destination — **Strict** (`link-anchor-vague`, `link-anchor-empty`, `link-bare-url`)
Banned anchors: `here`, `this page`, `this link`, `link`, `click here`, `read more`, `learn more`.
Never print a bare URL as a link.
> Read more about this [here](https://app.notion.com/p/moderntreasury/%E2%80%A6). → Read more about [locking on Category balance](https://app.notion.com/p/moderntreasury/%E2%80%A6).
### Internal links use project shorthand — **Strict** (`link-absolute-internal` is reported as flexible, judged in review)
Use `doc:slug` for guides and `ref:slug` for reference within a project. Across projects, use absolute `https://docs.moderntreasury.com` URLs. Do not use relative file paths such as `../x.md` or `./y`. Platform guides and API reference are distinct projects.
### Callouts use the component and approved pairs — **Strict** (`callout-emoji`)
Write `<Callout icon="📘" theme="info">`, `<Callout icon="🚧" theme="warn">` or `<Callout icon="💡" theme="default">`, with a closing `</Callout>`. An approved icon also requires its matching theme. Existing blockquote callouts remain recognized; use the component for new content.
📘 information, 🚧 early access or limitation, 💡 tip in a tutorial or quickstart. ❗️, 👍 and ⚠️ are not ours — map them to 📘 or 🚧.
How often you use callouts is project-specific.
### New and touched images have alt text — **Strict** (`image-alt`)
Use ReadMe's `<Image>` component. Describe what the reader learns, not the file: `<Image src="…" alt="Reconciliation rule matching two values" align="center" />`.
Alt is required for new and touched images, not an existing-image backfill. Draft checks all images; review uses `--base` to identify changed syntax. Markdown images remain recognized.
Mask customer data and account numbers in screenshots, and refer to a screenshot by what it shows rather than "the image below".
### One currency format per page — **Strict** (`currency-mixed`)
`$` when USD is the only currency on the page.
As soon as a second currency appears, use the ISO code after the amount (`1,200 USD`) everywhere on that page.
Never mix the two.
