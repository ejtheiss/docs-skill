# Notion contract

Source: implementation-time Notion schema inspection, reproduced below.
Target: `collection://3b2d6bfc-2683-80db-8f9c-000b634abb1a`.
Sources is **INTERNAL ONLY**. Never copy Sources into a public draft or Eric DM.

## Existing schema

| Property | Type / recorded options |
|---|---|
| Task name | title |
| Description | text |
| Admission | text |
| Stage | select: Harvested, Researched, Drafted, In Review, Ready to Push, Needs SME Review, Needs Human Answer, Not Generalizable, Watching, Shipped elsewhere |
| Answer Complexity | select: A1 Known, A2 Synthesis, A3 Open, N/A |
| Destination | select: Sample App, Integration Guide, API Reference, Docs |
| Model | select: PSP, BYOB, Both, Unknown |
| Complexity | select: Low, Med, High |
| Effort level | select: Small, Medium, Large |
| Product Area | multi_select: Payments, Ledgers, Platform, Onboarding / Legal Entities, Webhooks |
| Assignee | person |
| Due Date | date |
| Due date | date (distinct existing spelling; do not merge it) |
| Run Date | date |
| Signal Count | number: distinct accounts |
| Review Passes | number |
| Has Draft | checkbox: true iff body contains a Draft section; not an approval to push |
| Sources | text, INTERNAL ONLY |
| Open Questions | text |
| Target Path | text |
| Status | status; options not recorded in source |

## Live schema additions (2026-11-11)

- Admission, text, is added.
- Stage options Watching and Shipped elsewhere are added. Nothing else changed.

These additions are live per Eric's 2026-11-11 decision.
Dry-run outputs retain schema_changes_applied=false because this skill neither creates nor updates schema.
If the schema does not match, stop and report. Never modify it during a live run.

## Mapping

All new rows: generalized Task name, Description (gap), Admission (four checks),
Run Date, Signal Count, Answer Complexity, Destination, Target Path, internal
Sources, Open Questions, Review Passes. Never place conversations/account names
in the title, description, evidence summary or draft.

| Stage | Body / fields |
|---|---|
| Harvested | Internal evidence only; not a publishable draft |
| Researched | evidence.md labels and provenance |
| Watching | Admitted but outside top 3; Has Draft=false |
| Drafted / In Review | Candidate Draft; reviewer state, not permission to publish |
| Ready to Push | Clean validator + fresh rubric + no money-losing mistake; Has Draft=true |
| Needs SME Review | Unresolved after one revision, or fixture-only claim; Has Draft=true when a draft exists |
| Needs Human Answer | A3; Has Draft=false; no invented policy answer |
| Not Generalizable | Human-managed existing rows; new bespoke signals create no row |
| Shipped elsewhere | No new draft; merged PR links in Sources/Open Questions, Has Draft=false |

Closing requires an explicit reviewed judgment that the located content answers
this row. PR #109 does NOT answer the external-account-to-FBO workflow question.
The substituted identification-types row is covered by platform #176/#192.
Close-existing preserves unrelated existing row properties and supplies a no-draft body.

## Body templates

The script generates bodies from these templates. Draft content uses five
backticks so MDX and nested triple-backtick fences survive pasting.
Source URLs appear only in the Sources property and Signal section, never in
any other section, including the draft. Has Draft is __YES__ iff Draft exists.

``````draft-body
## Why this exists

{reason}

## Proposed target

{target}

## Draft

`````markdown
{draft}
`````

## Review record

Stage: {stage}. Review passes: {passes}.

## Signal

{signal}
``````

``````blocked-body
## Why this is blocked

{reason}

## What was established

{established}

## What is needed to unblock

{unblock}

## Signal

{signal}
``````

## Export and carry-forward

Normalize Notion exports to records with `id`, `properties` (plain property
values), and optionally a saved `candidate`. Native Notion property objects
and flat property exports are accepted; Watching rows need a stable id.
The carry command merges by candidate id or exact generalized question. A prior
Watching candidate without refreshed checks is research-pending, not admitted.
No row is duplicated; retain prior_row_id for an update, and keep unselected
existing Watching rows as-is. Refresh coverage before carrying a now-shipped row.

Dry-run JSONL is the exact Claude MCP handoff: `op=create|update`, `page_id`
only for updates, `properties` keyed by the live schema names and `body` as
Markdown, not a Draft/Evidence object. Updates include only changed properties;
the body follows the applicable template above.
MCP properties are flat: title/text/select values are strings, numbers are numbers,
checkboxes are `__YES__`/`__NO__`, multi-select is a JSON-array string, and dates
use `date:Run Date:start`, `date:Run Date:end`, `date:Run Date:is_datetime`.
These encodings were confirmed by a read-only fetch of this data source; they
are not Notion REST property objects. Missing effort is null; missing Product Area
is `[]`; Model defaults to Unknown. Supply recorded values rather than infer them.
Admission, Watching and Shipped elsewhere are live. Compare the live schema
before writes and stop on any mismatch. Scripts never change the schema.
`run.json` has a zero-based row index and `done=false` for each pending write,
and `dm_sent=false`. Only Claude updates completion after successful MCP writes.
