"""LLM clients. Production client speaks OpenAI-compatible /v1/chat/completions
(via stdlib urllib — no dependencies), so it works with OpenAI, Anthropic's
compatibility endpoint, local servers, or any other OpenAI-style API.
StubClient exists so the pipeline is testable without a key.
"""

import json
import os
import urllib.request


class LLMError(Exception):
    pass


class OpenAICompatClient:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.environ.get("BUCKETER_API_KEY", "")
        self.base_url = (
            base_url or os.environ.get("BUCKETER_API_BASE", "https://api.openai.com/v1")
        ).rstrip("/")
        self.model = model or os.environ.get("BUCKETER_MODEL", "gpt-4o-mini")
        if not self.api_key:
            raise LLMError(
                "No API key. Set BUCKETER_API_KEY (and optionally "
                "BUCKETER_API_BASE / BUCKETER_MODEL)."
            )

    def complete(self, system, user):
        body = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.load(resp)
        except Exception as exc:
            raise LLMError("LLM request failed: %s" % exc)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise LLMError("Unexpected LLM response shape: %r" % (data,)[:200])


class StubClient:
    """Deterministic stand-in for tests: returns canned text regardless of input."""

    def __init__(self, canned_text):
        self.canned_text = canned_text

    def complete(self, system, user):
        return self.canned_text
