# Harvest queries and metadata verification

## Verification performed

Read-only mintmcp server `mintmcp-devin-bundle`, tool
`snowflake-mcp__platform_sql`, query id
`01c852ad-010d-1452-0000-427341a4f4ba` returned metadata only (55 column rows).
No call, request or transcript data was fetched. Metadata query:

```sql
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM PRODUCTION.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'DBT_GONG'
  AND TABLE_NAME IN ('GONG_PROCESSED_CALL_ENRICHMENTS_FLAT',
                     'GONG_CALLS', 'GONG_TRANSCRIPT_SENTENCES')
ORDER BY TABLE_NAME, ORDINAL_POSITION;
```

Verified: enrichments CALL_ID TEXT, SCHEDULED_AT TIMESTAMP_TZ,
CUSTOMER_REQUESTS TEXT, N_REQUESTS NUMBER; calls CALL_ID TEXT, TITLE TEXT,
GONG_CALL_URL TEXT, EXTERNAL_PARTICIPANT_COUNT NUMBER, SFDC_ACCOUNT_ID TEXT;
transcripts CALL_ID TEXT, UTTERANCE_INDEX NUMBER, SENTENCE_INDEX NUMBER,
SENTENCE_TEXT TEXT. Reverify metadata before future harvest queries.
No join cardinality, freshness, account attribution or query cost was tested.

## Slack

Bind window_start/window_end to dates and post-filter exact timestamps to the
seven-day interval [start,end). Each query uses `count/limit=20`,
`sort=timestamp`, descending; do not silently paginate past the cap.
Exact query templates (one keyword/phrase search per line):

```text
"registered agent" after:{{window_start}} before:{{window_end}}
"legal entity" after:{{window_start}} before:{{window_end}}
"beneficial owner" after:{{window_start}} before:{{window_end}}
"KYB" after:{{window_start}} before:{{window_end}}
"onboarding" after:{{window_start}} before:{{window_end}}
in:#ext-customer-* "how do" after:{{window_start}} before:{{window_end}}
in:#ext-customer-* "documentation" after:{{window_start}} before:{{window_end}}
```

The wildcard channel expression is a search hint, not a reliable Slack wildcard
guarantee. Authoritatively post-filter returned channel names with
`name.startswith("ext-customer-")`. If wildcard search is unsupported, use the
keyword-only query and the same post-filter; record incompleteness at the cap.

Internal staff-concession queries (do not apply the external-channel filter):

```text
"docs are wrong" after:{{window_start}} before:{{window_end}}
"undocumented" after:{{window_start}} before:{{window_end}}
"manual review" after:{{window_start}} before:{{window_end}}
"could have auto-approved" after:{{window_start}} before:{{window_end}}
```

Record authorship/context as staff concession only after reading the thread.
Duplicate Slack/Gong observations from one account count as one signal.

## Gong template — not executed

```sql
SELECT e.CALL_ID, e.SCHEDULED_AT, e.CUSTOMER_REQUESTS, e.N_REQUESTS,
       c.TITLE, c.GONG_CALL_URL, c.EXTERNAL_PARTICIPANT_COUNT,
       c.SFDC_ACCOUNT_ID
FROM PRODUCTION.DBT_GONG.GONG_PROCESSED_CALL_ENRICHMENTS_FLAT AS e
JOIN PRODUCTION.DBT_GONG.GONG_CALLS AS c ON c.CALL_ID = e.CALL_ID
WHERE e.SCHEDULED_AT >= :window_start
  AND e.SCHEDULED_AT < :window_end
  AND e.N_REQUESTS > 0
  AND c.EXTERNAL_PARTICIPANT_COUNT > 0;
```

Start from enrichments, never scan all transcripts. After selecting a call:

```sql
SELECT UTTERANCE_INDEX, SENTENCE_INDEX, SENTENCE_TEXT
FROM PRODUCTION.DBT_GONG.GONG_TRANSCRIPT_SENTENCES
WHERE CALL_ID = :call_id
ORDER BY UTTERANCE_INDEX, SENTENCE_INDEX;
```

Account ids and call links are internal evidence only. Missing columns, unexpected
cost or a refused connection means stop and escalate, not improvise another scan.

## Pylon and sweep

`pylon.enabled: false`. If explicitly enabled in a future authorized run, first
discover its read-only tool schema; request issues created in [window_start,
window_end), keyword phrases from config, limit 20, newest first. No Pylon API
syntax or integration has been verified; do not fabricate one or call a writer.
`sweep.enabled: false`: later; no scheduled sweep is implemented.
