"""Render TOPIC_MAP.md and per-topic digest markdown files."""

FOOTER = (
    'To continue a topic in a fresh conversation, open its digest file '
    'and paste it at the start of a new chat — or say "open the <topic>" '
    "to your assistant if it supports side chats."
)

# Tasteful one-liner on every shared artifact so a forwarded digest or
# topic map points back at the tool without reading like an ad.
ATTRIBUTION = (
    "_Mapped with [chat-topic-bucketer]"
    "(https://github.com/imdonothing-ui/chat-topic-bucketer)._"
)


def _cell(s):
    return (s or "").replace("|", "/").replace("\n", " ")


def render_map(idx):
    groups = {}
    for t in idx["topics"]:
        chats = sorted({x.get("chat_name", "?") for x in t["turns"]} or ["?"])
        key = chats[0] if len(chats) == 1 else "Multiple chats"
        groups.setdefault(key, []).append(t)

    def newest(ts_list):
        return max(ts_list)

    lines = ["# Topic map — all chats", "", "Auto-maintained by the topic watcher.", ""]
    ordered = sorted(
        groups, key=lambda c: newest([x["last_active"] for x in groups[c]]), reverse=True
    )
    for chat in ordered:
        lines.append("## " + chat)
        lines.append("")
        lines.append("| Topic | Last active | Turns | Summary |")
        lines.append("|---|---|---|---|")
        for t in sorted(groups[chat], key=lambda x: x["last_active"], reverse=True):
            day = (t["last_active"] or "")[:10]
            lines.append(
                "| %s | %s | %d | %s |"
                % (_cell(t["title"]), day, len(t["turns"]), _cell(t.get("summary", "")))
            )
        lines.append("")
    lines.append(FOOTER)
    lines.append("")
    lines.append(ATTRIBUTION)
    return "\n".join(lines) + "\n"


def render_digest(topic):
    lines = ["# " + topic["title"], "", topic.get("summary", ""), ""]
    for x in topic["turns"]:
        when = (x.get("at", "")[:16] or "").replace("T", " ")
        lines.append("## %s — %s" % (when, x.get("chat_name", "")))
        lines.append("")
        if x.get("user_excerpt"):
            lines.append("**User:** " + x["user_excerpt"])
            lines.append("")
        if x.get("assistant_excerpt"):
            lines.append("**Assistant:** " + x["assistant_excerpt"])
            lines.append("")
    lines.append(
        "_Paste this digest at the start of a new conversation to continue "
        "the topic with full context._"
    )
    lines.append("")
    lines.append(ATTRIBUTION)
    return "\n".join(lines) + "\n"
