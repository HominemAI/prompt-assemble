"""Prompt sources - pluggable backends for retrieving prompts."""

import logging
import os
from .base import PromptSource
from .filesystem import FileSystemSource
from .database import DatabaseSource

logger = logging.getLogger(__name__)

__all__ = [
    "PromptSource",
    "FileSystemSource",
    "DatabaseSource",
    "create_database_source_from_env",
]


def create_database_source_from_env(table_prefix: str = None) -> DatabaseSource:
    """
    Create a DatabaseSource from PostgreSQL environment variables.

    Reads the following environment variables:
    - DB_HOSTNAME: PostgreSQL server hostname (default: localhost)
    - DB_PORT: PostgreSQL server port (default: 5432)
    - DB_USERNAME: PostgreSQL username (default: postgres)
    - DB_PASSWORD: PostgreSQL password (required)
    - DB_DATABASE: PostgreSQL database name (default: prompts)
    - PROMPT_ASSEMBLE_TABLE_PREFIX: Table prefix (optional)

    Args:
        table_prefix: Optional override for table prefix. If provided, takes
                     precedence over PROMPT_ASSEMBLE_TABLE_PREFIX env var.

    Returns:
        DatabaseSource instance configured for PostgreSQL

    Raises:
        ImportError: If psycopg2 is not installed
        SourceConnectionError: If database connection fails
    """
    try:
        import psycopg2
    except ImportError:
        raise ImportError(
            "psycopg2 is required for PostgreSQL support. "
            "Install with: pip install psycopg2-binary"
        )

    # Read environment variables with defaults
    hostname = os.getenv("DB_HOSTNAME", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    username = os.getenv("DB_USERNAME", "postgres")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_DATABASE", "prompts")

    if not password:
        raise ValueError(
            "DB_PASSWORD environment variable is required for PostgreSQL connection"
        )

    # Create connection
    conn = psycopg2.connect(
        host=hostname,
        port=port,
        user=username,
        password=password,
        database=database
    )

    logger.info(
        f"Connected to PostgreSQL: {username}@{hostname}:{port}/{database}"
    )

    # Use provided table_prefix or read from environment
    if table_prefix is None:
        table_prefix = os.getenv("PROMPT_ASSEMBLE_TABLE_PREFIX", "")

    # Create and return DatabaseSource
    return DatabaseSource(conn, table_prefix=table_prefix)
