from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg


PASSWORD_FILE = Path(os.getenv(
    "STANLEY_HEALTH_DB_PASSWORD_FILE",
    "/home/guosq/.openclaw/.secrets/stanley_health_postgres_password.key",
))


def connect():
    return psycopg.connect(
        host=os.getenv("STANLEY_HEALTH_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("STANLEY_HEALTH_DB_PORT", "5432")),
        dbname=os.getenv("STANLEY_HEALTH_DB_NAME", "stanley_health"),
        user=os.getenv("STANLEY_HEALTH_DB_USER", "stanley_health"),
        password=PASSWORD_FILE.read_text(encoding="utf-8").strip(),
    )


def list_runs() -> list[dict]:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT payload FROM runs ORDER BY run_date, start_time")
        return [row[0] for row in cursor.fetchall()]


def save_run(run: dict) -> None:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO runs (run_date, start_time, distance_km, duration, payload, updated_at)
            VALUES (%s, %s, %s, %s::interval, %s::jsonb, now())
            ON CONFLICT (run_date, start_time) DO UPDATE
            SET distance_km = EXCLUDED.distance_km,
                duration = EXCLUDED.duration,
                payload = EXCLUDED.payload,
                updated_at = now()
            """,
            (run["date"], run["start_time"], run["distance_km"], run["duration"], json.dumps(run, ensure_ascii=False)),
        )
