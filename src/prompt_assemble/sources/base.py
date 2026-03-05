"""Abstract base class for prompt sources."""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional

SourceListener = Callable[[str], None]  # event_type -> None


class PromptSource(ABC):
    """Abstract base class for prompt sources with listener support."""

    def __init__(self):
        """Initialize the source with listener support."""
        self._listeners: List[SourceListener] = []

    def add_listener(self, listener: SourceListener) -> None:
        """
        Add a listener to be notified of source events.

        Args:
            listener: Callable that receives event type string
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: SourceListener) -> None:
        """
        Remove a listener from the source.

        Args:
            listener: The listener to remove
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _emit(self, event_type: str) -> None:
        """
        Emit an event to all registered listeners.

        Args:
            event_type: The type of event (e.g., "refreshed", "prompt_added")
        """
        for listener in self._listeners:
            try:
                listener(event_type)
            except Exception as e:
                # Log but don't fail on listener errors
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Error in source listener: {e}")

    @abstractmethod
    def get_raw(self, name: str) -> str:
        """
        Get raw prompt content by name.

        Args:
            name: Prompt name

        Returns:
            Raw prompt content

        Raises:
            PromptNotFoundError: If prompt not found
        """
        pass

    @abstractmethod
    def find_by_tag(self, *tags: str) -> List[str]:
        """
        Find all prompt names matching ALL tags (AND intersection).

        Args:
            tags: One or more tags to search for

        Returns:
            List of prompt names matching all tags, in insertion order
        """
        pass

    @abstractmethod
    def list(self) -> List[str]:
        """
        List all available prompt names.

        Returns:
            List of prompt names in insertion order
        """
        pass

    @abstractmethod
    def refresh(self) -> None:
        """
        Refresh the source (e.g., reload from disk or database).

        This method should update internal state but not necessarily fetch
        all content into memory. Used to pick up external changes.
        """
        pass
