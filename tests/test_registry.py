"""Tests for registry functionality."""

import pytest

from prompt_assemble.registry import Registry, RegistryEntry


class TestRegistryEntry:
    """Test RegistryEntry dataclass."""

    def test_create_minimal(self):
        """Test creating entry with minimal fields."""
        entry = RegistryEntry(name="test")
        assert entry.name == "test"
        assert entry.description == ""
        assert entry.tags == []
        assert entry.owner is None
        assert entry.source_ref is None

    def test_create_full(self):
        """Test creating entry with all fields."""
        entry = RegistryEntry(
            name="test",
            description="A test entry",
            tags=["tag1", "tag2"],
            owner="alice",
            source_ref="/path/to/file",
        )
        assert entry.name == "test"
        assert entry.description == "A test entry"
        assert entry.tags == ["tag1", "tag2"]
        assert entry.owner == "alice"
        assert entry.source_ref == "/path/to/file"


class TestRegistry:
    """Test Registry class."""

    def test_register_and_get(self):
        """Test registering and retrieving entries."""
        registry = Registry()
        entry = RegistryEntry(name="test", tags=["foo"])
        registry.register(entry)

        retrieved = registry.get("test")
        assert retrieved is not None
        assert retrieved.name == "test"
        assert retrieved.tags == ["foo"]

    def test_register_updates_existing(self):
        """Test that registering updates existing entries."""
        registry = Registry()
        entry1 = RegistryEntry(name="test", tags=["old"])
        registry.register(entry1)

        entry2 = RegistryEntry(name="test", tags=["new"])
        registry.register(entry2)

        retrieved = registry.get("test")
        assert retrieved.tags == ["new"]

    def test_unregister(self):
        """Test unregistering entries."""
        registry = Registry()
        registry.register(RegistryEntry(name="test"))
        registry.unregister("test")

        assert registry.get("test") is None

    def test_unregister_nonexistent(self):
        """Test unregistering nonexistent entries (should not error)."""
        registry = Registry()
        registry.unregister("nonexistent")  # Should not raise

    def test_find_by_tags_empty(self):
        """Test finding with no tags returns all names."""
        registry = Registry()
        registry.register(RegistryEntry(name="a"))
        registry.register(RegistryEntry(name="b"))

        result = registry.find_by_tags()
        assert set(result) == {"a", "b"}

    def test_find_by_tags_single(self):
        """Test finding with single tag."""
        registry = Registry()
        registry.register(RegistryEntry(name="a", tags=["foo"]))
        registry.register(RegistryEntry(name="b", tags=["bar"]))
        registry.register(RegistryEntry(name="c", tags=["foo", "bar"]))

        result = registry.find_by_tags("foo")
        assert set(result) == {"a", "c"}

    def test_find_by_tags_multiple_and(self):
        """Test finding with multiple tags (AND intersection)."""
        registry = Registry()
        registry.register(RegistryEntry(name="a", tags=["foo"]))
        registry.register(RegistryEntry(name="b", tags=["bar"]))
        registry.register(RegistryEntry(name="c", tags=["foo", "bar"]))
        registry.register(RegistryEntry(name="d", tags=["foo", "baz"]))

        result = registry.find_by_tags("foo", "bar")
        assert result == ["c"]

    def test_find_by_tags_preserves_order(self):
        """Test that find_by_tags preserves insertion order."""
        registry = Registry()
        registry.register(RegistryEntry(name="first", tags=["x"]))
        registry.register(RegistryEntry(name="second", tags=["x"]))
        registry.register(RegistryEntry(name="third", tags=["x"]))

        result = registry.find_by_tags("x")
        assert result == ["first", "second", "third"]

    def test_find_by_tags_no_matches(self):
        """Test finding with nonexistent tag."""
        registry = Registry()
        registry.register(RegistryEntry(name="a", tags=["foo"]))

        result = registry.find_by_tags("nonexistent")
        assert result == []

    def test_list_names(self):
        """Test listing all names."""
        registry = Registry()
        registry.register(RegistryEntry(name="first"))
        registry.register(RegistryEntry(name="second"))

        result = registry.list_names()
        assert result == ["first", "second"]

    def test_list_names_empty(self):
        """Test listing names on empty registry."""
        registry = Registry()
        assert registry.list_names() == []

    def test_clear(self):
        """Test clearing the registry."""
        registry = Registry()
        registry.register(RegistryEntry(name="a"))
        registry.register(RegistryEntry(name="b"))

        registry.clear()

        assert registry.list_names() == []
        assert registry.get("a") is None
