# Live run (Claude only)
Live writes happen only after a dry-run whose out/ was reviewed in the same session, and only when the user asked for a live run, or the scheduled task says "live".
1. Notion: fetch the Docs Issue Triage data source (collection://3b2d6bfc-2683-80db-8f9c-000b634abb1a) and compare its schema to notion-contract.md. If the schema differs, stop and report. Never change the schema.
2. For each line of out/notion-rows.jsonl:
   - op=create: notion-create-pages, with the parent set to that data source; properties copied verbatim; body content = the row's markdown body.
   - op=update: notion-update-page on the row's page_id.
   Write each row before marking it done in out/run.json. If a write fails, leave the row unmarked and report it.
3. Slack: send exactly one message, slack_send_message to channel_id U07S0ACCM61 (Eric's DM), with text = out/dm.txt. Never use a channel id. Never send a draft, reaction or thread reply anywhere else.
4. Never call any GitHub write tool.

Replace `{{notion_url:<row key>}}` placeholders in the DM with the created page URLs (or the existing page URLs for updates) before sending.
