import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from .models import LlmCall

_DEFAULT_DB = Path(__file__).parent.parent.parent / "data" / "llm_calls.db"


class LlmCallRepository:
    def __init__(self, db_path: Path = _DEFAULT_DB) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_calls (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at  TEXT    NOT NULL,
                    provider    TEXT    NOT NULL,
                    model       TEXT    NOT NULL,
                    input_tokens  INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cost        REAL    NOT NULL,
                    latency     REAL    NOT NULL,
                    prompt      TEXT    NOT NULL,
                    answer      TEXT    NOT NULL,
                    max_tokens  INTEGER,
                    temperature REAL,
                    top_p       REAL,
                    top_k       INTEGER
                )
            """)

    def save(self, call: LlmCall) -> LlmCall:
        created_at = datetime.now(tz=UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO llm_calls
                    (created_at, provider, model, input_tokens, output_tokens,
                     cost, latency, prompt, answer, max_tokens, temperature, top_p, top_k)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    call.provider,
                    call.model,
                    call.input_tokens,
                    call.output_tokens,
                    call.cost,
                    call.latency,
                    call.prompt,
                    call.answer,
                    call.max_tokens,
                    call.temperature,
                    call.top_p,
                    call.top_k,
                ),
            )
            call.id = cast("int", cursor.lastrowid)
            call.created_at = datetime.fromisoformat(created_at)
            return call

    def get(self, call_id: int) -> LlmCall | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM llm_calls WHERE id = ?", (call_id,)).fetchone()
        return _row_to_llm_call(row) if row is not None else None

    def list_all(self, limit: int = 100, offset: int = 0) -> list[LlmCall]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM llm_calls ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [_row_to_llm_call(r) for r in rows]


def _row_to_llm_call(row: sqlite3.Row) -> LlmCall:
    return LlmCall(
        id=cast("int", row["id"]),
        created_at=datetime.fromisoformat(cast("str", row["created_at"])),
        provider=cast("str", row["provider"]),
        model=cast("str", row["model"]),
        input_tokens=cast("int", row["input_tokens"]),
        output_tokens=cast("int", row["output_tokens"]),
        cost=cast("float", row["cost"]),
        latency=cast("float", row["latency"]),
        prompt=cast("str", row["prompt"]),
        answer=cast("str", row["answer"]),
        max_tokens=cast("int | None", row["max_tokens"]),
        temperature=cast("float | None", row["temperature"]),
        top_p=cast("float | None", row["top_p"]),
        top_k=cast("int | None", row["top_k"]),
    )
