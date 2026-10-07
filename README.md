# Chat Topic Bucketer — a topic map + resumable digests for your AI chats

Never lose a thread again. This tool watches your conversations with an AI
assistant (Claude Code, ChatGPT, Muse, …), figures out the topic of each
turn, and files it into a living index. Later, pull up the **topic map** to
see every thread, or **open a topic** to continue it with full context —
no more scrolling back to find where topic A went.

Built for anyone who has thought *"what was that thing I asked about last
month?"* — people find this tool by searching for: **claude code
conversation history**, **resume chat**, **chat history search**, **continue
an old conversation**, **long chat management**, **organize AI conversations**.

## Demo (example session)

```text
> topic map

# Topic map — all chats

## Main chat
| Topic                              | Last active | Turns | Summary                                  |
| Splunk AI Foundations HM prep      | 2026-10-05  | 14    | data-moat framing, MiniMax H3 exhibit    |
| Sourdough starter troubleshooting  | 2026-10-03  | 12    | feeding schedule, hooch vs. discard      |

## Side chat — Interview prep
| Topic                              | Last active | Turns | Summary                                  |
| Meta PM evals: "describe a time…"  | 2026-09-29  | 8     | verify-every-claim status-report loop    |

> open the sourdough

# Sourdough starter troubleshooting
12 turns across 2 chats, last active 2026-10-03.
[digest renders here — paste it at the top of a new chat to continue]
_Mapped with chat-topic-bucketer._
```

On Muse the same flow ends in a real side chat with the digest loaded;
anywhere else, it's a digest file you paste — transcripts can't be moved,
only recapped.

## Install (pick one)

```bash
git clone https://github.com/imdonothing-ui/chat-topic-bucketer
```

- **Claude Code / skill-compatible agents:** copy `skills/chat-topic-bucketer/`
  into the agent's skills folder (e.g. `~/.claude/skills/`), open a fresh
  session, say **"topic map"**. The agent classifies with its own judgment —
  no API key needed.
- **Any MCP-capable agent:** `pip install "chat-topic-bucketer[mcp]"`, add
  `mcp/example-config.json` to the agent's MCP config. Tools: `topic_map`,
  `list_topics`, `apply_classified_turns`, `topic_digest`.
- **Anywhere else:** `pip install .` → `bucketer` CLI (`apply`/`add`/`map`/
  `digest`/`topics`).

Full details: [INSTALL.md](INSTALL.md).

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

> Set up the chat topic bucketer from https://github.com/imdonothing-ui/chat-topic-bucketer
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
| `skills/chat-topic-bucketer/` | Installable Agent Skill (Claude Code, Cursor, …) |
| `mcp/server.py` | MCP server: topic tools for any MCP-capable agent |
| `core/` | Portable classifier + index + digest rendering (zero dependencies) |
| `cli.py` | `add` / `apply` / `map` / `digest` / `topics` commands over the core |
| `tests/test_pipeline.py` | End-to-end test with a stubbed classifier (no key needed) |
| `adapters/muse/` | Watcher prompt + setup for the zero-key Muse path |
| `adapters/generic/` | Bring-your-own-transcript guide for any other assistant |
| `topics-schema.json` | JSON Schema shared by both engines |
| `topic-map-template.md` | Starting template for `TOPIC_MAP.md` |
| `server.json` | MCP registry listing (official `registry` format) — publish the
  package to PyPI, then submit this file's repo to the MCP registry |

## Registry & discovery

- `server.json` at the repo root declares this server to the official MCP
  registry (repo: `imdonothing-ui/chat-topic-bucketer`, package:
  `chat-topic-bucketer` 0.2.0, stdio transport). Two steps remain before it
  can be listed: publish the package to PyPI
  (`python3 -m build && python3 -m twine upload dist/*`), then open a PR
  adding the server to the registry.
- Suggested repo tagline for GitHub settings (settings page only, can't be
  set from code): *"topic map + resumable digests for Claude Code chats —
  find any conversation thread, continue it with full context"*
- Suggested repo topics/tags: `claude-code`, `mcp-server`, `agent-skill`,
  `conversation-history`, `chatgpt`, `productivity`

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
