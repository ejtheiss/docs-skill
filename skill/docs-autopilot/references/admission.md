# Admission contract

Record four text results in the proposed Admission property. Never replace an
unchecked predicate with PASS.

1. **Signal:** at least two distinct accounts, not bespoke architecture.
2. **Not answered:** docs-review locate searched refs; model reads quotes and
   judges not_answered or hard_to_find. Hard-to-find → Small discoverability gap,
   preferably a small link/navigation edit, not a duplicate page.
3. **Not in flight:** inspect open and recently merged PRs (90 days) across
   docs-readme-payments, docs-readme-ledgers, docs-readme-platform, plus Notion
   rows past Harvested. Any matching in-flight work blocks a new draft.
4. **Answerable:** A1 Known / A2 Synthesis with VERIFIED evidence can admit.
   A3 Open → Needs Human Answer, no draft, outside the drafting cap. Other unknowns
   need research, not an invented answer.

Rank staff-conceded first, then operational cost descending, signal count
descending, cost to fix ascending. Config topic weights break ties; stable id is
the final tie-breaker. Top 3 draft; next 5 Watching; all others discarded with
no row/write. Revalidate carried Watching items each window.

## Recorded input

`window.json` is a mapping with `candidates`, `prior_rows`, `merged_prs`,
`coverage`, `run_date`. Candidates have stable id, generalized question,
topics, operational_cost, cost_to_fix and checks:

```json
{
  "signal": {"accounts": ["account-key-1", "account-key-2"], "staff_conceded": true, "bespoke": false},
  "locate": {"searched": true, "judgment": "not_answered"},
  "in_flight": {"repos": ["docs-readme-payments", "docs-readme-ledgers", "docs-readme-platform"], "notion_checked": true, "open_prs": [], "recent_merged_prs": [], "notion_past_harvested": []},
  "answer": {"complexity": "A1 Known", "evidence": [{"label": "VERIFIED", "claim": "Evidence-backed statement", "source": "Internal evidence reference"}]}
}
```

These are recorded human/model check inputs, not assertions that the script
queried live systems. Keep raw accounts and conversations in input/evidence only;
`carry` stdout contains only candidate/prior-row IDs and distinct-account counts,
like run.json decisions; raw merged candidates stay internal to orchestration.
Admission emits counts/results, not account identifiers. `sources` supplies
internal links; `draft_file` is a pre-authored relative Markdown file,
`model_generalization_passed` records a model read, `validation` records the
docs-review draft result. `review` records strict_failures, rubric_passed,
money_losing_mistake, fresh_reviewer and passes. Maximum passes = initial + one
revision. No code generates factual prose. Fixture evidence must be labelled
fixture-only and cannot authorize a real product claim.
