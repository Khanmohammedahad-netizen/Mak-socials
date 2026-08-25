import pytest

from src.core.models import ApiCost
from src.providers.llm.base import LLMResult
from src.providers.llm.router import LLMRouter
from src.providers.task_class import TaskClass


class FakeProvider:
    def __init__(self, name, text="ok", tokens_in=10, tokens_out=20, cost_inr=0.0, error=None):
        self.name = name
        self.text = text
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.cost_inr = cost_inr
        self.error = error
        self.calls = 0

    def generate(self, prompt, *, system=None, options=None):
        self.calls += 1
        if self.error:
            raise self.error
        return LLMResult(
            text=self.text, tokens_in=self.tokens_in, tokens_out=self.tokens_out, cost_inr=self.cost_inr
        )


def test_generate_returns_text_and_logs_one_cost_row(db_session):
    fake_ollama = FakeProvider("ollama", text="a story")
    router = LLMRouter.__new__(LLMRouter)
    router._ollama = fake_ollama
    router._routes = {tc: fake_ollama for tc in TaskClass}

    text = router.generate(TaskClass.SCRIPT, "write a story", session=db_session)

    assert text == "a story"
    rows = db_session.query(ApiCost).all()
    assert len(rows) == 1
    assert rows[0].provider == "ollama"
    assert rows[0].task_class == "SCRIPT"
    assert rows[0].tokens_in == 10
    assert rows[0].tokens_out == 20


def test_non_ollama_primary_falls_back_to_ollama_on_error(db_session, caplog):
    failing = FakeProvider("flaky-provider", error=RuntimeError("connection refused"))
    fake_ollama = FakeProvider("ollama", text="fallback text")

    router = LLMRouter.__new__(LLMRouter)
    router._ollama = fake_ollama
    router._routes = {TaskClass.SCRIPT: failing}

    text = router.generate(TaskClass.SCRIPT, "write a story", session=db_session)

    assert text == "fallback text"
    assert failing.calls == 1
    assert fake_ollama.calls == 1

    rows = db_session.query(ApiCost).all()
    assert len(rows) == 1
    assert rows[0].provider == "ollama"  # attributed to whoever actually served it


def test_ollama_primary_failure_propagates_with_no_further_fallback(db_session):
    fake_ollama = FakeProvider("ollama", error=RuntimeError("ollama is down"))
    router = LLMRouter.__new__(LLMRouter)
    router._ollama = fake_ollama
    router._routes = {TaskClass.SCRIPT: fake_ollama}

    with pytest.raises(RuntimeError, match="ollama is down"):
        router.generate(TaskClass.SCRIPT, "write a story", session=db_session)

    assert db_session.query(ApiCost).count() == 0


def test_unrouted_task_class_defaults_to_ollama(db_session):
    fake_ollama = FakeProvider("ollama", text="default route")
    router = LLMRouter.__new__(LLMRouter)
    router._ollama = fake_ollama
    router._routes = {}  # nothing explicitly routed

    text = router.generate(TaskClass.HOOK, "give me a hook", session=db_session)
    assert text == "default route"
