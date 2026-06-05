import time

from dotenv import load_dotenv
from langsmith.wrappers import wrap_openai
from openai import OpenAI

from accounting import calculate_cost

load_dotenv()

MODEL = "gpt-4o-mini"

DEFAULT_MESSAGE = "Quais são os times da copa do mundo 2026?"


def call_llm(model: str = MODEL, max_tokens: int = 128, message: str = DEFAULT_MESSAGE) -> None:
    # wrap_openai instrumenta o cliente: cada chat.completions.create vira um trace.
    client = wrap_openai(OpenAI())

    start = time.perf_counter()
    model_response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": message}],
    )
    latency_ms = (time.perf_counter() - start) * 1000

    reply = model_response.choices[0].message.content or ""
    usage = model_response.usage

    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0
    cost_usd = calculate_cost(usage, "openai", model)

    print(f"Resposta:      {reply}")
    print(f"Modelo:        {MODEL}")
    print(f"Input tokens:  {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Custo (USD):   ${cost_usd:.6f}")
    print(f"Latencia:      {latency_ms:.1f} ms")


if __name__ == "__main__":
    call_llm()
