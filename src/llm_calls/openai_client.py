import time

from dotenv import load_dotenv
from langsmith.wrappers import wrap_openai
from openai import OpenAI, omit

from accounting import calculate_cost

from .base import CallLLMFn, LLMResponse

load_dotenv()

MODEL = "gpt-4o-mini"

DEFAULT_MESSAGE = "Quais são os times da copa do mundo 2026?"


class OpenAIProvider(CallLLMFn):
    def __call__(
        self,
        model: str,
        input_message: str,
        max_output_tokens: int,
        *,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,  # noqa: ARG002 — not supported by OpenAI
    ) -> LLMResponse:
        client = wrap_openai(OpenAI())

        start = time.perf_counter()
        model_response = client.chat.completions.create(
            model=model,
            max_tokens=max_output_tokens,
            messages=[{"role": "user", "content": input_message}],
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
        )


call_llm: CallLLMFn = OpenAIProvider()


if __name__ == "__main__":
    result = call_llm(MODEL, DEFAULT_MESSAGE, 128)
    print(f"Resposta:      {result.reply}")
    print(f"Modelo:        {MODEL}")
    print(f"Input tokens:  {result.input_tokens}")
    print(f"Output tokens: {result.output_tokens}")
    print(f"Custo (USD):   ${result.cost_usd:.6f}")
    print(f"Latencia:      {result.latency_ms:.1f} ms")
