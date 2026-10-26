import uuid
from datetime import datetime

from queuewatch import database

# The one status model used by the database, the runner and the CLI.
STATUSES = ["QUEUED", "RUNNING", "RETRYING", "SUCCESS", "FAILED"]

_UPDATABLE = {"status", "retries", "result", "error", "started_at", "finished_at"}


def now():
    return datetime.now().isoformat(timespec="seconds")


def create_job(task, input_value=""):
    job_id = uuid.uuid4().hex[:6]
    database.execute(
        "INSERT INTO jobs (id, task, input, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (job_id, task, input_value, "QUEUED", now()),
    )
    return job_id


def get_job(job_id):
    rows = database.query("SELECT * FROM jobs WHERE id = ?", (job_id,))
    return rows[0] if rows else None


def list_jobs(limit=10):
    return database.query("SELECT * FROM jobs ORDER BY rowid DESC LIMIT ?", (limit,))


def update_job(job_id, **fields):
    unknown = set(fields) - _UPDATABLE
    if unknown:
        raise ValueError(f"Cannot update column(s): {', '.join(sorted(unknown))}")
    assignments = ", ".join(f"{column} = ?" for column in fields)
    database.execute(
        f"UPDATE jobs SET {assignments} WHERE id = ?",
        (*fields.values(), job_id),
    )


def stats():
    rows = database.query("SELECT status, COUNT(*) AS count FROM jobs GROUP BY status")
    counts = {status: 0 for status in STATUSES}
    for row in rows:
        counts[row["status"]] = row["count"]
    return counts
