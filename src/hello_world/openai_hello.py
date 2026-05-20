import time

from dotenv import load_dotenv
from langsmith.wrappers import wrap_openai
from openai import OpenAI

load_dotenv()

MODEL = "gpt-4o-mini"

# Preco em USD por 1 milhao de tokens (tabela oficial da OpenAI).
# https://openai.com/api/pricing/
PRICE_PER_MTOK: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
}


def calc_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calcula o custo da chamada a partir dos tokens consumidos."""
    price = PRICE_PER_MTOK[model]
    return input_tokens / 1_000_000 * price["input"] + output_tokens / 1_000_000 * price["output"]


def main() -> None:
    # wrap_openai instrumenta o cliente: cada chat.completions.create vira um trace.
    client = wrap_openai(OpenAI())

    start = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=128,
        messages=[{"role": "user", "content": "Diga ola em uma frase curta."}],
    )
    latency_ms = (time.perf_counter() - start) * 1000

    reply = response.choices[0].message.content or ""
    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0
    cost_usd = calc_cost_usd(MODEL, input_tokens, output_tokens)

    print(f"Resposta:      {reply}")
    print(f"Modelo:        {MODEL}")
    print(f"Input tokens:  {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Custo (USD):   ${cost_usd:.6f}")
    print(f"Latencia:      {latency_ms:.1f} ms")


if __name__ == "__main__":
    main()
