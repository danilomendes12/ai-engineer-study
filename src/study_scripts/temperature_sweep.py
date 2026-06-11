"""Temperature sweep & decoding strategies milestone report.

Run:
    uv run python src/decoding_study/temperature_sweep.py

Covers:
  1. Decoding strategies explained (temperature, top_p, top_k)
  2. Temperature sweep 0 / 0.7 / 1.5 with observed variability
  3. tiktoken estimate vs API-reported token counts
  4. Cumulative cost spent from the SQLite DB
  5. Model selection rationale
"""

import sqlite3
import textwrap
from difflib import SequenceMatcher
from pathlib import Path

import tiktoken
from dotenv import load_dotenv

from llm_calls import call_llm

load_dotenv()

_DB_PATH = Path(__file__).parent.parent.parent / "data" / "llm_calls.db"

# gpt-4o-mini supports temperatures 0-2.0 and uses the o200k_base tokenizer,
# which lets us validate tiktoken counts against API-reported values exactly.
# Anthropic caps temperature at 1.0 and uses a proprietary tokenizer.
OPENAI_MODEL = "gpt-4o-mini"
PROMPT = (
    "Suggest a creative product name for a coffee shop with a space theme. "
    "Give only the name, nothing else."
)
MAX_TOKENS = 40
RUNS_PER_TEMP = 3
TEMPERATURES: list[float] = [0.0, 0.7, 1.5]


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _mean_pairwise_similarity(texts: list[str]) -> float:
    pairs = [(texts[i], texts[j]) for i in range(len(texts)) for j in range(i + 1, len(texts))]
    if not pairs:
        return 1.0
    return sum(_similarity(a, b) for a, b in pairs) / len(pairs)


def _tiktoken_count(text: str, encoding: str = "o200k_base") -> int:
    enc = tiktoken.get_encoding(encoding)
    return len(enc.encode(text))


def _per_model_cost() -> list[tuple[str, str, int, float]]:
    """Return [(provider, model, call_count, total_cost)] sorted by cost desc."""
    if not _DB_PATH.exists():
        return []
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT provider, model, COUNT(*), SUM(cost)
            FROM llm_calls
            WHERE response_status IN ('success', 'cancelled')
            GROUP BY provider, model
            ORDER BY SUM(cost) DESC
            """
        ).fetchall()
    return [(str(r[0]), str(r[1]), int(r[2]), float(r[3])) for r in rows]


def _section(title: str) -> None:
    width = 66
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print("=" * width)


def main() -> None:
    _section("1. DECODING STRATEGIES")
    print(
        textwrap.dedent("""
        temperature
          Scales the logits (raw model scores) before applying softmax.
          • 0   → deterministic: always picks the highest-probability token
          • 0.7 → light randomness; coherent but not repetitive
          • 1.0 → sample from the raw model distribution
          • 1.5 → flatten distribution; more surprising, risk of incoherence
          Anthropic API range: 0-1.0.  OpenAI supports 0-2.0.

        top_p  (nucleus sampling)
          Sample from the smallest set of tokens whose cumulative probability
          ≥ p. top_p=0.9 cuts the long tail while adapting to the local
          distribution. More principled than top_k because it is
          distribution-aware.

        top_k
          Restrict candidates to the k highest-logit tokens at each step.
          Fixed cutoff; does not adapt to the shape of the distribution.
          Anthropic exposes top_k; OpenAI does not.

        Recommended defaults
          Code / factual tasks:   temperature=0
          Chat / summaries:       temperature=0.7, top_p=0.9
          Creative / diverse:     temperature=1.0-1.5, top_p=0.95
    """)
    )

    _section(f"2. TEMPERATURE SWEEP  (model: {OPENAI_MODEL}, {RUNS_PER_TEMP} runs each)")
    print(f'  Prompt: "{PROMPT}"\n')

    results: dict[float, list[tuple[str, int, int]]] = {}

    for temp in TEMPERATURES:
        runs: list[tuple[str, int, int]] = []
        print(f"  temperature={temp}")
        for run_idx in range(RUNS_PER_TEMP):
            resp = call_llm(OPENAI_MODEL, PROMPT, MAX_TOKENS, "openai", temperature=temp)
            name = resp.reply.strip()
            api_out = resp.output_tokens
            tik_out = _tiktoken_count(name)
            runs.append((name, api_out, tik_out))
            print(f'    run {run_idx + 1}: "{name}"')
        results[temp] = runs

    _section("3. VARIABILITY ANALYSIS")
    print(f"  {'Temp':>5}  {'Mean similarity':>16}  {'Unique / 3':>10}")
    print("  " + "-" * 36)
    for temp in TEMPERATURES:
        texts = [r[0] for r in results[temp]]
        sim = _mean_pairwise_similarity(texts)
        unique = len({t.lower() for t in texts})
        print(f"  {temp:>5.1f}  {sim:>16.3f}  {unique:>10}/3")
    print(
        textwrap.dedent("""
        Observation
          temperature=0   → identical outputs every run (similarity ≈ 1.0)
          temperature=0.7 → some variation; names share themes but differ
          temperature=1.5 → high diversity; occasionally unusual phrasing
        """)
    )

    _section("4. TIKTOKEN vs API TOKEN COUNT")
    print(
        textwrap.dedent(f"""
        gpt-4o-mini uses the o200k_base tokenizer (OpenAI GPT-4o series).
        tiktoken with o200k_base should match the API-reported counts exactly.
        cl100k_base (GPT-4 / Claude proxy) is shown for comparison.

        {"Temp":>5}  {"Run":>3}  {"API out":>7}  {"o200k":>5}  {"cl100k":>6}  note
        {"─" * 45}""")
    )
    for temp in TEMPERATURES:
        for i, (text, api_tok, tik_o200k) in enumerate(results[temp]):
            tik_cl100k = _tiktoken_count(text, "cl100k_base")
            match = "✓ exact" if tik_o200k == api_tok else f"Δ{tik_o200k - api_tok:+d}"
            print(
                f"  {temp:>5.1f}  {i + 1:>3}  {api_tok:>7}  "
                f"{tik_o200k:>5}  {tik_cl100k:>6}  {match}"
            )
    print(
        textwrap.dedent("""
        Takeaways
          • Use tiktoken with the correct encoding for your model family:
              gpt-4o / gpt-4o-mini → o200k_base
              gpt-4 / gpt-3.5     → cl100k_base
          • For Anthropic/Claude models tiktoken is only an approximation
            (5-15% divergence); always use the API usage field for billing.
          • Short outputs amplify rounding noise - delta is larger as a % on
            1-3 token outputs.
        """)
    )

    _section("5. CUMULATIVE COST FROM DB")
    rows = _per_model_cost()
    if rows:
        total = sum(r[3] for r in rows)
        print(f"  {'Provider':<12} {'Model':<34} {'Calls':>5}  {'Cost USD':>10}")
        print("  " + "-" * 66)
        for provider, model, count, cost in rows:
            print(f"  {provider:<12} {model:<34} {count:>5}  ${cost:>9.6f}")
        print(f"\n  {'TOTAL':<48} ${total:>9.6f}")
    else:
        print("  No calls recorded yet — run some experiments first.")

    _section("6. MODEL SELECTION RATIONALE")
    print(
        textwrap.dedent("""
        claude-haiku-4-5   → default for most tasks
          Lowest latency and cost. Handles chat, extraction, classification,
          and short-form summaries well. Start every new task here.

        claude-sonnet-4-6  → complex reasoning / longer outputs
          Better instruction-following and coherence for multi-step tasks,
          code generation, tool use, and long-form writing.
          Cost is ~5x haiku; still practical for interactive workloads.

        claude-opus-4-8    → hard problems / LLM-as-judge
          Highest quality at the highest cost. Reserve for tasks where haiku
          and sonnet produce unacceptable errors, or when using a model to
          evaluate other models' outputs.

        gpt-4o-mini        → cross-provider baseline / token accounting
          Use when exact token counts matter (tiktoken o200k_base matches
          the API exactly) or as an OpenAI baseline for comparison.

        Gemini 1.5 Pro     → very long context (up to 1 M tokens)
          Use only when the input exceeds Claude's context budget.

        Decision rule:
          haiku → sonnet → opus.  Escalate only when quality clearly fails.
          Prefer Claude (Anthropic) as the primary provider; use OpenAI /
          Gemini for cross-provider comparison or provider-specific features.
        """)
    )


if __name__ == "__main__":
    main()
