from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    reply: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float


class CallLLMFn(ABC):
    @abstractmethod
    def __call__(
        self,
        model: str,
        input_message: str,
        max_output_tokens: int,
        *,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
    ) -> LLMResponse: ...
