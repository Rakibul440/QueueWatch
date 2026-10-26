"""The command-line interface. Each function below is one command."""
import typer

from queuewatch import ai_explainer, database, jobs, runner, ui

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def startup():
    """QueueWatch - run background jobs, track them, retry failures, explain errors."""
    database.init_db()  # make sure the table exists before any command runs


def _get_job_or_exit(job_id):
    job = jobs.get_job(job_id)
    if job is None:
        ui.error(f"No job found with ID '{job_id}'. Run 'queuewatch list' to see IDs.")
        raise typer.Exit(code=1)
    return job


@app.command()
def submit(
    task: str = typer.Argument(..., help="process-csv, generate-report or simulate-failure"),
    input_value: str = typer.Option(
        "", "--input", "--file", "-i", help="CSV path, or failure mode for simulate-failure"
    ),
    wait: bool = typer.Option(False, "--wait", "-w", help="Wait for the job to finish"),
):
    """Submit a job and run it in the background."""
    try:
        job_id = runner.submit(task, input_value, wait=wait)
    except ValueError as err:
        ui.error(str(err))
        raise typer.Exit(code=1)

    job = jobs.get_job(job_id)
    if not wait:
        ui.success("Job submitted")
        ui.show_job(job)
        ui.info(f"Check progress with: queuewatch status {job_id}")
    elif job["status"] == "SUCCESS":
        ui.success("Job finished successfully")
        ui.show_job(job)
    else:
        ui.error("Job failed")
        ui.show_job(job)
        ui.info(f"Get help with: queuewatch explain {job_id}")


@app.command()
def status(job_id: str = typer.Argument(..., help="Job ID, e.g. 8f2c1a")):
    """Show the details of one job."""
    ui.show_job(_get_job_or_exit(job_id))


@app.command(name="list")
def list_command(limit: int = typer.Option(10, "--limit", "-n", help="How many jobs to show")):
    """List recent jobs."""
    rows = jobs.list_jobs(limit)
    if not rows:
        ui.warning("No jobs yet. Try: queuewatch submit simulate-failure --wait")
        return
    ui.show_jobs_table(rows)


@app.command()
def stats():
    """Show how many jobs are in each status."""
    ui.show_stats(jobs.stats())


@app.command()
def retry(
    job_id: str = typer.Argument(..., help="ID of a FAILED job"),
    wait: bool = typer.Option(False, "--wait", "-w", help="Wait for the job to finish"),
):
    """Run a failed job again."""
    job = _get_job_or_exit(job_id)
    if job["status"] != "FAILED":
        ui.warning(f"Only FAILED jobs can be retried (this one is {job['status']}).")
        raise typer.Exit(code=1)

    runner.retry(job_id, wait=wait)
    ui.success(f"Job {job_id} queued again")
    ui.show_job(jobs.get_job(job_id))


@app.command()
def explain(job_id: str = typer.Argument(..., help="ID of a FAILED job")):
    """Ask the AI to explain why a job failed (optional feature)."""
    job = _get_job_or_exit(job_id)
    if job["status"] != "FAILED":
        ui.warning(f"Only FAILED jobs can be explained (this one is {job['status']}).")
        raise typer.Exit(code=1)

    ui.info("Asking the AI for an explanation...")
    try:
        text = ai_explainer.explain_failure(job["task"], job["error"])
    except ai_explainer.ExplainError as err:
        ui.warning(str(err))
        raise typer.Exit(code=1)
    ui.show_explanation(text)
