# Chat Topic Bucketer

You chat with Muse in one window. This tool watches the conversation, figures out the topic of each turn, and files it into a living index. Later, say **"topic map"** to see every thread, or **"open the \<topic\>"** to spin that thread off into its own side chat with a full digest — no more scrolling back to find where topic A went.

## How it works

1. A scheduled watcher (every ~15 minutes) reads new turns from your **main chat**.
2. It classifies each turn: attaches continuations to existing topics, creates a new topic only for genuinely new subjects. Short acknowledgments ("ok", "thanks") attach to the surrounding topic.
3. It maintains two files:
   - `topics.json` — machine-readable index (topics, turn references, excerpts, watermark of the last processed message).
   - `TOPIC_MAP.md` — human-readable table you can skim anytime.
4. On demand, your assistant materializes any topic as a side chat pre-loaded with a digest, so you can continue there with full context.

## Requirements

- [Muse](https://muse.ai) (or any compatible agent runtime) with access to:
  - `chat.list` / `chat.read_messages` / `chat.create` / `chat.send_message`
  - `cron.add` (scheduled agent tasks)
- That's it — no API keys, no extra services, no cost beyond the watcher's own agent runs.

## Setup (5 minutes, just talk to your assistant)

**1. Create the workspace and seed the index.** Say:

> Set up the chat topic bucketer from https://github.com/YOUR-USERNAME/chat-topic-bucketer. Create `~/workspace/chat-topics/`, find my main chat's ID with `chat.list`, seed `topics.json` (following `topics-schema.json`) from my last ~15 turns, and generate `TOPIC_MAP.md`.

**2. Install the watcher.** Say:

> Create a cron called `chat-topic-watcher` that runs every 15 minutes using the body in `watcher-prompt.md` (fill in my main chat ID). It should stay silent — the index files are the product.

**3. Use it.**
- **"topic map"** — lists topics with one-line summaries.
- **"open the \<topic\>"** — creates a side chat named after the topic and posts a digest there (summary + key exchanges, condensed). The original turns stay in the main chat.

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
- **Main chat only.** Side chats are already topic-scoped by design, so only the main chat is watched.

## License

MIT — see [LICENSE](LICENSE).
