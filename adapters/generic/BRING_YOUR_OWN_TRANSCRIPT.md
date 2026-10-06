# Bring your own transcript

The portable core (`/core`, `/cli.py`) doesn't care which assistant you use.
It only needs your conversation turns as **JSONL** — one JSON object per line:

```json
{"turn_id": "u1", "chat_id": "work", "chat_name": "Work chat", "seq": 1, "ts": "2026-10-06T09:00:00-07:00", "user": "How do I write a promo packet?", "assistant": "Start with scope..."}
```

Field notes:
- `turn_id`: any stable unique id per turn.
- `chat_id` / `chat_name`: which conversation the turn came from. Grouping works
  across chats, so keep these stable.
- `seq`: per-chat increasing number (message order). The core only classifies
  turns newer than each chat's watermark, so re-running the same file is safe.
- `ts`: ISO-8601 timestamp, used for ordering and display.
- `user` / `assistant`: the turn's text. Either may be empty.

## Getting transcripts out of common assistants

- **ChatGPT**: Settings → Data controls → Export data. You get a `conversations.json`;
  convert each conversation's `mapping` entries into the JSONL above (a ~20-line
  script; `title` becomes `chat_name`).
- **Claude**: Settings → Privacy → export, or copy/paste threads into the JSONL
  shape by hand for a first trial.
- **Anything else**: if you can see the text, you can shape it into JSONL.

## Running it

```bash
export BUCKETER_API_KEY="..."        # any OpenAI-compatible key
# optional: BUCKETER_API_BASE, BUCKETER_MODEL (default: OpenAI, gpt-4o-mini)

python3 cli.py --index ~/mychats/topics.json add --turns turns.jsonl
```

Or with Claude doing the classifying (native Anthropic support, no proxy):

```bash
export BUCKETER_ANTHROPIC_KEY="..."  # from console.anthropic.com
export BUCKETER_MODEL="..."          # a Claude model ID — Haiku-class is plenty

python3 cli.py --index ~/mychats/topics.json add --turns turns.jsonl --provider anthropic
```

Then, either way:

```bash
python3 cli.py --index ~/mychats/topics.json map        # the topic map
python3 cli.py --index ~/mychats/topics.json topics     # list topics
python3 cli.py --index ~/mychats/topics.json digest t-sourdough --out digests/sourdough.md
```

Run `add` on a schedule (cron, launchd, Task Scheduler) or by hand whenever you
want the index refreshed. Then, to "open" a topic anywhere: paste the digest
markdown at the start of a new conversation — every assistant accepts that.

## Testing without a key

```bash
python3 tests/test_pipeline.py   # full pipeline, stubbed classifier
```

For a dry run of the CLI with canned classifier output:
`cli.py add --turns turns.jsonl --mock-json canned.json`
