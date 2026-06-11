"""Unit tests for the stream persistence and cancellation path in llm_calls."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest

from db import LlmCallRepository
from llm_calls import StreamChunk, stream_llm
from llm_calls.base import CallLLMFn, LLMResponse

# ── Fake providers ─────────────────────────────────────────────────────────────


class _FixedStreamProvider(CallLLMFn):
    """Yields a predetermined sequence of chunks."""

    def __init__(self, chunks: list[StreamChunk]) -> None:
        self._chunks = chunks

    def __call__(
        self,
        model: str,
        input_message: str,
        max_output_tokens: int,
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
    ) -> LLMResponse:
        raise NotImplementedError

    def __stream__(
        self,
        model: str,
        input_message: str,
        max_output_tokens: int,
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
    ) -> Iterator[StreamChunk]:
        yield from self._chunks


class _ErrorStreamProvider(CallLLMFn):
    """Yields one delta then raises RuntimeError."""

    def __call__(
        self,
        model: str,
        input_message: str,
        max_output_tokens: int,
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
    ) -> LLMResponse:
        raise NotImplementedError

    def __stream__(
        self,
        model: str,
        input_message: str,
        max_output_tokens: int,
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
    ) -> Iterator[StreamChunk]:
        yield StreamChunk(type="delta", delta="partial")
        msg = "boom"
        raise RuntimeError(msg)


# ── Shared fixtures & helpers ──────────────────────────────────────────────────

_DONE = StreamChunk(
    type="done",
    input_tokens=10,
    output_tokens=5,
    cost_usd=0.001,
    latency_ms=100.0,
    ttft_ms=50.0,
)

_DELTAS = [
    StreamChunk(type="delta", delta="Hello"),
    StreamChunk(type="delta", delta=" World"),
]


@pytest.fixture
def repo(tmp_path: Path) -> LlmCallRepository:
    return LlmCallRepository(tmp_path / "test.db")


def _registry(provider_key: str, chunks: list[StreamChunk]) -> dict[str, CallLLMFn]:
    return {provider_key: _FixedStreamProvider(chunks)}


# ── Happy path ─────────────────────────────────────────────────────────────────


def test_completed_stream_status_is_success(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", _registry("fake", [*_DELTAS, _DONE])):
        list(stream_llm("fake-model", "prompt", 100, "fake", repository=repo))

    (record,) = repo.list_all()
    assert record.response_status == "success"


def test_completed_stream_answer_is_full_text(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", _registry("fake", [*_DELTAS, _DONE])):
        list(stream_llm("fake-model", "prompt", 100, "fake", repository=repo))

    (record,) = repo.list_all()
    assert record.answer == "Hello World"


def test_completed_stream_persists_token_counts(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", _registry("fake", [*_DELTAS, _DONE])):
        list(stream_llm("fake-model", "prompt", 100, "fake", repository=repo))

    (record,) = repo.list_all()
    assert record.input_tokens == 10
    assert record.output_tokens == 5


def test_completed_stream_persists_ttft(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", _registry("fake", [*_DELTAS, _DONE])):
        list(stream_llm("fake-model", "prompt", 100, "fake", repository=repo))

    (record,) = repo.list_all()
    assert record.ttft_ms == pytest.approx(50.0)


def test_completed_stream_done_chunk_carries_call_id(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", _registry("fake", [*_DELTAS, _DONE])):
        chunks = list(stream_llm("fake-model", "prompt", 100, "fake", repository=repo))

    done = next(c for c in chunks if c.type == "done")
    (record,) = repo.list_all()
    assert done.call_id == record.id


# ── Cancellation path ──────────────────────────────────────────────────────────


def test_cancelled_stream_status_is_cancelled(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", _registry("fake", [*_DELTAS, _DONE])):
        gen = stream_llm("fake-model", "prompt", 100, "fake", repository=repo)
        next(gen)  # consume one delta
        gen.close()  # triggers GeneratorExit → cancelled

    (record,) = repo.list_all()
    assert record.response_status == "cancelled"


def test_cancelled_stream_error_message_is_none(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", _registry("fake", [*_DELTAS, _DONE])):
        gen = stream_llm("fake-model", "prompt", 100, "fake", repository=repo)
        next(gen)
        gen.close()

    (record,) = repo.list_all()
    assert record.error_message is None


def test_cancelled_stream_preserves_partial_text(repo: LlmCallRepository) -> None:
    chunks = [StreamChunk(type="delta", delta="partial"), _DONE]
    with patch.dict("llm_calls._REGISTRY", _registry("fake", chunks)):
        gen = stream_llm("fake-model", "prompt", 100, "fake", repository=repo)
        next(gen)
        gen.close()

    (record,) = repo.list_all()
    assert record.answer == "partial"


def test_unstarted_generator_saves_nothing(repo: LlmCallRepository) -> None:
    # Closing a generator before the first next() call never enters the try/finally
    # block, so no record is saved. This is the correct Python generator behaviour.
    with patch.dict("llm_calls._REGISTRY", _registry("fake", [*_DELTAS, _DONE])):
        gen = stream_llm("fake-model", "prompt", 100, "fake", repository=repo)
        gen.close()

    assert repo.list_all() == []


# ── Error path ─────────────────────────────────────────────────────────────────


def test_error_stream_status_is_error(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", {"fake": _ErrorStreamProvider()}):
        gen = stream_llm("fake-model", "prompt", 100, "fake", repository=repo)
        with pytest.raises(RuntimeError):
            list(gen)

    (record,) = repo.list_all()
    assert record.response_status == "error"


def test_error_stream_persists_error_message(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", {"fake": _ErrorStreamProvider()}):
        gen = stream_llm("fake-model", "prompt", 100, "fake", repository=repo)
        with pytest.raises(RuntimeError):
            list(gen)

    (record,) = repo.list_all()
    assert record.error_message == "boom"


def test_error_stream_preserves_partial_text(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", {"fake": _ErrorStreamProvider()}):
        gen = stream_llm("fake-model", "prompt", 100, "fake", repository=repo)
        with pytest.raises(RuntimeError):
            list(gen)

    (record,) = repo.list_all()
    assert record.answer == "partial"


def test_exactly_one_record_saved_on_error(repo: LlmCallRepository) -> None:
    with patch.dict("llm_calls._REGISTRY", {"fake": _ErrorStreamProvider()}):
        gen = stream_llm("fake-model", "prompt", 100, "fake", repository=repo)
        with pytest.raises(RuntimeError):
            list(gen)

    assert len(repo.list_all()) == 1
