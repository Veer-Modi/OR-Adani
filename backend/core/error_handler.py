"""Centralized UI-safe error handling.

Problem:
- Raw stack traces confuse users and may leak technical details.

Solution:
- Wrap Streamlit page render functions with a safe handler.
- Show a short, friendly message to the user.
- Log the full stack trace to file (and optionally audit).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, TypeVar

import streamlit as st

from backend.core.logger import log_exception


T = TypeVar("T")


def safe_page(
    page_name: str,
    user_message: str = "Something went wrong. Please try again or contact an administrator.",
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """Decorator to protect Streamlit pages from crashing."""

    def _decorator(fn: Callable[..., T]) -> Callable[..., Optional[T]]:
        def _wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                log_exception(f"Page error: {page_name}", exc)
                st.error(user_message)
                return None

        return _wrapper

    return _decorator
