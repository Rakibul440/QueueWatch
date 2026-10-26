import pytest

from queuewatch import database


@pytest.fixture
def db(tmp_path, monkeypatch):
    """A fresh, empty database in a temp folder for every test."""
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("RETRY_DELAY_SECONDS", "0")   # no waiting in tests
    monkeypatch.setenv("MAX_RETRIES", "3")
    monkeypatch.setenv("LLM_API_KEY", "")            # tests never call the real AI
    monkeypatch.chdir(tmp_path)                      # reports/ is created in the temp folder
    database.init_db()
