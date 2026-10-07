#!/usr/bin/env python3
"""Portable chat-topic bucketer CLI. Works with any assistant: feed it turns as JSONL.

Turn JSONL schema (one JSON object per line):
  {"turn_id": "...", "chat_id": "...", "chat_name": "...", "seq": 12,
   "ts": "2026-10-06T14:00:00-07:00", "user": "...", "assistant": "..."}

Configuration via environment:
  BUCKETER_PROVIDER      openai (default) or anthropic
  BUCKETER_API_KEY       OpenAI-compatible API key (required unless --mock-json)
  BUCKETER_API_BASE      OpenAI-compatible base URL (default https://api.openai.com/v1)
  BUCKETER_ANTHROPIC_KEY Anthropic API key (when provider=anthropic)
  BUCKETER_MODEL         Model name (default gpt-4o-mini for openai;
                         required for anthropic — pick a Haiku-class model)

Commands:
  add      classify new turns from a JSONL file into the index
  map      print the topic map
  digest   print (or write) one topic's digest markdown
  topics   list topic ids and titles
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import classify, digest, index as idxmod
from core.llm import LLMError, StubClient, make_client


def load_turns(path):
    turns = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                turns.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit("Bad JSON on line %d of %s: %s" % (lineno, path, exc))
    return turns


def cmd_add(args):
    idx = idxmod.load(args.index)
    turns = load_turns(args.turns)
    fresh = idxmod.new_turns(idx, turns)
    if not fresh:
        print("No new turns since last watermark.")
        return
    if args.mock_json:
        with open(args.mock_json, encoding="utf-8") as f:
            client = StubClient(f.read())
    else:
        try:
            client = make_client(args.provider)
        except LLMError as exc:
            raise SystemExit(str(exc))
    try:
        result = classify.classify_turns(fresh, idx["topics"], client)
    except Exception as exc:
        raise SystemExit("Classification failed: %s" % exc)
    idxmod.apply(idx, {t["turn_id"]: t for t in fresh}, result)
    idxmod.save(args.index, idx)
    map_path = os.path.join(os.path.dirname(os.path.abspath(args.index)), "TOPIC_MAP.md")
    with open(map_path, "w", encoding="utf-8") as f:
        f.write(digest.render_map(idx))
    print(
        "Classified %d turn(s) into %d topic(s). Map written to %s"
        % (len(fresh), len(idx["topics"]), map_path)
    )


def cmd_apply(args):
    """Apply agent-classified turns (no LLM call): the agent did the classifying."""
    idx = idxmod.load(args.index)
    turns = load_turns(args.turns)
    with open(args.result, encoding="utf-8") as f:
        result = json.load(f)
    fresh = idxmod.new_turns(idx, turns)
    if not fresh:
        print("No new turns since last watermark.")
        return
    idxmod.apply(idx, {t["turn_id"]: t for t in fresh}, result)
    idxmod.save(args.index, idx)
    map_path = os.path.join(os.path.dirname(os.path.abspath(args.index)), "TOPIC_MAP.md")
    with open(map_path, "w", encoding="utf-8") as f:
        f.write(digest.render_map(idx))
    print(
        "Applied %d turn(s) into %d topic(s). Map written to %s"
        % (len(fresh), len(idx["topics"]), map_path)
    )


def find_topic(idx, needle):
    needle = needle.lower()
    exact = [t for t in idx["topics"] if t["id"] == needle]
    if exact:
        return exact[0]
    partial = [t for t in idx["topics"] if needle in t["title"].lower()]
    if len(partial) == 1:
        return partial[0]
    if partial:
        raise SystemExit(
            "Ambiguous — matches: %s"
            % ", ".join("%s (%s)" % (t["id"], t["title"]) for t in partial)
        )
    raise SystemExit("No topic matching %r. Try `topics` to list." % needle)


def cmd_map(args):
    print(digest.render_map(idxmod.load(args.index)))


def cmd_digest(args):
    topic = find_topic(idxmod.load(args.index), args.topic)
    text = digest.render_digest(topic)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print("Wrote %s" % args.out)
    else:
        print(text)


def cmd_topics(args):
    for t in idxmod.load(args.index)["topics"]:
        print("%s\t%s\t%d turns" % (t["id"], t["title"], len(t["turns"])))


def main():
    ap = argparse.ArgumentParser(description="Portable chat-topic bucketer")
    ap.add_argument("--index", default="topics.json", help="path to topics.json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="classify new turns from a JSONL file")
    p_add.add_argument("--turns", required=True, help="JSONL file of turns")
    p_add.add_argument("--mock-json", default=None, help="canned classifier JSON (testing)")
    p_add.add_argument(
        "--provider",
        default=None,
        choices=["openai", "anthropic"],
        help="LLM provider (default: $BUCKETER_PROVIDER or openai)",
    )
    p_add.set_defaults(fn=cmd_add)

    p_apply = sub.add_parser(
        "apply",
        help="apply agent-classified turns from a JSON result file (no LLM call)",
    )
    p_apply.add_argument("--turns", required=True, help="JSONL file of turns")
    p_apply.add_argument(
        "--result",
        required=True,
        help='JSON file with {"assignments": [...], "summaries": {...}}',
    )
    p_apply.set_defaults(fn=cmd_apply)

    p_map = sub.add_parser("map", help="print the topic map")
    p_map.set_defaults(fn=cmd_map)

    p_digest = sub.add_parser("digest", help="render one topic's digest")
    p_digest.add_argument("topic", help="topic id or distinctive title fragment")
    p_digest.add_argument("--out", default=None, help="write to file instead of stdout")
    p_digest.set_defaults(fn=cmd_digest)

    p_topics = sub.add_parser("topics", help="list topics")
    p_topics.set_defaults(fn=cmd_topics)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
