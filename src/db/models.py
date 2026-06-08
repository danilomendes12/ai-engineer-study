from dataclasses import dataclass
from datetime import datetime


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
