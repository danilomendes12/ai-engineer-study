import pytest

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
