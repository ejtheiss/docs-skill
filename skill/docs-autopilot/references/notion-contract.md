# Notion contract

Source: `~/work/notes/notion-schema.md` inspected during implementation.
Target: `collection://3b2d6bfc-2683-80db-8f9c-000b634abb1a`.
Sources is **INTERNAL ONLY**. Never copy Sources into a public draft or Eric DM.

## Existing schema

| Property | Type / recorded options |
|---|---|
| Task name | title |
| Description | text |
| Stage | select: Harvested, Researched, Drafted, In Review, Ready to Push, Needs SME Review, Needs Human Answer, Not Generalizable |
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
| Has Draft | checkbox: publishable draft under Draft; not an approval to push |
| Sources | text, INTERNAL ONLY |
| Open Questions | text |
| Target Path | text |
| Status | status; options not recorded in source |

## Proposed schema changes — Claude applies, not this skill

- Add Admission, text.
- Add Stage options Watching and Shipped elsewhere.

Dry-run outputs may describe these proposed fields/options with
schema_changes_applied=false. This skill neither creates nor updates schema.
Claude must apply/confirm them before any future real writer is implemented.

## Mapping

All new rows: generalized Task name, Description (gap), Admission (four checks),
Run Date, Signal Count, Answer Complexity, Destination, Target Path, internal
Sources, Open Questions, Review Passes. Never place conversations/account names
in the title, description, evidence summary or draft.

| Stage | Body / fields |
|---|---|
| Harvested | Internal evidence only; not a publishable draft |
| Researched | evidence.md labels and provenance |
| Watching (proposed) | Admitted but outside top 3; Has Draft=false |
| Drafted / In Review | Candidate Draft; reviewer state, not permission to publish |
| Ready to Push | Clean validator + fresh rubric + no money-losing mistake; Has Draft=true |
| Needs SME Review | Unresolved after one revision, or fixture-only claim; candidate body may exist but Has Draft=false |
| Needs Human Answer | A3; Has Draft=false; no invented policy answer |
| Not Generalizable | Human-managed existing rows; new bespoke signals create no row |
| Shipped elsewhere (proposed) | No new draft; merged PR links in Sources/Open Questions, Has Draft=false |

Closing requires an explicit reviewed judgment that the located content answers
this row. PR #109 does NOT answer the external-account-to-FBO workflow question.
The substituted identification-types row is covered by platform #176/#192.
Close-existing is a property patch; preserve unrelated existing row fields.

## Export and carry-forward

Normalize Notion exports to records with `id`, `properties` (plain property
values), and optionally a saved `candidate`. Native Notion property objects
and flat property exports are accepted; Watching rows need a stable id.
The carry command merges by candidate id or exact generalized question. A prior
Watching candidate without refreshed checks is research-pending, not admitted.
No row is duplicated; retain prior_row_id for an update, and keep unselected
existing Watching rows as-is. Refresh coverage before carrying a now-shipped row.

Dry-run JSONL records have id, operation=create|update, properties and optional
body={Draft,Evidence}. They are simulated intents, not API request payloads.
