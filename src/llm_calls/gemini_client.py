import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from accounting import calculate_cost

from .base import CallLLMFn, LLMResponse

load_dotenv()

MODEL = "gemini-2.0-flash"

DEFAULT_MESSAGE = "Quais são os times da copa do mundo 2026?"


class GeminiProvider(CallLLMFn):
    def __init__(self) -> None:
        self._client = genai.Client()

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
        config = types.GenerateContentConfig(
            max_output_tokens=max_output_tokens,
            system_instruction=system_prompt,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
        )

        start = time.perf_counter()
        model_response = self._client.models.generate_content(
            model=model,
            contents=input_message,
            config=config,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        reply = model_response.text or ""
        usage = model_response.usage_metadata
        input_tokens = usage.prompt_token_count or 0 if usage else 0
        output_tokens = usage.candidates_token_count or 0 if usage else 0
        cost_usd = calculate_cost(usage, "gemini", model) if usage else 0.0

        return LLMResponse(
            reply=reply,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )


call_llm: CallLLMFn = GeminiProvider()


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
