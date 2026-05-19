# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal learning/study repository for AI engineering. Code here consists of self-contained experiments and exercises against LLM provider SDKs (Anthropic, OpenAI) — not a production application. Expect throwaway scripts and small modules over a cohesive architecture.

## Environment & commands

This project uses **uv** as the package manager and Python **3.14**.

- Install/sync dependencies: `uv sync`
- Run a script: `uv run python <path>` (e.g. `uv run python main.py`)
- Lint: `uv run ruff check` (add `--fix` to autofix)
- Format: `uv run ruff format`
- Type check: `uv run mypy <path>`
- Run all pre-commit hooks manually: `uv run pre-commit run --all-files`
- Install the git hook: `uv run pre-commit install`

There is no test framework configured yet. If adding tests, wire up pytest in `pyproject.toml` first.

## Conventions

- New experiments go under `src/`, grouped into a subdirectory per topic (see `src/hello_world/`). `main.py` at the repo root is a standalone scratch entry point.
- pre-commit runs `ruff check --fix`, `ruff format`, and `mypy` on every commit — code must pass all three.
- API keys are loaded from a gitignored `.env` (use `python-dotenv`). Copy `.env.example` and fill in `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`. Never hardcode keys.
