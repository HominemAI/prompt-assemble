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

    def _resolve_variable_value(self, value: Any) -> str:
        """
        Convert a variable value (string or tagged dict) to its rendered string.

        Args:
            value: Either a string or a dict with 'value' and optional 'tag' keys

        Returns:
            Rendered string (with XML tags if present)
        """
        if isinstance(value, dict) and "value" in value:
            tag = value.get("tag")
            val_str = str(value["value"])
            if tag:
                return f"<{tag}>\n  {val_str}\n</{tag}>"
            return val_str
        return str(value)

    def _resolve_variable_sets(
        self,
        prompt_name: str,
        additional_set_ids: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Build merged variables from variable sets.

        Priority (lowest to highest):
          1. Subscribed sets (in subscription order)
          2. additional_set_ids (in given order)
          3. Per-prompt per-set overrides (applied on top of each set)

        Args:
            prompt_name: Prompt name to get subscriptions for
            additional_set_ids: Additional variable set IDs to include

        Returns:
            Merged variables dict with all values as strings
        """
        merged = {}

        # 1. Load subscribed sets
        for vs in self.get_active_variable_sets(prompt_name):
            overrides = self.get_variable_overrides(prompt_name, vs["id"])
            variables = {**vs["variables"], **overrides}
            for key, value in variables.items():
                merged[key] = self._resolve_variable_value(value)

        # 2. Load additional sets
        for set_id in (additional_set_ids or []):
            vs = self.get_variable_set(set_id)
            if vs:
                overrides = self.get_variable_overrides(prompt_name, set_id)
                variables = {**vs["variables"], **overrides}
                for key, value in variables.items():
                    merged[key] = self._resolve_variable_value(value)

        return merged

    def render(
            self,
            name: str,
            variables: Optional[Dict[str, Any]] = None,
            recursive: bool = True,
            max_depth: int = 10,
            owner: Optional[str] = None,
            tags: Optional[List[str]] = None,
            match_type: str = "exact",
            empty_render: str = "",
            variable_sets: Optional[List[str]] = None,
    ) -> str:
        """
        Load and render a prompt with variable substitution.

        Args:
            name: Prompt name (or partial name pattern if match_type='partial')
            variables: Dictionary of variable_name -> value
            recursive: Whether to resolve nested sigils
            max_depth: Maximum recursion depth
            owner: Filter by owner (optional)
            tags: Filter by tags (AND intersection, optional)
            match_type: "exact" (default) or "partial" for name matching
            empty_render: Default content to render if result is empty (default: "")
            variable_sets: List of variable set IDs to include (merged with subscriptions, lower priority than explicit variables)

        Returns:
            Rendered prompt, or empty_render if result is empty

        Raises:
            PromptNotFoundError: If prompt not found or multiple matches
            SubstitutionError: If substitution fails

        Examples:
            # Exact match
            render("my_prompt", variables={...})

            # Partial name match
            render("system", match_type="partial", variables={...})

            # By owner
            render("prompt", owner="john", variables={...})

            # By tags
            render("prompt", tags=["prod", "critical"], variables={...})

            # Combined search
            render("system", match_type="partial", owner="john",
                   tags=["prod"], variables={...})

            # With default content if empty
            render("prompt", variables={...}, empty_render="[No prompt found]")

            # With variable sets
            render("prompt", variable_sets=["set_id_1", "set_id_2"], variables={...})
        """
        # Resolve the actual prompt name using search if needed
        resolved_name = self._resolve_prompt_name(name, owner=owner, tags=tags, match_type=match_type)

        # Get raw content
        raw = self.get_raw(resolved_name)

        # Build merged variables: variable_sets (if provided) + subscriptions < explicit variables (highest priority)
        set_vars = self._resolve_variable_sets(resolved_name, variable_sets)
        explicit_vars = serialize_variables(variables or {})
        str_vars = {**set_vars, **explicit_vars}  # explicit vars always win

        # Build component resolver (loads prompts on demand)
        def _get_component(comp_name: str) -> str:
            return self.get_raw(comp_name)

        # Build tag resolver (finds prompts by tag, in reverse insertion order)
        def _resolve_tags(tags: List[str]) -> List[str]:
            matching = self.find_by_tag(*tags)
            # Return in reverse order (most recently loaded first)
            return list(reversed(matching))

        # Perform substitution
        result = substitute(
            raw,
            variables=str_vars,
            recursive=recursive,
            max_depth=max_depth,
            component_resolver=_get_component,
            tag_resolver=_resolve_tags,
        )

        # Return empty_render if result is empty, otherwise return result
        return empty_render if not result.strip() else result

    def find_by_tag(self, *tags: str) -> List[str]:
        """
        Find all prompt names matching ALL tags (AND intersection).

        Args:
            tags: One or more tags to search for

        Returns:
            List of prompt names matching all tags, in insertion order
        """
        return self.source.find_by_tag(*tags)

    def find_by_owner(self, owner: str) -> List[str]:
        """
        Find all prompt names owned by a specific owner.

        Args:
            owner: Owner name to search for

        Returns:
            List of prompt names owned by the owner, in insertion order
        """
        return self.source.find_by_owner(owner)

    def find_by_name(self, name_pattern: str) -> List[str]:
        """
        Find all prompt names matching a name pattern (partial match).

        Args:
            name_pattern: Partial name to search for (case-insensitive)

        Returns:
            List of prompt names containing the pattern, in insertion order
        """
        pattern = name_pattern.lower()
        return [name for name in self.list() if pattern in name.lower()]

    def _resolve_prompt_name(
        self,
        name: str,
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None,
        match_type: str = "exact",
    ) -> str:
        """
        Resolve a prompt name, optionally searching by pattern, owner, or tags.

        Args:
            name: Prompt name or pattern
            owner: Filter by owner
            tags: Filter by tags (AND intersection)
            match_type: "exact" or "partial"

        Returns:
            Resolved prompt name

        Raises:
            PromptNotFoundError: If no matches or multiple matches found
        """
        # Start with all prompts or search by name
        if match_type == "partial":
            candidates = self.find_by_name(name)
        else:
            # For exact match, check if it exists first
            if name in self.list():
                candidates = [name]
            else:
                candidates = []

        # Filter by owner if specified
        if owner is not None:
            owner_prompts = set(self.find_by_owner(owner))
            candidates = [c for c in candidates if c in owner_prompts]

        # Filter by tags if specified (AND intersection)
        if tags:
            tag_prompts = set(self.find_by_tag(*tags))
            candidates = [c for c in candidates if c in tag_prompts]

        # Handle results
        if len(candidates) == 0:
            filters = []
            if match_type == "partial":
                filters.append(f"name matching '{name}'")
            else:
                filters.append(f"name '{name}'")
            if owner:
                filters.append(f"owner '{owner}'")
            if tags:
                filters.append(f"tags {tags}")
            filter_str = " and ".join(filters)
            raise PromptNotFoundError(f"No prompts found matching: {filter_str}")

        if len(candidates) > 1:
            filters = []
            if match_type == "partial":
                filters.append(f"name pattern '{name}'")
            if owner:
                filters.append(f"owner '{owner}'")
            if tags:
                filters.append(f"tags {tags}")
            filter_str = " with ".join(filters) if filters else "search"

            raise PromptNotFoundError(
                f"Multiple prompts found ({len(candidates)}) matching {filter_str}: {candidates}. "
                f"Please be more specific."
            )

        return candidates[0]

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

    def create_variable_set(self, name: str, variables: Optional[Dict[str, str]] = None, owner: Optional[str] = None) -> str:
        """
        Create a new variable set.

        Args:
            name: Variable set name
            variables: Dictionary of variable_name -> value
            owner: Optional owner for scoped variable sets (None = global)

        Returns:
            Variable set ID

        Raises:
            ReadOnlySourceError: If source does not support variable sets
        """
        if not hasattr(self.source, "create_variable_set"):
            raise ReadOnlySourceError(
                f"{type(self.source).__name__} does not support variable sets"
            )
        return self.source.create_variable_set(name, variables, owner=owner)

    def get_variable_set(self, set_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a variable set by ID.

        Args:
            set_id: Variable set ID

        Returns:
            Variable set with id, name, and variables dict, or None if not found
        """
        if not hasattr(self.source, "get_variable_set"):
            return None
        return self.source.get_variable_set(set_id)

    def list_variable_sets(self) -> List[Dict[str, Any]]:
        """
        List all variable sets (global and all scoped).

        Returns:
            List of variable sets with id, name, owner, and variables
        """
        if not hasattr(self.source, "list_variable_sets"):
            return []
        return self.source.list_variable_sets()

    def list_global_variable_sets(self) -> List[Dict[str, Any]]:
        """
        List only global (unscoped) variable sets.

        Returns:
            List of global variable sets
        """
        if not hasattr(self.source, "list_global_variable_sets"):
            return []
        return self.source.list_global_variable_sets()

    def list_variable_sets_by_owner(self, owner: str) -> List[Dict[str, Any]]:
        """
        List variable sets scoped to a specific owner.

        Args:
            owner: Owner name

        Returns:
            List of variable sets owned by the specified owner
        """
        if not hasattr(self.source, "list_variable_sets_by_owner"):
            return []
        return self.source.list_variable_sets_by_owner(owner)

    def get_available_variable_sets(self, owner: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get variable sets available to a prompt owner.
        Returns global sets + sets scoped to the owner.

        Args:
            owner: Optional owner name (if None, returns only global sets)

        Returns:
            List of available variable sets
        """
        if not hasattr(self.source, "get_available_variable_sets"):
            return []
        return self.source.get_available_variable_sets(owner)

    def update_variable_set(
        self, set_id: str, name: Optional[str] = None, variables: Optional[Dict[str, str]] = None, owner: Optional[str] = None
    ) -> None:
        """
        Update a variable set.

        Args:
            set_id: Variable set ID
            name: New name (if changing)
            variables: New variables dict (if changing)
            owner: New owner (if changing scope)

        Raises:
            ReadOnlySourceError: If source does not support variable sets
        """
        if not hasattr(self.source, "update_variable_set"):
            raise ReadOnlySourceError(
                f"{type(self.source).__name__} does not support variable sets"
            )
        self.source.update_variable_set(set_id, name, variables, owner=owner)

    def delete_variable_set(self, set_id: str) -> None:
        """
        Delete a variable set.

        Args:
            set_id: Variable set ID

        Raises:
            ReadOnlySourceError: If source does not support variable sets
        """
        if not hasattr(self.source, "delete_variable_set"):
            raise ReadOnlySourceError(
                f"{type(self.source).__name__} does not support variable sets"
            )
        self.source.delete_variable_set(set_id)

    def get_active_variable_sets(self, prompt_id: str) -> List[Dict[str, Any]]:
        """
        Get variable sets linked to a prompt.

        Args:
            prompt_id: Prompt ID/name

        Returns:
            List of active variable sets for the prompt
        """
        if not hasattr(self.source, "get_active_variable_sets"):
            return []
        return self.source.get_active_variable_sets(prompt_id)

    def set_active_variable_sets(self, prompt_id: str, set_ids: List[str]) -> None:
        """
        Link variable sets to a prompt.

        Args:
            prompt_id: Prompt ID/name
            set_ids: List of variable set IDs to link

        Raises:
            ReadOnlySourceError: If source does not support variable sets
        """
        if not hasattr(self.source, "set_active_variable_sets"):
            raise ReadOnlySourceError(
                f"{type(self.source).__name__} does not support variable sets"
            )
        self.source.set_active_variable_sets(prompt_id, set_ids)

    def get_variable_overrides(self, prompt_id: str, set_id: str) -> Dict[str, str]:
        """
        Get variable overrides for a prompt's variable set.

        Args:
            prompt_id: Prompt ID/name
            set_id: Variable set ID

        Returns:
            Dictionary of variable overrides
        """
        if not hasattr(self.source, "get_variable_overrides"):
            return {}
        return self.source.get_variable_overrides(prompt_id, set_id)

    def set_variable_overrides(self, prompt_id: str, set_id: str, overrides: Dict[str, str]) -> None:
        """
        Set variable overrides for a prompt's variable set.

        Args:
            prompt_id: Prompt ID/name
            set_id: Variable set ID
            overrides: Dictionary of variable overrides

        Raises:
            ReadOnlySourceError: If source does not support variable sets
        """
        if not hasattr(self.source, "set_variable_overrides"):
            raise ReadOnlySourceError(
                f"{type(self.source).__name__} does not support variable sets"
            )
        self.source.set_variable_overrides(prompt_id, set_id, overrides)

    def add_variable_to_set(self, set_id: str, key: str, value: str, tag: Optional[str] = None) -> None:
        """
        Add or update a single variable in a set without modifying others.

        Args:
            set_id: Variable set ID
            key: Variable key
            value: Variable value (string or value part of tagged dict)
            tag: Optional XML wrapper tag for the variable

        Raises:
            ReadOnlySourceError: If source does not support variable sets
        """
        if not hasattr(self.source, "add_variable_to_set"):
            raise ReadOnlySourceError(
                f"{type(self.source).__name__} does not support variable sets"
            )
        self.source.add_variable_to_set(set_id, key, value, tag=tag)

    def remove_variable_from_set(self, set_id: str, key: str) -> None:
        """
        Remove a single variable from a set.

        Args:
            set_id: Variable set ID
            key: Variable key to remove

        Raises:
            ReadOnlySourceError: If source does not support variable sets
        """
        if not hasattr(self.source, "remove_variable_from_set"):
            raise ReadOnlySourceError(
                f"{type(self.source).__name__} does not support variable sets"
            )
        self.source.remove_variable_from_set(set_id, key)

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
        if not hasattr(self.source, "find_variable_sets"):
            return []
        return self.source.find_variable_sets(name=name, owner=owner, match_type=match_type)


def bulk_import(
    source: "PromptProvider",
    target: "PromptProvider",
    overwrite: bool = False,
    verbose: bool = False,
    batch_size: int = 200,
) -> Dict[str, Any]:
    """
    Bulk import all prompts from source to target with metadata.

    Transfers prompts with all metadata (content, description, tags, owner)
    from source provider to target provider. Target must support save_prompt.

    Uses batch processing to commit in chunks (default 200 prompts per transaction)
    for improved performance on large imports.

    Args:
        source: Source PromptProvider to import from
        target: Target PromptProvider to import to (must support save_prompt)
        overwrite: If True, overwrite existing prompts. If False (default), skip existing
        verbose: If True, log each import operation
        batch_size: Number of prompts to save per transaction (default: 200)

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

    # Load all source prompts and target names once
    source_names = source.list()
    target_names = set(target.list()) if not overwrite else set()

    # Build list of prompts to import (filter in-memory)
    to_import = []
    for name in source_names:
        if overwrite or name not in target_names:
            to_import.append(name)
        else:
            if verbose:
                logger.info(f"Skipping existing prompt: {name}")
            results["skipped"] += 1

    # Check if target supports batch operations (faster for large imports)
    has_batch_save = hasattr(target.source, "batch_save_prompts")

    # Process in batches
    for batch_start in range(0, len(to_import), batch_size):
        batch = to_import[batch_start : batch_start + batch_size]

        if has_batch_save:
            # Use batch save for better performance
            batch_prompts = []
            for name in batch:
                try:
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

                    batch_prompts.append({
                        "name": name,
                        "content": content,
                        **metadata
                    })
                except Exception as e:
                    results["errors"] += 1
                    error_detail = {"name": name, "error": str(e)}
                    results["errors_list"].append(error_detail)
                    logger.error(f"Error preparing prompt '{name}': {e}")

            # Save entire batch in one transaction
            if batch_prompts:
                try:
                    saved = target.source.batch_save_prompts(batch_prompts)
                    results["imported"] += saved
                    if verbose:
                        logger.info(f"Batch imported {saved} prompts")
                except Exception as e:
                    logger.error(f"Error in batch save: {e}")
                    results["errors"] += len(batch_prompts)
        else:
            # Fallback to individual saves for sources without batch support
            for name in batch:
                try:
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
