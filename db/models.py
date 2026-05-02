from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("securevista.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS sms_scans (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    risk_score REAL NOT NULL,
    risk_label TEXT NOT NULL,
    fraud_type TEXT,
    verdict TEXT NOT NULL,
    signals_found TEXT,
    sender_id TEXT,
    action TEXT DEFAULT 'NONE',
    evidence_id TEXT
);

CREATE TABLE IF NOT EXISTS call_sessions (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_sec INTEGER DEFAULT 0,
    peak_risk_score REAL DEFAULT 0,
    otp_count INTEGER DEFAULT 0,
    verdict TEXT DEFAULT 'SAFE',
    auto_cut INTEGER DEFAULT 0,
    transcript_excerpt TEXT,
    evidence_id TEXT
);

CREATE TABLE IF NOT EXISTS evidence_records (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    source TEXT NOT NULL,
    risk_score REAL NOT NULL,
    verdict TEXT NOT NULL,
    raw_text TEXT,
    sha256_hash TEXT NOT NULL,
    pdf_path TEXT,
    incident_id TEXT REFERENCES incidents(id)
);

CREATE TABLE IF NOT EXISTS trusted_contacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    upi_id TEXT,
    email TEXT,
    added_at TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    risk_tier TEXT NOT NULL,
    risk_score REAL NOT NULL,
    zone_id TEXT,
    subject_id TEXT,
    event_json TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    blockchain_tx_hash TEXT,
    polygonscan_url TEXT,
    resolution_status TEXT DEFAULT 'OPEN'
);

CREATE TABLE IF NOT EXISTS upi_transactions (
    txn_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    payer_vpa TEXT,
    payee_vpa TEXT,
    amount_inr REAL,
    txn_type TEXT,
    fraud_score REAL,
    fraud_flags TEXT,
    blocked INTEGER DEFAULT 0,
    incident_id TEXT REFERENCES incidents(id)
);

CREATE TABLE IF NOT EXISTS digital_fraud_events (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    channel TEXT,
    sender_id TEXT,
    fraud_type TEXT,
    fraud_score REAL,
    extracted_urls TEXT,
    guidance_text TEXT,
    incident_id TEXT REFERENCES incidents(id)
);

CREATE TABLE IF NOT EXISTS physical_events (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    subject_id TEXT,
    zone_id TEXT,
    event_type TEXT,
    confidence REAL,
    dwell_seconds INTEGER,
    pose_label TEXT,
    night_mode INTEGER,
    frame_snapshot_path TEXT,
    sha256_hash TEXT
);

CREATE TABLE IF NOT EXISTS correlation_events (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    physical_event_id TEXT,
    digital_event_id TEXT,
    correlation_type TEXT,
    composite_score REAL,
    actions_taken TEXT,
    incident_id TEXT REFERENCES incidents(id)
);

CREATE TABLE IF NOT EXISTS sos_events (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    triggered_by TEXT,
    location_zone TEXT,
    police_notified INTEGER DEFAULT 0,
    incident_id TEXT REFERENCES incidents(id)
);
"""


def connect(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
