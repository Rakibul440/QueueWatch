import json

import pytest

from queuewatch import tasks


def test_process_csv_totals(db, tmp_path):
    csv_file = tmp_path / "s.csv"
    csv_file.write_text("date,product,quantity,price\n2026-01-01,Pen,2,1.50\n2026-01-02,Book,1,10.00\n")
    result = tasks.process_csv(str(csv_file), 1)
    assert result == {"rows": 2, "total_quantity": 3, "total_revenue": 13.0}


def test_process_csv_missing_file_is_permanent(db):
    with pytest.raises(tasks.PermanentError):
        tasks.process_csv("does_not_exist.csv", 1)


def test_process_csv_bad_data_is_permanent(db, tmp_path):
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text("date,product,quantity,price\n2026-01-01,Pen,two,1.50\n")
    with pytest.raises(tasks.PermanentError):
        tasks.process_csv(str(csv_file), 1)


def test_simulate_failure_transient_recovers_on_third_attempt(db):
    with pytest.raises(tasks.TransientError):
        tasks.simulate_failure("transient", 1)
    with pytest.raises(tasks.TransientError):
        tasks.simulate_failure("transient", 2)
    assert "Recovered" in tasks.simulate_failure("transient", 3)["message"]


def test_generate_report_writes_json_file(db):
    result = tasks.generate_report("my_report", 1)
    with open(result["report_file"]) as file:
        report = json.load(file)
    assert "job_counts" in report
