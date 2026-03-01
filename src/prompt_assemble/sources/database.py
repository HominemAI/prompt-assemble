"""Database source for prompts with versioning support."""

import logging
import os
import time
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

        # Auto-refresh configuration
        self.refresh_interval_seconds = int(os.getenv("PROMPT_ASSEMBLE_REFRESH_INTERVAL", "30"))
        self._last_refresh_time = 0

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
            # Always try to create all tables - CREATE TABLE IF NOT EXISTS is safe
            logger.info("Creating/verifying prompts table...")
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

            # Variable Sets tables - these might not exist in older databases
            logger.info("Creating/verifying variable_sets table...")
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table('variable_sets')} (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            logger.info("variable_sets table created/verified")

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table('variable_set_variables')} (
                    id TEXT PRIMARY KEY,
                    variable_set_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(variable_set_id, key),
                    FOREIGN KEY (variable_set_id) REFERENCES {self._table('variable_sets')}(id)
                )
                """
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table('variable_set_selections')} (
                    id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    variable_set_id TEXT NOT NULL,
                    list_order INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(prompt_id, variable_set_id),
                    FOREIGN KEY (prompt_id) REFERENCES {self._table('prompts')}(id),
                    FOREIGN KEY (variable_set_id) REFERENCES {self._table('variable_sets')}(id)
                )
                """
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table('variable_set_overrides')} (
                    id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    variable_set_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    override_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(prompt_id, variable_set_id, key),
                    FOREIGN KEY (prompt_id) REFERENCES {self._table('prompts')}(id),
                    FOREIGN KEY (variable_set_id) REFERENCES {self._table('variable_sets')}(id)
                )
                """
            )

            self.connection.commit()
            logger.info("✓ Database schema successfully created/verified")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"ERROR ensuring schema: {e}")
            raise
        finally:
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

        # Update last refresh timestamp
        self._last_refresh_time = time.time()

    def _should_refresh(self) -> bool:
        """Check if enough time has passed since last refresh."""
        elapsed = time.time() - self._last_refresh_time
        return elapsed >= self.refresh_interval_seconds

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
        if self._should_refresh():
            self.refresh()
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
        if self._should_refresh():
            self.refresh()
        return self._registry.find_by_tags(*tags)

    def list(self) -> list[str]:
        """List all available prompt names."""
        if self._should_refresh():
            self.refresh()
        return self._registry.list_names()

    def save_prompt(
        self,
        name: str,
        content: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        owner: Optional[str] = None,
        increment_version: bool = True,
    ) -> str:
        """
        Save or update a prompt.

        Args:
            name: Prompt name
            content: Prompt content
            description: Prompt description
            tags: List of tags
            owner: Owner identifier
            increment_version: Whether to increment version (False for cache-only saves)

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
                # Only increment version for real saves, not cache saves
                new_version = current_version + 1 if increment_version else current_version

                logger.debug(f"Updating existing prompt {name}: current_version={current_version}, new_version={new_version}, increment_version={increment_version}")

                # Update prompt
                cursor.execute(
                    f"UPDATE {self._table('prompts')} SET content = %s, version = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (content, new_version, prompt_id),
                )

                # Save version history only for real saves (not cache/auto-saves)
                if increment_version:
                    logger.debug(f"Creating version history entry for {name}: version={new_version}")
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

    # Variable Sets Management Methods

    def create_variable_set(self, name: str, variables: Optional[Dict[str, str]] = None) -> str:
        """
        Create a new variable set.

        Args:
            name: Variable set name
            variables: Dict of key-value pairs

        Returns:
            Variable set ID
        """
        import uuid

        if variables is None:
            variables = {}

        cursor = self.connection.cursor()
        try:
            set_id = str(uuid.uuid4())
            cursor.execute(
                f"INSERT INTO {self._table('variable_sets')} (id, name) VALUES (%s, %s)",
                (set_id, name),
            )

            # Add variables
            for key, value in variables.items():
                cursor.execute(
                    f"INSERT INTO {self._table('variable_set_variables')} (id, variable_set_id, key, value) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), set_id, key, value),
                )

            self.connection.commit()
            return set_id
        finally:
            cursor.close()

    def get_variable_set(self, set_id: str) -> Optional[Dict[str, Any]]:
        """Get a variable set by ID."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SELECT id, name FROM {self._table('variable_sets')} WHERE id = %s", (set_id,))
            row = cursor.fetchone()
            if not row:
                return None

            set_id, name = row
            cursor.execute(
                f"SELECT key, value FROM {self._table('variable_set_variables')} WHERE variable_set_id = %s",
                (set_id,),
            )

            variables = {row[0]: row[1] for row in cursor.fetchall()}
            return {"id": set_id, "name": name, "variables": variables}
        finally:
            cursor.close()

    def list_variable_sets(self) -> List[Dict[str, Any]]:
        """List all variable sets."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SELECT id, name FROM {self._table('variable_sets')} ORDER BY name")
            sets = []
            for row in cursor.fetchall():
                set_id, name = row
                cursor.execute(
                    f"SELECT key, value FROM {self._table('variable_set_variables')} WHERE variable_set_id = %s",
                    (set_id,),
                )
                variables = {r[0]: r[1] for r in cursor.fetchall()}
                sets.append({"id": set_id, "name": name, "variables": variables})
            return sets
        finally:
            cursor.close()

    def update_variable_set(self, set_id: str, name: Optional[str] = None, variables: Optional[Dict[str, str]] = None) -> None:
        """Update a variable set."""
        cursor = self.connection.cursor()
        try:
            if name:
                cursor.execute(
                    f"UPDATE {self._table('variable_sets')} SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (name, set_id),
                )

            if variables is not None:
                # Delete existing variables
                cursor.execute(
                    f"DELETE FROM {self._table('variable_set_variables')} WHERE variable_set_id = %s",
                    (set_id,),
                )
                # Add new variables
                for key, value in variables.items():
                    cursor.execute(
                        f"INSERT INTO {self._table('variable_set_variables')} (id, variable_set_id, key, value) VALUES (%s, %s, %s, %s)",
                        (str(uuid.uuid4()), set_id, key, value),
                    )

            self.connection.commit()
        finally:
            cursor.close()

    def delete_variable_set(self, set_id: str) -> None:
        """Delete a variable set."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                f"DELETE FROM {self._table('variable_set_variables')} WHERE variable_set_id = %s",
                (set_id,),
            )
            cursor.execute(
                f"DELETE FROM {self._table('variable_set_selections')} WHERE variable_set_id = %s",
                (set_id,),
            )
            cursor.execute(
                f"DELETE FROM {self._table('variable_set_overrides')} WHERE variable_set_id = %s",
                (set_id,),
            )
            cursor.execute(
                f"DELETE FROM {self._table('variable_sets')} WHERE id = %s",
                (set_id,),
            )
            self.connection.commit()
        finally:
            cursor.close()

    def get_active_variable_sets(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Get all active variable sets for a prompt, in order."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                f"""
                SELECT vs.id, vs.name
                FROM {self._table('variable_set_selections')} vss
                JOIN {self._table('variable_sets')} vs ON vss.variable_set_id = vs.id
                WHERE vss.prompt_id = %s
                ORDER BY vss.list_order
                """,
                (prompt_id,),
            )

            sets = []
            for row in cursor.fetchall():
                set_id, name = row
                cursor.execute(
                    f"SELECT key, value FROM {self._table('variable_set_variables')} WHERE variable_set_id = %s",
                    (set_id,),
                )
                variables = {r[0]: r[1] for r in cursor.fetchall()}
                sets.append({"id": set_id, "name": name, "variables": variables})
            return sets
        finally:
            cursor.close()

    def set_active_variable_sets(self, prompt_id: str, set_ids: List[str]) -> None:
        """Set the active variable sets for a prompt."""
        cursor = self.connection.cursor()
        try:
            # Remove existing selections
            cursor.execute(
                f"DELETE FROM {self._table('variable_set_selections')} WHERE prompt_id = %s",
                (prompt_id,),
            )
            # Add new selections in order
            for order, set_id in enumerate(set_ids):
                cursor.execute(
                    f"INSERT INTO {self._table('variable_set_selections')} (id, prompt_id, variable_set_id, list_order) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), prompt_id, set_id, order),
                )
            self.connection.commit()
        finally:
            cursor.close()

    def get_variable_overrides(self, prompt_id: str, set_id: str) -> Dict[str, str]:
        """Get override values for a specific set in a prompt."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                f"SELECT key, override_value FROM {self._table('variable_set_overrides')} WHERE prompt_id = %s AND variable_set_id = %s",
                (prompt_id, set_id),
            )
            return {row[0]: row[1] for row in cursor.fetchall()}
        finally:
            cursor.close()

    def set_variable_overrides(self, prompt_id: str, set_id: str, overrides: Dict[str, str]) -> None:
        """Set override values for a specific set in a prompt."""
        cursor = self.connection.cursor()
        try:
            # Remove existing overrides
            cursor.execute(
                f"DELETE FROM {self._table('variable_set_overrides')} WHERE prompt_id = %s AND variable_set_id = %s",
                (prompt_id, set_id),
            )
            # Add new overrides
            for key, value in overrides.items():
                cursor.execute(
                    f"INSERT INTO {self._table('variable_set_overrides')} (id, prompt_id, variable_set_id, key, override_value) VALUES (%s, %s, %s, %s, %s)",
                    (str(uuid.uuid4()), prompt_id, set_id, key, value),
                )
            self.connection.commit()
        finally:
            cursor.close()
