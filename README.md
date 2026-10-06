# Chat Topic Bucketer

You chat with Muse in one window. This tool watches the conversation, figures out the topic of each turn, and files it into a living index. Later, say **"topic map"** to see every thread, or **"open the \<topic\>"** to spin that thread off into its own side chat with a full digest — no more scrolling back to find where topic A went.

## How it works

1. A scheduled watcher (every ~15 minutes) scans your **main chat and all side chats** for new turns.
2. It classifies each turn: attaches continuations to existing topics, creates a new topic only for genuinely new subjects. One subject is one topic **even across chats** — if a thread continues in a different chat, its turns join the same topic. Short acknowledgments ("ok", "thanks") attach to the surrounding topic.
3. It maintains two files:
   - `topics.json` — machine-readable index (per-chat watermarks, topics, turn references with chat IDs, excerpts).
   - `TOPIC_MAP.md` — human-readable table, grouped by chat, you can skim anytime.
4. On demand, your assistant materializes any topic as a side chat pre-loaded with a digest, so you can continue there with full context. If the topic already lives in a single side chat, it just points you there instead of duplicating it.

## Requirements

- [Muse](https://muse.ai) (or any compatible agent runtime) with access to:
  - `chat.list` / `chat.read_messages` / `chat.create` / `chat.send_message`
  - `cron.add` (scheduled agent tasks)
- That's it — no API keys, no extra services, no cost beyond the watcher's own agent runs.

## Setup (5 minutes, just talk to your assistant)

**1. Create the workspace and seed the index.** Say:

> Set up the chat topic bucketer from https://github.com/YOUR-USERNAME/chat-topic-bucketer. Create `~/workspace/chat-topics/`, list my chats with `chat.list`, seed `topics.json` (following `topics-schema.json`, with a watermark per chat) from recent turns in each chat, and generate `TOPIC_MAP.md` grouped by chat.

**2. Install the watcher.** Say:

> Create a cron called `chat-topic-watcher` that runs every 15 minutes using the body in `watcher-prompt.md`. It should stay silent — the index files are the product.

**3. Use it.**
- **"topic map"** — lists topics grouped by chat, with one-line summaries.
- **"open the \<topic\>"** — if the topic already lives in one side chat, I'll point you there; otherwise I create a side chat named after the topic and post a digest (summary + key exchanges, condensed). The original turns stay where they are.

## What's in this repo

| File | Purpose |
|---|---|
| `watcher-prompt.md` | The scheduled job's instructions (fill in `<MAIN_CHAT_ID>`) |
| `topics-schema.json` | JSON Schema for `topics.json` |
| `topic-map-template.md` | Starting template for `TOPIC_MAP.md` |
| `README.md` | This file |

## Privacy

Your `topics.json` contains your conversation excerpts and **never leaves your machine** — it's local working state, not part of this repo. Only the templates and prompts are published here.

## Limitations (honest)

- **Polling, not real-time.** New turns appear in the index within ~15 minutes of the watcher run.
- **Transcripts are immutable.** "Opening" a topic creates a side chat with a faithful digest, not the original messages moved over.
- **Classification is heuristic.** It occasionally files a turn under the wrong topic; the index is easy to fix by hand.
- **Active chats only.** Archived chats aren't watched (their history can be backfilled on request).

## License

MIT — see [LICENSE](LICENSE).
