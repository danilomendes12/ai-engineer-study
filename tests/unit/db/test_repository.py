from pathlib import Path

import pytest

from db import LlmCall, LlmCallRepository


def _call(**kwargs: object) -> LlmCall:
    defaults: dict[str, object] = {
        "provider": "anthropic",
        "model": "claude-haiku-4-5",
        "input_tokens": 100,
        "output_tokens": 50,
        "cost": 0.001,
        "latency": 1.0,
        "prompt": "hello",
        "answer": "world",
    }
    defaults.update(kwargs)
    return LlmCall(**defaults)  # type: ignore[arg-type]


@pytest.fixture
def repo(tmp_path: Path) -> LlmCallRepository:
    return LlmCallRepository(tmp_path / "test.db")


# ── save / get round-trip ──────────────────────────────────────────────────────


def test_save_assigns_id_and_created_at(repo: LlmCallRepository) -> None:
    saved = repo.save(_call())
    assert saved.id is not None
    assert saved.created_at is not None


def test_get_returns_saved_record(repo: LlmCallRepository) -> None:
    saved = repo.save(_call(provider="openai", model="gpt-4o-mini"))
    retrieved = repo.get(saved.id)  # type: ignore[arg-type]
    assert retrieved is not None
    assert retrieved.provider == "openai"
    assert retrieved.model == "gpt-4o-mini"


def test_get_unknown_id_returns_none(repo: LlmCallRepository) -> None:
    assert repo.get(99999) is None


# ── system_prompt persistence ──────────────────────────────────────────────────


def test_system_prompt_is_persisted(repo: LlmCallRepository) -> None:
    saved = repo.save(_call(system_prompt="You are a helpful assistant."))
    retrieved = repo.get(saved.id)  # type: ignore[arg-type]
    assert retrieved is not None
    assert retrieved.system_prompt == "You are a helpful assistant."


def test_system_prompt_defaults_to_null(repo: LlmCallRepository) -> None:
    saved = repo.save(_call())
    retrieved = repo.get(saved.id)  # type: ignore[arg-type]
    assert retrieved is not None
    assert retrieved.system_prompt is None


def test_system_prompt_visible_in_list_all(repo: LlmCallRepository) -> None:
    repo.save(_call(system_prompt="Prompt A"))
    repo.save(_call(system_prompt=None))
    records = repo.list_all()
    prompts = {r.system_prompt for r in records}
    assert "Prompt A" in prompts
    assert None in prompts


# ── list_all filters ───────────────────────────────────────────────────────────


def test_list_all_model_filter(repo: LlmCallRepository) -> None:
    repo.save(_call(model="model-a"))
    repo.save(_call(model="model-b"))
    repo.save(_call(model="model-b"))
    results = repo.list_all(model="model-b")
    assert len(results) == 2
    assert all(r.model == "model-b" for r in results)


def test_list_all_limit_and_offset(repo: LlmCallRepository) -> None:
    for _ in range(5):
        repo.save(_call())
    assert len(repo.list_all(limit=3)) == 3
    assert len(repo.list_all(limit=3, offset=3)) == 2
