<!-- Compiled from Notion by scripts/notion_sync.py. Do not edit; edit https://app.notion.com/p/3c8d6bfc26838079bbe1f3ef57ef817a
     policy 718466089eff · synced 2026-09-03T21:34:37+00:00 -->
How to validate a page against this guide, in what order, and what to do with what you find.
There is a companion skill — **docs-style-review** — that carries a runnable checker for every strict rule that can be checked mechanically. This page is the procedure; the skill is the tooling.
## The order of work
Do the cheap mechanical pass first, so close reading is spent on voice and accuracy.
1. **Identify the project.** Ledgers, Payments, platform guides, or API reference. Read **01 — Base Style** plus that one overlay.
2. **Run the checker** on the changed pages. Fix every strict finding.
3. **Read the flexible findings.** Each is a judgment call — long sentences, passive voice, absolute links, acronyms. Fix what is genuinely worse; leave what reads better.
4. **Read the page for voice.** The three questions the checker cannot answer:
	- Does the tense match where the action happens — present inside Modern Treasury, future at the bank?
	- Is the person right and consistent within each section?
	- Do procedural sections open with verbs?
5. **Check accuracy.** Endpoints, field names, enum values and screenshots against the current product. Style is not worth much on a page that is wrong.
6. **Check consistency choices.** Anything in **06 — Flexible Conventions** must be consistent within its boundary: new-tab links, code order, callout use.
## What "correct" means for each finding
<table header-row="true">
<tr>
<td>Finding</td>
<td>Correction</td>
</tr>
<tr>
<td>Strict violation</td>
<td>Fix it in this change. No discussion needed.</td>
</tr>
<tr>
<td>Flexible note</td>
<td>Judge it. Fix if the alternative reads better.</td>
</tr>
<tr>
<td>Rule you disagree with</td>
<td>Fix the page now, raise the rule separately. Do not leave a page mid-standard.</td>
</tr>
<tr>
<td>Rule that does not exist</td>
<td>Not a finding. Do not invent style in review.</td>
</tr>
</table>
## Scope of a correction
- **Editing a page:** bring the parts you touch into compliance. You are not required to clean the rest, and you should not silently rewrite unrelated sections.
- **New page:** no strict violations, ever.
- **Corpus-wide cleanups:** one rule at a time, as its own change, so the diff is reviewable.
## Reviewing someone else's page
Say which rule, and quote the guide. "This reads oddly" is not review feedback; "base style, active voice — name the actor" is. If your objection is not in the guide, it is a suggestion, and label it as one.
## Frequent corrections
The corrections that come up most, with the fix:
<table header-row="true">
<tr>
<td>Problem</td>
<td>Fix</td>
</tr>
<tr>
<td>Fence tagged `curl` or `bash`</td>
<td>`shell`</td>
</tr>
<tr>
<td>`MT` in prose</td>
<td>Modern Treasury</td>
</tr>
<tr>
<td>`LA`, `LT`, `EP`, `PO`, `IPD`</td>
<td>Full object name</td>
</tr>
<tr>
<td>`in order to`</td>
<td>`to`</td>
</tr>
<tr>
<td>`Note that X`</td>
<td>`X`, or a 📘 callout</td>
</tr>
<tr>
<td>`simply`, `just`, `easily`</td>
<td>Delete</td>
</tr>
<tr>
<td>Lowercase object (`ledger account`)</td>
<td>Capitalize, or inline-code if it is a field</td>
</tr>
<tr>
<td>Anchor text `here` / `learn more`</td>
<td>Name the destination</td>
</tr>
<tr>
<td>Bold heading</td>
<td>Plain heading</td>
</tr>
<tr>
<td>Image with no alt text</td>
<td>Describe what the image shows</td>
</tr>
<tr>
<td>`excerpt` present in frontmatter</td>
<td>Delete it — we do not use excerpts</td>
</tr>
<tr>
<td>30+ word sentence</td>
<td>Split at the comma joining two facts</td>
</tr>
<tr>
<td>Absolute link to a page in the same repo</td>
<td>Relative path</td>
</tr>
<tr>
<td>`$` and ISO codes on one page</td>
<td>Pick one for the whole page</td>
</tr>
</table>
## When the guide is wrong
The guide describes how we write, so it is expected to change. If a rule is wrong or missing, propose the edit to the page it belongs in and say what pages it affects. Do not encode a personal preference as a rule, and do not enforce an unwritten one.
<empty-block/>
