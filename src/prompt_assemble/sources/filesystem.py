"""File system source for prompts."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..exceptions import PromptNotFoundError, SourceConnectionError, ReadOnlySourceError
from ..registry import Registry, RegistryEntry
from .base import PromptSource

logger = logging.getLogger(__name__)


class FileSystemSource(PromptSource):
    """Load prompts from the file system."""

    def __init__(self, root: str | Path):
        """
        Initialize FileSystemSource.

        Args:
            root: Root directory to search for .prompt files

        Raises:
            SourceConnectionError: If root directory doesn't exist
        """
        super().__init__()
        self.root = Path(root)
        if not self.root.exists():
            raise SourceConnectionError(f"Root directory does not exist: {root}")
        if not self.root.is_dir():
            raise SourceConnectionError(f"Root is not a directory: {root}")

        self._registry = Registry()
        self._content_store: Dict[str, str] = {}
        self.refresh()

    def refresh(self) -> None:
        """Refresh prompts from disk."""
        self._registry.clear()
        self._content_store.clear()

        # Walk root directory in sorted order for stable ordering
        for dirpath, dirnames, filenames in self._walk_sorted(self.root):
            dirpath = Path(dirpath)

            # Load _registry.json if it exists
            dir_registry = self._load_dir_registry(dirpath)

            # Process .prompt files in this directory
            for filename in sorted(filenames):
                if not filename.endswith(".prompt"):
                    continue

                filepath = dirpath / filename
                stem = filename[:-7]  # Remove .prompt extension

                try:
                    # Build name from path
                    name = self._build_name(filepath)

                    # Read content
                    content = filepath.read_text(encoding="utf-8")
                    self._content_store[name] = content

                    # Create or load registry entry
                    if stem in dir_registry:
                        entry_data = dir_registry[stem]
                        entry = RegistryEntry(
                            name=name,
                            description=entry_data.get("description", ""),
                            tags=entry_data.get("tags", []),
                            owner=entry_data.get("owner"),
                            source_ref=str(filepath),
                        )
                    else:
                        entry = RegistryEntry(
                            name=name,
                            source_ref=str(filepath),
                        )

                    self._registry.register(entry)
                except Exception as e:
                    logger.warning(f"Failed to load prompt {filepath}: {e}")

        # Emit refresh event
        self._emit("refreshed")

    def get_raw(self, name: str) -> str:
        """Get raw prompt content by name."""
        if name not in self._content_store:
            raise PromptNotFoundError(f"Prompt not found: {name}")
        return self._content_store[name]

    def find_by_tag(self, *tags: str) -> List[str]:
        """Find all prompt names matching ALL tags (AND intersection)."""
        return self._registry.find_by_tags(*tags)

    def list(self) -> List[str]:
        """List all available prompt names."""
        return self._registry.list_names()

    def is_stale(self) -> bool:
        """Check if any files have been modified since last refresh."""
        for dirpath, dirnames, filenames in self._walk_sorted(self.root):
            dirpath = Path(dirpath)
            for filename in filenames:
                if not filename.endswith(".prompt"):
                    continue
                filepath = dirpath / filename
                # This is a simple check - could be enhanced with mtime tracking
                name = self._build_name(filepath)
                if name not in self._content_store:
                    return True
        return False

    def _build_name(self, filepath: Path) -> str:
        """Build a prompt name from a file path."""
        relative = filepath.relative_to(self.root)
        parts = list(relative.parts[:-1])  # All but filename
        stem = relative.stem  # Filename without extension

        parts.append(stem)

        # Convert to underscore-joined name
        name_parts = []
        for part in parts:
            normalized = part.replace("-", "_").replace(" ", "_")
            name_parts.append(normalized)

        return "_".join(name_parts)

    def _load_dir_registry(self, directory: Path) -> dict:
        """Load _registry.json from a directory."""
        registry_file = directory / "_registry.json"
        if not registry_file.exists():
            return {}

        try:
            data = json.loads(registry_file.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning(f"Failed to load registry from {registry_file}: {e}")
            return {}

    def save_prompt(
        self,
        name: str,
        content: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        owner: Optional[str] = None,
    ) -> None:
        """
        Save or update a prompt.

        Args:
            name: Prompt name
            content: Prompt content
            description: Prompt description
            tags: List of tags
            owner: Owner identifier
        """
        if tags is None:
            tags = []

        # Try to find existing prompt file
        existing_path = self._find_prompt_file(name)

        if existing_path:
            # Update existing file
            filepath = existing_path
            registry_dir = filepath.parent
        else:
            # Create new file at root level
            filepath = self.root / f"{name}.prompt"
            registry_dir = self.root

        # Write content
        filepath.write_text(content, encoding="utf-8")

        # Update registry.json in the appropriate directory
        registry_file = registry_dir / "_registry.json"
        if registry_file.exists():
            try:
                registry_data = json.loads(registry_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to load existing registry: {e}")
                registry_data = {}
        else:
            registry_data = {}

        # Update or create entry (use stem for the key)
        stem = filepath.stem
        registry_data[stem] = {
            "description": description,
            "tags": tags,
            "owner": owner,
        }

        # Write updated registry
        registry_file.write_text(
            json.dumps(registry_data, indent=2),
            encoding="utf-8",
        )

        # Refresh and emit event
        self.refresh()
        self._emit("prompt_saved")

    def delete_prompt(self, name: str) -> None:
        """
        Delete a prompt and its metadata.

        Args:
            name: Prompt name

        Raises:
            PromptNotFoundError: If prompt not found
        """
        # Find the prompt file
        filepath = self._find_prompt_file(name)
        if not filepath:
            raise PromptNotFoundError(f"Prompt not found: {name}")

        # Remove the file
        filepath.unlink()

        # Update registry.json in the appropriate directory
        registry_dir = filepath.parent
        registry_file = registry_dir / "_registry.json"

        if registry_file.exists():
            try:
                registry_data = json.loads(registry_file.read_text(encoding="utf-8"))
                stem = filepath.stem
                if stem in registry_data:
                    del registry_data[stem]
                    # Write updated registry
                    registry_file.write_text(
                        json.dumps(registry_data, indent=2),
                        encoding="utf-8",
                    )
            except Exception as e:
                logger.warning(f"Failed to update registry after delete: {e}")

        # Refresh and emit event
        self.refresh()
        self._emit("prompt_deleted")

    def _find_prompt_file(self, name: str) -> Optional[Path]:
        """
        Find a prompt file by name, searching the tree.

        Looks for both the exact name and with underscore replacements.
        Returns the first match found.

        Args:
            name: Prompt name

        Returns:
            Path to the prompt file or None if not found
        """
        # First, check in content store (from last refresh)
        if name in self._content_store:
            # Find the actual file path
            for dirpath, dirnames, filenames in self._walk_sorted(self.root):
                dirpath = Path(dirpath)
                for filename in filenames:
                    if not filename.endswith(".prompt"):
                        continue
                    filepath = dirpath / filename
                    if self._build_name(filepath) == name:
                        return filepath
        return None

    @staticmethod
    def _walk_sorted(root: Path):
        """Walk directory tree with sorted directories and files."""
        dirs = []
        files = []

        for item in sorted(root.iterdir()):
            if item.is_dir():
                dirs.append(item)
            else:
                files.append(item.name)

        yield str(root), [d.name for d in dirs], files

        for d in dirs:
            yield from FileSystemSource._walk_sorted(d)
