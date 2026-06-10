import time
from collections.abc import Iterator

from dotenv import load_dotenv
from langsmith.wrappers import wrap_openai
from openai import OpenAI, omit
from openai.types.chat import ChatCompletionMessageParam

from accounting import calculate_cost

from .base import CallLLMFn, LLMResponse, StreamChunk

load_dotenv()

MODEL = "gpt-4o-mini"

DEFAULT_MESSAGE = "Quais são os times da copa do mundo 2026?"


class OpenAIProvider(CallLLMFn):
    def __init__(self) -> None:
        self._client = wrap_openai(OpenAI())

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

        ignored: list[str] = []
        if top_k is not None:
            ignored.append("top_k")

        messages: list[ChatCompletionMessageParam] = []
        if system_prompt is not None:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": input_message})

        start = time.perf_counter()
        model_response = client.chat.completions.create(
            model=model,
            max_completion_tokens=max_output_tokens,
            messages=messages,
            temperature=temperature if temperature is not None else omit,
            top_p=top_p if top_p is not None else omit,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        reply = model_response.choices[0].message.content or ""
        usage = model_response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        cost_usd = calculate_cost(usage, "openai", model)

        return LLMResponse(
            reply=reply,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            ignored_params=ignored,
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
        ignored: list[str] = []
        if top_k is not None:
            ignored.append("top_k")

        messages: list[ChatCompletionMessageParam] = []
        if system_prompt is not None:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": input_message})

        start = time.perf_counter()
        ttft_ms: float | None = None
        response = self._client.chat.completions.create(
            model=model,
            max_completion_tokens=max_output_tokens,
            messages=messages,
            temperature=temperature if temperature is not None else omit,
            top_p=top_p if top_p is not None else omit,
            stream=True,
            stream_options={"include_usage": True},
        )

        last_usage = None
        for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta.content
                if delta:
                    if ttft_ms is None:
                        ttft_ms = (time.perf_counter() - start) * 1000
                    yield StreamChunk(type="delta", delta=delta)
            if chunk.usage:
                last_usage = chunk.usage

        latency_ms = (time.perf_counter() - start) * 1000
        input_tokens = last_usage.prompt_tokens if last_usage else 0
        output_tokens = last_usage.completion_tokens if last_usage else 0
        cost_usd = calculate_cost(last_usage, "openai", model) if last_usage else 0.0
        yield StreamChunk(
            type="done",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            ttft_ms=ttft_ms,
            ignored_params=ignored,
        )


call_llm: CallLLMFn = OpenAIProvider()


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
