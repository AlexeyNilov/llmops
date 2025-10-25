import sqlite3
import json


class KeyNotFoundInDB(Exception):
    pass


def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            key  TEXT UNIQUE NOT NULL,
            data JSON NOT NULL
        )
    """
    )
    conn.commit()
    return conn


def upsert(conn, key: str, data: dict):
    """Insert or update a JSON document by key."""
    conn.execute(
        """
        INSERT INTO issues (key, data)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET
            data=excluded.data
    """,
        (key, json.dumps(data)),
    )
    conn.commit()


def fetch(conn, key: str) -> dict:
    cursor = conn.execute("SELECT data FROM issues WHERE key = ?", (key,))
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    raise KeyNotFoundInDB


def fetch_all(conn):
    """Yield all items as (id, key, data_dict)."""
    cursor = conn.execute("SELECT id, key, data FROM issues ORDER BY key")
    for row in cursor:
        yield row[0], row[1], json.loads(row[2])
