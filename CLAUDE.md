# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal learning/study repository for AI engineering. Code here consists of self-contained experiments and exercises against LLM provider SDKs (Anthropic, OpenAI, Gemini) — not a production application. Expect throwaway scripts and small modules over a cohesive architecture.

## Environment & commands

This project uses **uv** as the package manager and Python **3.12**.

- Install/sync dependencies: `uv sync`
- Run a script: `uv run python <path>` (e.g. `uv run python main.py`)
- Lint: `uv run ruff check` (add `--fix` to autofix)
- Format: `uv run ruff format`
- Type check: `uv run mypy <path>`
- Run all pre-commit hooks manually: `uv run pre-commit run --all-files`
- Install the git hook: `uv run pre-commit install`
- Run tests: `uv run pytest`

## Key modules

### `src/llm_calls/`
Abstract LLM call layer with a unified interface across three providers:
- `base.py` — `CallLLMFn` ABC, `LLMResponse` and `StreamChunk` dataclasses.
- `anthropic_client.py`, `openai_client.py`, `gemini_client.py` — concrete implementations.
- `__init__.py` — exports `call_llm(model, message, max_tokens, provider)` and `stream_llm(...)`. Both functions automatically persist every call to the SQLite repository (see below).

### `src/db/`
Persistence and analytics layer backed by SQLite (`data/llm_calls.db`):
- `models.py` — `LlmCall` dataclass (the persisted record) plus analytics output types (`CostStats`, `LatencyPercentiles`, `TtftPercentiles`, `DailySpend`).
- `repository.py` — `LlmCallRepository`: `save`, `get`, `list_all`.
- `analytics.py` — `LlmCallAnalytics`: `cost_per_call`, `latency_percentiles`, `ttft_percentiles`, `daily_spend`.

### `src/rest/`
API HTTP construída com FastAPI, exposta via uvicorn:
- `schemas.py` — modelos Pydantic de request/response (`CallRequest`, `CallResponse`, `LlmCallSchema`, `StatsResponse` e auxiliares).
- `app.py` — instância FastAPI com as rotas abaixo. Usa `_repo` e `_analytics` como singletons de módulo.

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/calls` | Executa uma chamada LLM e persiste o resultado |
| `GET` | `/calls` | Lista chamadas (`?model=`, `?limit=`, `?offset=`) |
| `GET` | `/calls/{id}` | Retorna um registro específico |
| `GET` | `/stats` | Agregações de custo, latência, TTFT e gasto diário (`?model=`, `?days=`) |

Rodar localmente: `uv run uvicorn rest.app:app --reload`
Documentação interativa: `http://localhost:8000/docs`

### `tests/`
Pytest suite (`uv run pytest`):
- `tests/db/test_analytics.py` — unit tests for every analytics query using an in-memory SQLite fixture.
- `tests/test_providers.py` — integration tests calling real provider APIs (Anthropic, OpenAI, Gemini) for both `call_llm` and `stream_llm`, and verifying persistence. Gemini is marked `xfail` to tolerate quota failures.

## Conventions

- New experiments go under `src/`, grouped into a subdirectory per topic (see `src/hello_world/`). `main.py` at the repo root is a standalone scratch entry point.
- pre-commit runs `ruff check --fix`, `ruff format`, and `mypy` (all in strict mode) on every commit — code must pass all three.
- GitHub Actions CI runs ruff + mypy on every push and PR — see `.github/workflows/ci.yml`.
- API keys are loaded from a gitignored `.env` (use `python-dotenv`). Copy `.env.example` and fill in `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` / `LANGSMITH_API_KEY`. Never hardcode keys.
- For REST routes, annotate return types instead of using `response_model=` (ruff FAST001 flags it as redundant).
- **Anthropic (Claude) is the primary LLM provider**; OpenAI and Gemini are kept for comparison. Default new experiments to the `anthropic` SDK unless the exercise is explicitly cross-provider.
- When adding a new provider, implement `CallLLMFn` in `src/llm_calls/` and register it in `_REGISTRY` in `__init__.py`.
