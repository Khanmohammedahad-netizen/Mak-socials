"""faster-whisper provider — scaffolding for Phase 2's clip engine.

NOT wired into the live pipeline yet. engine/subtitle_generator.py still
uses openai-whisper today (docs/AUDIT.md §6a confirms it already runs
with word_timestamps=True correctly — it works, it's just the slower
implementation). Migrating that call site onto faster-whisper and
verifying word-level timings survive the swap is PROMPT 4 / Phase 2A's
explicit task ("If the audit found openai-whisper, migrate and verify
word-level timings exist on every segment"), not this phase's.
"""

from __future__ import annotations

from src.providers.asr.base import ASRResult, Word


class FasterWhisperProvider:
    name = "faster-whisper"

    def __init__(self, model_size: str = "medium", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None  # lazy: loading is the slow part

    def _model_instance(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size, device=self.device, compute_type=self.compute_type
            )
        return self._model

    def transcribe(self, audio_path: str) -> ASRResult:
        model = self._model_instance()
        segments, _info = model.transcribe(audio_path, word_timestamps=True)

        words: list[Word] = []
        full_text_parts: list[str] = []
        for segment in segments:
            full_text_parts.append(segment.text)
            if segment.words:
                for w in segment.words:
                    words.append(Word(text=w.word.strip(), start_s=w.start, end_s=w.end))

        return ASRResult(text="".join(full_text_parts).strip(), words=words)
