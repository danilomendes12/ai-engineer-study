import sqlite3
from pathlib import Path

import pytest

from db import LlmCall, LlmCallAnalytics, LlmCallRepository


def _call(**kwargs: object) -> LlmCall:
    defaults: dict[str, object] = {
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
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
def db(tmp_path: Path) -> tuple[LlmCallRepository, LlmCallAnalytics]:
    path = tmp_path / "test.db"
    return LlmCallRepository(path), LlmCallAnalytics(path)


# ── cost_per_call ──────────────────────────────────────────────────────────────


def test_cost_per_call_empty_db(db: tuple[LlmCallRepository, LlmCallAnalytics]) -> None:
    _, analytics = db
    stats = analytics.cost_per_call()
    assert stats.count == 0
    assert stats.total == 0.0
    assert stats.avg == 0.0


def test_cost_per_call_aggregates_all(db: tuple[LlmCallRepository, LlmCallAnalytics]) -> None:
    repo, analytics = db
    repo.save(_call(cost=0.01))
    repo.save(_call(cost=0.03))

    stats = analytics.cost_per_call()
    assert stats.count == 2
    assert stats.total == pytest.approx(0.04)
    assert stats.avg == pytest.approx(0.02)
    assert stats.min == pytest.approx(0.01)
    assert stats.max == pytest.approx(0.03)
    assert stats.model is None


def test_cost_per_call_filters_by_model(db: tuple[LlmCallRepository, LlmCallAnalytics]) -> None:
    repo, analytics = db
    repo.save(_call(model="model-a", cost=0.10))
    repo.save(_call(model="model-b", cost=0.20))
    repo.save(_call(model="model-b", cost=0.30))

    stats = analytics.cost_per_call(model="model-b")
    assert stats.count == 2
    assert stats.total == pytest.approx(0.50)
    assert stats.model == "model-b"


def test_cost_per_call_unknown_model_returns_zeros(
    db: tuple[LlmCallRepository, LlmCallAnalytics],
) -> None:
    repo, analytics = db
    repo.save(_call(cost=0.01))
    stats = analytics.cost_per_call(model="nonexistent")
    assert stats.count == 0
    assert stats.total == 0.0


# ── latency_percentiles ────────────────────────────────────────────────────────


def test_latency_percentiles_empty_db(db: tuple[LlmCallRepository, LlmCallAnalytics]) -> None:
    _, analytics = db
    assert analytics.latency_percentiles() is None


def test_latency_percentiles_single_record(
    db: tuple[LlmCallRepository, LlmCallAnalytics],
) -> None:
    repo, analytics = db
    repo.save(_call(latency=2.5))

    result = analytics.latency_percentiles()
    assert result is not None
    assert result.p50 == pytest.approx(2.5)
    assert result.p90 == pytest.approx(2.5)
    assert result.p99 == pytest.approx(2.5)


def test_latency_percentiles_large_dataset(
    db: tuple[LlmCallRepository, LlmCallAnalytics],
) -> None:
    repo, analytics = db
    for i in range(1, 101):
        repo.save(_call(latency=float(i)))

    result = analytics.latency_percentiles()
    assert result is not None
    assert result.p50 == pytest.approx(50.5)
    assert result.p90 == pytest.approx(90.9)
    assert result.p99 == pytest.approx(99.99)
    assert result.model is None


def test_latency_percentiles_filters_by_model(
    db: tuple[LlmCallRepository, LlmCallAnalytics],
) -> None:
    repo, analytics = db
    for i in range(1, 101):
        repo.save(_call(model="slow-model", latency=float(i) * 10))
    for i in range(1, 101):
        repo.save(_call(model="fast-model", latency=float(i)))

    result = analytics.latency_percentiles(model="fast-model")
    assert result is not None
    assert result.p99 == pytest.approx(99.99)
    assert result.model == "fast-model"


# ── ttft_percentiles ───────────────────────────────────────────────────────────


def test_ttft_percentiles_empty_db(db: tuple[LlmCallRepository, LlmCallAnalytics]) -> None:
    _, analytics = db
    assert analytics.ttft_percentiles() is None


def test_ttft_percentiles_all_null(db: tuple[LlmCallRepository, LlmCallAnalytics]) -> None:
    repo, analytics = db
    repo.save(_call(ttft_ms=None))
    repo.save(_call(ttft_ms=None))
    assert analytics.ttft_percentiles() is None


def test_ttft_percentiles_excludes_nulls(
    db: tuple[LlmCallRepository, LlmCallAnalytics],
) -> None:
    repo, analytics = db
    repo.save(_call(ttft_ms=None))
    repo.save(_call(ttft_ms=100.0))
    repo.save(_call(ttft_ms=200.0))
    repo.save(_call(ttft_ms=None))

    # n=2 → small-dataset path; index n//2=1 → the larger value
    result = analytics.ttft_percentiles()
    assert result is not None
    assert result.p50 == pytest.approx(200.0)
    assert result.p90 == pytest.approx(200.0)
    assert result.p99 == pytest.approx(200.0)


def test_ttft_percentiles_large_dataset(
    db: tuple[LlmCallRepository, LlmCallAnalytics],
) -> None:
    repo, analytics = db
    for i in range(1, 101):
        repo.save(_call(ttft_ms=float(i)))

    result = analytics.ttft_percentiles()
    assert result is not None
    assert result.p50 == pytest.approx(50.5)
    assert result.p90 == pytest.approx(90.9)
    assert result.p99 == pytest.approx(99.99)


def test_ttft_percentiles_filters_by_model(
    db: tuple[LlmCallRepository, LlmCallAnalytics],
) -> None:
    repo, analytics = db
    for i in range(1, 101):
        repo.save(_call(model="streaming-model", ttft_ms=float(i)))
    repo.save(_call(model="other-model", ttft_ms=999.0))

    result = analytics.ttft_percentiles(model="streaming-model")
    assert result is not None
    assert result.p99 == pytest.approx(99.99)
    assert result.model == "streaming-model"


# ── daily_spend ────────────────────────────────────────────────────────────────


def test_daily_spend_empty_db(db: tuple[LlmCallRepository, LlmCallAnalytics]) -> None:
    _, analytics = db
    assert analytics.daily_spend() == []


def test_daily_spend_groups_todays_records(
    db: tuple[LlmCallRepository, LlmCallAnalytics],
) -> None:
    repo, analytics = db
    repo.save(_call(cost=0.01))
    repo.save(_call(cost=0.02))
    repo.save(_call(cost=0.07))

    results = analytics.daily_spend(days=1)
    assert len(results) == 1
    assert results[0].count == 3
    assert results[0].total == pytest.approx(0.10)


def test_daily_spend_multi_day(db: tuple[LlmCallRepository, LlmCallAnalytics]) -> None:
    repo, analytics = db
    path = repo._db_path  # noqa: SLF001
    rows = [
        ("2026-06-08T10:00:00+00:00", 0.05),
        ("2026-06-09T10:00:00+00:00", 0.10),
        ("2026-06-09T11:00:00+00:00", 0.20),
    ]
    conn = sqlite3.connect(path)
    conn.executemany(
        """
        INSERT INTO llm_calls
            (created_at, provider, model, input_tokens, output_tokens,
             cost, latency, prompt, answer)
        VALUES (?, 'anthropic', 'claude-sonnet-4-6', 10, 5, ?, 1.0, 'p', 'a')
        """,
        rows,
    )
    conn.commit()
    conn.close()

    results = analytics.daily_spend(days=30)
    by_date = {r.date: r for r in results}

    assert by_date["2026-06-08"].total == pytest.approx(0.05)
    assert by_date["2026-06-08"].count == 1
    assert by_date["2026-06-09"].total == pytest.approx(0.30)
    assert by_date["2026-06-09"].count == 2
