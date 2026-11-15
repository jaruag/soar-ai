"""Persistence layer: stores scan results in a small SQLite database.
Powers the scan history (each scan is saved and can be reopened).
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/soar.db")


def _connect() -> sqlite3.Connection:
    """Open a connection to the SQLite database, creating the folder if needed."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db() -> None:
    """Create the scans table if it does not exist yet."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ecosystem  TEXT NOT NULL,
                package    TEXT NOT NULL,
                version    TEXT NOT NULL,
                findings   TEXT NOT NULL,
                scanned_at TEXT NOT NULL
            )
        """)


def save_scan(ecosystem: str, package: str, version: str, findings: list) -> None:
    """Store a scan result in the history."""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO scans (ecosystem, package, version, findings, scanned_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                ecosystem,
                package,
                version,
                json.dumps(findings),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def get_history(limit: int = 50) -> list[dict]:
    """Return recent scans, newest first, each with a short verdict summary."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, ecosystem, package, version, findings, scanned_at "
            "FROM scans ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

    history = []
    for row in rows:
        findings = json.loads(row["findings"])

        counts = {"critical": 0, "review": 0, "likely_noise": 0}
        for finding in findings:
            counts[finding["verdict"]] = counts.get(finding["verdict"], 0) + 1

        history.append({
            "id": row["id"],
            "ecosystem": row["ecosystem"],
            "package": row["package"],
            "version": row["version"],
            "scanned_at": row["scanned_at"],
            "counts": counts,
            "total": len(findings),
        })

    return history


def get_scan_by_id(scan_id: int) -> dict | None:
    """Return a single stored scan with its full findings, or None if not found."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT ecosystem, package, version, findings FROM scans WHERE id=?",
            (scan_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "ecosystem": row["ecosystem"],
        "package": row["package"],
        "version": row["version"],
        "findings": json.loads(row["findings"]),
    }