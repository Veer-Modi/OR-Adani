"""Configuration manager.

Goal:
- Keep environment-based settings in one place.
- Provide safe defaults for development.

Beginner note:
- In production, secrets and environment-specific settings should come from environment variables.
- Locally, you can use a .env file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


# Load variables from .env into process environment.
# If .env does not exist, this does nothing (that's okay).
load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    app_env: str
    session_timeout_minutes: int

    # Logging
    log_level: str
    log_dir: str
    audit_log_to_mongo: bool

    # Solver defaults
    default_time_limit_seconds: int
    default_mip_gap: float
    solver_logs_enabled: bool


def _get_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return bool(default)
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return int(default)
    try:
        return int(v)
    except Exception:
        return int(default)


def _get_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None:
        return float(default)
    try:
        return float(v)
    except Exception:
        return float(default)


def get_config() -> AppConfig:
    """Load configuration from environment variables."""

    app_env = os.getenv("APP_ENV", "development").strip().lower()

    return AppConfig(
        app_env=app_env,
        session_timeout_minutes=_get_int("SESSION_TIMEOUT_MINUTES", 60),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        log_dir=os.getenv("LOG_DIR", "logs").strip(),
        audit_log_to_mongo=_get_bool("AUDIT_LOG_TO_MONGO", True),
        default_time_limit_seconds=_get_int("SOLVER_TIME_LIMIT_SECONDS", 60),
        default_mip_gap=_get_float("SOLVER_MIP_GAP", 0.01),
        solver_logs_enabled=_get_bool("SOLVER_LOGS_ENABLED", True),
    )
