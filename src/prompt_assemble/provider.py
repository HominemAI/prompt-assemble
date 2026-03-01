"""High-level provider for loading and rendering prompts."""

from typing import Any, Dict, Optional

from .core import substitute
from .exceptions import PromptNotFoundError
from .serialization import serialize_variables
from .sources.base import PromptSource


class PromptProvider:
    """Unified interface for loading and rendering prompts."""

    def __init__(self, source: PromptSource):
        """
        Initialize PromptProvider.

        Args:
            source: PromptSource implementation to use
        """
        self.source = source

    def get_raw(self, name: str) -> str:
        """
        Get raw (unprocessed) prompt content.

        Args:
            name: Prompt name

        Returns:
            Raw prompt content

        Raises:
            PromptNotFoundError: If prompt not found
        """
        return self.source.get_raw(name)

    def render(
        self,
        name: str,
        variables: Optional[Dict[str, Any]] = None,
        recursive: bool = True,
        max_depth: int = 10,
    ) -> str:
        """
        Load and render a prompt with variable substitution.

        Args:
            name: Prompt name
            variables: Dictionary of variable_name -> value
            recursive: Whether to resolve nested sigils
            max_depth: Maximum recursion depth

        Returns:
            Rendered prompt

        Raises:
            PromptNotFoundError: If prompt not found
            SubstitutionError: If substitution fails
        """
        # Get raw content
        raw = self.get_raw(name)

        # Serialize all variables to strings
        if variables is None:
            variables = {}
        str_vars = serialize_variables(variables)

        # Build component resolver (loads prompts on demand)
        def _get_component(comp_name: str) -> str:
            return self.get_raw(comp_name)

        # Build tag resolver (finds prompts by tag, in reverse insertion order)
        def _resolve_tags(tags: list[str]) -> list[str]:
            matching = self.find_by_tag(*tags)
            # Return in reverse order (most recently loaded first)
            return list(reversed(matching))

        # Perform substitution
        return substitute(
            raw,
            variables=str_vars,
            recursive=recursive,
            max_depth=max_depth,
            component_resolver=_get_component,
            tag_resolver=_resolve_tags,
        )

    def find_by_tag(self, *tags: str) -> list[str]:
        """
        Find all prompt names matching ALL tags (AND intersection).

        Args:
            tags: One or more tags to search for

        Returns:
            List of prompt names matching all tags, in insertion order
        """
        return self.source.find_by_tag(*tags)

    def list(self) -> list[str]:
        """
        List all available prompt names.

        Returns:
            List of prompt names in insertion order
        """
        return self.source.list()
