"""topics.json read/write, watermark tracking, applying classifier output.
Schema matches topics-schema.json at the repo root.
"""

import json
import os
import re

SLUG_RE = re.compile(r"^t-[a-z0-9-]{1,40}$")


def new_index():
    return {"watermarks": {}, "topics": []}


def load(path):
    if not os.path.exists(path):
        return new_index()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # tolerate the legacy single-watermark shape
    if "watermark" in data and "watermarks" not in data:
        old = data.pop("watermark")
        data["watermarks"] = {old.get("main_chat_id", ""): old.get("main_chat_seq", -1)}
    data.setdefault("watermarks", {})
    data.setdefault("topics", [])
    return data


def save(path, idx):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def new_turns(idx, turns):
    """Turns newer than each chat's watermark, oldest first.

    Each turn: {turn_id, chat_id, chat_name, seq, ts, user, assistant}.
    """
    fresh = [
        t
        for t in turns
        if t.get("seq", 0) > idx["watermarks"].get(t.get("chat_id", ""), -1)
    ]
    fresh.sort(key=lambda t: (t.get("ts", ""), t.get("seq", 0)))
    return fresh


def _slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return "t-" + (s[:40] or "topic")


def apply(idx, turns_by_id, result):
    """Fold classifier output into the index. Idempotent per turn_id."""
    topics = {t["id"]: t for t in idx["topics"]}
    for a in result.get("assignments", []) or []:
        turn = turns_by_id.get(a.get("turn_id"))
        topic_id = a.get("topic")
        if not turn or not topic_id:
            continue
        if topic_id not in topics:
            if not SLUG_RE.match(topic_id):
                topic_id = _slugify(a.get("new_topic_title") or topic_id)
            base, n = topic_id, 2
            while topic_id in topics:
                topic_id = "%s-%d" % (base, n)
                n += 1
            title = (a.get("new_topic_title") or topic_id[2:].replace("-", " "))[:60]
            topics[topic_id] = {
                "id": topic_id,
                "title": title,
                "summary": "",
                "last_active": turn.get("ts", ""),
                "turns": [],
            }
            idx["topics"].append(topics[topic_id])
        t = topics[topic_id]
        if not any(x["turn_id"] == turn["turn_id"] for x in t["turns"]):
            t["turns"].append(
                {
                    "turn_id": turn["turn_id"],
                    "chat_id": turn.get("chat_id", ""),
                    "chat_name": turn.get("chat_name", ""),
                    "seq": turn.get("seq", 0),
                    "at": turn.get("ts", ""),
                    "user_excerpt": (turn.get("user") or "")[:200],
                    "assistant_excerpt": (turn.get("assistant") or "")[:300],
                }
            )
        if turn.get("ts", "") > t.get("last_active", ""):
            t["last_active"] = turn["ts"]
        cid = turn.get("chat_id", "")
        wm = idx["watermarks"]
        wm[cid] = max(wm.get(cid, -1), turn.get("seq", 0))
    for tid, summ in (result.get("summaries") or {}).items():
        if tid in topics and summ:
            topics[tid]["summary"] = summ[:500]
    return idx
