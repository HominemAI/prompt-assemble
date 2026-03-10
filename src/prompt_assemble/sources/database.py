"""Database source for prompts with versioning support."""

import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from ..exceptions import PromptNotFoundError, SourceConnectionError
from ..registry import Registry, RegistryEntry
from .base import PromptSource

logger = logging.getLogger(__name__)


class DatabaseSource(PromptSource):
    """Load prompts from a PostgreSQL or other SQL database with version support.

    Supports any DBAPI2-compatible database including PostgreSQL, SQLite, MySQL, etc.
    PostgreSQL is the recommended backend for production use.
    Implements connection pooling to avoid connection exhaustion.
    """

    def __init__(self, connection: Any = None, connection_pool: Any = None, table_prefix: Optional[str] = None):
        """
        Initialize DatabaseSource.

        Args:
            connection: DBAPI2-compatible database connection (e.g., psycopg2.connect())
                       For backward compatibility. If provided, creates a pool with minconn=1, maxconn=5.
            connection_pool: psycopg2.pool.SimpleConnectionPool instance (preferred for production)
            table_prefix: Optional prefix for all table names.
                         If not provided, reads from PROMPT_ASSEMBLE_TABLE_PREFIX env var.
                         Defaults to empty string if neither is provided.

        Raises:
            SourceConnectionError: If connection is invalid

        Environment Variables:
            PROMPT_ASSEMBLE_TABLE_PREFIX: Prefix for all table names (e.g., "myapp_")

        Examples:
            PostgreSQL with connection pool (recommended):
                import psycopg2
                from psycopg2 import pool
                pool = pool.SimpleConnectionPool(1, 10,
                    host='localhost', database='prompts', user='postgres', password='...')
                source = DatabaseSource(connection_pool=pool)

            PostgreSQL with single connection (backward compatible):
                import psycopg2
                conn = psycopg2.connect("dbname=prompts user=postgres")
                source = DatabaseSource(conn, table_prefix="prod_")

            SQLite (development):
                import sqlite3
                conn = sqlite3.connect("prompts.db")
                source = DatabaseSource(conn)
        """
        super().__init__()

        if connection_pool is not None:
            self._pool = connection_pool
            self.connection = None  # Use pool instead
        elif connection is not None:
            # Backward compatibility: wrap single connection in a simple pool
            try:
                import psycopg2.pool
                # Create a minimal pool with 1 connection (the provided one won't be used,
                # but we'll use the pool for consistency)
                self._pool = None
                self.connection = connection  # Keep for backward compat
            except ImportError:
                # For non-psycopg2 databases, just use the connection directly
                self._pool = None
                self.connection = connection
        else:
            raise SourceConnectionError("Either connection or connection_pool must be provided")

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
        self._last_refresh_time: float = 0.0

        # Verify connection and initialize schema
        try:
            self._ensure_schema()
            self.refresh()
        except Exception as e:
            raise SourceConnectionError(f"Failed to initialize database: {e}")

    @contextmanager
    def _get_cursor(self):
        """Context manager to safely get and close a database cursor.

        Handles both connection pool and direct connection scenarios.
        Automatically closes the cursor and returns the connection to the pool.
        """
        connection = None
        cursor = None
        try:
            if self._pool is not None:
                # Get connection from pool with retry logic
                try:
                    connection = self._pool.getconn()
                except Exception as e:
                    logger.error(f"Failed to get connection from pool: {e}")
                    raise
            else:
                # Use direct connection
                if self.connection is None:
                    raise SourceConnectionError("Database connection is not initialized")
                connection = self.connection

            # Verify connection is alive before using
            try:
                if connection.closed:
                    raise SourceConnectionError("Database connection is closed")
            except AttributeError:
                # SQLite connections don't have a 'closed' attribute, that's ok
                pass

            cursor = connection.cursor()
            yield cursor
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception as e:
                    logger.debug(f"Error closing cursor: {e}")

            if connection is not None and self._pool is not None:
                try:
                    self._pool.putconn(connection)
                except Exception as e:
                    logger.debug(f"Error returning connection to pool: {e}")

    def _table(self, name: str) -> str:
        """Get the full table name with prefix."""
        return f"{self.table_prefix}{name}"

    def _table_exists(self, cursor, table_name: str) -> bool:
        """Check if a table exists in the database.

        Note: PostgreSQL stores unquoted table names as lowercase in information_schema,
        so we check with lowercase to handle case-insensitive matching.
        """
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)",
            (table_name.lower(),)
        )
        result = cursor.fetchone()
        return bool(result[0]) if result else False

    def _ensure_schema(self) -> None:
        """Ensure database schema exists."""
        with self._get_cursor() as cursor:
            try:
                # Enable autocommit for schema operations to avoid transaction abort (PostgreSQL only)
                try:
                    cursor.connection.autocommit = True
                except (AttributeError, TypeError):
                    # SQLite and other databases don't support autocommit
                    pass

                # Check and create tables only if they don't exist
                table_name = self._table('prompts')
                if not self._table_exists(cursor, table_name):
                    logger.info(f"Creating table: {table_name}")
                    cursor.execute(
                        f"""
                        CREATE TABLE {table_name} (
                            id TEXT PRIMARY KEY,
                            name TEXT UNIQUE NOT NULL,
                            content TEXT NOT NULL,
                            version INTEGER NOT NULL DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        """
                    )
                    logger.info(f"✓ Table {table_name} created")
                else:
                    logger.info(f"✓ Table {table_name} already exists")

                table_name = self._table('prompt_registry')
                if not self._table_exists(cursor, table_name):
                    logger.info(f"Creating table: {table_name}")
                    cursor.execute(
                        f"""
                        CREATE TABLE {table_name} (
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
                    logger.info(f"✓ Table {table_name} created")
                else:
                    logger.info(f"✓ Table {table_name} already exists")

                table_name = self._table('prompt_tags')
                if not self._table_exists(cursor, table_name):
                    logger.info(f"Creating table: {table_name}")
                    cursor.execute(
                        f"""
                        CREATE TABLE {table_name} (
                            prompt_id TEXT NOT NULL,
                            tag TEXT NOT NULL,
                            PRIMARY KEY (prompt_id, tag),
                            FOREIGN KEY (prompt_id) REFERENCES {self._table('prompts')}(id)
                        )
                        """
                    )
                    logger.info(f"✓ Table {table_name} created")
                else:
                    logger.info(f"✓ Table {table_name} already exists")

                table_name = self._table('prompt_versions')
                if not self._table_exists(cursor, table_name):
                    logger.info(f"Creating table: {table_name}")
                    cursor.execute(
                        f"""
                        CREATE TABLE {table_name} (
                            id TEXT PRIMARY KEY,
                            prompt_id TEXT NOT NULL,
                            version INTEGER NOT NULL,
                            content TEXT NOT NULL,
                            revision_comment TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(prompt_id, version),
                            FOREIGN KEY (prompt_id) REFERENCES {self._table('prompts')}(id)
                        )
                        """
                    )
                    logger.info(f"✓ Table {table_name} created")
                else:
                    logger.info(f"✓ Table {table_name} already exists")
                    # Add revision_comment column if it doesn't exist (for backwards compatibility)
                    try:
                        cursor.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN revision_comment TEXT"
                        )
                        logger.info(f"Added revision_comment column to {table_name}")
                    except Exception as e:
                        # Silently ignore if column already exists
                        if "already exists" not in str(e).lower() and "duplicate column" not in str(e).lower():
                            logger.debug(f"Could not add revision_comment column: {e}")

                # Variable Sets tables - these might not exist in older databases
                table_name = self._table('variable_sets')
                if not self._table_exists(cursor, table_name):
                    logger.info(f"Creating table: {table_name}")
                    try:
                        cursor.execute(
                            f"""
                            CREATE TABLE {table_name} (
                                id TEXT PRIMARY KEY,
                                name TEXT UNIQUE NOT NULL,
                                owner TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                            """
                        )
                        logger.info(f"✓ Table {table_name} created")
                    except Exception as e:
                        logger.warning(f"Could not create variable_sets table: {e}")
                else:
                    logger.info(f"✓ Table {table_name} already exists")
                    # Add owner column if it doesn't exist (for backwards compatibility)
                    try:
                        cursor.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN owner TEXT"
                        )
                        logger.info(f"Added owner column to {table_name}")
                    except Exception as e:
                        # Silently ignore if column already exists
                        if "already exists" not in str(e).lower() and "duplicate column" not in str(e).lower():
                            logger.debug(f"Could not add owner column to {table_name}: {e}")

                table_name = self._table('variable_set_variables')
                if not self._table_exists(cursor, table_name):
                    logger.info(f"Creating table: {table_name}")
                    try:
                        cursor.execute(
                            f"""
                            CREATE TABLE {table_name} (
                                id TEXT PRIMARY KEY,
                                variable_set_id TEXT NOT NULL,
                                key TEXT NOT NULL,
                                value TEXT NOT NULL,
                                tag TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(variable_set_id, key),
                                FOREIGN KEY (variable_set_id) REFERENCES {self._table('variable_sets')}(id)
                            )
                            """
                        )
                        logger.info(f"✓ Table {table_name} created")
                    except Exception as e:
                        logger.warning(f"Could not create variable_set_variables table: {e}")
                else:
                    logger.info(f"✓ Table {table_name} already exists")
                    # Add tag column if it doesn't exist (for backwards compatibility)
                    try:
                        cursor.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN tag TEXT"
                        )
                        logger.info(f"Added tag column to {table_name}")
                    except Exception as e:
                        # Silently ignore if column already exists
                        if "already exists" not in str(e).lower() and "duplicate column" not in str(e).lower():
                            logger.debug(f"Could not add tag column to {table_name}: {e}")

                table_name = self._table('variable_set_selections')
                if not self._table_exists(cursor, table_name):
                    logger.info(f"Creating table: {table_name}")
                    try:
                        cursor.execute(
                            f"""
                            CREATE TABLE {table_name} (
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
                        logger.info(f"✓ Table {table_name} created")
                    except Exception as e:
                        logger.warning(f"Could not create variable_set_selections table: {e}")
                else:
                    logger.info(f"✓ Table {table_name} already exists")

                table_name = self._table('variable_set_overrides')
                if not self._table_exists(cursor, table_name):
                    logger.info(f"Creating table: {table_name}")
                    try:
                        cursor.execute(
                            f"""
                            CREATE TABLE {table_name} (
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
                        logger.info(f"✓ Table {table_name} created")
                    except Exception as e:
                        logger.warning(f"Could not create variable_set_overrides table: {e}")
                else:
                    logger.info(f"✓ Table {table_name} already exists")

                logger.info("✓ Database schema successfully created/verified")
                # Commit any pending changes
                try:
                    cursor.connection.commit()
                except:
                    pass
            except Exception as e:
                logger.error(f"ERROR ensuring schema: {e}")
                try:
                    cursor.connection.rollback()
                except:
                    pass
                raise
            finally:
                # Disable autocommit after schema operations (PostgreSQL only)
                try:
                    cursor.connection.autocommit = False
                except (AttributeError, TypeError):
                    # SQLite and other databases don't support autocommit
                    pass
                try:
                    cursor.connection.commit()
                except:
                    pass

    def refresh(self) -> None:
        """Refresh metadata from database (not content)."""
        self._ensure_connection()
        self._registry.clear()
        self._metadata_cache.clear()

        with self._get_cursor() as cursor:
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

        # Emit refresh event
        self._emit("refreshed")

        # Update last refresh timestamp
        self._last_refresh_time = time.time()

    def _should_refresh(self) -> bool:
        """Check if enough time has passed since last refresh."""
        elapsed = time.time() - self._last_refresh_time
        return elapsed >= self.refresh_interval_seconds

    def _ensure_connection(self):
        """Verify connection is alive (no-op for connection pools)."""
        # When using a connection pool, connections are managed by the pool
        # and we get a fresh connection from getconn() each time
        if self._pool is not None:
            # Connection pool handles reconnection automatically
            return

        # For direct connections, verify it's still alive
        if self.connection is None:
            raise SourceConnectionError("Database connection is not initialized")
        try:
            if hasattr(self.connection, 'closed') and self.connection.closed:
                raise SourceConnectionError("Database connection is closed")
        except Exception:
            # If check fails, let _get_cursor handle it
            pass

    def get_raw(self, name: str) -> str:
        """Get the current version of a prompt by name."""
        if self._should_refresh():
            self.refresh()
        self._ensure_connection()
        with self._get_cursor() as cursor:
            cursor.execute(
                f"SELECT content FROM {self._table('prompts')} WHERE name = %s ORDER BY version DESC LIMIT 1",
                (name,),
            )
            row = cursor.fetchone()
            if row is None:
                raise PromptNotFoundError(f"Prompt not found: {name}")
            return str(row[0])

    def delete_prompt(self, name: str) -> None:
        """Delete a prompt and its associated data."""
        self._ensure_connection()
        with self._get_cursor() as cursor:
            # Get prompt ID
            cursor.execute(
                f"SELECT id FROM {self._table('prompts')} WHERE name = %s",
                (name,),
            )
            row = cursor.fetchone()
            if row is None:
                raise PromptNotFoundError(f"Prompt not found: {name}")

            prompt_id = row[0]

            # Delete variable set selections (foreign key constraint)
            cursor.execute(
                f"DELETE FROM {self._table('variable_set_selections')} WHERE prompt_id = %s",
                (prompt_id,),
            )

            # Delete variable set overrides (foreign key constraint)
            cursor.execute(
                f"DELETE FROM {self._table('variable_set_overrides')} WHERE prompt_id = %s",
                (prompt_id,),
            )

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

            cursor.connection.commit()
            self.refresh()
            self._emit("prompt_deleted")

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
        with self._get_cursor() as cursor:
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
            return str(row[0])

    def find_by_tag(self, *tags: str) -> List[str]:
        """Find all prompt names matching ALL tags (AND intersection)."""
        if self._should_refresh():
            self.refresh()
        return self._registry.find_by_tags(*tags)

    def find_by_owner(self, owner: str) -> List[str]:
        """Find all prompt names owned by a specific owner."""
        if self._should_refresh():
            self.refresh()
        return self._registry.find_by_owner(owner)

    def list(self) -> List[str]:
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
            revision_comment: Optional[str] = None,
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
            revision_comment: Optional comment for this revision

        Returns:
            Prompt ID
        """
        import uuid

        if tags is None:
            tags = []

        self._ensure_connection()
        with self._get_cursor() as cursor:
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
                    f"INSERT INTO {self._table('prompt_versions')} (id, prompt_id, version, content, revision_comment) VALUES (%s, %s, %s, %s, %s)",
                    (str(uuid.uuid4()), prompt_id, 1, content, revision_comment),
                )
            else:
                prompt_id, current_version = row
                # Only increment version for real saves, not cache saves
                new_version = current_version + 1 if increment_version else current_version

                logger.debug(
                    f"Updating existing prompt {name}: current_version={current_version}, new_version={new_version}, increment_version={increment_version}")

                # Update prompt
                cursor.execute(
                    f"UPDATE {self._table('prompts')} SET content = %s, version = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (content, new_version, prompt_id),
                )

                # Save version history only for real saves (not cache/auto-saves)
                if increment_version:
                    logger.debug(f"Creating version history entry for {name}: version={new_version}")
                    cursor.execute(
                        f"INSERT INTO {self._table('prompt_versions')} (id, prompt_id, version, content, revision_comment) VALUES (%s, %s, %s, %s, %s)",
                        (str(uuid.uuid4()), prompt_id, new_version, content, revision_comment),
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

            # Clean up old versions - keep only the 20 most recent
            if increment_version:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {self._table('prompt_versions')} WHERE prompt_id = %s",
                    (prompt_id,),
                )
                version_count = cursor.fetchone()[0]

                if version_count > 20:
                    # Delete oldest versions, keeping only 20 most recent
                    versions_to_delete = version_count - 20
                    logger.debug(f"Cleaning up {versions_to_delete} old versions for {name}, keeping 20 most recent")
                    cursor.execute(
                        f"""
                        DELETE FROM {self._table('prompt_versions')}
                        WHERE prompt_id = %s AND id NOT IN (
                            SELECT id FROM {self._table('prompt_versions')}
                            WHERE prompt_id = %s
                            ORDER BY version DESC
                            LIMIT 20
                        )
                        """,
                        (prompt_id, prompt_id),
                    )

            cursor.connection.commit()
            self.refresh()
            self._emit("prompt_saved")
            return prompt_id

    def batch_save_prompts(self, prompts: List[Dict[str, Any]]) -> int:
        """
        Save multiple prompts in a single transaction (for bulk import).

        Much faster than calling save_prompt() individually because it batches
        all database operations into one transaction.

        Args:
            prompts: List of dicts with keys: name, content, description, tags, owner

        Returns:
            Number of prompts successfully saved
        """
        import uuid

        if not prompts:
            return 0

        self._ensure_connection()
        saved_count = 0

        with self._get_cursor() as cursor:
            try:
                cursor.connection.autocommit = False

                for prompt_data in prompts:
                    try:
                        name = prompt_data["name"]
                        content = prompt_data["content"]
                        description = prompt_data.get("description", "")
                        tags = prompt_data.get("tags", [])
                        owner = prompt_data.get("owner")

                        # Check if prompt exists
                        cursor.execute(
                            f"SELECT id FROM {self._table('prompts')} WHERE name = %s",
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
                        else:
                            prompt_id = row[0]
                            # Update existing prompt
                            cursor.execute(
                                f"UPDATE {self._table('prompts')} SET content = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                                (content, prompt_id),
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

                        # Delete existing tags and add new ones
                        cursor.execute(
                            f"DELETE FROM {self._table('prompt_tags')} WHERE prompt_id = %s",
                            (prompt_id,),
                        )
                        for tag in tags:
                            cursor.execute(
                                f"INSERT INTO {self._table('prompt_tags')} (prompt_id, tag) VALUES (%s, %s)",
                                (prompt_id, tag),
                            )

                        saved_count += 1

                    except Exception as e:
                        logger.error(f"Error saving prompt {prompt_data.get('name', 'unknown')}: {e}")
                        # Continue with next prompt instead of failing entire batch

                # Commit all changes at once
                cursor.connection.commit()

            except Exception as e:
                cursor.connection.rollback()
                logger.error(f"Error in batch save: {e}")
                raise

        self.refresh()
        self._emit("prompt_saved")
        return saved_count

    # Variable Sets Management Methods

    def _parse_variable_value(self, value: Any) -> tuple[str, Optional[str]]:
        """
        Parse a variable value (string or tagged dict) into (value_str, tag_str).

        Args:
            value: Either a string or a dict with 'value' and optional 'tag' keys

        Returns:
            Tuple of (value_string, tag_string_or_none)
        """
        if isinstance(value, dict) and "value" in value:
            return str(value["value"]), value.get("tag")
        return str(value), None

    def _get_set_variables(self, cursor: Any, set_id: str) -> Dict[str, Any]:
        """
        Get all variables for a set, handling both simple and tagged formats.

        Returns:
            Dict mapping keys to either simple strings or {"value": str, "tag": str}
        """
        cursor.execute(
            f"SELECT key, value, tag FROM {self._table('variable_set_variables')} WHERE variable_set_id = %s",
            (set_id,),
        )
        variables = {}
        for key, value, tag in cursor.fetchall():
            if tag:
                variables[key] = {"value": value, "tag": tag}
            else:
                variables[key] = value
        return variables

    def create_variable_set(self, name: str, variables: Optional[Dict[str, str]] = None, owner: Optional[str] = None) -> str:
        """
        Create a new variable set.

        Args:
            name: Variable set name
            variables: Dict of key-value pairs (simple strings or tagged dicts with 'value'/'tag' keys)
            owner: Optional owner for scoped variable sets (None = global)

        Returns:
            Variable set ID
        """
        import uuid

        if variables is None:
            variables = {}

        with self._get_cursor() as cursor:
            set_id = str(uuid.uuid4())
            cursor.execute(
                f"INSERT INTO {self._table('variable_sets')} (id, name, owner) VALUES (%s, %s, %s)",
                (set_id, name, owner),
            )

            # Add variables
            for key, value in variables.items():
                val_str, tag = self._parse_variable_value(value)
                cursor.execute(
                    f"INSERT INTO {self._table('variable_set_variables')} (id, variable_set_id, key, value, tag) VALUES (%s, %s, %s, %s, %s)",
                    (str(uuid.uuid4()), set_id, key, val_str, tag),
                )

            cursor.connection.commit()
            return set_id

    def get_variable_set(self, set_id: str) -> Optional[Dict[str, Any]]:
        """Get a variable set by ID."""
        with self._get_cursor() as cursor:
            cursor.execute(f"SELECT id, name, owner FROM {self._table('variable_sets')} WHERE id = %s", (set_id,))
            row = cursor.fetchone()
            if not row:
                return None

            set_id, name, owner = row
            variables = self._get_set_variables(cursor, set_id)
            return {"id": set_id, "name": name, "owner": owner, "variables": variables}

    def list_variable_sets(self) -> List[Dict[str, Any]]:
        """List all variable sets (global and all scoped)."""
        with self._get_cursor() as cursor:
            cursor.execute(f"SELECT id, name, owner FROM {self._table('variable_sets')} ORDER BY name")
            sets = []
            for row in cursor.fetchall():
                set_id, name, owner = row
                variables = self._get_set_variables(cursor, set_id)
                sets.append({"id": set_id, "name": name, "owner": owner, "variables": variables})
            return sets

    def list_global_variable_sets(self) -> List[Dict[str, Any]]:
        """List only global (unscoped) variable sets."""
        with self._get_cursor() as cursor:
            cursor.execute(f"SELECT id, name FROM {self._table('variable_sets')} WHERE owner IS NULL ORDER BY name")
            sets = []
            for row in cursor.fetchall():
                set_id, name = row
                variables = self._get_set_variables(cursor, set_id)
                sets.append({"id": set_id, "name": name, "owner": None, "variables": variables})
            return sets

    def list_variable_sets_by_owner(self, owner: str) -> List[Dict[str, Any]]:
        """List variable sets scoped to a specific owner."""
        with self._get_cursor() as cursor:
            cursor.execute(f"SELECT id, name FROM {self._table('variable_sets')} WHERE owner = %s ORDER BY name", (owner,))
            sets = []
            for row in cursor.fetchall():
                set_id, name = row
                variables = self._get_set_variables(cursor, set_id)
                sets.append({"id": set_id, "name": name, "owner": owner, "variables": variables})
            return sets

    def get_available_variable_sets(self, owner: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get variable sets available to a prompt owner.
        Returns global sets + sets scoped to the owner.
        """
        global_sets = self.list_global_variable_sets()
        if owner:
            owner_sets = self.list_variable_sets_by_owner(owner)
            return global_sets + owner_sets
        return global_sets

    def update_variable_set(self, set_id: str, name: Optional[str] = None,
                            variables: Optional[Dict[str, str]] = None, owner: Optional[str] = None) -> None:
        """Update a variable set."""
        import uuid
        self._ensure_connection()
        with self._get_cursor() as cursor:
            # Build update query
            updates = []
            params = []
            if name:
                updates.append("name = %s")
                params.append(name)
            if owner is not None:
                updates.append("owner = %s")
                params.append(owner)

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(set_id)
                update_sql = ", ".join(updates)
                cursor.execute(
                    f"UPDATE {self._table('variable_sets')} SET {update_sql} WHERE id = %s",
                    params,
                )

            if variables is not None:
                # Delete existing variables
                cursor.execute(
                    f"DELETE FROM {self._table('variable_set_variables')} WHERE variable_set_id = %s",
                    (set_id,),
                )
                # Add new variables
                for key, value in variables.items():
                    val_str, tag = self._parse_variable_value(value)
                    cursor.execute(
                        f"INSERT INTO {self._table('variable_set_variables')} (id, variable_set_id, key, value, tag) VALUES (%s, %s, %s, %s, %s)",
                        (str(uuid.uuid4()), set_id, key, val_str, tag),
                    )

            cursor.connection.commit()

    def delete_variable_set(self, set_id: str) -> None:
        """Delete a variable set."""
        self._ensure_connection()
        with self._get_cursor() as cursor:
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
            cursor.connection.commit()

    def get_active_variable_sets(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Get all active variable sets for a prompt, in order."""
        with self._get_cursor() as cursor:
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
                variables = self._get_set_variables(cursor, set_id)
                sets.append({"id": set_id, "name": name, "variables": variables})
            return sets

    def set_active_variable_sets(self, prompt_id: str, set_ids: List[str]) -> None:
        """Set the active variable sets for a prompt."""
        import uuid
        with self._get_cursor() as cursor:
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
            cursor.connection.commit()

    def add_variable_to_set(self, set_id: str, key: str, value: str, tag: Optional[str] = None) -> None:
        """
        Add or update a single variable in a set without modifying others.

        Args:
            set_id: Variable set ID
            key: Variable key
            value: Variable value (string or value part of tagged dict)
            tag: Optional XML wrapper tag for the variable
        """
        import uuid
        self._ensure_connection()
        with self._get_cursor() as cursor:
            # Try insert first (if key doesn't exist)
            cursor.execute(
                f"SELECT id FROM {self._table('variable_set_variables')} WHERE variable_set_id = %s AND key = %s",
                (set_id, key),
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing
                cursor.execute(
                    f"UPDATE {self._table('variable_set_variables')} SET value = %s, tag = %s, updated_at = CURRENT_TIMESTAMP WHERE variable_set_id = %s AND key = %s",
                    (value, tag, set_id, key),
                )
            else:
                # Insert new
                cursor.execute(
                    f"INSERT INTO {self._table('variable_set_variables')} (id, variable_set_id, key, value, tag) VALUES (%s, %s, %s, %s, %s)",
                    (str(uuid.uuid4()), set_id, key, value, tag),
                )

            cursor.connection.commit()

    def remove_variable_from_set(self, set_id: str, key: str) -> None:
        """
        Remove a single variable from a set.

        Args:
            set_id: Variable set ID
            key: Variable key to remove
        """
        self._ensure_connection()
        with self._get_cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {self._table('variable_set_variables')} WHERE variable_set_id = %s AND key = %s",
                (set_id, key),
            )
            cursor.connection.commit()

    def find_variable_sets(self, name: Optional[str] = None, owner: Optional[str] = None,
                          match_type: str = "exact") -> List[Dict[str, Any]]:
        """
        Find variable sets by name and/or owner.

        Args:
            name: Variable set name to search for (optional)
            owner: Owner filter (optional)
            match_type: "exact" or "partial" for name matching

        Returns:
            List of matching variable sets with their variables
        """
        with self._get_cursor() as cursor:
            # Build WHERE clause
            conditions = []
            params = []

            if name is not None:
                if match_type == "partial":
                    conditions.append("name ILIKE %s")
                    params.append(f"%{name}%")
                else:
                    conditions.append("name = %s")
                    params.append(name)

            if owner is not None:
                conditions.append("owner = %s")
                params.append(owner)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            cursor.execute(
                f"SELECT id, name, owner FROM {self._table('variable_sets')} WHERE {where_clause} ORDER BY name",
                params,
            )

            sets = []
            for row in cursor.fetchall():
                set_id, set_name, set_owner = row
                variables = self._get_set_variables(cursor, set_id)
                sets.append({
                    "id": set_id,
                    "name": set_name,
                    "owner": set_owner,
                    "variables": variables,
                })
            return sets

    def get_variable_overrides(self, prompt_id: str, set_id: str) -> Dict[str, str]:
        """Get override values for a specific set in a prompt."""
        with self._get_cursor() as cursor:
            cursor.execute(
                f"SELECT key, override_value FROM {self._table('variable_set_overrides')} WHERE prompt_id = %s AND variable_set_id = %s",
                (prompt_id, set_id),
            )
            return {row[0]: row[1] for row in cursor.fetchall()}

    def set_variable_overrides(self, prompt_id: str, set_id: str, overrides: Dict[str, str]) -> None:
        """Set override values for a specific set in a prompt."""
        import uuid
        self._ensure_connection()
        with self._get_cursor() as cursor:
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
            cursor.connection.commit()
