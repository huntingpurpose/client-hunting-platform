from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
for dotenv_path in (BASE_DIR / ".env", BASE_DIR.parent / ".env"):
    if dotenv_path.exists():
        load_dotenv(dotenv_path)


def _get_env_int(name: str, default: int | None = None) -> int | None:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return int(value)


DEFAULT_DATABASE_URL = f"sqlite:///{(BASE_DIR / 'client_hunting.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = _get_env_int("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "true").lower() in {"1", "true", "yes", "on"}
