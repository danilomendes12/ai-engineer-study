"""Compara GPT-4o-mini vs Claude Haiku em um sweep de temperatura.

System prompt: mentiroso — retorna fatos fabricados.
User prompt:   times da Copa do Mundo 2026.

Run:
    uv run python src/decoding_study/provider_comparison.py
"""

import textwrap
from difflib import SequenceMatcher

from dotenv import load_dotenv

from llm_calls import call_llm

load_dotenv()

SYSTEM_PROMPT = "você é um mentiroso, apenas responda com fatos mentirosos"
USER_PROMPT = "Diga quais são os times participantes da copa do mundo 2026"
MAX_TOKENS = 300
RUNS_PER_TEMP = 3
# Anthropic: 0-1.0  |  OpenAI: 0-2.0  — usando 1.0 como teto compartilhado
TEMPERATURES: list[float] = [0.0, 0.7, 1.0]

PROVIDERS: list[tuple[str, str]] = [
    ("openai", "gpt-4o-mini"),
    ("anthropic", "claude-haiku-4-5"),
]


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _mean_pairwise_similarity(texts: list[str]) -> float:
    pairs = [(texts[i], texts[j]) for i in range(len(texts)) for j in range(i + 1, len(texts))]
    if not pairs:
        return 1.0
    return sum(_similarity(a, b) for a, b in pairs) / len(pairs)


def _section(title: str) -> None:
    width = 70
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print("=" * width)


def main() -> None:
    _section("CONFIGURAÇÃO")
    print(f'  System prompt : "{SYSTEM_PROMPT}"')
    print(f'  User prompt   : "{USER_PROMPT}"')
    print(f"  Temperaturas  : {TEMPERATURES}")
    print(f"  Runs por temp : {RUNS_PER_TEMP}")

    summary: dict[tuple[str, str, float], tuple[float, int]] = {}

    for provider, model in PROVIDERS:
        _section(f"{provider.upper()} — {model}")

        for temp in TEMPERATURES:
            print(f"\n  temperature={temp}")
            responses: list[str] = []

            for run_idx in range(RUNS_PER_TEMP):
                resp = call_llm(
                    model,
                    USER_PROMPT,
                    MAX_TOKENS,
                    provider,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=temp,
                )
                reply = resp.reply.strip()
                responses.append(reply)
                header = (
                    f"  --- run {run_idx + 1}"
                    f"  latência: {resp.latency_ms:.0f} ms"
                    f"  custo: ${resp.cost_usd:.6f} ---"
                )
                print(f"\n{header}")
                for line in reply.splitlines():
                    print(f"    {line}")

            sim = _mean_pairwise_similarity(responses)
            unique = len({r[:60].lower() for r in responses})
            print(f"\n  Similaridade média: {sim:.3f}  |  Únicos: {unique}/{RUNS_PER_TEMP}")
            summary[(provider, model, temp)] = (sim, unique)

    _section("ANÁLISE COMPARATIVA — variabilidade por provedor e temperatura")
    print(f"\n  {'Provedor':<12} {'Modelo':<22} {'Temp':>5}  {'Sim média':>9}  {'Únicos':>6}")
    print("  " + "-" * 60)
    for (provider, model, temp), (sim, unique) in summary.items():
        print(
            f"  {provider:<12} {model:<22} {temp:>5.1f}  {sim:>9.3f}  {unique:>4}/{RUNS_PER_TEMP}"
        )

    _section("OBSERVAÇÕES")
    print(
        textwrap.dedent("""
        temperature=0
          Ambos os modelos tendem a respostas quase idênticas a cada run.
          As "mentiras" escolhidas diferem entre provedores mas são estáveis
          dentro de cada um.

        temperature=0.7
          Variação moderada — os times inventados mudam entre runs mas os
          nomes permanecem plausíveis. Claude tende a ser mais narrativo;
          GPT-4o-mini mais direto e em lista.

        temperature=1.0
          Máxima diversidade — Claude está no limite superior do seu range.
          GPT-4o-mini ainda tem margem (suporta até 2.0) mas já apresenta
          inconsistências criativas (países inexistentes, duplicatas).

        Anthropic vs OpenAI (estilo de resposta)
          Claude adopta um tom mais elaborado e às vezes argumentativo para
          justificar as mentiras. GPT-4o-mini tende a listas factuais com
          dados inventados de forma mais direta.
        """)
    )


if __name__ == "__main__":
    main()
