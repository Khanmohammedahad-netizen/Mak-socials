import audioop
import wave

import pytest

from src.core.models import ApiCost
from src.providers.tts.base import TTSResult
from src.providers.tts.piper import DEFAULT_MODEL_PATH, PiperProvider
from src.providers.tts.router import TTSRouter


class FakeTTSProvider:
    def __init__(self, name, error=None):
        self.name = name
        self.error = error
        self.calls = []

    async def synthesize(self, text, out_path, **kwargs):
        self.calls.append((text, out_path, kwargs))
        if self.error:
            raise self.error
        with open(out_path, "w") as f:
            f.write("fake audio bytes")
        return TTSResult(audio_path=out_path, cost_inr=0.0)


async def test_primary_success_logs_one_cost_row(db_session, tmp_path):
    primary = FakeTTSProvider("edge-tts")
    fallback = FakeTTSProvider("piper")
    router = TTSRouter(primary=primary, fallback=fallback)

    out = str(tmp_path / "out.mp3")
    result_path = await router.synthesize("hello", out, session=db_session)

    assert result_path == out
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 0
    rows = db_session.query(ApiCost).all()
    assert len(rows) == 1
    assert rows[0].provider == "edge-tts"
    assert rows[0].task_class == "TTS"


async def test_primary_failure_falls_back_to_piper_and_logs_one_row(db_session, tmp_path):
    primary = FakeTTSProvider("edge-tts", error=RuntimeError("endpoint broke"))
    fallback = FakeTTSProvider("piper")
    router = TTSRouter(primary=primary, fallback=fallback)

    out = str(tmp_path / "out.mp3")
    await router.synthesize("hello", out, session=db_session)

    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1
    rows = db_session.query(ApiCost).all()
    assert len(rows) == 1
    assert rows[0].provider == "piper"


@pytest.mark.skipif(
    not DEFAULT_MODEL_PATH.exists(),
    reason="Piper voice model not fetched (assets/tts_models/) — see PiperProvider docstring",
)
async def test_piper_produces_audible_non_silent_output_when_edge_tts_forced_to_fail(
    db_session, tmp_path
):
    """The literal Phase 1 acceptance criterion: Piper must produce real
    audible output, not a silent stub, when edge-tts is unavailable."""

    class AlwaysFailingEdge:
        name = "edge-tts"

        async def synthesize(self, text, out_path, **kwargs):
            raise RuntimeError("Microsoft's undocumented endpoint is down")

    router = TTSRouter(primary=AlwaysFailingEdge(), fallback=PiperProvider())
    out = str(tmp_path / "fallback_test.wav")

    result_path = await router.synthesize(
        "This is a test of the piper text to speech fallback.",
        out,
        session=db_session,
    )

    with wave.open(result_path, "rb") as w:
        assert w.getnframes() > 0
        data = w.readframes(w.getnframes())
        rms = audioop.rms(data, w.getsampwidth())

    assert rms > 100, f"output is near-silent (rms={rms}) — not real audible speech"

    rows = db_session.query(ApiCost).all()
    assert len(rows) == 1
    assert rows[0].provider == "piper"
