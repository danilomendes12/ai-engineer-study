def calculate_cost (usage, provider, model):
    price = get_price_from_model_and_provider(model, provider)
    input_tokens = get_usage_input_tokens(usage, model)
    output_tokens = get_usage_output_tokens(usage, model)

    return input_tokens / 1_000_000 * price["input"] + output_tokens / 1_000_000 * price["output"]

def get_price_from_model_and_provider(model: str, provider: str) -> dict[str, float]:
    import litellm

    # litellm uses "provider/model" for non-OpenAI providers
    litellm_model = model if provider == "openai" else f"{provider}/{model}"
    info = litellm.get_model_info(litellm_model)
    return {
        "input": float(info["input_cost_per_token"]) * 1_000_000,
        "output": float(info["output_cost_per_token"]) * 1_000_000,
    }


def _get_field(usage, *names):
    for name in names:
        if isinstance(usage, dict):
            if name in usage:
                return usage[name]
        elif hasattr(usage, name):
            return getattr(usage, name)
    return None


def get_usage_input_tokens(usage, model):
    value = _get_field(usage, "input_tokens", "prompt_tokens")
    if value is None:
        raise ValueError(f"Input usage format not supported for model {model}")
    return value


def get_usage_output_tokens(usage, model):
    value = _get_field(usage, "output_tokens", "completion_tokens")
    if value is None:
        raise ValueError(f"Output usage format not supported for model {model}")
    return value