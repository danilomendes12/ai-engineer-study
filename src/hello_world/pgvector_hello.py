import os
import time

import psycopg
from dotenv import load_dotenv
from langsmith.wrappers import wrap_openai
from openai import OpenAI
from pgvector.psycopg import register_vector  # type: ignore[import-untyped]

load_dotenv()

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536

# Preco em USD por 1 milhao de tokens (tabela oficial da OpenAI).
# https://openai.com/api/pricing/
PRICE_PER_MTOK: dict[str, float] = {
    "text-embedding-3-small": 0.02,
    "text-embedding-3-large": 0.13,
}

DOCS: list[str] = [
    "carro vermelho",
    "automovel azul",
    "banana madura",
]

QUERY = "veiculo"


def embed(client: OpenAI, texts: list[str]) -> tuple[list[list[float]], int]:
    """Gera embeddings via OpenAI. Retorna vetores e total de tokens consumidos."""
    response = client.embeddings.create(model=EMBED_MODEL, input=texts)
    vectors = [item.embedding for item in response.data]
    return vectors, response.usage.total_tokens


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    client = wrap_openai(OpenAI())

    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS hello_vectors (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                embedding vector({EMBED_DIM}) NOT NULL
            )
            """,
        )
        conn.execute("TRUNCATE hello_vectors RESTART IDENTITY")

        start = time.perf_counter()
        doc_vectors, embed_tokens = embed(client, DOCS)
        embed_ms = (time.perf_counter() - start) * 1000

        conn.cursor().executemany(
            "INSERT INTO hello_vectors (text, embedding) VALUES (%s, %s)",
            list(zip(DOCS, doc_vectors, strict=True)),
        )

        start = time.perf_counter()
        query_vectors, query_tokens = embed(client, [QUERY])
        query_ms = (time.perf_counter() - start) * 1000

        # Operador <=> retorna cosine distance: 0 = identico, 2 = oposto.
        # Cast %s::vector e necessario: register_vector adapta numpy/Vector,
        # mas list[float] cai no adapter padrao do psycopg (double precision[]).
        rows = conn.execute(
            "SELECT text, embedding <=> %s::vector AS distance "
            "FROM hello_vectors ORDER BY distance",
            (query_vectors[0],),
        ).fetchall()

    total_tokens = embed_tokens + query_tokens
    cost_usd = total_tokens / 1_000_000 * PRICE_PER_MTOK[EMBED_MODEL]

    print(f"Query:         {QUERY}")
    print(f"Modelo:        {EMBED_MODEL}")
    print(f"Tokens:        {total_tokens}")
    print(f"Custo (USD):   ${cost_usd:.6f}")
    print(f"Embed docs:    {embed_ms:.1f} ms ({len(DOCS)} textos)")
    print(f"Embed query:   {query_ms:.1f} ms")
    print()
    print("Resultados (ordenados por cosine distance):")
    for text, distance in rows:
        print(f"  [{distance:.4f}] {text}")


if __name__ == "__main__":
    main()
