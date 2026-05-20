from dotenv import load_dotenv
from langsmith.wrappers import wrap_openai
from openai import OpenAI

load_dotenv()

EMBED_MODEL = "text-embedding-3-small"

# Preco em USD por 1 milhao de tokens (tabela oficial da OpenAI).
# https://openai.com/api/pricing/
PRICE_PER_MTOK: dict[str, float] = {
    "text-embedding-3-small": 0.02,
    "text-embedding-3-large": 0.13,
}

TEXT = "Hello world"


def main() -> None:
    client = wrap_openai(OpenAI())

    response = client.embeddings.create(model=EMBED_MODEL, input=TEXT)
    vector = response.data[0].embedding
    tokens = response.usage.total_tokens
    cost_usd = tokens / 1_000_000 * PRICE_PER_MTOK[EMBED_MODEL]

    print(f"Texto:         {TEXT}")
    print(f"Modelo:        {EMBED_MODEL}")
    print(f"Dimensao:      {len(vector)}")
    print(f"Primeiros 5:   {vector[:5]}")
    print(f"Tokens:        {tokens}")
    print(f"Custo (USD):   ${cost_usd:.8f}")


if __name__ == "__main__":
    main()
