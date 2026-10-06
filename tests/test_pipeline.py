"""End-to-end pipeline test with a stubbed classifier (no API key needed).

Covers: new-topic creation, continuation, cross-chat continuation, short-ack
attachment, watermark advancement, idempotent re-runs, digest + map rendering.
Run:  python3 tests/test_pipeline.py
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from core import digest
from core import index as idxmod
from core.classify import classify_turns
from core.llm import StubClient

TURNS = [
    {"turn_id": "u1", "chat_id": "work", "chat_name": "Work chat", "seq": 1,
     "ts": "2026-10-06T09:00:00-07:00",
     "user": "How do I write a good promo packet for senior TPM?",
     "assistant": "Start with scope: org-level outcomes, then evidence per pillar."},
    {"turn_id": "u2", "chat_id": "work", "chat_name": "Work chat", "seq": 2,
     "ts": "2026-10-06T09:05:00-07:00",
     "user": "ok", "assistant": "Want a template outline next?"},
    {"turn_id": "u3", "chat_id": "life", "chat_name": "Personal", "seq": 1,
     "ts": "2026-10-06T09:10:00-07:00",
     "user": "Best noise cancelling headphones under $300?",
     "assistant": "Sony WH-1000XM5 is the safe pick at that budget."},
    {"turn_id": "u4", "chat_id": "work", "chat_name": "Work chat", "seq": 3,
     "ts": "2026-10-06T09:15:00-07:00",
     "user": "What about the peer feedback section of the packet?",
     "assistant": "Ask for 3-4 specific stories: influence without authority."},
    {"turn_id": "u5", "chat_id": "life", "chat_name": "Personal", "seq": 2,
     "ts": "2026-10-06T09:20:00-07:00",
     "user": "Is the Sony comfortable for long flights?",
     "assistant": "Yes — light clamp, good for 8+ hours."},
    {"turn_id": "u6", "chat_id": "work2", "chat_name": "Work overflow", "seq": 1,
     "ts": "2026-10-06T09:25:00-07:00",
     "user": "For the promo packet, how do I quantify cross-org impact?",
     "assistant": "Attach numbers to decisions you drove: latency halved, cost cut."},
    {"turn_id": "u7", "chat_id": "work", "chat_name": "Work chat", "seq": 4,
     "ts": "2026-10-06T09:30:00-07:00",
     "user": "What's the capital of France?",
     "assistant": "Paris."},
]

# Canned classifier output: u1/u2/u4/u6 -> t-promo-packet (u6 crosses chats),
# u3/u5 -> t-headphones, u7 -> t-random-trivia.
CANNED = json.dumps({
    "assignments": [
        {"turn_id": "u1", "topic": "t-promo-packet", "new_topic_title": "Promo packet prep"},
        {"turn_id": "u2", "topic": "t-promo-packet"},
        {"turn_id": "u3", "topic": "t-headphones", "new_topic_title": "Headphone shopping"},
        {"turn_id": "u4", "topic": "t-promo-packet"},
        {"turn_id": "u5", "topic": "t-headphones"},
        {"turn_id": "u6", "topic": "t-promo-packet"},
        {"turn_id": "u7", "topic": "t-random-trivia", "new_topic_title": "Random trivia"},
    ],
    "summaries": {
        "t-promo-packet": "Preparing a senior TPM promo packet: structure, peer feedback, quantifying cross-org impact.",
        "t-headphones": "Shopping for sub-$300 noise-cancelling headphones; Sony WH-1000XM5 leading, comfort checked.",
        "t-random-trivia": "One-off trivia question.",
    },
})


def main():
    tmp = tempfile.mkdtemp()
    idx_path = os.path.join(tmp, "topics.json")
    idx = idxmod.load(idx_path)
    fresh = idxmod.new_turns(idx, TURNS)
    assert len(fresh) == 7, fresh

    result = classify_turns(fresh, idx["topics"], StubClient(CANNED))
    idx = idxmod.apply(idx, {t["turn_id"]: t for t in fresh}, result)
    idxmod.save(idx_path, idx)

    assert len(idx["topics"]) == 3, [t["id"] for t in idx["topics"]]
    by_id = {t["id"]: t for t in idx["topics"]}
    promo = by_id["t-promo-packet"]
    assert [x["turn_id"] for x in promo["turns"]] == ["u1", "u2", "u4", "u6"], promo["turns"]
    assert sorted({x["chat_name"] for x in promo["turns"]}) == ["Work chat", "Work overflow"]
    assert len(by_id["t-headphones"]["turns"]) == 2
    assert idx["watermarks"] == {"work": 4, "life": 2, "work2": 1}, idx["watermarks"]

    # idempotent re-run: nothing new
    idx2 = idxmod.load(idx_path)
    assert idxmod.new_turns(idx2, TURNS) == []

    # legacy single-watermark migration still loads
    legacy = {"watermark": {"main_chat_id": "x", "main_chat_seq": 9}, "topics": []}
    lp = os.path.join(tmp, "legacy.json")
    with open(lp, "w") as f:
        json.dump(legacy, f)
    assert idxmod.load(lp)["watermarks"] == {"x": 9}

    # rendering
    m = digest.render_map(idx)
    assert "Promo packet prep" in m and "Headphone shopping" in m
    d = digest.render_digest(promo)
    assert "cross-org impact" in d and "Work overflow" in d

    print("All pipeline tests passed (3 topics, 7 turns, cross-chat merge, idempotency, legacy migration).")


if __name__ == "__main__":
    main()
