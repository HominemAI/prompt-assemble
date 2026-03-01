"""Database source for prompts with versioning support."""

import logging
import os
from typing import Any, Dict, List, Optional

from ..exceptions import PromptNotFoundError, SourceConnectionError
from ..registry import Registry, RegistryEntry
from .base import PromptSource

logger = logging.getLogger(__name__)


class DatabaseSource(PromptSource):
    """Load prompts from a PostgreSQL or other SQL database with version support.

    Supports any DBAPI2-compatible database including PostgreSQL, SQLite, MySQL, etc.
    PostgreSQL is the recommended backend for production use.
    """

    def __init__(self, connection: Any, table_prefix: Optional[str] = None):
        """
        Initialize DatabaseSource.

        Args:
            connection: DBAPI2-compatible database connection (e.g., psycopg2.connect())
            table_prefix: Optional prefix for all table names.
                         If not provided, reads from PROMPT_ASSEMBLE_TABLE_PREFIX env var.
                         Defaults to empty string if neither is provided.

        Raises:
            SourceConnectionError: If connection is invalid

        Environment Variables:
            PROMPT_ASSEMBLE_TABLE_PREFIX: Prefix for all table names (e.g., "myapp_")

        Examples:
            PostgreSQL (recommended):
                import psycopg2
                conn = psycopg2.connect("dbname=prompts user=postgres")
                source = DatabaseSource(conn, table_prefix="prod_")

            SQLite (development):
                import sqlite3
                conn = sqlite3.connect("prompts.db")
                source = DatabaseSource(conn)
        """
        super().__init__()
        self.connection = connection

        # Determine table prefix from argument, env var, or default to empty
        if table_prefix is not None:
            self.table_prefix = table_prefix
        else:
            self.table_prefix = os.getenv("PROMPT_ASSEMBLE_TABLE_PREFIX", "")

        logger.info(f"DatabaseSource initialized with table prefix: '{self.table_prefix}'")

        self._registry = Registry()
        self._metadata_cache: Dict[str, dict] = {}

        # Verify connection and initialize schema
        try:
            self._ensure_schema()
            self.refresh()
        except Exception as e:
            raise SourceConnectionError(f"Failed to initialize database: {e}")

    def _table(self, name: str) -> str:
        """Get the full table name with prefix."""
        return f"{self.table_prefix}{name}"

    def _ensure_schema(self) -> None:
        """Ensure database schema exists."""
        cursor = self.connection.cursor()
        try:
            # Check if tables exist by trying to query them
            cursor.execute(f"SELECT 1 FROM {self._table('prompts')} LIMIT 1")
        except Exception:
            # Tables don't exist, rollback failed transaction and create them
            self.connection.rollback()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table('prompts')} (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table('prompt_registry')} (
                    id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL UNIQUE,
                    description TEXT,
                    owner TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prompt_id) REFERENCES {self._table('prompts')}(id)
                )
                """
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table('prompt_tags')} (
                    prompt_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (prompt_id, tag),
                    FOREIGN KEY (prompt_id) REFERENCES {self._table('prompts')}(id)
                )
                """
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table('prompt_versions')} (
                    id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(prompt_id, version),
                    FOREIGN KEY (prompt_id) REFERENCES {self._table('prompts')}(id)
                )
                """
            )

            self.connection.commit()

        cursor.close()

    def refresh(self) -> None:
        """Refresh metadata from database (not content)."""
        self._ensure_connection()
        self._registry.clear()
        self._metadata_cache.clear()

        cursor = self.connection.cursor()
        try:
            # Get all prompts with their metadata
            cursor.execute(
                f"""
                SELECT p.id, p.name, p.version, pr.description, pr.owner
                FROM {self._table('prompts')} p
                LEFT JOIN {self._table('prompt_registry')} pr ON p.id = pr.prompt_id
                ORDER BY p.created_at ASC
                """
            )

            for row in cursor.fetchall():
                prompt_id, name, version, description, owner = row
                self._metadata_cache[prompt_id] = {
                    "name": name,
                    "version": version,
                    "description": description or "",
                    "owner": owner,
                }

                # Get tags for this prompt
                cursor.execute(
                    f"SELECT tag FROM {self._table('prompt_tags')} WHERE prompt_id = %s",
                    (prompt_id,),
                )
                tags = [row[0] for row in cursor.fetchall()]

                # Register
                entry = RegistryEntry(
                    name=name,
                    description=description or "",
                    tags=tags,
                    owner=owner,
                    source_ref=prompt_id,
                )
                self._registry.register(entry)

        finally:
            cursor.close()

        # Emit refresh event
        self._emit("refreshed")

    def _ensure_connection(self):
        """Reconnect if the connection is closed."""
        if hasattr(self, '_connection_factory'):
            try:
                # Check if connection is still alive
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            except Exception:
                # Connection is dead, reconnect
                self.connection = self._connection_factory()

    def get_raw(self, name: str) -> str:
        """Get the current version of a prompt by name."""
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                f"SELECT content FROM {self._table('prompts')} WHERE name = %s ORDER BY version DESC LIMIT 1",
                (name,),
            )
            row = cursor.fetchone()
            if row is None:
                raise PromptNotFoundError(f"Prompt not found: {name}")
            return row[0]
        finally:
            cursor.close()

    def delete_prompt(self, name: str) -> None:
        """Delete a prompt and its associated data."""
        cursor = self.connection.cursor()
        try:
            # Get prompt ID
            cursor.execute(
                f"SELECT id FROM {self._table('prompts')} WHERE name = %s",
                (name,),
            )
            row = cursor.fetchone()
            if row is None:
                raise PromptNotFoundError(f"Prompt not found: {name}")

            prompt_id = row[0]

            # Delete tags
            cursor.execute(
                f"DELETE FROM {self._table('prompt_tags')} WHERE prompt_id = %s",
                (prompt_id,),
            )

            # Delete versions
            cursor.execute(
                f"DELETE FROM {self._table('prompt_versions')} WHERE prompt_id = %s",
                (prompt_id,),
            )

            # Delete registry entry
            cursor.execute(
                f"DELETE FROM {self._table('prompt_registry')} WHERE prompt_id = %s",
                (prompt_id,),
            )

            # Delete prompt
            cursor.execute(
                f"DELETE FROM {self._table('prompts')} WHERE id = %s",
                (prompt_id,),
            )

            self.connection.commit()
            self.refresh()
            self._emit("prompt_deleted")

        finally:
            cursor.close()

    def get_prompt_version(self, name: str, version: Optional[int] = None) -> str:
        """
        Get a specific version of a prompt.

        Args:
            name: Prompt name
            version: Version number (None for latest)

        Returns:
            Prompt content

        Raises:
            PromptNotFoundError: If prompt or version not found
        """
        cursor = self.connection.cursor()
        try:
            if version is None:
                cursor.execute(
                    f"SELECT content FROM {self._table('prompts')} WHERE name = %s ORDER BY version DESC LIMIT 1",
                    (name,),
                )
            else:
                cursor.execute(
                    f"SELECT content FROM {self._table('prompt_versions')} WHERE prompt_id IN "
                    f"(SELECT id FROM {self._table('prompts')} WHERE name = %s) AND version = %s",
                    (name, version),
                )

            row = cursor.fetchone()
            if row is None:
                raise PromptNotFoundError(f"Prompt not found: {name} (version {version})")
            return row[0]
        finally:
            cursor.close()

    def find_by_tag(self, *tags: str) -> list[str]:
        """Find all prompt names matching ALL tags (AND intersection)."""
        return self._registry.find_by_tags(*tags)

    def list(self) -> list[str]:
        """List all available prompt names."""
        return self._registry.list_names()

    def save_prompt(
        self,
        name: str,
        content: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        owner: Optional[str] = None,
    ) -> str:
        """
        Save or update a prompt.

        Args:
            name: Prompt name
            content: Prompt content
            description: Prompt description
            tags: List of tags
            owner: Owner identifier

        Returns:
            Prompt ID
        """
        import uuid

        if tags is None:
            tags = []

        cursor = self.connection.cursor()
        try:
            # Check if prompt exists
            cursor.execute(
                f"SELECT id, version FROM {self._table('prompts')} WHERE name = %s",
                (name,),
            )
            row = cursor.fetchone()

            if row is None:
                # Create new prompt
                prompt_id = str(uuid.uuid4())
                cursor.execute(
                    f"INSERT INTO {self._table('prompts')} (id, name, content, version) VALUES (%s, %s, %s, %s)",
                    (prompt_id, name, content, 1),
                )

                # Save version history
                cursor.execute(
                    f"INSERT INTO {self._table('prompt_versions')} (id, prompt_id, version, content) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), prompt_id, 1, content),
                )
            else:
                prompt_id, current_version = row
                new_version = current_version + 1

                # Update prompt
                cursor.execute(
                    f"UPDATE {self._table('prompts')} SET content = %s, version = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (content, new_version, prompt_id),
                )

                # Save version history
                cursor.execute(
                    f"INSERT INTO {self._table('prompt_versions')} (id, prompt_id, version, content) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), prompt_id, new_version, content),
                )

            # Update or create registry entry
            cursor.execute(
                f"SELECT id FROM {self._table('prompt_registry')} WHERE prompt_id = %s",
                (prompt_id,),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    f"INSERT INTO {self._table('prompt_registry')} (id, prompt_id, description, owner) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), prompt_id, description, owner),
                )
            else:
                cursor.execute(
                    f"UPDATE {self._table('prompt_registry')} SET description = %s, owner = %s WHERE prompt_id = %s",
                    (description, owner, prompt_id),
                )

            # Update tags
            cursor.execute(
                f"DELETE FROM {self._table('prompt_tags')} WHERE prompt_id = %s",
                (prompt_id,),
            )
            for tag in tags:
                cursor.execute(
                    f"INSERT INTO {self._table('prompt_tags')} (prompt_id, tag) VALUES (%s, %s)",
                    (prompt_id, tag),
                )

            self.connection.commit()
            self.refresh()
            self._emit("prompt_saved")
            return prompt_id

        finally:
            cursor.close()
