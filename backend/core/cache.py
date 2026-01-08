"""Caching helpers.

Goal:
- Improve performance by caching static/master data.

Important:
- Streamlit caches are per-process.
- Caching is safe for master data that changes infrequently (plants, routes).

We keep caching in a separate module so business logic remains unchanged.
"""

from __future__ import annotations

from typing import Any, Callable, List

import streamlit as st


def cache_data(ttl_seconds: int = 60) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Small wrapper around st.cache_data with a TTL."""

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        return st.cache_data(ttl=ttl_seconds, show_spinner=False)(fn)

    return _decorator


@cache_data(ttl_seconds=60)
def cached_get_all_plants(include_inactive: bool = False):
    from backend.plant.plant_service import get_all_plants

    return get_all_plants(include_inactive=include_inactive)


@cache_data(ttl_seconds=60)
def cached_get_all_routes(include_disabled: bool = True):
    from backend.transport.transport_service import get_all_routes

    return get_all_routes(include_disabled=include_disabled)
