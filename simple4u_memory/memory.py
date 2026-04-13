"""Memory management — SQLite + FTS5 for persistent storage and semantic search."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Memory:
    id: int
    text: str
    category: str
    created_at: str
    metadata: dict


class MemoryStore:
    """SQLite-backed memory with FTS5 for semantic-ish search."""

    def __init__(self, home: Path):
        self.home = home
        self.home.mkdir(parents=True, exist_ok=True)
        self.db_path = self.home / "memory.db"
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                created_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                text,
                category,
                content='memories',
                content_rowid='id'
            );

            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, text, category)
                VALUES (new.id, new.text, new.category);
            END;

            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, text, category)
                VALUES ('delete', old.id, old.text, old.category);
            END;

            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, text, category)
                VALUES ('delete', old.id, old.text, old.category);
                INSERT INTO memories_fts(rowid, text, category)
                VALUES (new.id, new.text, new.category);
            END;

            CREATE TABLE IF NOT EXISTS journals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                session_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()
        conn.close()

    def remember(self, text: str, category: str = "general", metadata: dict | None = None) -> int:
        """Save a fact to memory. Returns the memory id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "INSERT INTO memories (text, category, created_at, metadata) VALUES (?, ?, ?, ?)",
            (
                text,
                category,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(metadata or {}),
            ),
        )
        memory_id = cursor.lastrowid or 0
        conn.commit()
        conn.close()
        return memory_id

    def recall(self, query: str, limit: int = 10, category: str | None = None) -> list[Memory]:
        """Search memories using FTS5."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        if query.strip():
            # Escape FTS5 special chars by wrapping each word as prefix match
            words = [w for w in query.split() if w.strip()]
            fts_query = " OR ".join(f'"{w}"*' for w in words) if words else query

            if category:
                rows = conn.execute(
                    """
                    SELECT m.id, m.text, m.category, m.created_at, m.metadata
                    FROM memories m
                    JOIN memories_fts fts ON m.id = fts.rowid
                    WHERE memories_fts MATCH ? AND m.category = ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, category, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT m.id, m.text, m.category, m.created_at, m.metadata
                    FROM memories m
                    JOIN memories_fts fts ON m.id = fts.rowid
                    WHERE memories_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()
        else:
            # Empty query — return recent memories
            if category:
                rows = conn.execute(
                    "SELECT id, text, category, created_at, metadata FROM memories WHERE category = ? ORDER BY id DESC LIMIT ?",
                    (category, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, text, category, created_at, metadata FROM memories ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()

        conn.close()
        return [
            Memory(
                id=r["id"],
                text=r["text"],
                category=r["category"],
                created_at=r["created_at"],
                metadata=json.loads(r["metadata"] or "{}"),
            )
            for r in rows
        ]

    def list_all(self, category: str | None = None, limit: int = 100) -> list[Memory]:
        return self.recall(query="", category=category, limit=limit)

    def forget(self, memory_id: int) -> bool:
        """Delete a memory by id. Returns True if deleted."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def journal(self, text: str, session_date: str | None = None) -> int:
        """Write an end-of-session journal entry."""
        session_date = session_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "INSERT INTO journals (text, session_date, created_at) VALUES (?, ?, ?)",
            (text, session_date, datetime.now(timezone.utc).isoformat()),
        )
        journal_id = cursor.lastrowid or 0
        conn.commit()
        conn.close()

        # Also write to file for human readability
        journal_dir = self.home / "journals"
        journal_dir.mkdir(exist_ok=True)
        journal_file = journal_dir / f"{session_date}.md"
        with journal_file.open("a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.now(timezone.utc).strftime('%H:%M UTC')}\n\n{text}\n")

        return journal_id

    def recent_journals(self, days: int = 7) -> list[dict]:
        """Return journal entries from last N days."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, text, session_date, created_at
            FROM journals
            WHERE created_at >= datetime('now', ?)
            ORDER BY created_at DESC
            """,
            (f"-{days} days",),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
