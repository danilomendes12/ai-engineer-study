import litellm


def _litellm_model(provider: str, model: str) -> str:
    if provider == "gemini":
        return f"gemini/{model}"
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
