"""Structured logging + audit trail.

This module provides:
- File logging (rotating log file)
- Optional MongoDB audit log storage

Design goal:
- UI shows friendly messages.
- Detailed troubleshooting information goes to logs.

Audit log examples:
- login success/failure
- data CRUD actions
- optimization runs
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

from backend.core.config_manager import get_config


_LOGGER: logging.Logger | None = None


def get_logger() -> logging.Logger:
    global _LOGGER

    if _LOGGER is not None:
        return _LOGGER

    cfg = get_config()
    logger = logging.getLogger("clinker_app")

    # Avoid duplicate handlers on Streamlit re-runs.
    if logger.handlers:
        _LOGGER = logger
        return logger

    logger.setLevel(getattr(logging, cfg.log_level, logging.INFO))

    os.makedirs(cfg.log_dir, exist_ok=True)
    log_path = os.path.join(cfg.log_dir, "app.log")

    handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Also log to console (useful for dev).
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    _LOGGER = logger
    return logger


def _audit_doc(event_type: str, actor_email: str | None, details: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event_type": event_type,
        "actor_email": actor_email,
        "details": dict(details or {}),
        "created_at": datetime.now(timezone.utc),
    }


def audit_log(event_type: str, actor_email: str | None, details: Dict[str, Any]) -> None:
    """Write an audit log entry to file and (optionally) MongoDB."""

    logger = get_logger()
    safe_details = details or {}

    # Always log to file.
    logger.info("AUDIT | %s | %s", event_type, json.dumps({"actor": actor_email, **safe_details}, default=str))

    cfg = get_config()
    if not cfg.audit_log_to_mongo:
        return

    try:
        from backend.database.mongo import get_audit_logs_collection

        coll = get_audit_logs_collection()
        coll.insert_one(_audit_doc(event_type, actor_email, safe_details))
    except Exception:
        # Never fail the app because audit logging failed.
        logger.warning("AUDIT | failed to write to MongoDB", exc_info=True)


def log_exception(message: str, exc: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    logger = get_logger()
    logger.error("%s | context=%s", message, json.dumps(context or {}, default=str), exc_info=True)
