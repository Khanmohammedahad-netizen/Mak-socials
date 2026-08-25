from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class TTSResult:
    audio_path: str
    cost_inr: float = 0.0


class TTSProvider(Protocol):
    name: str

    async def synthesize(self, text: str, out_path: str, **kwargs) -> TTSResult: ...
