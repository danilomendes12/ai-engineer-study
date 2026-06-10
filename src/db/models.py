from dataclasses import dataclass
from datetime import datetime


@dataclass
class CostStats:
    count: int
    total: float
    avg: float
    min: float
    max: float
    model: str | None = None


@dataclass
class LatencyPercentiles:
    p50: float
    p90: float
    p99: float
    model: str | None = None


@dataclass
class TtftPercentiles:
    p50: float
    p90: float
    p99: float
    model: str | None = None


@dataclass
class DailySpend:
    date: str
    total: float
    count: int


@dataclass
class LlmCall:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency: float
    prompt: str
    answer: str
    id: int | None = None
    created_at: datetime | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    ttft_ms: float | None = None
    response_status: str | None = None
    error_message: str | None = None
