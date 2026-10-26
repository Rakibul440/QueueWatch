from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

STATUS_STYLES = {
    "QUEUED": "cyan",
    "RUNNING": "blue",
    "RETRYING": "yellow",
    "SUCCESS": "green",
    "FAILED": "red",
}


def _print(message, style):
    # markup=False and highlight=False print the text exactly as given
    # (error messages can contain [brackets] that rich would misread).
    console.print(message, style=style, markup=False, highlight=False)


def success(message):
    _print(f"✔ {message}", "bold green")


def warning(message):
    _print(f"⚠ {message}", "bold yellow")


def error(message):
    _print(f"✖ {message}", "bold red")


def info(message):
    _print(message, "cyan")


def show_job(job):
    """Print one job. Every line gets the colour of its status."""
    style = STATUS_STYLES.get(job["status"], "white")
    lines = [
        ("Job ID", job["id"]),
        ("Task", job["task"]),
        ("Input", job["input"] or "-"),
        ("Status", job["status"]),
        ("Retries", job["retries"]),
        ("Submitted", job["created_at"]),
        ("Started", job["started_at"] or "-"),
        ("Finished", job["finished_at"] or "-"),
    ]
    if job["result"]:
        lines.append(("Result", job["result"]))
    if job["error"]:
        lines.append(("Error", job["error"]))
    for label, value in lines:
        _print(f"{label:<10} {value}", style)


def show_jobs_table(rows):
    """Print a table where each whole row is coloured by status."""
    table = Table(header_style="bold white")
    for column in ["JOB ID", "TASK", "STATUS", "RETRIES", "SUBMITTED"]:
        table.add_column(column)
    for job in rows:
        table.add_row(
            job["id"],
            job["task"],
            job["status"],
            str(job["retries"]),
            job["created_at"],
            style=STATUS_STYLES.get(job["status"], "white"),
        )
    console.print(table)


def show_stats(counts):
    for status, count in counts.items():
        bar = "█" * min(count, 30)
        _print(f"{status:<10} {count:>3}  {bar}", STATUS_STYLES[status])
    _print(f"{'TOTAL':<10} {sum(counts.values()):>3}", "bold white")


def show_explanation(text):
    console.print(
        Panel(Text(text), title="AI explanation (advisory only)", border_style="magenta")
    )
