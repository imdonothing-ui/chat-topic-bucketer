# Install

Three ways in, depending on your agent. All three share the same
`topics.json` index, so you can mix them.

## 1. Skill (recommended — Claude Code and other skill-compatible agents)

The skill teaches the agent the whole workflow: trigger phrases
("topic map", "open the \<topic\>"), how to classify with its own judgment
(no API key needed), and the scripts that keep the JSON valid.

```bash
git clone https://github.com/imdonothing-ui/chat-topic-bucketer ~/chat-topic-bucketer
mkdir -p ~/.claude/skills
cp -r ~/chat-topic-bucketer/skills/chat-topic-bucketer ~/.claude/skills/
```

Then open a fresh session and just say **"topic map"**. Other agents that
support the [Agent Skills](https://agentskills.io) format: copy the same
`skills/chat-topic-bucketer/` directory into that agent's skills location.

## 2. MCP server (any MCP-capable agent)

For agents that prefer tools over scripts. The agent classifies; the server
does the bookkeeping (no API key needed).

```bash
pip install "chat-topic-bucketer[mcp]"
```

Add this server block to your agent's MCP configuration (exact location
varies by agent — see `mcp/example-config.json`):

```json
{
  "mcpServers": {
    "chat-topic-bucketer": {
      "command": "python3",
      "args": ["/absolute/path/to/chat-topic-bucketer/mcp/server.py"],
      "env": { "BUCKETER_INDEX": "/absolute/path/to/topics.json" }
    }
  }
}
```

Available tools: `topic_map`, `list_topics`, `apply_classified_turns`,
`topic_digest`.

## 3. CLI (generic — works anywhere Python runs)

```bash
git clone https://github.com/imdonothing-ui/chat-topic-bucketer
cd chat-topic-bucketer && pip install .
bucketer --help
```

- `bucketer apply --index <topics.json> --turns turns.jsonl --result result.json`
  — file turns you (or your agent) classified.
- `bucketer add --turns turns.jsonl --provider anthropic` — classify with an
  LLM (`BUCKETER_ANTHROPIC_KEY` / `BUCKETER_API_KEY`).
- `bucketer map` / `bucketer topics` / `bucketer digest <topic>`.

Turns are plain JSONL (`turn_id, chat_id, chat_name, seq, ts, user,
assistant`); see `adapters/generic/BRING_YOUR_OWN_TRANSCRIPT.md` for getting
transcripts out of ChatGPT/Claude.

## Which should I pick?

| | Skill | MCP | CLI |
|---|---|---|---|
| Install effort | copy one folder | pip + one config block | pip |
| Classifier | the agent itself | the agent itself | LLM API key |
| Best for | Claude Code, Cursor, any Agent-Skills agent | agents with first-class MCP | scripts, cron jobs, bulk imports |
