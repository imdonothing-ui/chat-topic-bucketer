---
name: chat-topic-bucketer
description: Maintain a living topic index across the user's AI conversations. Use when the user says "topic map", asks to "open the <topic>", wants to resume an earlier subject without scrolling, or when a session has clearly covered a new subject worth filing.
---

# Chat topic bucketer

You keep a **topic index** of the user's conversations so they can see every
subject at a glance ("topic map") and jump back into any subject later
("open the \<topic\>"). One subject is one topic, even when it spans multiple
chats or sessions.

## Index location

Default: `~/chat-topics/topics.json` (override with `$BUCKETER_INDEX`).
Schema: `topics-schema.json` at the repo root — `watermarks` (chat_id → last
processed seq) plus `topics`, each with id, title, summary, last_active, and
turn records carrying chat_id/chat_name. A rendered map lives next to it as
`TOPIC_MAP.md`. Never commit these files anywhere: they hold conversation
excerpts.

## Trigger phrases

- **"topic map"** → read the index and show topics grouped by chat: title,
  last active, turn count, one-line summary.
- **"open the \<topic\>"** → find the topic (by id or title fragment). Print
  its digest (summary + key exchanges). If the platform supports starting a
  new chat/session, offer to open one with the digest as the opening context —
  transcripts can't be moved, only recapped.
- Unprompted: when the current session has covered a clear new subject, offer
  once to file it ("want me to add this to your topic index?").

## Transcript sources

- **This conversation:** you already have the turns — use them directly.
- **Claude Code past sessions:** session transcripts are JSONL files under
  `~/.claude/projects/` (one file per session; lines have `type` and
  `message` fields). Pair user/assistant messages into turns.
- **Anything else:** ask the user to paste or export the thread, then shape it
  into turn JSONL: `{"turn_id","chat_id","chat_name","seq","ts","user","assistant"}`
  (one JSON object per line; `seq` increases per chat; `ts` is ISO-8601).

## Workflow

1. **Collect** turns newer than each chat's watermark in `topics.json`.
2. **Classify with your own judgment** (you are the classifier — no API key
   needed):
   - Attach a turn to the existing topic it continues, across chats/sessions.
   - New topic (id `t-short-kebab-slug`, title ≤ 6 words) only for a genuinely
     new subject.
   - Short acknowledgments ("ok", "thanks") attach to the surrounding topic.
   - Ignore pure scaffolding (system notices, tool chatter) as its own topic,
     but classify any user-facing message by its real subject.
   - Write/refresh each touched topic's 1–2 sentence summary.
3. **Apply** via the bundled scripts so the JSON stays valid (repo root, or
   `bucketer` if pip-installed):
   - Write turns to `turns.jsonl` and your classification to `result.json`
     as `{"assignments": [{"turn_id","topic","new_topic_title?"}],
     "summaries": {"<topic_id>": "..."}}`.
   - Run: `python3 cli.py --index <index> apply --turns turns.jsonl --result result.json`
   - This updates watermarks, `topics.json`, and regenerates `TOPIC_MAP.md`.
4. **Report** briefly: topics touched, nothing more.

## Scripts (repo root)

- `cli.py` — `apply` (agent-classified), `add` (LLM-classified via
  `BUCKETER_API_KEY`/`BUCKETER_ANTHROPIC_KEY`), `map`, `digest <topic>`,
  `topics`. After `pip install .`, the same commands are available as `bucketer`.
- `core/` — zero-dependency library (index read/write, map + digest rendering).
- `mcp/server.py` — MCP server exposing the same operations as tools
  (`pip install .[mcp]`), for agents that prefer tools over scripts.
