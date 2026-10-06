# Chat Topic Bucketer

You chat with an AI assistant in one window. This tool watches the conversation,
figures out the topic of each turn, and files it into a living index. Later,
pull up the **topic map** to see every thread, or **open a topic** to continue
it with full context — no more scrolling back to find where topic A went.

## Two engines, one index

| | **Muse adapter** (`adapters/muse/`) | **Portable core** (`core/`, `cli.py`) |
|---|---|---|
| Works with | Muse | Any assistant (ChatGPT, Claude, …) |
| Classifier | The scheduled agent itself | Any OpenAI-compatible LLM |
| API key | None needed | `BUCKETER_API_KEY` |
| Scheduler | Muse cron (15 min) | Your own cron, or manual runs |
| "Open topic" | Real side chat via `chat.create` | Digest markdown you paste anywhere |
| Deps | — | None (stdlib only, Python 3.9+) |

Both read and write the same `topics.json` (see `topics-schema.json`), so you
can mix them — e.g. bucket an exported ChatGPT history with the core, then
keep watching live chats with the Muse adapter.

## Quickstart

**On Muse** (no key needed) — see `adapters/muse/SETUP.md`. In short, tell
your assistant:

> Set up the chat topic bucketer from https://github.com/YOUR-USERNAME/chat-topic-bucketer
> using the Muse adapter.

Then use it by chatting: **"topic map"** lists topics; **"open the \<topic\>"**
materializes (or points to) a side chat with a digest.

**Anywhere else** — see `adapters/generic/BRING_YOUR_OWN_TRANSCRIPT.md`:

```bash
export BUCKETER_API_KEY="..."   # any OpenAI-compatible key
python3 cli.py --index mychats/topics.json add --turns turns.jsonl
python3 cli.py --index mychats/topics.json map
python3 cli.py --index mychats/topics.json digest t-sourdough --out digests/sourdough.md
```

Turns are plain JSONL (`turn_id, chat_id, chat_name, seq, ts, user, assistant`);
one subject stays one topic even across chats. To "open" a topic, paste its
digest at the start of a new conversation.

## What's in this repo

| Path | Purpose |
|---|---|
| `core/` | Portable classifier + index + digest rendering (zero dependencies) |
| `cli.py` | `add` / `map` / `digest` / `topics` commands over the core |
| `tests/test_pipeline.py` | End-to-end test with a stubbed classifier (no key needed) |
| `adapters/muse/` | Watcher prompt + setup for the zero-key Muse path |
| `adapters/generic/` | Bring-your-own-transcript guide for any other assistant |
| `topics-schema.json` | JSON Schema shared by both engines |
| `topic-map-template.md` | Starting template for `TOPIC_MAP.md` |

## Privacy

Your `topics.json` holds conversation excerpts and **never leaves your machine**
— it's local working state, gitignored here. Only code, prompts, and templates
are published.

## Limitations (honest)

- **Classification is heuristic.** The model occasionally misfiles a turn; the
  index is plain JSON and easy to fix by hand.
- **"Open topic" fidelity varies.** On Muse it's a real side chat with a digest;
  elsewhere it's a digest file you paste — transcripts can't be moved, only
  recapped.
- **Polling, not real-time.** The watcher/index refreshes on a schedule (or
  whenever you run `add`).
- **"Topic map" / "open the \<topic\>" are conventions**, not enforced commands —
  they work because the adapter setup teaches your assistant to honor them.

## License

MIT — see [LICENSE](LICENSE).
