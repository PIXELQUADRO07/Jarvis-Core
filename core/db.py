"""
core/db.py — Persistenza conversazioni su SQLite
Salva ogni messaggio con timestamp, sessione, modello, token usage.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from logger import debug, error


class ConversationDB:
    """Database SQLite per la storia completa delle conversazioni."""

    def __init__(self, db_path: str = "db/jarvis.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                session       TEXT    NOT NULL DEFAULT 'default',
                role          TEXT    NOT NULL,
                content       TEXT    NOT NULL,
                model         TEXT,
                prompt_tokens INTEGER DEFAULT 0,
                reply_tokens  INTEGER DEFAULT 0,
                language      TEXT    DEFAULT 'it',
                created_at    TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_session ON messages(session);
            CREATE INDEX IF NOT EXISTS idx_created ON messages(created_at);

            CREATE TABLE IF NOT EXISTS sessions_meta (
                name       TEXT PRIMARY KEY,
                created_at TEXT,
                updated_at TEXT,
                msg_count  INTEGER DEFAULT 0,
                model      TEXT
            );
            """)
        debug("DB schema initialized")

    # ── Messaggi ──────────────────────────────────────────────────────────

    def save_message(
        self,
        session: str,
        role: str,
        content: str,
        model: str = "",
        prompt_tokens: int = 0,
        reply_tokens: int = 0,
        language: str = "it",
    ) -> int:
        now = datetime.now().isoformat()
        with self._conn() as c:
            cur = c.execute(
                """INSERT INTO messages
                   (session, role, content, model, prompt_tokens, reply_tokens, language, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (session, role, content, model, prompt_tokens, reply_tokens, language, now),
            )
            msg_id = cur.lastrowid
            c.execute(
                """INSERT INTO sessions_meta (name, created_at, updated_at, msg_count, model)
                   VALUES (?, ?, ?, 1, ?)
                   ON CONFLICT(name) DO UPDATE SET
                       updated_at = excluded.updated_at,
                       msg_count  = msg_count + 1,
                       model      = excluded.model""",
                (session, now, now, model),
            )
        debug(f"DB saved msg id={msg_id} session={session} role={role}")
        return msg_id

    def load_session(self, session: str, limit: int = 100) -> List[Dict]:
        with self._conn() as c:
            rows = c.execute(
                """SELECT role, content FROM messages
                   WHERE session = ?
                   ORDER BY id DESC LIMIT ?""",
                (session, limit),
            ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def search(self, query: str, session: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Ricerca full-text nelle conversazioni."""
        with self._conn() as c:
            if session:
                rows = c.execute(
                    """SELECT id, session, role, content, created_at FROM messages
                       WHERE session = ? AND content LIKE ? ORDER BY id DESC LIMIT ?""",
                    (session, f"%{query}%", limit),
                ).fetchall()
            else:
                rows = c.execute(
                    """SELECT id, session, role, content, created_at FROM messages
                       WHERE content LIKE ? ORDER BY id DESC LIMIT ?""",
                    (f"%{query}%", limit),
                ).fetchall()
        return [dict(r) for r in rows]

    def export_session_markdown(self, session: str) -> str:
        """Esporta una sessione in Markdown."""
        msgs = self.load_session(session, limit=10000)
        if not msgs:
            return ""
        lines = [f"# Conversazione JARVIS — sessione: {session}\n",
                 f"**Esportato:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n---\n"]
        for m in msgs:
            label = "👤 **Tu**" if m["role"] == "user" else "🤖 **JARVIS**"
            lines.append(f"### {label}\n\n{m['content']}\n\n")
        return "".join(lines)

    def cleanup_old_messages(self, days: int = 30) -> int:
        """Elimina messaggi più vecchi di `days` giorni."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        with self._conn() as c:
            cur = c.execute("DELETE FROM messages WHERE created_at < ?", (cutoff,))
            deleted = cur.rowcount
        debug(f"DB cleanup: deleted {deleted} old messages (>{days} days)")
        return deleted

    def get_stats(self, session: Optional[str] = None) -> Dict:
        with self._conn() as c:
            if session:
                row = c.execute(
                    "SELECT COUNT(*) n, SUM(prompt_tokens+reply_tokens) t FROM messages WHERE session=?",
                    (session,),
                ).fetchone()
            else:
                row = c.execute(
                    "SELECT COUNT(*) n, SUM(prompt_tokens+reply_tokens) t FROM messages"
                ).fetchone()
            sessions = c.execute("SELECT COUNT(*) n FROM sessions_meta").fetchone()["n"]
        return {
            "messages": row["n"] or 0,
            "total_tokens": row["t"] or 0,
            "sessions": sessions,
        }

    def list_sessions(self) -> List[Dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT name, created_at, updated_at, msg_count, model FROM sessions_meta ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


# ── Singleton ───────────────────────────────────────────────────────────────
_db: Optional[ConversationDB] = None


def get_db() -> ConversationDB:
    global _db
    if _db is None:
        from config import get_config
        _db = ConversationDB(get_config().db_file)
    return _db
