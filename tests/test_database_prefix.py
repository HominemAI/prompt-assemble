"""Tests for DatabaseSource table prefix functionality.

NOTE: These tests require PostgreSQL. Use pytest -k "not test_database_prefix" to skip them.
Run with: PGHOST=localhost PGUSER=postgres PGPASSWORD=... PGDATABASE=test_prompts pytest tests/test_database_prefix.py
"""

import sqlite3
import os

import pytest

from prompt_assemble.sources import DatabaseSource


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
def test_table_prefix_from_env():
    """Test reading table prefix from environment variable."""
    os.environ["PROMPT_ASSEMBLE_TABLE_PREFIX"] = "test_"

    conn = sqlite3.connect(":memory:")
    source = DatabaseSource(conn)

    assert source.table_prefix == "test_"

    # Clean up
    del os.environ["PROMPT_ASSEMBLE_TABLE_PREFIX"]


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
def test_table_prefix_from_argument():
    """Test providing table prefix as constructor argument."""
    conn = sqlite3.connect(":memory:")
    source = DatabaseSource(conn, table_prefix="custom_")

    assert source.table_prefix == "custom_"


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
def test_table_prefix_argument_overrides_env():
    """Test that constructor argument overrides environment variable."""
    os.environ["PROMPT_ASSEMBLE_TABLE_PREFIX"] = "env_"

    conn = sqlite3.connect(":memory:")
    source = DatabaseSource(conn, table_prefix="arg_")

    assert source.table_prefix == "arg_"

    # Clean up
    del os.environ["PROMPT_ASSEMBLE_TABLE_PREFIX"]


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
def test_default_no_prefix():
    """Test that default has no prefix when env and arg not provided."""
    # Ensure env var is not set
    os.environ.pop("PROMPT_ASSEMBLE_TABLE_PREFIX", None)

    conn = sqlite3.connect(":memory:")
    source = DatabaseSource(conn)

    assert source.table_prefix == ""


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
def test_table_prefix_in_table_names():
    """Test that prefixed table names are used in SQL queries."""
    conn = sqlite3.connect(":memory:")
    source = DatabaseSource(conn, table_prefix="myapp_")

    # Verify tables were created with prefix
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = [
        "myapp_prompts",
        "myapp_prompt_registry",
        "myapp_prompt_tags",
        "myapp_prompt_versions",
    ]

    assert set(tables) == set(expected_tables)


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
def test_save_and_retrieve_with_prefix():
    """Test saving and retrieving prompts with table prefix."""
    conn = sqlite3.connect(":memory:")
    source = DatabaseSource(conn, table_prefix="app_")

    # Save a prompt
    source.save_prompt(
        name="test_prompt",
        content="Test content",
        description="Test description",
        tags=["test", "sample"],
        owner="alice",
    )

    # Retrieve it
    content = source.get_raw("test_prompt")
    assert content == "Test content"

    # Verify it's in the list
    prompts = source.list()
    assert "test_prompt" in prompts


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
def test_versioning_with_prefix():
    """Test version tracking with table prefix."""
    conn = sqlite3.connect(":memory:")
    source = DatabaseSource(conn, table_prefix="v_")

    # Save first version
    source.save_prompt("versioned", "v1", tags=["v"])
    assert source.get_raw("versioned") == "v1"

    # Save second version
    source.save_prompt("versioned", "v2", tags=["v"])
    assert source.get_raw("versioned") == "v2"

    # Retrieve specific version
    v1 = source.get_prompt_version("versioned", version=1)
    assert v1 == "v1"

    v2 = source.get_prompt_version("versioned", version=2)
    assert v2 == "v2"


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
def test_tags_with_prefix():
    """Test tag functionality with table prefix."""
    conn = sqlite3.connect(":memory:")
    source = DatabaseSource(conn, table_prefix="tag_")

    source.save_prompt("p1", "content", tags=["a", "b"])
    source.save_prompt("p2", "content", tags=["b", "c"])
    source.save_prompt("p3", "content", tags=["a", "c"])

    # Find by single tag
    assert set(source.find_by_tag("a")) == {"p1", "p3"}
    assert set(source.find_by_tag("b")) == {"p1", "p2"}
    assert set(source.find_by_tag("c")) == {"p2", "p3"}

    # Find by multiple tags (AND intersection)
    assert set(source.find_by_tag("a", "b")) == {"p1"}
    assert set(source.find_by_tag("b", "c")) == {"p2"}
    assert set(source.find_by_tag("a", "c")) == {"p3"}


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
def test_multiple_sources_different_prefixes():
    """Test multiple DatabaseSource instances with different prefixes."""
    # Source 1 with prefix
    conn1 = sqlite3.connect(":memory:")
    source1 = DatabaseSource(conn1, table_prefix="app1_")
    source1.save_prompt("p1", "App1 content", tags=["app1"])

    # Source 2 with different prefix but same connection would use different tables
    conn2 = sqlite3.connect(":memory:")
    source2 = DatabaseSource(conn2, table_prefix="app2_")
    source2.save_prompt("p1", "App2 content", tags=["app2"])

    # Verify they have different content
    assert source1.get_raw("p1") == "App1 content"
    assert source2.get_raw("p1") == "App2 content"


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
def test_empty_prefix_is_valid():
    """Test that empty string prefix is valid and creates unprefixed tables."""
    conn = sqlite3.connect(":memory:")
    source = DatabaseSource(conn, table_prefix="")

    source.save_prompt("test", "content")

    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]

    # Tables should have no prefix
    expected_tables = [
        "prompts",
        "prompt_registry",
        "prompt_tags",
        "prompt_versions",
    ]

    assert set(tables) == set(expected_tables)
