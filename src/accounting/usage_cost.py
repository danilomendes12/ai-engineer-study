from .pricing import PRICES


def calculate_cost(usage: object, provider: str, model: str) -> float:
    price = get_price_from_model_and_provider(model, provider)
    input_tokens = get_usage_input_tokens(usage, model)
    output_tokens = get_usage_output_tokens(usage, model)
    return input_tokens / 1_000_000 * price["input"] + output_tokens / 1_000_000 * price["output"]


def get_price_from_model_and_provider(model: str, provider: str) -> dict[str, float]:
    provider_prices = PRICES.get(provider)
    if provider_prices is None:
        msg = f"Unknown provider: {provider!r}"
        raise ValueError(msg)
    price = provider_prices.get(model)
    if price is None:
        msg = f"Unknown model {model!r} for provider {provider!r}"
        raise ValueError(msg)
    return price


def _get_field(usage: object, *names: str) -> int | None:
    for name in names:
        if isinstance(usage, dict):
            if name in usage:
                return usage[name]  # type: ignore[no-any-return]
        elif hasattr(usage, name):
            return getattr(usage, name)  # type: ignore[no-any-return]
    return None


def get_usage_input_tokens(usage: object, model: str) -> int:
    value = _get_field(usage, "input_tokens", "prompt_tokens")
    if value is None:
        msg = f"Input usage format not supported for model {model}"
        raise ValueError(msg)
    return value


def get_usage_output_tokens(usage: object, model: str) -> int:
    value = _get_field(usage, "output_tokens", "completion_tokens")
    if value is None:
        msg = f"Output usage format not supported for model {model}"
        raise ValueError(msg)
    return value
