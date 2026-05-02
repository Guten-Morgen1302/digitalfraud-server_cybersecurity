import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("SQLITE_DB_PATH", "shieldguard_calls.db")


def init_db():
    """Initialize SQLite tables on startup."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            started_at TEXT,
            ended_at TEXT,
            total_chunks INTEGER DEFAULT 0,
            final_otp_count INTEGER DEFAULT 0,
            final_verdict TEXT DEFAULT 'Safe'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            chunk_index INTEGER,
            transcript TEXT,
            score REAL,
            status TEXT,
            otp_count INTEGER,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] SQLite initialized.")


def log_session_chunk(
    session_id: str,
    chunk_index: int,
    transcript: str,
    score: float,
    status: str,
    otp_count: int,
    timestamp: str
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert chunk log
    cursor.execute("""
        INSERT INTO call_chunks 
        (session_id, chunk_index, transcript, score, status, otp_count, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, chunk_index, transcript, score, status, otp_count, timestamp))

    # Upsert session record
    cursor.execute("""
        INSERT INTO call_sessions (session_id, started_at, total_chunks, final_otp_count)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            total_chunks = total_chunks + 1,
            final_otp_count = ?
    """, (session_id, timestamp, otp_count, otp_count))

    conn.commit()
    conn.close()


def finalize_session(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE call_sessions SET ended_at = ? WHERE session_id = ?
    """, (datetime.utcnow().isoformat(), session_id))
    conn.commit()
    conn.close()
