"""Thin wrapper over the exact edge_tts.Communicate(...).save() call
already used in engine/tts_engine.py — same signature, so migrating
that call site onto this class changes nothing about what's sent to
Microsoft's endpoint.
"""

from __future__ import annotations

import edge_tts

from src.providers.tts.base import TTSResult


class EdgeTTSProvider:
    name = "edge-tts"

    async def synthesize(
        self,
        text: str,
        out_path: str,
        *,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
    ) -> TTSResult:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
        await communicate.save(out_path)
        return TTSResult(audio_path=out_path, cost_inr=0.0)
