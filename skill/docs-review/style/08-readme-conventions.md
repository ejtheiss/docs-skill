# ReadMe conventions

Use these authoring conventions with **01 — Base Style** and the project overlay.
Examples come from the HEAD corpus recorded in `dev/gate/evidence/phase-a.md`.
Corpus syntax is evidence of what ReadMe content contains, not proof that every
existing page meets the current policy. No browser rendering is claimed here.

## Frontmatter

Start a page with YAML between `---` delimiters. `title` is required
(`frontmatter-title`). Do not add `excerpt` (`frontmatter-excerpt`, reported
flexible). Include only fields the page uses: for example, explicit `hidden` or
`deprecated` publication settings, populated `metadata` settings, or populated
`next` navigation. Do not copy empty `metadata`/`next` blocks or empty child values.
The page templates start with `title` only; add other fields deliberately.

```yaml
---
title: Connect accounts
---
```

Corpus witness: `docs-readme-payments/docs/Bring your own Bank/virtual-accounts/creating-nested-internal-accounts.md`
starts with `title`, `deprecated`, `hidden` and a populated `metadata.robots`, with
no excerpt. Older exports such as
`docs-readme-ledgers/docs/Categories/nest-ledger-categories.md` also contain empty
metadata children and `next.description`; these are legacy export noise, not
fields to carry into a new template.

## Callout components

Use a paired component with both attributes (`callout-emoji`):

```html
<Callout icon="📘" theme="info">
  Confirm the prerequisites before you start.
</Callout>
```

| Icon | Theme | Purpose |
|---|---|---|
| 📘 | `info` | Information and prerequisites |
| 🚧 | `warn` | Limitations and early access |
| 💡 | `default` | Tips in tutorials and quickstarts |

Attribute order and single or double quotes do not change the pair. Emoji
variation selectors are accepted. Missing/wrong themes and unapproved icons are
findings. Existing blockquote callouts remain recognized, but new content uses
the component.

Corpus witnesses: the nested-accounts page above uses `icon="📘" theme="info"`;
`docs-readme-ledgers/docs/Get Started/ledgers-tutorials/bill-payments-tutorial.md`
uses `icon="💡" theme="default"`. The measured corpus also contains mismatched and
missing attributes; do not copy those forms.

## Code tabs

Every fence declares a language (`fence-untagged`). Use `curl` for curl requests,
`json` for payloads/responses, and `shell` only for non-request commands
(`fence-language`). A label follows the language; only the first token is the
language. Consecutive fences are the code-tab authoring pattern:

````text
```curl cURL
curl https://example.com
```
```json Response
{}
```
````

Corpus witness: `docs-readme-payments/docs/Bring your own Bank/virtual-accounts/creating-virtual-accounts.md`
contains consecutive `curl` fences labeled “Create a Virtual Account with an
account number” and “Create a Virtual Account without an account number”. Labels
are allowed, not forbidden captions. Reference request snippets belong in guides
instead (`reference-no-shell`).

## Navigation links

Within a project, use `[Guide](doc:slug)` or `[Object](ref:slug)`. Across projects,
use an absolute `https://docs.moderntreasury.com` URL. Do not substitute relative
file paths (`link-absolute-internal`, reported flexible). Platform guides and API
reference are separate projects for this policy.

Corpus witness: `docs-readme-payments/docs/Payments/receiving-payments/receiving-ach-debits.md`
uses `doc:initiate-an-ach-debit` locally and an absolute platform reference URL
for `create-internal-account`. `docs-readme-platform/custom_blocks/ReturnObjectAttributes.md`
uses `ref:returns` and other reference shorthand. The corpus also contains older
cross-project shorthand; that does not override the cross-project URL decision.

## Image components

Use `<Image>` with `src` and meaningful `alt` for new/touched images (`image-alt`).
Untouched existing images are not backfilled. Use `align`, `width`, `border` and
`caption` only when needed; a caption is not a substitute for alt text. ReadMe
uses JSX booleans for borders:

```html
<Image src="https://files.readme.io/example.png" alt="Selected account permissions" align="center" border={false} />
```

Corpus witness: `docs-readme-platform/docs/Developer Tools/api-keys-1/api-key-permissions.md`
contains an Image with `alt`, `align="center"`, `border={false}`, `caption` and
`src`. `docs-readme-payments/docs/Workflows & Reporting/payment-order-management/create-payment-orders-in-bulk.md`
also uses optional `width` values. Both self-closing components and paired forms
occur in the corpus. Markdown images remain recognized by the checker.
