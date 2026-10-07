# Muse adapter

The zero-extra-cost path: on Muse, the assistant itself does the classifying,
so no LLM API key is needed. The watcher is a scheduled agent task; the
"open the topic" flow uses Muse's side chats.

## Setup

**1. Create the workspace and seed the index.** Say to your assistant:

> Set up the chat topic bucketer from https://github.com/imdonothing-ui/chat-topic-bucketer
> using the Muse adapter. Create `~/workspace/chat-topics/`, list my chats with
> `chat.list`, seed `topics.json` (following `topics-schema.json`, one watermark
> per chat) from recent turns in each chat, and generate `TOPIC_MAP.md` grouped
> by chat.

**2. Install the watcher.** Say:

> Create a cron called `chat-topic-watcher` that runs every 15 minutes using the
> body in `adapters/muse/watcher-prompt.md`. It should stay silent — the index
> files are the product.

**3. Use it.**
- **"topic map"** — your assistant lists topics grouped by chat, with one-line summaries.
- **"open the \<topic\>"** — if the topic already lives in one side chat, your
  assistant points you there; otherwise it creates a side chat named after the
  topic and posts a digest (summary + key exchanges, condensed).

## How it differs from the portable core

| | Muse adapter (this folder) | Portable core (`/core`, `/cli.py`) |
|---|---|---|
| Classifier | The scheduled agent itself | Any OpenAI-compatible LLM via API |
| API key | None needed | `BUCKETER_API_KEY` required |
| Scheduler | Muse cron | Your own cron / manual runs |
| "Open topic" | Real side chat via `chat.create` | Digest markdown you paste anywhere |
| Transcript source | `chat.read_messages` | Any JSONL you supply |

Both write the same `topics.json` schema, so you can mix them: e.g. run the
portable core over an exported ChatGPT history, then keep watching new chats
with the Muse adapter.
