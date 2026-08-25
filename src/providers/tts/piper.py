"""Local, offline TTS fallback for when edge-tts's undocumented Microsoft
endpoint breaks (blueprint §10 R10: "keep Piper wired as a working
fallback, not a TODO"). Runs entirely on-device — free, no network.

Needs a voice model on disk. Default path matches what this project's
setup fetches into assets/tts_models/ (gitignored — see .gitignore,
same treatment as assets/backgrounds/: a binary asset, not source).
"""

from __future__ import annotations

import os
import wave
from pathlib import Path

from pydub import AudioSegment

from src.providers.tts.base import TTSResult

DEFAULT_MODEL_PATH = Path("assets") / "tts_models" / "en_US-lessac-low.onnx"


class PiperModelNotFoundError(FileNotFoundError):
    pass


class PiperProvider:
    name = "piper"

    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path or os.environ.get("PIPER_MODEL_PATH", DEFAULT_MODEL_PATH))
        self._voice = None  # lazy-loaded; the model load itself is the slow part

    def _voice_instance(self):
        if self._voice is None:
            if not self.model_path.exists():
                raise PiperModelNotFoundError(
                    f"Piper voice model not found at {self.model_path}. "
                    "This is the working TTS fallback (blueprint §10 R10) — "
                    "it must not silently no-op. Fetch a voice model, e.g. "
                    "en_US-lessac-low from https://huggingface.co/rhasspy/piper-voices "
                    "and its matching .onnx.json config into that path."
                )
            from piper import PiperVoice

            self._voice = PiperVoice.load(str(self.model_path))
        return self._voice

    async def synthesize(self, text: str, out_path: str, **kwargs) -> TTSResult:
        voice = self._voice_instance()

        wav_path = out_path if out_path.lower().endswith(".wav") else out_path + ".piper_tmp.wav"
        with wave.open(wav_path, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)

        if wav_path != out_path:
            AudioSegment.from_file(wav_path).export(out_path, format=_format_from_ext(out_path))
            os.remove(wav_path)

        return TTSResult(audio_path=out_path, cost_inr=0.0)


def _format_from_ext(path: str) -> str:
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    return ext or "mp3"
