"""SQLite storage helpers for MCP server state."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, Optional


@dataclass
class AgentRecord:
    agent_id: str
    name: str
    voice_id: str
    prompt: str
    phone_number: Optional[str]
    created_at: datetime


@dataclass
class TranscriptRecord:
    call_id: str
    transcript: str
    collected_at: datetime


class Storage:
    """Lightweight SQLite wrapper for persisting MCP artifacts."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._initialize()

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    voice_id TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    phone_number TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transcripts (
                    call_id TEXT PRIMARY KEY,
                    transcript TEXT NOT NULL,
                    collected_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save_agent(self, record: AgentRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agents(agent_id, name, voice_id, prompt, phone_number, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.agent_id,
                    record.name,
                    record.voice_id,
                    record.prompt,
                    record.phone_number,
                    record.created_at.isoformat(),
                ),
            )
            conn.commit()

    def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT agent_id, name, voice_id, prompt, phone_number, created_at FROM agents WHERE agent_id=?",
                (agent_id,),
            ).fetchone()
            if not row:
                return None
            return AgentRecord(
                agent_id=row["agent_id"],
                name=row["name"],
                voice_id=row["voice_id"],
                prompt=row["prompt"],
                phone_number=row["phone_number"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def save_transcript(self, record: TranscriptRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO transcripts(call_id, transcript, collected_at)
                VALUES (?, ?, ?)
                """,
                (record.call_id, record.transcript, record.collected_at.isoformat()),
            )
            conn.commit()

    def get_transcript(self, call_id: str) -> Optional[TranscriptRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT call_id, transcript, collected_at FROM transcripts WHERE call_id=?",
                (call_id,),
            ).fetchone()
            if not row:
                return None
            return TranscriptRecord(
                call_id=row["call_id"],
                transcript=row["transcript"],
                collected_at=datetime.fromisoformat(row["collected_at"]),
            )

    def upsert_transcript(self, call_id: str, transcript: str) -> TranscriptRecord:
        record = TranscriptRecord(call_id=call_id, transcript=transcript, collected_at=datetime.utcnow())
        self.save_transcript(record)
        return record
