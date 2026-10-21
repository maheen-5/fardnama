"""Database configuration and connection placeholder."""

import os


def get_database_url() -> str | None:
    """Return the configured database URL, if present."""
    return os.getenv("DATABASE_URL")


def get_connection():
    """Database connections are not implemented in the Mid-1 prototype."""
    raise NotImplementedError("PostgreSQL persistence is Final-1")
