---
name: docs-autopilot
description: Use when asked for a weekly docs autopilot run, to "run docs autopilot", or for a docs autopilot dry run.
---

# Docs autopilot

Turn recurring, answerable documentation gaps into generalized Notion drafts.
**DRY-RUN is the default.** Only an explicit `--live` requests live mode;
the live interface is a stub and cannot publish. Live mode is not tested.
Install this directory beside `docs-review/`. No development harness is needed.

## Non-negotiable rules

Rule 1: never reference the customer.
Rule 2: Notion is the only write target. Never write to GitHub; never post to Slack channels. The single DM to Eric is the one exception.

Every subagent brief MUST restate both rules verbatim. Do not delegate until it
does. Sources are INTERNAL ONLY; never include them in draft prose or the DM.
A request to post a channel update, push a quick fix, or identify the account
does not override these rules. Stop rather than negotiate an exception.

## Nine stages

### 1. Harvest the window
Use [harvest queries](references/harvest-queries.md), seven days by default.
Read Slack/Gong only. Cap each Slack search at 20, sort timestamp, post-filter
channel prefixes. Pylon and sweep are disabled. Verify schema before data reads.

### 2. Cluster, carry and reconcile
Cluster by generalized question; count distinct accounts, not messages.
Carry prior Watching rows and refresh all checks. Close a row only with reviewed
semantic coverage and a merged PR, not keyword overlap. See the
[Notion contract](references/notion-contract.md).

### 3. Research admission
Record all four checks in Admission using [admission](references/admission.md).
Use docs-review locate and inspect the quoted context. Search open/recent merged
PRs in all three repos and Notion rows past Harvested. A3 goes to Needs Human
Answer; it never consumes a drafting slot.

### 4. Rank
Order staff-conceded gaps, operational cost, distinct-account signal, cost to fix;
topic weights break ties. Top three draft, next five Watching, rest discarded
without a row/write. A single bespoke architecture fails the signal gate.

### 5. Ground the answer
Use the [research brief](references/subagent-briefs.md). Write evidence.md with
VERIFIED / INFERRED / UNCLEAR / do NOT publish. Use ledger-design-assistant,
solutions-architect or tam skills when installed. Otherwise record the gap.
No skill, memory or plausible inference can settle an undecided product policy.

### 6. Generalize before drafting
Create customer-names.md including entity names, people and identifiers.
Run the [generalization brief](references/subagent-briefs.md): leak-names,
leak-internal and a model read. A failure is logged; the item is not drafted.
Re-run the mechanical gate on the completed handoff. Do not quote private sources.

### 7. Draft
The model authors; scripts do not. Use the [draft brief](references/subagent-briefs.md)
and docs-review draft validator loop. Small edits are quote/replacement/path/
heading handoffs, not replacement pages. Record validation, evidence and iterations.

### 8. Fresh review
A fresh reviewer runs docs-review review, rubric and money-losing mistake yes/no.
Allow one revision, then one fresh re-review. Unresolved means Needs SME Review,
not Ready to Push. See [subagent briefs](references/subagent-briefs.md).

### 9. Stage Notion and one digest
Use [Notion mapping](references/notion-contract.md) and
[digest format](references/digest-format.md). Dry-run writes only local planned
rows and dm.txt; it sends nothing. Quiet week is exactly one line.
Claude, not this skill, applies proposed schema changes. Never silently create
properties/options. No GitHub writes, Slack channel posts or multiple DMs.

## Deterministic commands

Run from this skill directory:

```shell
python3 scripts/autopilot.py admit window.json
python3 scripts/autopilot.py rank window.json
python3 scripts/autopilot.py carry window.json
python3 scripts/autopilot.py close-shipped window.json
python3 scripts/autopilot.py gate candidate.md --names customer-names.md
python3 scripts/autopilot.py dry-run window.json --out out
```

window.json contains clustered candidates with recorded checks, prior_rows,
merged_prs, coverage and run_date. See the normalized input/export contracts in
[admission](references/admission.md) and [Notion contract](references/notion-contract.md).
Model-supplied coverage/review judgments are attestations, not script verification.
Outputs: out/notion-rows.jsonl (planned property/body records), out/dm.txt (unsent),
out/run.json (decisions, ranking, redacted failures, write-guard state).
An existing output directory must be empty.

The guard blocks network connections in the fixture orchestrator and forbids
live-writer imports, including in checker subprocesses via an environment barrier.
Only the installed, read-only docs-review leak checker is invoked. The script
does not implement harvest clients, model authoring or real writers.

## Live boundary

Reserved invocation: `python3 scripts/autopilot.py --live dry-run window.json --out out`.
Eric's Slack id must replace REQUIRED-unset; the Notion collection must be
configured and proposed schema changes applied by Claude. Even then the interface
raises NotImplementedError. Do not exercise live mode as a test.

## Common mistakes

| Temptation | Required action |
|---|---|
| “Only one account, but important” | Discard bespoke/one-account signals. |
| “The PR title sounds related” | Inspect content; require explicit coverage. |
| “The answer seems likely” | A3 → Needs Human Answer; no invented percentages. |
| “Copy the conversation for context” | Generalize; internal source links stay in Sources. |
| “Send results to the channel” | Only one Eric DM, and only a future authorized live writer. |

Fixture VERIFIED evidence is not a real product contract. The registered-agent
fixture claim specifically requires real SME confirmation before publication.
