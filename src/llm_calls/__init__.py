from collections.abc import Generator, Iterator

from db import LlmCall, LlmCallRepository

from .anthropic_client import AnthropicProvider
from .base import CallLLMFn, LLMResponse, StreamChunk
from .gemini_client import GeminiProvider
from .openai_client import OpenAIProvider

_REGISTRY: dict[str, CallLLMFn] = {
    "anthropic": AnthropicProvider(),
    "openai": OpenAIProvider(),
    "gemini": GeminiProvider(),
}

_DEFAULT_REPO: LlmCallRepository | None = None


def _get_repo() -> LlmCallRepository:
    global _DEFAULT_REPO  # noqa: PLW0603
    if _DEFAULT_REPO is None:
        _DEFAULT_REPO = LlmCallRepository()
    return _DEFAULT_REPO


def call_llm(
    model: str,
    input_message: str,
    max_output_tokens: int,
    provider: str,
    *,
    system_prompt: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    repository: LlmCallRepository | None = None,
) -> LLMResponse:
    if provider not in _REGISTRY:
        msg = f"Unknown provider '{provider}'. Available: {list(_REGISTRY)}"
        raise ValueError(msg)

    repo = repository if repository is not None else _get_repo()

    try:
        result = _REGISTRY[provider](
            model,
            input_message,
            max_output_tokens,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
        )
    except Exception as e:
        repo.save(
            LlmCall(
                provider=provider,
                model=model,
                input_tokens=0,
                output_tokens=0,
                cost=0.0,
                latency=0.0,
                prompt=input_message,
                answer="",
                max_tokens=max_output_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                response_status="error",
                error_message=str(e),
                system_prompt=system_prompt,
            )
        )
        raise

    repo.save(
        LlmCall(
            provider=provider,
            model=model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost=result.cost_usd,
            latency=result.latency_ms,
            prompt=input_message,
            answer=result.reply,
            max_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            response_status="success",
            system_prompt=system_prompt,
        )
    )
    return result


def stream_llm(
    model: str,
    input_message: str,
    max_output_tokens: int,
    provider: str,
    *,
    system_prompt: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    repository: LlmCallRepository | None = None,
) -> Iterator[StreamChunk]:
    if provider not in _REGISTRY:
        msg = f"Unknown provider '{provider}'. Available: {list(_REGISTRY)}"
        raise ValueError(msg)

    repo = repository if repository is not None else _get_repo()
    inner = _REGISTRY[provider].__stream__(
        model,
        input_message,
        max_output_tokens,
        system_prompt=system_prompt,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
    )
    return _persist_stream(
        inner,
        repo,
        provider,
        model,
        input_message,
        max_output_tokens,
        system_prompt,
        temperature,
        top_p,
        top_k,
    )


def _persist_stream(
    gen: Iterator[StreamChunk],
    repo: LlmCallRepository,
    provider: str,
    model: str,
    prompt: str,
    max_tokens: int,
    system_prompt: str | None,
    temperature: float | None,
    top_p: float | None,
    top_k: int | None,
) -> Generator[StreamChunk, None, None]:
    deltas: list[str] = []
    done: StreamChunk | None = None
    try:
        for chunk in gen:
            if chunk.type == "delta" and chunk.delta:
                deltas.append(chunk.delta)
            elif chunk.type == "done":
                done = chunk
            yield chunk
    except Exception as e:
        repo.save(
            LlmCall(
                provider=provider,
                model=model,
                input_tokens=0,
                output_tokens=0,
                cost=0.0,
                latency=0.0,
                prompt=prompt,
                answer="".join(deltas),
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                response_status="error",
                error_message=str(e),
                system_prompt=system_prompt,
            )
        )
        raise

    if done is not None:
        repo.save(
            LlmCall(
                provider=provider,
                model=model,
                input_tokens=done.input_tokens or 0,
                output_tokens=done.output_tokens or 0,
                cost=done.cost_usd or 0.0,
                latency=done.latency_ms or 0.0,
                prompt=prompt,
                answer="".join(deltas),
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                ttft_ms=done.ttft_ms,
                response_status="success",
                system_prompt=system_prompt,
            )
        )


__all__ = ["CallLLMFn", "LLMResponse", "StreamChunk", "call_llm", "stream_llm"]
