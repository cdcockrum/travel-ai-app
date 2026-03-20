import json
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "travel_app.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trips (
                trip_id TEXT PRIMARY KEY,
                trip_data TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_trip(trip_id: str, trip_data: dict[str, Any]) -> None:
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO trips (trip_id, trip_data)
            VALUES (?, ?)
            """,
            (trip_id, json.dumps(trip_data)),
        )
        conn.commit()
    finally:
        conn.close()


def get_trip(trip_id: str) -> dict[str, Any] | None:
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT trip_data FROM trips WHERE trip_id = ?",
            (trip_id,),
        ).fetchone()

        if not row:
            return None

        return json.loads(row["trip_data"])
    finally:
        conn.close()


def list_all_trips() -> list[dict[str, Any]]:
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT trip_data FROM trips ORDER BY rowid DESC"
        ).fetchall()

        return [json.loads(row["trip_data"]) for row in rows]
    finally:
        conn.close()


def delete_trip(trip_id: str) -> bool:
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM trips WHERE trip_id = ?",
            (trip_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()