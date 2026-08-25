"""Thin wrapper over the existing `ollama` client usage in
engine/script_generator.py and engine/lib/title_optimizer.py. Same call
shape (model, system, prompt, options), so migrating those call sites
onto this class does not change what gets sent to Ollama — only adds
routing + cost logging around it.
"""

from __future__ import annotations

from ollama import Client

from src.providers.llm.base import LLMResult


class OllamaProvider:
    name = "ollama"

    def __init__(self, model: str, host: str = "http://localhost:11434"):
        self.model = model
        self.client = Client(host=host)

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        options: dict | None = None,
    ) -> LLMResult:
        kwargs: dict = {"model": self.model, "prompt": prompt}
        if system is not None:
            kwargs["system"] = system
        if options is not None:
            kwargs["options"] = options

        response = self.client.generate(**kwargs)
        return LLMResult(
            text=response["response"].strip(),
            tokens_in=response.get("prompt_eval_count"),
            tokens_out=response.get("eval_count"),
            cost_inr=0.0,  # local model, free
        )

    def chat(self, messages: list[dict], *, options: dict | None = None) -> LLMResult:
        """Mirrors the ollama client's .chat() call shape used by
        engine/lib/title_optimizer.py — separate from generate() because
        Ollama's chat endpoint takes a message list, not a system+prompt
        pair, and the two are not interchangeable for a chat-tuned model.
        """
        kwargs: dict = {"model": self.model, "messages": messages}
        if options is not None:
            kwargs["options"] = options

        response = self.client.chat(**kwargs)
        return LLMResult(
            text=response["message"]["content"].strip(),
            tokens_in=response.get("prompt_eval_count"),
            tokens_out=response.get("eval_count"),
            cost_inr=0.0,
        )
