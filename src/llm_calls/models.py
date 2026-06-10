import contextlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class ModelEntry:
    provider: str
    model: str


_STATIC_MODELS: list[ModelEntry] = [
    # ── Anthropic ──────────────────────────────────────────────────────────────
    ModelEntry("anthropic", "claude-haiku-4-5"),
    ModelEntry("anthropic", "claude-sonnet-4-6"),
    ModelEntry("anthropic", "claude-opus-4-8"),
    ModelEntry("anthropic", "claude-3-5-haiku-20241022"),
    ModelEntry("anthropic", "claude-3-5-sonnet-20241022"),
    ModelEntry("anthropic", "claude-3-opus-20240229"),
    # ── OpenAI ────────────────────────────────────────────────────────────────
    ModelEntry("openai", "gpt-4o-mini"),
    ModelEntry("openai", "gpt-4o"),
    ModelEntry("openai", "gpt-4-turbo"),
    ModelEntry("openai", "o1-mini"),
    ModelEntry("openai", "o1-preview"),
    ModelEntry("openai", "o3-mini"),
    ModelEntry("openai", "gpt-3.5-turbo"),
    # ── Gemini ────────────────────────────────────────────────────────────────
    ModelEntry("gemini", "gemini-2.0-flash"),
    ModelEntry("gemini", "gemini-2.0-flash-exp"),
    ModelEntry("gemini", "gemini-1.5-pro"),
    ModelEntry("gemini", "gemini-1.5-flash"),
    ModelEntry("gemini", "gemini-1.5-flash-8b"),
]


def _fetch_ollama_models() -> list[ModelEntry]:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    url = f"{base_url.rstrip('/')}/models"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})  # noqa: S310
    with urllib.request.urlopen(req, timeout=1) as resp:  # noqa: S310
        data = json.loads(resp.read())

    if not isinstance(data, dict):
        return []
    items = data.get("data", [])
    if not isinstance(items, list):
        return []

    entries: list[ModelEntry] = []
    for item in items:
        if isinstance(item, dict):
            model_id = item.get("id", "")
            if isinstance(model_id, str) and model_id:
                entries.append(ModelEntry(provider="ollama", model=model_id))
    return entries


def list_models() -> list[ModelEntry]:
    """Returns curated cloud models plus any models installed in the local Ollama instance."""
    models = list(_STATIC_MODELS)
    with contextlib.suppress(urllib.error.URLError, OSError, ValueError):
        models.extend(_fetch_ollama_models())
    return models
