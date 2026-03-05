"""Tests for listener/callback functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from prompt_assemble import RegistryEvent, RegistryListener
from prompt_assemble.registry import Registry, RegistryEntry
from prompt_assemble.sources import FileSystemSource, DatabaseSource
import sqlite3


class TestRegistryListeners:
    """Test registry listener functionality."""

    def test_add_listener(self):
        """Test adding a listener to registry."""
        registry = Registry()
        listener = Mock()

        registry.add_listener(listener)
        assert listener in registry._listeners

    def test_remove_listener(self):
        """Test removing a listener from registry."""
        registry = Registry()
        listener = Mock()

        registry.add_listener(listener)
        registry.remove_listener(listener)
        assert listener not in registry._listeners

    def test_listener_called_on_register(self):
        """Test that listener is called when entry is registered."""
        registry = Registry()
        listener = Mock()
        registry.add_listener(listener)

        entry = RegistryEntry(name="test", tags=["foo"])
        registry.register(entry)

        listener.assert_called_once()
        event = listener.call_args[0][0]
        assert isinstance(event, RegistryEvent)
        assert event.event_type == "registered"
        assert event.entry.name == "test"

    def test_listener_called_on_unregister(self):
        """Test that listener is called when entry is unregistered."""
        registry = Registry()
        registry.register(RegistryEntry(name="test"))

        listener = Mock()
        registry.add_listener(listener)
        registry.unregister("test")

        listener.assert_called_once()
        event = listener.call_args[0][0]
        assert event.event_type == "unregistered"
        assert event.name == "test"

    def test_listener_called_on_clear(self):
        """Test that listener is called when registry is cleared."""
        registry = Registry()
        registry.register(RegistryEntry(name="test"))

        listener = Mock()
        registry.add_listener(listener)
        registry.clear()

        listener.assert_called_once()
        event = listener.call_args[0][0]
        assert event.event_type == "cleared"
        assert event.entry is None

    def test_multiple_listeners(self):
        """Test that multiple listeners are all called."""
        registry = Registry()
        listener1 = Mock()
        listener2 = Mock()
        listener3 = Mock()

        registry.add_listener(listener1)
        registry.add_listener(listener2)
        registry.add_listener(listener3)

        registry.register(RegistryEntry(name="test"))

        listener1.assert_called_once()
        listener2.assert_called_once()
        listener3.assert_called_once()

    def test_duplicate_listener_not_added_twice(self):
        """Test that same listener is not added twice."""
        registry = Registry()
        listener = Mock()

        registry.add_listener(listener)
        registry.add_listener(listener)

        registry.register(RegistryEntry(name="test"))

        # Called exactly once, not twice
        listener.assert_called_once()

    def test_listener_receives_correct_entry(self):
        """Test that listener receives complete entry information."""
        registry = Registry()
        received_events = []

        def capture_event(event: RegistryEvent):
            received_events.append(event)

        registry.add_listener(capture_event)

        entry = RegistryEntry(
            name="test",
            description="Test entry",
            tags=["foo", "bar"],
            owner="alice",
            source_ref="/path/to/file",
        )
        registry.register(entry)

        assert len(received_events) == 1
        event = received_events[0]
        assert event.entry.name == "test"
        assert event.entry.description == "Test entry"
        assert event.entry.tags == ["foo", "bar"]
        assert event.entry.owner == "alice"
        assert event.entry.source_ref == "/path/to/file"

    def test_listener_error_does_not_crash(self):
        """Test that listener exceptions are caught."""
        registry = Registry()

        def failing_listener(event):
            raise ValueError("Listener error")

        registry.add_listener(failing_listener)

        # Should not raise
        registry.register(RegistryEntry(name="test"))


class TestFileSystemSourceListeners:
    """Test FileSystemSource listener functionality."""

    def test_source_emits_refreshed_event(self):
        """Test that source emits refreshed event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "test.prompt").write_text("content")

            listener = Mock()
            source = FileSystemSource(tmpdir)
            source.add_listener(listener)

            # First call from init is already done, so refresh
            source.refresh()

            listener.assert_called()
            event_type = listener.call_args[0][0]
            assert event_type == "refreshed"

    def test_source_listener_on_init(self):
        """Test that listener is called during initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "test.prompt").write_text("content")

            listener = Mock()
            source = FileSystemSource(tmpdir)
            source.add_listener(listener)

            # Listener added after init, so no call yet
            listener.assert_not_called()

            # Now refresh should call it
            source.refresh()
            listener.assert_called_once()

    def test_multiple_source_listeners(self):
        """Test multiple listeners on source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "test.prompt").write_text("content")

            listener1 = Mock()
            listener2 = Mock()

            source = FileSystemSource(tmpdir)
            source.add_listener(listener1)
            source.add_listener(listener2)

            source.refresh()

            listener1.assert_called()
            listener2.assert_called()

    def test_remove_source_listener(self):
        """Test removing a listener from source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "test.prompt").write_text("content")

            listener = Mock()
            source = FileSystemSource(tmpdir)
            source.add_listener(listener)
            source.remove_listener(listener)

            source.refresh()

            listener.assert_not_called()


@pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
class TestDatabaseSourceListeners:
    """Test DatabaseSource listener functionality."""

    def test_source_emits_refreshed_event(self):
        """Test that source emits refreshed event."""
        conn = sqlite3.connect(":memory:")
        listener = Mock()

        source = DatabaseSource(conn)
        source.add_listener(listener)

        source.refresh()

        listener.assert_called()
        event_type = listener.call_args[0][0]
        assert event_type == "refreshed"

    def test_source_emits_prompt_saved_event(self):
        """Test that source emits prompt_saved event."""
        conn = sqlite3.connect(":memory:")
        listener = Mock()

        source = DatabaseSource(conn)
        source.add_listener(listener)

        source.save_prompt(name="test", content="content")

        # Should be called at least twice: once for refresh in save_prompt
        assert listener.call_count >= 1
        # Last call should be prompt_saved
        last_event = listener.call_args[0][0]
        assert last_event == "prompt_saved"


class TestListenerIntegration:
    """Test listener integration across modules."""

    def test_registry_event_dataclass(self):
        """Test RegistryEvent dataclass."""
        entry = RegistryEntry(name="test")
        event = RegistryEvent(event_type="registered", entry=entry)

        assert event.event_type == "registered"
        assert event.entry.name == "test"
        assert event.name is None

    def test_registry_event_with_name(self):
        """Test RegistryEvent with name for unregister."""
        event = RegistryEvent(event_type="unregistered", name="test_prompt")

        assert event.event_type == "unregistered"
        assert event.name == "test_prompt"
        assert event.entry is None

    def test_listener_tracking_changes(self):
        """Test using listener to track all registry changes."""
        registry = Registry()
        changes = []

        def track_changes(event: RegistryEvent):
            changes.append(event.event_type)

        registry.add_listener(track_changes)

        registry.register(RegistryEntry(name="a"))
        registry.register(RegistryEntry(name="b"))
        registry.unregister("a")
        registry.clear()

        assert changes == ["registered", "registered", "unregistered", "cleared"]

    def test_filesystem_listener_tracking_refreshes(self):
        """Test using listener to track filesystem refreshes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "test.prompt").write_text("v1")

            refreshes = []

            def track_refreshes(event_type: str):
                if event_type == "refreshed":
                    refreshes.append(event_type)

            source = FileSystemSource(tmpdir)
            source.add_listener(track_refreshes)

            # Initial refresh in __init__ already done
            source.refresh()
            source.refresh()

            assert len(refreshes) == 2

    @pytest.mark.skip(reason="Requires PostgreSQL (not supported with SQLite)")
    def test_database_listener_tracking_saves(self):
        """Test using listener to track database saves."""
        conn = sqlite3.connect(":memory:")
        saves = []

        def track_saves(event_type: str):
            if event_type == "prompt_saved":
                saves.append(event_type)

        source = DatabaseSource(conn)
        source.add_listener(track_saves)

        source.save_prompt(name="p1", content="c1")
        source.save_prompt(name="p2", content="c2")

        assert len(saves) == 2
