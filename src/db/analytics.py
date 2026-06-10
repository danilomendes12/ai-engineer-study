import sqlite3
from pathlib import Path
from statistics import quantiles

from .models import CostStats, DailySpend, LatencyPercentiles, TtftPercentiles

_DEFAULT_DB = Path(__file__).parent.parent.parent / "data" / "llm_calls.db"


def _compute_percentiles(values: list[float]) -> tuple[float, float, float]:
    n = len(values)
    _min_for_quantiles = 4
    if n < _min_for_quantiles:
        return values[n // 2], values[-1], values[-1]
    # quantiles(data, n=100) returns 99 cut points; index i → p(i+1)
    cuts = quantiles(values, n=100)
    return cuts[49], cuts[89], cuts[98]


class LlmCallAnalytics:
    def __init__(self, db_path: Path = _DEFAULT_DB) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def cost_per_call(self, model: str | None = None) -> CostStats:
        sql = "SELECT COUNT(*), SUM(cost), AVG(cost), MIN(cost), MAX(cost) FROM llm_calls"
        params: list[str] = []
        if model is not None:
            sql += " WHERE model = ?"
            params.append(model)
        with self._connect() as conn:
            row = conn.execute(sql, params).fetchone()
        return CostStats(
            count=row[0] or 0,
            total=row[1] or 0.0,
            avg=row[2] or 0.0,
            min=row[3] or 0.0,
            max=row[4] or 0.0,
            model=model,
        )

    def latency_percentiles(self, model: str | None = None) -> LatencyPercentiles | None:
        sql = "SELECT latency FROM llm_calls"
        params: list[str] = []
        if model is not None:
            sql += " WHERE model = ?"
            params.append(model)
        sql += " ORDER BY latency"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        if not rows:
            return None
        p50, p90, p99 = _compute_percentiles([float(r[0]) for r in rows])
        return LatencyPercentiles(p50=p50, p90=p90, p99=p99, model=model)

    def ttft_percentiles(self, model: str | None = None) -> TtftPercentiles | None:
        sql = "SELECT ttft_ms FROM llm_calls WHERE ttft_ms IS NOT NULL"
        params: list[str] = []
        if model is not None:
            sql += " AND model = ?"
            params.append(model)
        sql += " ORDER BY ttft_ms"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        if not rows:
            return None
        p50, p90, p99 = _compute_percentiles([float(r[0]) for r in rows])
        return TtftPercentiles(p50=p50, p90=p90, p99=p99, model=model)

    def daily_spend(self, days: int = 30) -> list[DailySpend]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DATE(created_at) AS day, SUM(cost), COUNT(*)
                FROM llm_calls
                WHERE created_at >= DATE('now', ?)
                GROUP BY day
                ORDER BY day DESC
                """,
                (f"-{days} days",),
            ).fetchall()
        return [DailySpend(date=str(r[0]), total=float(r[1]), count=int(r[2])) for r in rows]
