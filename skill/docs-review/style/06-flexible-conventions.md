<!-- Compiled from Notion by scripts/notion_sync.py. Do not edit; edit https://app.notion.com/p/3c8d6bfc26838011a16ccf4511c8a0c7
     policy 718466089eff · synced 2026-09-03T21:34:37+00:00 -->
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
<td>**"we" vs "you"**</td>
<td>Project default (see overlays); a page can use both</td>
<td>The section</td>
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
<td>Writer's choice; a screenshot needs alt text either way</td>
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
These get raised as questions often enough to name explicitly. They are settled in **01 — Base Style**, and are not writer's choice:
- Heading level of the first heading (h1).
- Code fence language tags (`shell`, `json`, `sql` — never `curl`, `bash`, `sh`).
- Callout emoji set (📘, 🚧, 💡).
- `MT`, and object shorthand such as `LA` or `LT`.
- Anchor text (never `here`, `learn more`).
- Currency format within a page.
- Alt text on images.
## Needs a decision, not yet settled
Two items are written as strict rules in this guide but have a backlog cost attached, so the owning team should confirm before enforcement lands on existing pages:
1. **h1 as the first heading.** Most existing pages start at h2. Applying this is a mechanical heading shift across the corpus.
2. **Alt text on every image.** Almost no existing image has it. New and edited images comply; the backfill is separate scheduled work.
Until those are confirmed, the checker reports them, and you fix them in pages you touch rather than opening a corpus-wide cleanup.
