import pytest
import requests

from queuewatch import ai_explainer


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def test_sanitize_removes_secrets_emails_and_paths():
    dirty = "Cannot open /home/alex/data/sales.csv for alex@mail.com with api_key=abc123 sk-ABCDEFGH12345"
    clean = ai_explainer.sanitize(dirty)
    assert "alex@mail.com" not in clean
    assert "/home/alex" not in clean
    assert "abc123" not in clean
    assert "sk-ABCDEFGH12345" not in clean


def test_sanitize_removes_windows_paths():
    assert "Users" not in ai_explainer.sanitize(r"Missing C:\Users\Sam\data.csv")


def test_sanitize_limits_length():
    assert len(ai_explainer.sanitize("x " * 1000)) <= 500


def test_missing_api_key_gives_friendly_error(db):
    with pytest.raises(ai_explainer.ExplainError) as err:
        ai_explainer.explain_failure("process_csv", "boom")
    assert "LLM_API_KEY" in str(err.value)


def test_successful_explanation(db, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    reply = FakeResponse(200, {"content": [{"type": "text", "text": "Failure summary: test"}]})
    monkeypatch.setattr(ai_explainer.requests, "post", lambda *a, **k: reply)
    assert ai_explainer.explain_failure("process_csv", "boom") == "Failure summary: test"


def test_network_failure_is_handled(db, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")

    def broken_post(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(ai_explainer.requests, "post", broken_post)
    with pytest.raises(ai_explainer.ExplainError):
        ai_explainer.explain_failure("process_csv", "boom")


def test_rate_limit_is_handled(db, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr(ai_explainer.requests, "post", lambda *a, **k: FakeResponse(429))
    with pytest.raises(ai_explainer.ExplainError) as err:
        ai_explainer.explain_failure("process_csv", "boom")
    assert "rate" in str(err.value).lower()


def test_bad_response_format_is_handled(db, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr(
        ai_explainer.requests, "post", lambda *a, **k: FakeResponse(200, {"oops": 1})
    )
    with pytest.raises(ai_explainer.ExplainError):
        ai_explainer.explain_failure("process_csv", "boom")
