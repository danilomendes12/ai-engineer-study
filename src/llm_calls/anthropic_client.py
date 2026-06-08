import time
from collections.abc import Iterator

from anthropic import Anthropic, omit
from anthropic.types import TextBlock
from dotenv import load_dotenv
from langsmith.wrappers import wrap_anthropic

from accounting import calculate_cost

from .base import CallLLMFn, LLMResponse, StreamChunk

load_dotenv()

MODEL = "claude-haiku-4-5"

DEFAULT_MESSAGE = "Quais são os times da copa do mundo 2026?"


class AnthropicProvider(CallLLMFn):
    def __init__(self) -> None:
        self._client = wrap_anthropic(Anthropic())

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
        client = self._client

        start = time.perf_counter()
        model_response = client.messages.create(
            model=model,
            max_tokens=max_output_tokens,
            system=system_prompt if system_prompt is not None else omit,
            messages=[{"role": "user", "content": input_message}],
            temperature=temperature if temperature is not None else omit,
            top_p=top_p if top_p is not None else omit,
            top_k=top_k if top_k is not None else omit,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        reply = "".join(b.text for b in model_response.content if isinstance(b, TextBlock))
        input_tokens = model_response.usage.input_tokens
        output_tokens = model_response.usage.output_tokens
        cost_usd = calculate_cost(model_response.usage, "anthropic", model)

        return LLMResponse(
            reply=reply,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )

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
        start = time.perf_counter()
        ttft_ms: float | None = None
        with self._client.messages.stream(
            model=model,
            max_tokens=max_output_tokens,
            system=system_prompt if system_prompt is not None else omit,
            messages=[{"role": "user", "content": input_message}],
            temperature=temperature if temperature is not None else omit,
            top_p=top_p if top_p is not None else omit,
            top_k=top_k if top_k is not None else omit,
        ) as s:
            for text in s.text_stream:
                if ttft_ms is None:
                    ttft_ms = (time.perf_counter() - start) * 1000
                yield StreamChunk(type="delta", delta=text)
            final = s.get_final_message()

        latency_ms = (time.perf_counter() - start) * 1000
        yield StreamChunk(
            type="done",
            input_tokens=final.usage.input_tokens,
            output_tokens=final.usage.output_tokens,
            cost_usd=calculate_cost(final.usage, "anthropic", model),
            latency_ms=latency_ms,
            ttft_ms=ttft_ms,
        )


call_llm: CallLLMFn = AnthropicProvider()


if __name__ == "__main__":
    result = call_llm(
        MODEL, DEFAULT_MESSAGE, 1280, system_prompt="Você é um assistente útil e prestativo."
    )
    print(f"Resposta:      {result.reply}")
    print(f"Modelo:        {MODEL}")
    print(f"Input tokens:  {result.input_tokens}")
    print(f"Output tokens: {result.output_tokens}")
    print(f"Custo (USD):   ${result.cost_usd:.6f}")
    print(f"Latencia:      {result.latency_ms:.1f} ms")
