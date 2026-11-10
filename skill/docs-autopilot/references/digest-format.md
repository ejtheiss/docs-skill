# The single unsent DM

One DM to Eric only, after Notion staging. The placeholder recipient
REQUIRED-unset must be replaced before a future authorized live DM. No channel
posts, no follow-up DMs and no customer names, account ids or private Sources.

Normal format lists every item's title, stage and Notion link:

```text
Docs autopilot: 1 draft; 0 watching items; 0 open questions; 0 shipped items.
- Which fields are required? | Needs SME Review | {{notion_url:row-key}}
```

Counts describe staged rows, not publication; use singular for 1 and plural
otherwise (draft/drafts, watching item/items, open question/questions, shipped
item/items). Dry-run uses stable row-key placeholders; Claude replaces these
with created or existing Notion page URLs at live write. Never include Slack/Gong
source links in the DM.

Quiet week is exactly:

```text
nothing qualified
```

One newline, no greeting, recap, filler, consolation or additional messages.
DRY-RUN saves dm.txt; it does not send it.
