"""MongoDB connection helper.

We use pymongo to connect to MongoDB.

Important notes:
- The connection string (URI) is stored in environment variables.
- We create a unique index on email to prevent duplicate accounts.
"""

from __future__ import annotations

from pymongo import MongoClient

from utils.config import (
    get_mongo_db_name,
    get_mongo_uri,
    get_users_collection_name,
)


# We keep one shared client per app run.
# Streamlit reruns code, but the module global helps reuse connection.
_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Create (or reuse) a MongoClient."""

    global _client

    if _client is None:
        _client = MongoClient(get_mongo_uri())

    return _client


def get_db():
    """Get the MongoDB database object."""

    client = get_client()
    return client[get_mongo_db_name()]


def get_users_collection():
    """Get the users collection and ensure indexes exist."""

    db = get_db()
    users = db[get_users_collection_name()]

    # Unique index ensures email cannot be duplicated.
    # If the index already exists, MongoDB keeps it.
    users.create_index("email", unique=True)

    return users


def get_plants_collection():
    """Get the plants collection and ensure indexes exist."""

    db = get_db()
    plants = db["plants"]

    # Plant names should be unique (prevents duplicate plants).
    plants.create_index("name", unique=True)

    return plants


def get_demands_collection():
    """Get the demands collection and ensure indexes exist."""

    db = get_db()
    demands = db["demands"]

    # Prevent duplicates per plant/month/demand_type.
    demands.create_index(
        [("plant_id", 1), ("month", 1), ("demand_type", 1)],
        unique=True,
    )

    return demands


def get_transport_routes_collection():
    """Get the transport_routes collection and ensure indexes exist."""

    db = get_db()
    routes = db["transport_routes"]

    # Prevent duplicate routes per (from, to, mode).
    routes.create_index(
        [("from_plant_id", 1), ("to_plant_id", 1), ("transport_mode", 1)],
        unique=True,
    )

    return routes


def get_inventory_policies_collection():
    """Get the inventory_policies collection and ensure indexes exist."""

    db = get_db()
    policies = db["inventory_policies"]

    # One policy per plant.
    policies.create_index("plant_id", unique=True)

    return policies


def get_optimization_results_collection():
    """Get the optimization_results collection for run history."""

    db = get_db()
    results = db["optimization_results"]

    # Sort and filter convenience.
    results.create_index("created_at")

    return results


def get_demand_uncertainty_collection():
    """Get the demand_uncertainty_settings collection.

    We store a single "global" settings document.
    """

    db = get_db()
    settings = db["demand_uncertainty_settings"]

    # Singleton settings document (key="global").
    settings.create_index("key", unique=True)

    return settings


def get_audit_logs_collection():
    """Get the audit_logs collection.

    This collection stores security and operational audit events:
    - logins
    - data changes
    - optimization runs
    - admin actions
    """

    db = get_db()
    logs = db["audit_logs"]

    # Useful for filtering and retention policies.
    logs.create_index("created_at")
    logs.create_index("event_type")
    logs.create_index("actor_email")

    return logs
