"""Structural test only. Not wired into the live pipeline this phase
(see faster_whisper.py's module docstring) — real transcription is
exercised in Phase 2's clip engine tests, not here."""

from src.providers.asr.base import ASRResult, Word
from src.providers.asr.faster_whisper import FasterWhisperProvider


def test_provider_is_lazy_no_model_load_on_construction():
    provider = FasterWhisperProvider(model_size="tiny")
    assert provider._model is None  # loading only happens on first transcribe()


def test_result_dataclasses_hold_word_level_timing():
    result = ASRResult(text="hi there", words=[Word("hi", 0.0, 0.3), Word("there", 0.3, 0.7)])
    assert result.words[0].start_s == 0.0
    assert result.words[1].end_s == 0.7
