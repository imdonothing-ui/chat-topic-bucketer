"""MCP server smoke test. Skips if the optional `mcp` package is not installed
(pip install "chat-topic-bucketer[mcp]"). Run: python3 tests/test_mcp_server.py
"""

import importlib.util
import json
import os
import sys
import tempfile

try:
    import mcp  # noqa: F401
except ImportError:
    print("SKIP: 'mcp' package not installed")
    sys.exit(0)

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
spec = importlib.util.spec_from_file_location(
    "bucketer_mcp_server", os.path.join(REPO, "mcp", "server.py")
)
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)


def main():
    tmp = tempfile.mkdtemp()
    idx = os.path.join(tmp, "topics.json")
    turns = [
        {
            "turn_id": "m1",
            "chat_id": "c",
            "chat_name": "C",
            "seq": 1,
            "ts": "2026-10-06T10:00:00-07:00",
            "user": "Best espresso ratio?",
            "assistant": "1:2 in 25-30s.",
        }
    ]
    result = {
        "assignments": [
            {"turn_id": "m1", "topic": "t-espresso", "new_topic_title": "Espresso brewing"}
        ],
        "summaries": {"t-espresso": "Dialing in espresso."},
    }
    out = srv.apply_classified_turns(idx, json.dumps(turns), json.dumps(result))
    assert "1 turn" in out, out
    assert "No new turns" in srv.apply_classified_turns(
        idx, json.dumps(turns), json.dumps(result)
    )
    topics = json.loads(srv.list_topics(idx))
    assert topics[0]["id"] == "t-espresso" and topics[0]["turns"] == 1, topics
    assert srv.topic_digest(idx, "espresso").startswith("# Espresso brewing")
    assert "| Topic |" in srv.topic_map(idx)
    print("MCP server tests passed (4 tools, idempotent apply).")


if __name__ == "__main__":
    main()
