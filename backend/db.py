"""SQLite connection and one-time schema setup for auth."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Add the auth columns/tables if they don't exist yet. Safe to run every startup."""
    with get_connection() as conn:
        user_cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)")}
        if "email_verified_at" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN email_verified_at TEXT")
            # Accounts that existed before email verification are treated as verified.
            conn.execute("UPDATE users SET email_verified_at = created_at")

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            -- Loading a customer's history is "WHERE user_id = ? ORDER BY id".
            CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id);
            """
        )
