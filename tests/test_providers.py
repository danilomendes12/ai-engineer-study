from pathlib import Path

import pytest

from db import LlmCall, LlmCallRepository
from llm_calls import LLMResponse, StreamChunk, call_llm, stream_llm

SOCCER_QUESTION = "Which national teams are participating in the 2026 FIFA World Cup?"
MAX_TOKENS = 256

_xfail_gemini = pytest.mark.xfail(
    strict=False,
    reason="Gemini may fail due to insufficient API credits",
)

PROVIDERS = [
    ("anthropic", "claude-haiku-4-5"),
    ("openai", "gpt-4o-mini"),
    pytest.param("gemini", "gemini-2.0-flash", marks=_xfail_gemini),
]


@pytest.fixture
def repo(tmp_path: Path) -> LlmCallRepository:
    return LlmCallRepository(tmp_path / "test.db")


@pytest.mark.parametrize(("provider", "model"), PROVIDERS)
def test_call_returns_reply(provider: str, model: str) -> None:
    result: LLMResponse = call_llm(model, SOCCER_QUESTION, MAX_TOKENS, provider)
    assert isinstance(result.reply, str)
    assert len(result.reply) > 0


@pytest.mark.parametrize(("provider", "model"), PROVIDERS)
def test_stream_yields_reply(provider: str, model: str) -> None:
    chunks: list[StreamChunk] = list(stream_llm(model, SOCCER_QUESTION, MAX_TOKENS, provider))

    delta_chunks = [c for c in chunks if c.type == "delta" and c.delta]
    done_chunks = [c for c in chunks if c.type == "done"]

    assert len(delta_chunks) > 0, "must have at least one delta chunk with text"
    assert len(done_chunks) == 1, "must end with exactly one done chunk"

    full_reply = "".join(c.delta for c in delta_chunks if c.delta)
    assert len(full_reply) > 0


@pytest.mark.parametrize(("provider", "model"), PROVIDERS)
def test_call_persists(provider: str, model: str, repo: LlmCallRepository) -> None:
    call_llm(model, SOCCER_QUESTION, MAX_TOKENS, provider, repository=repo)

    saved: list[LlmCall] = repo.list_all()
    assert len(saved) == 1

    record = saved[0]
    assert record.provider == provider
    assert record.model == model
    assert record.input_tokens > 0
    assert record.output_tokens > 0
    assert record.cost > 0
    assert record.latency > 0
    assert record.prompt == SOCCER_QUESTION
    assert len(record.answer) > 0
    assert record.response_status == "success"
    assert record.error_message is None
    assert record.id is not None
    assert record.created_at is not None


@pytest.mark.parametrize(("provider", "model"), PROVIDERS)
def test_stream_persists(provider: str, model: str, repo: LlmCallRepository) -> None:
    list(stream_llm(model, SOCCER_QUESTION, MAX_TOKENS, provider, repository=repo))

    saved: list[LlmCall] = repo.list_all()
    assert len(saved) == 1

    record = saved[0]
    assert record.provider == provider
    assert record.model == model
    assert record.input_tokens > 0
    assert record.output_tokens > 0
    assert record.cost > 0
    assert record.latency > 0
    assert record.prompt == SOCCER_QUESTION
    assert len(record.answer) > 0
    assert record.ttft_ms is not None
    assert record.ttft_ms > 0
    assert record.response_status == "success"
    assert record.error_message is None


SYSTEM_PROMPT = "You are a concise assistant. Answer in one sentence."


@pytest.mark.parametrize(("provider", "model"), PROVIDERS)
def test_call_persists_system_prompt(provider: str, model: str, repo: LlmCallRepository) -> None:
    call_llm(
        model,
        SOCCER_QUESTION,
        MAX_TOKENS,
        provider,
        system_prompt=SYSTEM_PROMPT,
        repository=repo,
    )
    saved: list[LlmCall] = repo.list_all()
    assert saved[0].system_prompt == SYSTEM_PROMPT


@pytest.mark.parametrize(("provider", "model"), PROVIDERS)
def test_stream_persists_system_prompt(provider: str, model: str, repo: LlmCallRepository) -> None:
    list(
        stream_llm(
            model,
            SOCCER_QUESTION,
            MAX_TOKENS,
            provider,
            system_prompt=SYSTEM_PROMPT,
            repository=repo,
        )
    )
    saved: list[LlmCall] = repo.list_all()
    assert saved[0].system_prompt == SYSTEM_PROMPT
