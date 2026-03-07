"""High-level provider for loading and rendering prompts."""

from typing import Any, Callable, Dict, List, Optional
import logging

from .core import substitute
from .exceptions import PromptNotFoundError, ReadOnlySourceError
from .serialization import serialize_variables
from .sources.base import PromptSource

logger = logging.getLogger(__name__)


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
        def _resolve_tags(tags: List[str]) -> List[str]:
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

    def find_by_tag(self, *tags: str) -> List[str]:
        """
        Find all prompt names matching ALL tags (AND intersection).

        Args:
            tags: One or more tags to search for

        Returns:
            List of prompt names matching all tags, in insertion order
        """
        return self.source.find_by_tag(*tags)

    def list(self) -> List[str]:
        """
        List all available prompt names.

        Returns:
            List of prompt names in insertion order
        """
        return self.source.list()

    def save_prompt(
        self,
        name: str,
        content: str,
        **kwargs,
    ) -> None:
        """
        Save or update a prompt.

        Args:
            name: Prompt name
            content: Prompt content
            **kwargs: Additional arguments (description, tags, owner, etc.)

        Raises:
            ReadOnlySourceError: If source does not support saving
        """
        if not hasattr(self.source, "save_prompt"):
            raise ReadOnlySourceError(
                f"{type(self.source).__name__} does not support saving"
            )
        return self.source.save_prompt(name, content, **kwargs)

    def delete_prompt(self, name: str) -> None:
        """
        Delete a prompt.

        Args:
            name: Prompt name

        Raises:
            ReadOnlySourceError: If source does not support deleting
            PromptNotFoundError: If prompt not found
        """
        if not hasattr(self.source, "delete_prompt"):
            raise ReadOnlySourceError(
                f"{type(self.source).__name__} does not support deleting"
            )
        self.source.delete_prompt(name)


def bulk_import(
    source: "PromptProvider",
    target: "PromptProvider",
    skip_existing: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Bulk import all prompts from source to target with metadata.

    Transfers prompts with all metadata (content, description, tags, owner)
    from source provider to target provider. Target must support save_prompt.

    Args:
        source: Source PromptProvider to import from
        target: Target PromptProvider to import to (must support save_prompt)
        skip_existing: If True, skip prompts already in target
        verbose: If True, log each import operation

    Returns:
        Dict with import statistics:
        - imported: Number of prompts successfully imported
        - skipped: Number of prompts skipped (already exist or other reasons)
        - errors: Number of prompts with errors
        - errors_list: List of error details (name, error message)

    Raises:
        ReadOnlySourceError: If target doesn't support save_prompt
    """
    # Verify target supports saving
    if not hasattr(target.source, "save_prompt"):
        raise ReadOnlySourceError(
            f"{type(target.source).__name__} does not support saving"
        )

    results = {
        "imported": 0,
        "skipped": 0,
        "errors": 0,
        "errors_list": [],
    }

    target_names = set(target.list()) if skip_existing else set()

    for name in source.list():
        try:
            # Skip if already exists and skip_existing is True
            if skip_existing and name in target_names:
                if verbose:
                    logger.info(f"Skipping existing prompt: {name}")
                results["skipped"] += 1
                continue

            # Get content from source
            content = source.get_raw(name)

            # Get metadata from source's registry if available
            metadata = {
                "description": "",
                "tags": [],
                "owner": None,
            }

            if hasattr(source.source, "_registry"):
                entry = source.source._registry.get(name)
                if entry:
                    metadata = {
                        "description": entry.description,
                        "tags": entry.tags,
                        "owner": entry.owner,
                    }

            # Save to target with metadata
            target.save_prompt(name, content, **metadata)

            if verbose:
                logger.info(
                    f"Imported prompt '{name}' with {len(metadata.get('tags', []))} tags"
                )

            results["imported"] += 1

        except Exception as e:
            results["errors"] += 1
            error_detail = {"name": name, "error": str(e)}
            results["errors_list"].append(error_detail)
            logger.error(f"Error importing prompt '{name}': {e}")

    return results
