import time

from anthropic import Anthropic
from anthropic.types import TextBlock
from dotenv import load_dotenv
from langsmith.wrappers import wrap_anthropic

from accounting import calculate_cost

load_dotenv()

MODEL = "claude-haiku-4-5"

DEFAULT_MESSAGE = "Quais são os times da copa do mundo 2026?"


def call_llm(model: str = MODEL, max_tokens: int = 128, message: str = DEFAULT_MESSAGE) -> None:
    client = wrap_anthropic(Anthropic())

    start = time.perf_counter()
    model_response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": message}],
    )
    latency_ms = (time.perf_counter() - start) * 1000

    reply = "".join(b.text for b in model_response.content if isinstance(b, TextBlock))

    input_tokens = model_response.usage.input_tokens
    output_tokens = model_response.usage.output_tokens
    cost_usd = calculate_cost(model_response.usage, "anthropic", model)

    print(f"Resposta:      {reply}")
    print(f"Modelo:        {MODEL}")
    print(f"Input tokens:  {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Custo (USD):   ${cost_usd:.6f}")
    print(f"Latencia:      {latency_ms:.1f} ms")


if __name__ == "__main__":
    call_llm()
