"""Unit tests for accounting/usage_cost.py — no network calls."""

from types import SimpleNamespace

import pytest

from accounting.usage_cost import (
    calculate_cost,
    estimate_partial_cost,
    get_usage_input_tokens,
    get_usage_output_tokens,
)

# ── get_usage_input_tokens ─────────────────────────────────────────────────────


def test_input_tokens_from_input_tokens_attr() -> None:
    assert get_usage_input_tokens(SimpleNamespace(input_tokens=42), "m") == 42


def test_input_tokens_from_prompt_tokens_attr() -> None:
    assert get_usage_input_tokens(SimpleNamespace(prompt_tokens=10), "m") == 10


def test_input_tokens_from_prompt_token_count_attr() -> None:
    assert get_usage_input_tokens(SimpleNamespace(prompt_token_count=7), "m") == 7


def test_input_tokens_from_dict() -> None:
    assert get_usage_input_tokens({"input_tokens": 5}, "m") == 5


def test_input_tokens_unknown_field_raises() -> None:
    with pytest.raises(ValueError, match="not supported"):
        get_usage_input_tokens(SimpleNamespace(unknown=99), "m")


# ── get_usage_output_tokens ────────────────────────────────────────────────────


def test_output_tokens_from_output_tokens_attr() -> None:
    assert get_usage_output_tokens(SimpleNamespace(output_tokens=30), "m") == 30


def test_output_tokens_from_completion_tokens_attr() -> None:
    assert get_usage_output_tokens(SimpleNamespace(completion_tokens=20), "m") == 20


def test_output_tokens_from_candidates_token_count_attr() -> None:
    assert get_usage_output_tokens(SimpleNamespace(candidates_token_count=15), "m") == 15


def test_output_tokens_from_dict() -> None:
    assert get_usage_output_tokens({"output_tokens": 8}, "m") == 8


def test_output_tokens_unknown_field_raises() -> None:
    with pytest.raises(ValueError, match="not supported"):
        get_usage_output_tokens(SimpleNamespace(unknown=99), "m")


# ── calculate_cost ─────────────────────────────────────────────────────────────


def test_calculate_cost_positive_for_openai() -> None:
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=50)
    cost = calculate_cost(usage, "openai", "gpt-4o-mini")
    assert cost > 0


def test_calculate_cost_positive_for_anthropic() -> None:
    usage = SimpleNamespace(input_tokens=100, output_tokens=50)
    cost = calculate_cost(usage, "anthropic", "claude-haiku-4-5")
    assert cost > 0


def test_calculate_cost_scales_with_token_count() -> None:
    small = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
    large = SimpleNamespace(prompt_tokens=1000, completion_tokens=500)
    assert calculate_cost(large, "openai", "gpt-4o-mini") > calculate_cost(
        small, "openai", "gpt-4o-mini"
    )


def test_calculate_cost_output_more_expensive_than_zero_input() -> None:
    zero_input = SimpleNamespace(prompt_tokens=0, completion_tokens=100)
    zero_output = SimpleNamespace(prompt_tokens=100, completion_tokens=0)
    # Both should be positive (input and output have separate rates)
    assert calculate_cost(zero_input, "openai", "gpt-4o-mini") > 0
    assert calculate_cost(zero_output, "openai", "gpt-4o-mini") > 0


# ── estimate_partial_cost ──────────────────────────────────────────────────────


def test_estimate_partial_cost_ollama_cost_is_zero() -> None:
    _, _, cost = estimate_partial_cost("ollama", "llama3.2", "hello", None, "world")
    assert cost == 0.0


def test_estimate_partial_cost_ollama_counts_tokens() -> None:
    in_tok, out_tok, _ = estimate_partial_cost("ollama", "llama3.2", "hello", None, "world")
    assert in_tok > 0
    assert out_tok > 0


def test_estimate_partial_cost_known_model_positive_cost() -> None:
    _, _, cost = estimate_partial_cost("openai", "gpt-4o-mini", "hello", None, "world")
    assert cost > 0


def test_estimate_partial_cost_unknown_model_returns_zeros() -> None:
    result = estimate_partial_cost("unknown-provider", "unknown-model", "hi", None, "response")
    assert result == (0, 0, 0.0)


def test_estimate_partial_cost_system_prompt_increases_input_tokens() -> None:
    in_without, _, _ = estimate_partial_cost("openai", "gpt-4o-mini", "hi", None, "reply")
    in_with, _, _ = estimate_partial_cost(
        "openai", "gpt-4o-mini", "hi", "You are a helpful assistant.", "reply"
    )
    assert in_with > in_without


def test_estimate_partial_cost_empty_output_yields_zero_output_tokens() -> None:
    _, out_tok, _ = estimate_partial_cost("openai", "gpt-4o-mini", "hi", None, "")
    assert out_tok == 0
