"""edge-tts primary, Piper fallback, exactly one api_costs row logged
per synthesize() call — same pattern as the LLM router. See
src/providers/tts/piper.py for why Piper must actually work, not stub.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from engine.utils.logger import logger
from src.providers.cost_logger import log_api_cost
from src.providers.tts.base import TTSProvider
from src.providers.tts.edge import EdgeTTSProvider
from src.providers.tts.piper import PiperProvider


class TTSRouter:
    def __init__(self, primary: TTSProvider | None = None, fallback: TTSProvider | None = None):
        self._primary = primary or EdgeTTSProvider()
        self._fallback = fallback or PiperProvider()

    async def synthesize(
        self,
        text: str,
        out_path: str,
        *,
        source_id: str | None = None,
        session: Session | None = None,
        **kwargs,
    ) -> str:
        try:
            result = await self._primary.synthesize(text, out_path, **kwargs)
            provider_used = self._primary
        except Exception as exc:
            logger.warning(
                f"tts_router: provider={self._primary.name} failed ({exc}); "
                "falling back to piper"
            )
            result = await self._fallback.synthesize(text, out_path)
            provider_used = self._fallback

        log_api_cost(
            provider=provider_used.name,
            task_class="TTS",
            source_id=source_id,
            cost_inr=result.cost_inr,
            session=session,
        )
        return result.audio_path
