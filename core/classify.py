"""Turn -> topic classification. Pure logic; the LLM client is injected,
so this works with any model (or a stub in tests).
"""

import json

SYSTEM = """You are a conversation topic classifier. Given existing topics and a batch of new conversation turns (chronological), assign every turn to a topic.

Rules:
- Attach a turn to an existing topic when it continues that subject, even if the turn is in a different chat than the topic's earlier turns. One subject is one topic across chats.
- Create a new topic ONLY for a genuinely new subject. New topic ids look like t-short-kebab-slug. Titles are 6 words or fewer.
- Short acknowledgments ("ok", "thanks", "got it") attach to the surrounding topic: prefer the most recent turn's topic in the same chat, else the best-matching existing topic.
- Ignore pure system/developer scaffolding as its own topic, but classify any user-facing assistant message by its real subject.
- Provide an updated 1-2 sentence summary for every topic that gained turns or whose understanding changed.

Return ONLY valid JSON, no prose, no markdown fences:
{
  "assignments": [
    {"turn_id": "...", "topic": "<existing topic id, or a new t-... id>", "new_topic_title": "<only when creating, else omit>"}
  ],
  "summaries": {"<topic id>": "<updated 1-2 sentence summary>"}
}"""


def build_user_message(topics, turns):
    known = [
        {"id": t["id"], "title": t["title"], "summary": t.get("summary", "")}
        for t in topics
    ]
    new = [
        {
            "turn_id": t["turn_id"],
            "chat": t.get("chat_name", ""),
            "user": (t.get("user") or "")[:500],
            "assistant": (t.get("assistant") or "")[:800],
        }
        for t in turns
    ]
    return (
        "EXISTING TOPICS:\n"
        + json.dumps(known, ensure_ascii=False)
        + "\n\nNEW TURNS (chronological):\n"
        + json.dumps(new, ensure_ascii=False)
    )


def _extract_json(text):
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object found in model output")
    return json.loads(text[start : end + 1])


def classify_turns(turns, topics, client):
    """Returns {"assignments": [...], "summaries": {...}}. Retries once on bad JSON."""
    if not turns:
        return {"assignments": [], "summaries": {}}
    user_msg = build_user_message(topics, turns)
    try:
        return _extract_json(client.complete(SYSTEM, user_msg))
    except Exception:
        retry_system = SYSTEM + "\nIMPORTANT: your last reply was not valid JSON. Reply with ONLY the JSON object."
        return _extract_json(client.complete(retry_system, user_msg))
