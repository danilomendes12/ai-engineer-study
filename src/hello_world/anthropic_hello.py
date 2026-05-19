import time

from anthropic import Anthropic
from anthropic.types import TextBlock
from dotenv import load_dotenv
from langsmith.wrappers import wrap_anthropic

load_dotenv()

MODEL = "claude-haiku-4-5"

# Preco em USD por 1 milhao de tokens (tabela oficial da Anthropic).
# https://www.anthropic.com/pricing
PRICE_PER_MTOK: dict[str, dict[str, float]] = {
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00},
}


def calc_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calcula o custo da chamada a partir dos tokens consumidos."""
    price = PRICE_PER_MTOK[model]
    return input_tokens / 1_000_000 * price["input"] + output_tokens / 1_000_000 * price["output"]


def main() -> None:
    # wrap_anthropic instrumenta o cliente: cada messages.create vira um trace.
    client = wrap_anthropic(Anthropic())

    start = time.perf_counter()
    message = client.messages.create(
        model=MODEL,
        max_tokens=128,
        messages=[{"role": "user", "content": "Diga ola em uma frase curta."}],
    )
    latency_ms = (time.perf_counter() - start) * 1000

    reply = "".join(b.text for b in message.content if isinstance(b, TextBlock))
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    cost_usd = calc_cost_usd(MODEL, input_tokens, output_tokens)

    print(f"Resposta:      {reply}")
    print(f"Modelo:        {MODEL}")
    print(f"Input tokens:  {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Custo (USD):   ${cost_usd:.6f}")
    print(f"Latencia:      {latency_ms:.1f} ms")


if __name__ == "__main__":
    main()
