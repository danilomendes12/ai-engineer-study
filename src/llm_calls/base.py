from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class LLMResponse:
    reply: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    ignored_params: list[str] = field(default_factory=list)


@dataclass
class StreamChunk:
    """WebSocket-compatible streaming chunk. Serialize with dataclasses.asdict()."""

    type: Literal["delta", "done"]
    delta: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: float | None = None
    ttft_ms: float | None = None
    ignored_params: list[str] = field(default_factory=list)


class CallLLMFn(ABC):
    @abstractmethod
    def __call__(
        self,
        model: str,
        input_message: str,
        max_output_tokens: int,
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
    ) -> LLMResponse: ...

    @abstractmethod
    def __stream__(
        self,
        model: str,
        input_message: str,
        max_output_tokens: int,
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
    ) -> Iterator[StreamChunk]: ...
