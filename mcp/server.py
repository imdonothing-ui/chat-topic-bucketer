#!/usr/bin/env python3
"""MCP server for chat-topic-bucketer (stdio transport).

The agent does the classifying (it has the judgment); the server does the
bookkeeping: index read/write, map rendering, digests. This keeps the server
keyless and dependency-light.

Install: pip install "chat-topic-bucketer[mcp]"
Run: python3 mcp/server.py   (or: bucketer-mcp, if a console script is added)
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from core import digest
from core import index as idxmod

try:
    # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server
except ImportError:
    try:
        # mcp 2.x renamed FastMCP -> MCPServer
        from mcp.server.mcpserver import MCPServer as _Server
    except ImportError:
        raise SystemExit(
            'The "mcp" package is required: pip install "chat-topic-bucketer[mcp]"'
        )

mcp = _Server("chat-topic-bucketer")

DEFAULT_INDEX = os.environ.get("BUCKETER_INDEX", os.path.expanduser("~/chat-topics/topics.json"))


def _find_topic(idx, needle):
    needle = needle.lower()
    for t in idx["topics"]:
        if t["id"] == needle:
            return t
    matches = [t for t in idx["topics"] if needle in t["title"].lower()]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise ValueError(
            "Ambiguous topic %r; matches: %s"
            % (needle, ", ".join("%s (%s)" % (t["id"], t["title"]) for t in matches))
        )
    raise ValueError("No topic matching %r" % needle)


# Tools are plain functions registered explicitly, so they stay directly
# callable (and testable) without going through the MCP framework.
def _register(fn):
    mcp.tool()(fn)
    return fn


@_register
def topic_map(index_path: str = "") -> str:
    """Return the topic map (markdown), regenerated from the current index."""
    return digest.render_map(idxmod.load(index_path or DEFAULT_INDEX))


@_register
def list_topics(index_path: str = "") -> str:
    """Return topic ids, titles, turn counts and last-active times as JSON."""
    idx = idxmod.load(index_path or DEFAULT_INDEX)
    return json.dumps(
        [
            {
                "id": t["id"],
                "title": t["title"],
                "turns": len(t["turns"]),
                "last_active": t["last_active"],
                "summary": t.get("summary", ""),
            }
            for t in idx["topics"]
        ],
        ensure_ascii=False,
    )


@_register
def apply_classified_turns(index_path: str, turns_json: str, result_json: str) -> str:
    """File agent-classified turns into the index.

    turns_json: JSON array of turn objects
      {"turn_id","chat_id","chat_name","seq","ts","user","assistant"}.
    result_json: {"assignments": [{"turn_id","topic","new_topic_title?"}],
      "summaries": {"<topic_id>": "<1-2 sentence summary>"}}.
    Only turns newer than each chat's watermark are applied; the call is
    idempotent per turn_id. Returns a short status line.
    """
    path = index_path or DEFAULT_INDEX
    idx = idxmod.load(path)
    turns = json.loads(turns_json)
    result = json.loads(result_json)
    fresh = idxmod.new_turns(idx, turns)
    if not fresh:
        return "No new turns since last watermark."
    idxmod.apply(idx, {t["turn_id"]: t for t in fresh}, result)
    idxmod.save(path, idx)
    map_path = os.path.join(os.path.dirname(os.path.abspath(path)), "TOPIC_MAP.md")
    with open(map_path, "w", encoding="utf-8") as f:
        f.write(digest.render_map(idx))
    return "Applied %d turn(s) into %d topic(s)." % (len(fresh), len(idx["topics"]))


@_register
def topic_digest(index_path: str, topic: str) -> str:
    """Return one topic's digest markdown (summary + key exchanges), by id or title fragment."""
    idx = idxmod.load(index_path or DEFAULT_INDEX)
    return digest.render_digest(_find_topic(idx, topic))


if __name__ == "__main__":
    mcp.run()
