import sqlite3

from queuewatch import config

CREATE_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS jobs (
    id          TEXT PRIMARY KEY,
    task        TEXT NOT NULL,
    input       TEXT,
    status      TEXT NOT NULL,
    retries     INTEGER NOT NULL DEFAULT 0,
    result      TEXT,
    error       TEXT,
    created_at  TEXT NOT NULL,
    started_at  TEXT,
    finished_at TEXT
)
"""


def _connect():
    conn = sqlite3.connect(config.database_path())
    conn.row_factory = sqlite3.Row  # lets us read columns by name
    return conn


def init_db():
    execute(CREATE_JOBS_TABLE)


def execute(sql, params=()):
    conn = _connect()
    try:
        with conn:  # commits on success, rolls back on error
            conn.execute(sql, params)
    finally:
        conn.close()


def query(sql, params=()):
    conn = _connect()
    try:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()
