<!-- Compiled from Notion by scripts/notion_sync.py. Do not edit; edit https://app.notion.com/p/3c8d6bfc2683805a9d6ffa77cef00542
     policy 718466089eff · synced 2026-09-03T21:34:37+00:00 -->

<!-- Authored but not enforced: nothing — every row is active. -->
How we write documentation. Base style applies to every page; each project adds an overlay for what is specific to it.
## How to use this guide
- **Writing a new page:** read **01 — Base Style**, then the one overlay for your repo.
- **Editing an existing page:** fix strict violations in what you touch. You do not have to clean the whole page.
- **Reviewing:** the strict rules are the review checklist. Run the checker (**07 — Review & Correction**) before reading closely, so review time goes to voice and accuracy rather than fences and heading levels.
## Strict versus flexible
Every rule in this guide is labeled.
<table header-row="true">
<colgroup>
<col>
<col width="533">
</colgroup>
<tr>
<td>Label</td>
<td>Meaning</td>
</tr>
<tr>
<td>**Strict**</td>
<td>Not a preference. A page that breaks it is wrong and gets corrected. Most strict rules are checked automatically.</td>
</tr>
<tr>
<td>**Moderate**</td>
<td>A measured convention rather than a correctness question. Departing from it needs a reason in review; it does not fail a page on its own.</td>
</tr>
<tr>
<td>**Flexible**</td>
<td>Deliberate latitude. Choose per page or per section, then stay consistent within it.</td>
</tr>
</table>
If a rule is not in this guide, it is not a rule.<br>
<database url="https://app.notion.com/p/3c8d6bfc268380688793ec324ec19379" inline="true" data-source-url="collection://3c8d6bfc-2683-8003-af98-000b2a389cc2">Docs Style Guides</database>
## The rule tables
The prose in these pages explains the rules. The two databases below are the machine-readable projection of them: the checker's severities, thresholds, word lists and code tables compile from these rows, so changing a rule's list or grade is an edit here rather than a code change.
<table header-row="true">
<tr>
<td>Table</td>
<td>What it holds</td>
</tr>
<tr>
<td>**Docs Style Rules**</td>
<td>One row per rule: severity, project scope, numeric threshold, and which value table it reads.</td>
</tr>
<tr>
<td>**Docs Style Rule Values**</td>
<td>The lists and maps themselves: object names and shorthand, filler words, vague link anchors, code-fence tags, acronym expansions, currency codes, callout emoji, per-project URL prefixes.</td>
</tr>
</table>
Two things to know before editing them:
A rule carries two grades, because they answer different questions. **Guide severity** is what a reviewer applies when reading the page. **Reported severity** is the grade a checker run prints, and it can only be as strong as the rule's measured precision — so `sentence-length` is strict guidance reported as flexible until it is adjudicated, and `passive-voice` is flexible in both columns because adjudication put its actionability at 0.62. Where the two differ, the row says why.
- **`Active`**** is the gate, not a preference.** A value or rule whose `Active` box is unchecked is compiled but not enforced. A new entry starts unchecked whenever activating it would change what the checker reports, because a rule's precision was measured against a specific list. An entry that only writes down what the checker already does starts checked. The sync lists every inactive entry in the refreshed local copies of these pages, so a writer can see the difference between what the guide asks for and what a run will tell them.
- **The checker never reads Notion while it runs.** A sync step compiles these tables into a hashed local artifact, and every report names the hash. That is what makes a verdict reproducible, and it means a Notion edit reaches the checker only after a re-sync.
## The four projects
<table header-row="true">
<tr>
<td>Project</td>
<td>Repo</td>
<td>Voice in one line</td>
</tr>
<tr>
<td>Ledgers</td>
<td>`docs-readme-ledgers`</td>
<td>Teaching. We walk through a worked model together.</td>
</tr>
<tr>
<td>Payments</td>
<td>`docs-readme-payments`</td>
<td>Operational. You run payments; here is how you use MT PSP (incl BYO docs)</td>
</tr>
<tr>
<td>Platform guides</td>
<td>`docs-readme-platform/docs`</td>
<td>Task. Numbered steps to configure the product.</td>
</tr>
<tr>
<td>API reference</td>
<td>`docs-readme-platform/reference`</td>
<td>Descriptive. Objects and fields, no procedures.</td>
</tr>
</table>
A page belongs to exactly one project. Where an overlay contradicts base style, the overlay wins for that project.
<database url="https://app.notion.com/p/c3d7ff559aea4a2b9c2f5fc504ac7a9e" inline="false" data-source-url="collection://ce42afb4-f477-42c3-8636-5f5120fda9b0">Docs Style Rules</database>
<database url="https://app.notion.com/p/400c96361a4240d8b60827c1b32f3044" inline="false" data-source-url="collection://10238de1-ce37-45e9-a46c-1c79e1fad729">Docs Style Rule Values</database>
