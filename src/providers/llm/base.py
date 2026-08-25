from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    text: str
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_inr: float = 0.0


class LLMProvider(Protocol):
    name: str

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        options: dict | None = None,
    ) -> LLMResult: ...
