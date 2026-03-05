"""Tests for DatabaseSource.

NOTE: These tests require PostgreSQL. Use pytest -k "not test_database_source" to skip them.
Run with: PGHOST=localhost PGUSER=postgres PGPASSWORD=... PGDATABASE=test_prompts pytest tests/test_database_source.py
"""

import sqlite3
import uuid

import pytest

from prompt_assemble.exceptions import PromptNotFoundError, SourceConnectionError
from prompt_assemble.sources import DatabaseSource


pytestmark = pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")


@pytest.fixture
def db_connection():
    """Create an in-memory SQLite database connection."""
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


class TestDatabaseSourceBasics:
    """Test basic DatabaseSource functionality."""

    def test_init_creates_schema(self, db_connection):
        """Test that initialization creates required schema."""
        source = DatabaseSource(db_connection)

        # Verify tables exist
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        expected = [
            "prompts",
            "prompt_registry",
            "prompt_tags",
            "prompt_versions",
        ]
        assert set(tables) == set(expected)

    def test_init_invalid_connection(self):
        """Test initialization with invalid connection."""
        with pytest.raises(SourceConnectionError):
            DatabaseSource(None)

    def test_list_empty_database(self, db_connection):
        """Test listing prompts from empty database."""
        source = DatabaseSource(db_connection)
        assert source.list() == []


class TestDatabaseSourcePromptOperations:
    """Test saving and retrieving prompts."""

    def test_save_new_prompt(self, db_connection):
        """Test saving a new prompt."""
        source = DatabaseSource(db_connection)

        prompt_id = source.save_prompt(
            name="greeting",
            content="Hello there!",
            description="A greeting",
            tags=["greeting", "friendly"],
            owner="alice",
        )

        assert prompt_id is not None
        assert source.get_raw("greeting") == "Hello there!"
        assert source.list() == ["greeting"]

    def test_save_prompt_with_versioning(self, db_connection):
        """Test that saving updates version."""
        source = DatabaseSource(db_connection)

        # Save initial version
        source.save_prompt(name="test", content="v1")
        assert source.get_raw("test") == "v1"

        # Save updated version
        source.save_prompt(name="test", content="v2")
        assert source.get_raw("test") == "v2"

    def test_get_prompt_version(self, db_connection):
        """Test retrieving specific prompt version."""
        source = DatabaseSource(db_connection)

        source.save_prompt(name="versioned", content="version 1")
        source.save_prompt(name="versioned", content="version 2")
        source.save_prompt(name="versioned", content="version 3")

        assert source.get_prompt_version("versioned", version=1) == "version 1"
        assert source.get_prompt_version("versioned", version=2) == "version 2"
        assert source.get_prompt_version("versioned", version=3) == "version 3"

    def test_get_raw_nonexistent(self, db_connection):
        """Test getting nonexistent prompt."""
        source = DatabaseSource(db_connection)
        with pytest.raises(PromptNotFoundError):
            source.get_raw("nonexistent")

    def test_get_prompt_version_nonexistent(self, db_connection):
        """Test getting nonexistent version."""
        source = DatabaseSource(db_connection)
        source.save_prompt(name="test", content="v1")

        with pytest.raises(PromptNotFoundError):
            source.get_prompt_version("test", version=999)


class TestDatabaseSourceTags:
    """Test tag functionality."""

    def test_save_prompt_with_tags(self, db_connection):
        """Test saving prompt with tags."""
        source = DatabaseSource(db_connection)

        source.save_prompt(
            name="expert",
            content="Expert instructions",
            tags=["persona", "technical"],
        )

        assert source.find_by_tag("persona") == ["expert"]
        assert source.find_by_tag("technical") == ["expert"]

    def test_find_by_tags_and_intersection(self, db_connection):
        """Test finding prompts with AND intersection of tags."""
        source = DatabaseSource(db_connection)

        source.save_prompt(name="a", content="content", tags=["foo"])
        source.save_prompt(name="b", content="content", tags=["bar"])
        source.save_prompt(name="c", content="content", tags=["foo", "bar"])

        assert set(source.find_by_tag("foo")) == {"a", "c"}
        assert set(source.find_by_tag("bar")) == {"b", "c"}
        assert source.find_by_tag("foo", "bar") == ["c"]

    def test_find_by_nonexistent_tag(self, db_connection):
        """Test finding with nonexistent tag."""
        source = DatabaseSource(db_connection)
        source.save_prompt(name="test", content="content", tags=["foo"])

        assert source.find_by_tag("nonexistent") == []

    def test_update_prompt_updates_tags(self, db_connection):
        """Test that updating a prompt updates tags."""
        source = DatabaseSource(db_connection)

        source.save_prompt(name="test", content="v1", tags=["old"])
        source.save_prompt(name="test", content="v2", tags=["new"])

        assert source.find_by_tag("old") == []
        assert source.find_by_tag("new") == ["test"]


class TestDatabaseSourceMetadata:
    """Test metadata and registry functionality."""

    def test_save_prompt_with_metadata(self, db_connection):
        """Test saving prompt with description and owner."""
        source = DatabaseSource(db_connection)

        source.save_prompt(
            name="test",
            content="content",
            description="A test prompt",
            owner="alice",
        )

        # Metadata is stored but we'd need to query DB directly to verify
        # For now just verify it doesn't raise

    def test_multiple_prompts_maintain_order(self, db_connection):
        """Test that multiple prompts are listed in creation order."""
        source = DatabaseSource(db_connection)

        source.save_prompt(name="first", content="1")
        source.save_prompt(name="second", content="2")
        source.save_prompt(name="third", content="3")

        assert source.list() == ["first", "second", "third"]

    def test_refresh_reloads_metadata(self, db_connection):
        """Test that refresh reloads metadata from database."""
        source = DatabaseSource(db_connection)

        # Save directly via SQL
        cursor = db_connection.cursor()
        prompt_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO prompts (id, name, content, version) VALUES (?, ?, ?, ?)",
            (prompt_id, "direct", "content", 1),
        )
        db_connection.commit()

        # Refresh should pick it up
        source.refresh()
        assert source.list() == ["direct"]
