"""Routes each TaskClass to a provider, logs exactly one api_costs row
per generate() call, and falls back to Ollama on a non-Ollama primary's
failure (logged at WARNING) — per Task D. Every TaskClass in Phase 1
routes to Ollama by default (SCORING/CAPTION/HOOK per the blueprint's
explicit routing table, plus SCRIPT/TITLE for the two existing call
sites this phase migrates). There is nothing to fall back FROM yet,
since nothing routes anywhere else by default — the fallback path
exists for when a later phase points a TaskClass somewhere other than
Ollama (see src/providers/llm/anthropic.py).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from engine.utils.logger import logger
from src.providers.cost_logger import log_api_cost
from src.providers.llm.base import LLMProvider
from src.providers.llm.ollama import OllamaProvider
from src.providers.task_class import TaskClass


class LLMRouter:
    def __init__(
        self,
        ollama_model: str,
        routes: dict[TaskClass, LLMProvider] | None = None,
        ollama_host: str = "http://localhost:11434",
    ):
        self._ollama = OllamaProvider(model=ollama_model, host=ollama_host)
        self._routes: dict[TaskClass, LLMProvider] = routes or {
            tc: self._ollama for tc in TaskClass
        }

    def generate(
        self,
        task_class: TaskClass,
        prompt: str,
        *,
        system: str | None = None,
        options: dict | None = None,
        source_id: str | None = None,
        clip_id: str | None = None,
        session: Session | None = None,
    ) -> str:
        provider = self._routes.get(task_class, self._ollama)

        try:
            result = provider.generate(prompt, system=system, options=options)
            provider_used = provider
        except Exception as exc:
            if provider is self._ollama:
                raise
            logger.warning(
                f"llm_router: provider={provider.name} failed for "
                f"task_class={task_class.value} ({exc}); falling back to ollama"
            )
            result = self._ollama.generate(prompt, system=system, options=options)
            provider_used = self._ollama

        log_api_cost(
            provider=provider_used.name,
            task_class=task_class.value,
            source_id=source_id,
            clip_id=clip_id,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_inr=result.cost_inr,
            session=session,
        )
        return result.text

    def chat(
        self,
        task_class: TaskClass,
        messages: list[dict],
        *,
        options: dict | None = None,
        source_id: str | None = None,
        clip_id: str | None = None,
        session: Session | None = None,
    ) -> str:
        """Same routing/fallback/cost-logging as generate(), for the one
        existing call site (title_optimizer.py) that uses Ollama's chat
        API rather than generate. Only OllamaProvider implements .chat()
        today — a non-Ollama route configured for a TaskClass used here
        would need chat() too, or this raises AttributeError, which is
        the honest failure mode rather than silently doing the wrong
        thing.
        """
        provider = self._routes.get(task_class, self._ollama)

        try:
            result = provider.chat(messages, options=options)
            provider_used = provider
        except Exception as exc:
            if provider is self._ollama:
                raise
            logger.warning(
                f"llm_router: provider={provider.name} failed for "
                f"task_class={task_class.value} ({exc}); falling back to ollama"
            )
            result = self._ollama.chat(messages, options=options)
            provider_used = self._ollama

        log_api_cost(
            provider=provider_used.name,
            task_class=task_class.value,
            source_id=source_id,
            clip_id=clip_id,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_inr=result.cost_inr,
            session=session,
        )
        return result.text
