import socket
from pathlib import Path

import pytest

from db import LlmCall, LlmCallRepository
from llm_calls import LLMResponse, StreamChunk, call_llm, stream_llm

SOCCER_QUESTION = "Which national teams are participating in the 2026 FIFA World Cup?"
MAX_TOKENS = 256
PROVIDER = "ollama"
MODEL = "llama3.2"
SYSTEM_PROMPT = "You are a concise assistant. Answer in one sentence."


def _ollama_available() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=1):
            return True
    except OSError:
        return False


skip_if_no_ollama = pytest.mark.skipif(
    not _ollama_available(),
    reason="Ollama not running — start with: ollama serve",
)


@pytest.fixture
def repo(tmp_path: Path) -> LlmCallRepository:
    return LlmCallRepository(tmp_path / "test.db")


@skip_if_no_ollama
def test_call_returns_reply() -> None:
    result: LLMResponse = call_llm(MODEL, SOCCER_QUESTION, MAX_TOKENS, PROVIDER)
    assert isinstance(result.reply, str)
    assert len(result.reply) > 0


@skip_if_no_ollama
def test_call_cost_is_zero() -> None:
    result: LLMResponse = call_llm(MODEL, SOCCER_QUESTION, MAX_TOKENS, PROVIDER)
    assert result.cost_usd == 0.0


@skip_if_no_ollama
def test_stream_yields_reply() -> None:
    chunks: list[StreamChunk] = list(stream_llm(MODEL, SOCCER_QUESTION, MAX_TOKENS, PROVIDER))

    delta_chunks = [c for c in chunks if c.type == "delta" and c.delta]
    done_chunks = [c for c in chunks if c.type == "done"]

    assert len(delta_chunks) > 0, "must have at least one delta chunk with text"
    assert len(done_chunks) == 1, "must end with exactly one done chunk"

    full_reply = "".join(c.delta for c in delta_chunks if c.delta)
    assert len(full_reply) > 0


@skip_if_no_ollama
def test_call_persists(repo: LlmCallRepository) -> None:
    call_llm(MODEL, SOCCER_QUESTION, MAX_TOKENS, PROVIDER, repository=repo)

    saved: list[LlmCall] = repo.list_all()
    assert len(saved) == 1

    record = saved[0]
    assert record.provider == PROVIDER
    assert record.model == MODEL
    assert record.input_tokens > 0
    assert record.output_tokens > 0
    assert record.cost == 0.0  # local model — no billing
    assert record.latency > 0
    assert record.prompt == SOCCER_QUESTION
    assert len(record.answer) > 0
    assert record.response_status == "success"
    assert record.error_message is None
    assert record.id is not None
    assert record.created_at is not None


@skip_if_no_ollama
def test_stream_persists(repo: LlmCallRepository) -> None:
    list(stream_llm(MODEL, SOCCER_QUESTION, MAX_TOKENS, PROVIDER, repository=repo))

    saved: list[LlmCall] = repo.list_all()
    assert len(saved) == 1

    record = saved[0]
    assert record.provider == PROVIDER
    assert record.model == MODEL
    assert record.input_tokens > 0
    assert record.output_tokens > 0
    assert record.cost == 0.0
    assert record.latency > 0
    assert record.prompt == SOCCER_QUESTION
    assert len(record.answer) > 0
    assert record.ttft_ms is not None
    assert record.ttft_ms > 0
    assert record.response_status == "success"
    assert record.error_message is None


@skip_if_no_ollama
def test_call_persists_system_prompt(repo: LlmCallRepository) -> None:
    call_llm(
        MODEL,
        SOCCER_QUESTION,
        MAX_TOKENS,
        PROVIDER,
        system_prompt=SYSTEM_PROMPT,
        repository=repo,
    )
    saved: list[LlmCall] = repo.list_all()
    assert saved[0].system_prompt == SYSTEM_PROMPT


@skip_if_no_ollama
def test_stream_persists_system_prompt(repo: LlmCallRepository) -> None:
    list(
        stream_llm(
            MODEL,
            SOCCER_QUESTION,
            MAX_TOKENS,
            PROVIDER,
            system_prompt=SYSTEM_PROMPT,
            repository=repo,
        )
    )
    saved: list[LlmCall] = repo.list_all()
    assert saved[0].system_prompt == SYSTEM_PROMPT
