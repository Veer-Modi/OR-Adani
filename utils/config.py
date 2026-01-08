"""Application configuration.

This file reads settings from environment variables.

Why environment variables?
- You should NOT hardcode secrets (like DB passwords) into code.
- It makes it easy to change settings per machine (dev vs prod).

We use a .env file locally (loaded by python-dotenv).
"""

import os

from dotenv import load_dotenv

# Load variables from .env into process environment.
# If .env does not exist, this does nothing (that's okay).
load_dotenv()


def get_mongo_uri() -> str:
    """MongoDB connection string."""

    # Example: mongodb://localhost:27017
    value = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    return value


def get_mongo_db_name() -> str:
    """MongoDB database name."""

    value = os.getenv("MONGO_DB_NAME", "auth_system")
    return value


def get_users_collection_name() -> str:
    """MongoDB collection name for user documents."""

    value = os.getenv("MONGO_USERS_COLLECTION", "users")
    return value
