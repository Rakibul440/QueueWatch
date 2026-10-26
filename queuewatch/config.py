import os
from pathlib import Path


def _load_env_file(path=".env"):
    env_file = Path(path)
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        # setdefault: real environment variables win over the .env file
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


def database_path():
    return os.environ.get("DATABASE_PATH", "queuewatch.db")


def max_retries():
    return int(os.environ.get("MAX_RETRIES", "3"))


def retry_delay():
    return float(os.environ.get("RETRY_DELAY_SECONDS", "1"))


def llm_api_key():
    return os.environ.get("LLM_API_KEY", "")


def llm_model():
    return os.environ.get("LLM_MODEL", "claude-sonnet-5-5")


def llm_api_url():
    return os.environ.get("LLM_API_URL", "https://api.anthropic.com/v1/messages")
