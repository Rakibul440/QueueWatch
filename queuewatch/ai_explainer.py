import re

import requests

from queuewatch import config


class ExplainError(Exception):
    """If Ai API fails , It'will show"""


def sanitize(text):
    text = text or ""
    # things like api_key=abc123, token: xyz, password=...
    text = re.sub(r"(?i)\b(api[_-]?key|token|password|secret)\b\s*[=:]\s*\S+", r"\1=<hidden>", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "<email>", text)           # emails
    text = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}", "<secret>", text)           # sk-... style keys
    text = re.sub(r"\b[A-Za-z0-9_-]{32,}\b", "<secret>", text)           # long random tokens
    text = re.sub(r"[A-Za-z]:\\[^\s'\"]+", "<path>", text)               # C:\folder\file
    text = re.sub(r"(?<!\w)/(?:[\w.\-]+/)*[\w.\-]+", "<path>", text)     # /folder/file
    return text[:500]


def build_prompt(task, error):
    return (
        "A background job failed in a small Python job-runner.\n"
        f"Task name: {task}\n"
        f"Error: {error}\n\n"
        "In plain language, reply in exactly this format and keep it short:\n"
        "Failure summary: one sentence.\n"
        "Possible causes: 2-3 short bullet points.\n"
        "Suggested checks: 2-3 numbered steps.\n"
        "You cannot see the system, so do not claim certainty."
    )


def explain_failure(task, error):
    """Return the AI's explanation text, or raise ExplainError."""
    api_key = config.llm_api_key()
    if not api_key:
        raise ExplainError("No LLM_API_KEY found. Add it to your .env file to use 'explain'.")

    prompt = build_prompt(task, sanitize(error))
    try:
        response = requests.post(
            config.llm_api_url(),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config.llm_model(),
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20,
        )
    except requests.RequestException:
        raise ExplainError("Could not reach the AI service (network problem or timeout).")

    if response.status_code == 429:
        raise ExplainError("The AI service is rate-limiting requests. Wait a bit and try again.")
    if response.status_code != 200:
        raise ExplainError(f"The AI service returned an error (HTTP {response.status_code}).")

    try:
        text = response.json()["content"][0]["text"].strip()
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        raise ExplainError("The AI service sent a response in an unexpected format.")
    if not text:
        raise ExplainError("The AI service sent an empty answer.")
    return text
