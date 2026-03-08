"""In-memory registry for prompt metadata."""

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional


@dataclass
class RegistryEntry:
    """Metadata entry for a prompt."""

    name: str
    description: str = ""
    tags: list = field(default_factory=list)
    owner: Optional[str] = None
    source_ref: Optional[str] = None  # file path or DB UUID


@dataclass
class RegistryEvent:
    """Event emitted by registry when entries change."""

    event_type: str  # "registered", "unregistered", "cleared"
    entry: Optional[RegistryEntry] = None  # None for "cleared" event
    name: Optional[str] = None  # For unregister, the name that was removed


RegistryListener = Callable[[RegistryEvent], None]


class Registry:
    """In-memory registry for prompt metadata with listener support."""

    def __init__(self):
        """Initialize the registry."""
        self._entries: dict[str, RegistryEntry] = {}
        self._listeners: List[RegistryListener] = []

    def add_listener(self, listener: RegistryListener) -> None:
        """
        Add a listener to be notified of registry changes.

        Args:
            listener: Callable that receives RegistryEvent
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: RegistryListener) -> None:
        """
        Remove a listener from the registry.

        Args:
            listener: The listener to remove
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _emit(self, event: RegistryEvent) -> None:
        """
        Emit an event to all registered listeners.

        Args:
            event: The event to emit
        """
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                # Log but don't fail on listener errors
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Error in registry listener: {e}")

    def register(self, entry: RegistryEntry) -> None:
        """Register a new prompt entry."""
        self._entries[entry.name] = entry
        self._emit(RegistryEvent(event_type="registered", entry=entry))

    def unregister(self, name: str) -> None:
        """Remove a prompt entry from the registry."""
        if name in self._entries:
            del self._entries[name]
            self._emit(RegistryEvent(event_type="unregistered", name=name))

    def get(self, name: str) -> Optional[RegistryEntry]:
        """Get a registry entry by name."""
        return self._entries.get(name)

    def find_by_tags(self, *tags: str) -> List[str]:
        """Find all prompt names matching ALL tags (AND intersection)."""
        if not tags:
            return self.list_names()

        matching_names = []
        for name, entry in self._entries.items():
            if all(tag in entry.tags for tag in tags):
                matching_names.append(name)

        return matching_names

    def find_by_owner(self, owner: str) -> List[str]:
        """Find all prompt names owned by a specific owner."""
        matching_names = []
        for name, entry in self._entries.items():
            if entry.owner == owner:
                matching_names.append(name)

        return matching_names

    def list_names(self) -> List[str]:
        """List all registered prompt names in insertion order."""
        return list(self._entries.keys())

    def clear(self) -> None:
        """Clear all entries from the registry."""
        self._entries.clear()
        self._emit(RegistryEvent(event_type="cleared"))
