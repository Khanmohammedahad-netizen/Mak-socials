"""Optional fallback provider — not in Phase 1's default routing (every
TaskClass routes to ollama; see src/providers/llm/router.py). Listed in
the blueprint's architecture (§11, §10 cost table) as a paid fallback
if the free local path ever needs backup. No call site uses this yet.

Raw HTTP via `requests` (already a project dependency) rather than
pulling in the `anthropic` SDK for a provider nothing calls by default.
"""

from __future__ import annotations

import os

import requests

from src.providers.llm.base import LLMResult

# Approximate, for cost-tracking purposes only — not a billing source of
# truth. Claude Haiku list pricing in USD per token, times a static
# USD->INR rate. Update if either changes materially.
_USD_TO_INR = 83.0
_HAIKU_USD_PER_INPUT_TOKEN = 0.80 / 1_000_000
_HAIKU_USD_PER_OUTPUT_TOKEN = 4.00 / 1_000_000


class AnthropicConfigError(RuntimeError):
    pass


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str = "claude-haiku-4-5", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        options: dict | None = None,
    ) -> LLMResult:
        if not self.api_key:
            raise AnthropicConfigError(
                "ANTHROPIC_API_KEY not set — this provider has no default "
                "route in Phase 1 and must be configured explicitly to use."
            )

        payload: dict = {
            "model": self.model,
            "max_tokens": (options or {}).get("num_predict", 1024),
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            payload["system"] = system

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        text = "".join(block.get("text", "") for block in data.get("content", []))
        usage = data.get("usage", {})
        tokens_in = usage.get("input_tokens")
        tokens_out = usage.get("output_tokens")
        cost_inr = 0.0
        if tokens_in is not None and tokens_out is not None:
            cost_inr = (
                tokens_in * _HAIKU_USD_PER_INPUT_TOKEN
                + tokens_out * _HAIKU_USD_PER_OUTPUT_TOKEN
            ) * _USD_TO_INR

        return LLMResult(text=text.strip(), tokens_in=tokens_in, tokens_out=tokens_out, cost_inr=cost_inr)
