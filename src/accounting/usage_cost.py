import litellm


def _litellm_model(provider: str, model: str) -> str:
    if provider == "gemini":
        return f"gemini/{model}"
    if provider == "ollama":
        return f"ollama/{model}"
    return model


def calculate_cost(usage: object, provider: str, model: str) -> float:
    litellm_model = _litellm_model(provider, model)
    input_tokens = get_usage_input_tokens(usage, model)
    output_tokens = get_usage_output_tokens(usage, model)
    input_cost, output_cost = litellm.cost_per_token(
        model=litellm_model,
        prompt_tokens=input_tokens,
        completion_tokens=output_tokens,
    )
    return input_cost + output_cost


def _get_field(usage: object, *names: str) -> int | None:
    for name in names:
        if isinstance(usage, dict):
            if name in usage:
                return usage[name]  # type: ignore[no-any-return]
        elif hasattr(usage, name):
            return getattr(usage, name)  # type: ignore[no-any-return]
    return None


def get_usage_input_tokens(usage: object, model: str) -> int:
    value = _get_field(usage, "input_tokens", "prompt_tokens", "prompt_token_count")
    if value is None:
        msg = f"Input usage format not supported for model {model}"
        raise ValueError(msg)
    return value


def get_usage_output_tokens(usage: object, model: str) -> int:
    value = _get_field(usage, "output_tokens", "completion_tokens", "candidates_token_count")
    if value is None:
        msg = f"Output usage format not supported for model {model}"
        raise ValueError(msg)
    return value


def estimate_partial_cost(
    provider: str,
    model: str,
    prompt: str,
    system_prompt: str | None,
    partial_output: str,
) -> tuple[int, int, float]:
    """Estimate cost for a cancelled/partial stream from raw text.

    Falls back to (0, 0, 0.0) when litellm doesn't recognise the model.
    Ollama is always (n, m, 0.0) — local models have no monetary cost.
    """
    litellm_model = _litellm_model(provider, model)
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    try:
        input_tokens: int = litellm.token_counter(model=litellm_model, messages=messages)
        output_tokens: int = (
            litellm.token_counter(model=litellm_model, text=partial_output) if partial_output else 0
        )
        if provider == "ollama":
            return input_tokens, output_tokens, 0.0
        input_cost, output_cost = litellm.cost_per_token(
            model=litellm_model,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
        )
        return input_tokens, output_tokens, input_cost + output_cost
    except Exception:  # noqa: BLE001
        return 0, 0, 0.0
