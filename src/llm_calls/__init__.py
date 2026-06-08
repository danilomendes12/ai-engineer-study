from .anthropic_client import AnthropicProvider
from .base import CallLLMFn, LLMResponse
from .openai_client import OpenAIProvider

_REGISTRY: dict[str, CallLLMFn] = {
    "anthropic": AnthropicProvider(),
    "openai": OpenAIProvider(),
}


def call_llm(
    model: str,
    input_message: str,
    max_output_tokens: int,
    provider: str,
    *,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
) -> LLMResponse:
    if provider not in _REGISTRY:
        msg = f"Unknown provider '{provider}'. Available: {list(_REGISTRY)}"
        raise ValueError(msg)
    return _REGISTRY[provider](
        model,
        input_message,
        max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
    )


__all__ = ["CallLLMFn", "LLMResponse", "call_llm"]
