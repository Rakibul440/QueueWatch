import pytest

from queuewatch import jobs


def test_create_and_get_job(db):
    job_id = jobs.create_job("process_csv", "examples/sales.csv")
    job = jobs.get_job(job_id)
    assert job["task"] == "process_csv"
    assert job["status"] == "QUEUED"
    assert job["retries"] == 0


def test_unknown_job_returns_none(db):
    assert jobs.get_job("nope00") is None


def test_list_jobs_newest_first(db):
    first = jobs.create_job("process_csv", "a.csv")
    second = jobs.create_job("generate_report", "")
    ids = [job["id"] for job in jobs.list_jobs()]
    assert ids == [second, first]


def test_stats_counts_each_status(db):
    a = jobs.create_job("simulate_failure", "")
    b = jobs.create_job("simulate_failure", "")
    jobs.create_job("simulate_failure", "")
    jobs.update_job(a, status="SUCCESS")
    jobs.update_job(b, status="FAILED")
    counts = jobs.stats()
    assert counts["SUCCESS"] == 1
    assert counts["FAILED"] == 1
    assert counts["QUEUED"] == 1
    assert counts["RUNNING"] == 0


def test_update_rejects_unknown_column(db):
    job_id = jobs.create_job("simulate_failure", "")
    with pytest.raises(ValueError):
        jobs.update_job(job_id, evil="x")
