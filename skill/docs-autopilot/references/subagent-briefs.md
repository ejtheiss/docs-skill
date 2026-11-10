# Subagent briefs

Every dispatch copies the two rules below verbatim into that brief. Inputs are
bounded to the current item/window; no subagent gets permission to publish.

## Harvest brief

Rule 1: never reference the customer.
Rule 2: Notion is the only write target. Never write to GitHub; never post to Slack channels. The single DM to Eric is the one exception.

Read [harvest queries](harvest-queries.md). Collect seven-day Slack/Gong evidence,
bounded Slack searches and thread context. Prefix-filter external channels.
Record staff concessions and operational cost without promoting guesses to facts.
Cluster generalized questions and deduplicate accounts across sources. Return
internal evidence, links and incomplete-search notes. No Notion, Slack or GitHub
writes by this subagent.

## Research brief

Rule 1: never reference the customer.
Rule 2: Notion is the only write target. Never write to GitHub; never post to Slack channels. The single DM to Eric is the one exception.

Use docs-review locate with task-scoped `--snapshot` and connector `--prs`
inputs, following its runtime source instructions; inspect quotes and check all three repos'
open/recently merged PRs and existing Notion rows. Write evidence.md with sections
VERIFIED, INFERRED, UNCLEAR and do NOT publish. Record source, scope, timestamp and
claim for each entry. Use ledger-design-assistant, solutions-architect or tam
skills when present; record unavailable skills rather than inventing expertise.
A1/A2 needs grounded VERIFIED facts; A3 must go to Needs Human Answer. Internal
conversations alone cannot authorize publishing undecided company policy.

## Generalization brief

Rule 1: never reference the customer.
Rule 2: Notion is the only write target. Never write to GitHub; never post to Slack channels. The single DM to Eric is the one exception.

Before drafting or staging any row, prepare generalized facts/questions plus customer-names.md
(one entity/person/account/KYB identifier or name per line; # comments).
Run `autopilot.py gate candidate.md --names customer-names.md` for leak checks,
then read the full generalized material as a model. Check indirect identifiers,
unusual architecture and hints not caught by whole-word matching. Failure:
log only safe rule/line/reason, do not draft or stage a row. Use this gate for
every row, including non-draft Needs Human Answer and Watching items, then again
on the generated row text. Never run `review.py` on a fragment.
Sources stay internal, never embedded in publishable prose.

## Draft brief

Rule 1: never reference the customer.
Rule 2: Notion is the only write target. Never write to GitHub; never post to Slack channels. The single DM to Eric is the one exception.

Read evidence.md; use only VERIFIED, scope-labelled claims. Use docs-review
draft.py with the destination template; the model writes prose. For small edits
preserve quote/replacement/path/heading and verify the quote at the target ref.
The model authors candidate.md from evidence in that template shape; copying
a fixture is eval behavior only.
Run draft.py validate, edit, validate until zero strict within the configured
iteration cap. The autopilot permits only one revision after fresh review.
Store validation output; never treat fixture VERIFIED evidence as a real fact.
The registered-agent eval claim is fixture-only and needs real SME confirmation.
Flag business_registeredprimary as a reviewer-judgment concern: it is a single
span, not a code-span-adjacent finding.

## Fresh-review brief

Rule 1: never reference the customer.
Rule 2: Notion is the only write target. Never write to GitHub; never post to Slack channels. The single DM to Eric is the one exception.

Review as a fresh agent, not the author. Small edits are checked only with
`draft.py validate`, never `review.py` on the fragment. For whole pages, run docs-review review; inspect the
rubric, verify accuracy/tense/person and record money-losing mistake: yes/no.
Model judgments are labelled reviewer judgment, not checker findings. Allow
one revision and one fresh re-review. Unresolved accuracy, strict errors, rubric
failure, a money-losing mistake or an unanswered policy decision means Needs SME
Review. Never approve because the mechanical checker is clean.
