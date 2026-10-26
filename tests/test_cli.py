from typer.testing import CliRunner

from queuewatch.main import app

cli = CliRunner()


def test_submit_wait_success(db, tmp_path):
    csv_file = tmp_path / "s.csv"
    csv_file.write_text("date,product,quantity,price\n2026-01-01,Pen,2,1.50\n")
    result = cli.invoke(app, ["submit", "process-csv", "--file", str(csv_file), "--wait"])
    assert result.exit_code == 0
    assert "SUCCESS" in result.output


def test_submit_failure_shows_failed(db):
    result = cli.invoke(app, ["submit", "simulate-failure", "--input", "permanent", "--wait"])
    assert result.exit_code == 0
    assert "FAILED" in result.output


def test_submit_unknown_task_is_rejected(db):
    result = cli.invoke(app, ["submit", "hack-the-planet"])
    assert result.exit_code == 1
    assert "Unknown task" in result.output


def test_status_unknown_job_is_friendly(db):
    result = cli.invoke(app, ["status", "zzzzzz"])
    assert result.exit_code == 1
    assert "No job found" in result.output


def test_list_when_empty(db):
    result = cli.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No jobs yet" in result.output


def test_list_and_stats_after_a_job(db):
    cli.invoke(app, ["submit", "simulate-failure", "--wait"])
    assert "simulate_failure" in cli.invoke(app, ["list"]).output
    assert "SUCCESS" in cli.invoke(app, ["stats"]).output


def test_retry_only_works_on_failed_jobs(db):
    from queuewatch import jobs
    cli.invoke(app, ["submit", "simulate-failure", "--wait"])   # this one succeeds
    job_id = jobs.list_jobs()[0]["id"]
    result = cli.invoke(app, ["retry", job_id])
    assert result.exit_code == 1
    assert "Only FAILED" in result.output


def test_explain_without_api_key_shows_warning(db):
    cli.invoke(app, ["submit", "simulate-failure", "--input", "permanent", "--wait"])
    from queuewatch import jobs
    job_id = jobs.list_jobs()[0]["id"]
    result = cli.invoke(app, ["explain", job_id])
    assert result.exit_code == 1
    assert "LLM_API_KEY" in result.output
