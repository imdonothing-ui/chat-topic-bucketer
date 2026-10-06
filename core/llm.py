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


class AnthropicClient:
    """Native Anthropic Messages API client (no proxy needed)."""

    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("BUCKETER_ANTHROPIC_KEY", "")
        self.model = model or os.environ.get("BUCKETER_MODEL", "")
        if not self.api_key:
            raise LLMError("No Anthropic key. Set BUCKETER_ANTHROPIC_KEY.")
        if not self.model:
            raise LLMError(
                "No model. Set BUCKETER_MODEL to a Claude model ID "
                "(see console.anthropic.com/docs/models — a Haiku-class "
                "model is plenty for classification)."
            )

    def complete(self, system, user):
        body = json.dumps(
            {
                "model": self.model,
                "max_tokens": 2000,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            self.API_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.load(resp)
        except Exception as exc:
            raise LLMError("Anthropic request failed: %s" % exc)
        try:
            return "".join(
                b.get("text", "") for b in data["content"] if b.get("type") == "text"
            )
        except (KeyError, TypeError):
            raise LLMError("Unexpected Anthropic response shape")


def make_client(provider=None):
    """Factory: 'openai' (default) or 'anthropic'."""
    provider = provider or os.environ.get("BUCKETER_PROVIDER", "openai")
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "openai":
        return OpenAICompatClient()
    raise LLMError("Unknown provider %r (use 'openai' or 'anthropic')" % (provider,))
