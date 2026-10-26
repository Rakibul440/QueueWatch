
import json
import subprocess
import sys
import time
from pathlib import Path

from queuewatch import config, jobs
from queuewatch.tasks import TASKS, TransientError


def run_job(job_id):
    job = jobs.get_job(job_id)
    if job is None:
        return
    task = TASKS[job["task"]]

    jobs.update_job(
        job_id, status="RUNNING", started_at=jobs.now(),
        finished_at=None, retries=0, error=None, result=None,
    )

    attempt = 0
    while True:
        attempt += 1
        try:
            result = task(job["input"], attempt)
        except TransientError as err:
            retries_used = attempt - 1
            if retries_used >= config.max_retries():
                jobs.update_job(
                    job_id, status="FAILED", finished_at=jobs.now(),
                    error=f"{err} (gave up after {retries_used} retries)",
                )
                return
            # Retry later, waiting longer each time (exponential backoff).
            jobs.update_job(job_id, status="RETRYING", retries=attempt, error=str(err))
            time.sleep(config.retry_delay() * 2 ** retries_used)
            jobs.update_job(job_id, status="RUNNING")
        except Exception as err:
            # Anything else is treated as permanent: no retry.
            jobs.update_job(
                job_id, status="FAILED", finished_at=jobs.now(),
                error=f"{type(err).__name__}: {err}",
            )
            return
        else:
            jobs.update_job(
                job_id, status="SUCCESS", finished_at=jobs.now(),
                result=json.dumps(result), error=None,
            )
            return


def start_background(job_id):
    subprocess.Popen(
        [sys.executable, "-m", "queuewatch.runner", job_id],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _launch(job_id, wait):
    if wait:
        run_job(job_id)  # run here and block until done
    else:
        start_background(job_id)


def submit(task_name, input_value="", wait=False):
    name = task_name.replace("-", "_")  # allow process-csv as well as process_csv
    if name not in TASKS:
        valid = ", ".join(t.replace("_", "-") for t in TASKS)
        raise ValueError(f"Unknown task '{task_name}'. Choose one of: {valid}")
    if name == "process_csv" and not Path(input_value).is_file():
        raise ValueError(f"CSV file not found: '{input_value}'. Use --file path/to/file.csv")

    job_id = jobs.create_job(name, input_value)
    _launch(job_id, wait)
    return job_id


def retry(job_id, wait=False):
    jobs.update_job(
        job_id, status="QUEUED", retries=0, error=None, result=None, finished_at=None
    )
    _launch(job_id, wait)


if __name__ == "__main__":
    run_job(sys.argv[1])
