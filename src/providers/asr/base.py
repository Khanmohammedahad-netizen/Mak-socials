from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Word:
    text: str
    start_s: float
    end_s: float


@dataclass
class ASRResult:
    text: str
    words: list[Word]


class ASRProvider(Protocol):
    name: str

    def transcribe(self, audio_path: str) -> ASRResult: ...
