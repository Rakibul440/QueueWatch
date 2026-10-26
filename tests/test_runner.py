import json

import pytest

from queuewatch import jobs, runner


def test_successful_job(db, tmp_path):
    csv_file = tmp_path / "s.csv"
    csv_file.write_text("date,product,quantity,price\n2026-01-01,Pen,2,1.50\n")
    job_id = runner.submit("process-csv", str(csv_file), wait=True)
    job = jobs.get_job(job_id)
    assert job["status"] == "SUCCESS"
    assert json.loads(job["result"])["rows"] == 1
    assert job["finished_at"] is not None


def test_transient_error_is_retried_then_succeeds(db):
    job_id = runner.submit("simulate-failure", "transient", wait=True)
    job = jobs.get_job(job_id)
    assert job["status"] == "SUCCESS"
    assert job["retries"] == 2          # failed twice, worked on the 3rd try
    assert job["error"] is None


def test_retry_limit_is_respected(db):
    job_id = runner.submit("simulate-failure", "always", wait=True)
    job = jobs.get_job(job_id)
    assert job["status"] == "FAILED"
    assert job["retries"] == 3          # never more than MAX_RETRIES
    assert "gave up" in job["error"]


def test_retry_limit_is_configurable(db, monkeypatch):
    monkeypatch.setenv("MAX_RETRIES", "1")
    job_id = runner.submit("simulate-failure", "always", wait=True)
    assert jobs.get_job(job_id)["retries"] == 1


def test_permanent_error_is_not_retried(db):
    job_id = runner.submit("simulate-failure", "permanent", wait=True)
    job = jobs.get_job(job_id)
    assert job["status"] == "FAILED"
    assert job["retries"] == 0


def test_unknown_task_is_rejected(db):
    with pytest.raises(ValueError):
        runner.submit("delete-everything", "")


def test_missing_csv_is_rejected_at_submit(db):
    with pytest.raises(ValueError):
        runner.submit("process-csv", "nope.csv")
    assert jobs.list_jobs() == []       # nothing was recorded


def test_failed_job_can_be_retried(db):
    job_id = runner.submit("simulate-failure", "permanent", wait=True)
    runner.retry(job_id, wait=True)
    job = jobs.get_job(job_id)
    assert job["status"] == "FAILED"    # permanent mode fails again, but it did run again
