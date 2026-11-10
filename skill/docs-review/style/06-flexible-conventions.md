Where we deliberately allow variation. The rule in every case is the same: **choose once, then stay consistent within the page** (or within the section, where noted). None of these is a defect in review, and none is worth an argument.
<table header-row="true">
<tr>
<td>Convention</td>
<td>Latitude</td>
<td>Consistency boundary</td>
</tr>
<tr>
<td>**Links opening in a new tab**</td>
<td>Writer's choice</td>
<td>The page</td>
</tr>
<tr>
<td>**Callout frequency**</td>
<td>Rare in Ledgers, common in platform guides</td>
<td>The project</td>
</tr>
<tr>
<td>**Payload-first vs request-first code order**</td>
<td>Writer's choice</td>
<td>The page</td>
</tr>
<tr>
<td>**How much code a page carries**</td>
<td>A Ledgers tutorial may be mostly code; a platform guide may have none</td>
<td>The page</td>
</tr>
<tr>
<td>**Table vs bullets for comparing options**</td>
<td>Writer's choice; a table wins past three attributes</td>
<td>The section</td>
</tr>
<tr>
<td>**Screenshot vs prose description of the UI**</td>
<td>Writer's choice; new and touched screenshots require alt text</td>
<td>The page</td>
</tr>
<tr>
<td>**Sentence length below the 30-word limit**</td>
<td>Vary it; short sentences in procedures, longer in concept prose</td>
<td>—</td>
</tr>
<tr>
<td>**Where a concept is explained**</td>
<td>Inline, or a link to the concept page</td>
<td>The page</td>
</tr>
<tr>
<td>**Diagram tooling and colors**</td>
<td>Any, as long as it is legible in ReadMe's light theme</td>
<td>—</td>
</tr>
</table>
## Not flexible
These choices are settled in **01 — Base Style**, subject to their stated contexts:
- First body heading is h1 on new pages and in draft mode (`body-h1`); no existing-page backfill. Levels never skip (`heading-skip`).
- Requests use `curl`; payloads use `json`; queries use `sql`. `shell` is only for non-request commands. ReadMe tab labels after the tag are allowed (`fence-language`).
- Callout components pair 📘 with `info`, 🚧 with `warn`, and 💡 with `default` (`callout-emoji`).
- Write Modern Treasury and full object names (`mt-shorthand`, `object-shorthand`).
- Anchor text names the destination (`link-anchor-vague`). Use `doc:`/`ref:` within a project and absolute documentation URLs across projects (`link-absolute-internal`, reported flexible).
- Currency format is consistent within a page (`currency-mixed`).
- New and touched images require alt text (`image-alt`).
- Person follows the overlay, not a corpus majority; field and event names use inline code, not backslash-escaped prose (reviewer judgment).

## Decisions on existing content
Both backlog questions are decided:
1. **h1 first:** new pages only, with draft treating every file as new. Do not shift headings on existing pages merely to backfill h1.
2. **Alt text:** required on new and touched images only. Untouched images are not backfilled.

Review without `--base` does not activate either contextual rule. Use `--base <git-ref>` to identify new files and touched image syntax, or `--mode draft` to check new-page readiness.
