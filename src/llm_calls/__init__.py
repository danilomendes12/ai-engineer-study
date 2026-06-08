from .anthropic_client import AnthropicProvider
from .base import CallLLMFn, LLMResponse
from .gemini_client import GeminiProvider
from .openai_client import OpenAIProvider

_REGISTRY: dict[str, CallLLMFn] = {
    "anthropic": AnthropicProvider(),
    "openai": OpenAIProvider(),
    "gemini": GeminiProvider(),
}


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
) -> LLMResponse:
    if provider not in _REGISTRY:
        msg = f"Unknown provider '{provider}'. Available: {list(_REGISTRY)}"
        raise ValueError(msg)
    return _REGISTRY[provider](
        model,
        input_message,
        max_output_tokens,
        system_prompt=system_prompt,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
    )


__all__ = ["CallLLMFn", "LLMResponse", "call_llm"]
