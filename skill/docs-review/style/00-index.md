
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
## Guide pages
Read **01 — Base Style** and the project overlay (**02** Ledgers, **03** Payments, **04** platform guides, **05** API reference). **06** describes deliberate flexibility and context limits; **07** covers review and correction.
Read [08 — ReadMe Conventions](08-readme-conventions.md) for component syntax, frontmatter, tabs and navigation links.

## Policy and reported grades
The prose is edited directly. Machine-readable policy lives in `docs-review/config/policy.yaml` and each subskill's `config/rules.yaml`. Change prose and matching policy together. A policy hash covers severities, scope, contexts, thresholds, values and exemptions; no Notion sync is involved.
A rule has two grades: guide severity for review and reported severity for checker output. For example, `em-dash` is strict guidance reported flexible. `--list-rules` prints the authoritative reported rules and contexts. Reviewer judgments are not invented checker findings.

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
