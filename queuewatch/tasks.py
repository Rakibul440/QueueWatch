import csv
import json
from datetime import datetime
from pathlib import Path

from queuewatch import jobs


class TransientError(Exception):
    """A temporary problem. Retrying might fix it."""


class PermanentError(Exception):
    """A real problem (bad input, missing file). Retrying will not help."""


def process_csv(input_value, attempt):
    path = Path(input_value)
    if not input_value or not path.is_file():
        raise PermanentError(f"CSV file not found: {input_value}")

    rows = 0
    total_quantity = 0
    total_revenue = 0.0
    try:
        with path.open(newline="") as file:
            for row in csv.DictReader(file):
                quantity = int(row["quantity"])
                price = float(row["price"])
                rows += 1
                total_quantity += quantity
                total_revenue += quantity * price
    except (KeyError, ValueError) as err:
        raise PermanentError(f"Bad CSV data: {err!r}")

    return {
        "rows": rows,
        "total_quantity": total_quantity,
        "total_revenue": round(total_revenue, 2),
    }


def generate_report(input_value, attempt):
    name = Path(input_value).name if input_value else "report"
    folder = Path("reports")
    folder.mkdir(exist_ok=True)
    output_file = folder / f"{name}.json"

    report = {"generated_at": jobs.now(), "job_counts": jobs.stats()}
    output_file.write_text(json.dumps(report, indent=2))
    return {"report_file": str(output_file)}


def simulate_failure(input_value, attempt):
    mode = input_value or "transient"

    if mode == "transient":
        if attempt < 3:
            raise TransientError(f"Temporary glitch on attempt {attempt}")
        return {"message": f"Recovered on attempt {attempt}"}
    if mode == "always":
        raise TransientError("Service is still unavailable")
    if mode == "permanent":
        raise PermanentError("Invalid configuration - retrying will not help")
    raise PermanentError(f"Unknown mode '{mode}'. Use transient, always or permanent.")


# Names used on the command line map to functions here.
TASKS = {
    "process_csv": process_csv,
    "generate_report": generate_report,
    "simulate_failure": simulate_failure,
}
