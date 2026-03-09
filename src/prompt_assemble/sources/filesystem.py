"""File system source for prompts."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        self._metadata_dir_cache: Optional[Path] = None
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
                    # Get prompt name (filename without extension)
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

    def find_by_owner(self, owner: str) -> List[str]:
        """Find all prompt names owned by a specific owner."""
        return self._registry.find_by_owner(owner)

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
        """Build a prompt name from a file path.

        The name is simply the filename without the .prompt extension,
        matching the UI's FileSystemBackend behavior. Directory structure
        is tracked separately in the registry's filePath field.
        """
        return filepath.stem

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
        increment_version: bool = True,
        revision_comment: Optional[str] = None,
    ) -> str:
        """
        Save or update a prompt.

        Args:
            name: Prompt name
            content: Prompt content
            description: Prompt description
            tags: List of tags
            owner: Owner identifier
            increment_version: Whether to save a version snapshot
            revision_comment: Optional comment for this revision

        Returns:
            Prompt name (as id equivalent)
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

        # Save version if requested
        if increment_version:
            self._save_prompt_version(name, content, revision_comment)

        # Refresh and emit event
        self.refresh()
        self._emit("prompt_saved")
        return name

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

    @property
    def _metadata_dir(self) -> Path:
        """Get or create the .prompt-assemble metadata directory."""
        if self._metadata_dir_cache is None:
            self._metadata_dir_cache = self.root / ".prompt-assemble"
            self._metadata_dir_cache.mkdir(exist_ok=True)
        return self._metadata_dir_cache

    def _load_json_store(self, filename: str) -> dict:
        """Load JSON from .prompt-assemble/<filename>."""
        filepath = self._metadata_dir / filename
        if not filepath.exists():
            return {}
        try:
            return json.loads(filepath.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load {filename}: {e}")
            return {}

    def _save_json_store(self, filename: str, data: dict) -> None:
        """Save JSON to .prompt-assemble/<filename>."""
        filepath = self._metadata_dir / filename
        filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _save_prompt_version(
        self, name: str, content: str, revision_comment: Optional[str] = None
    ) -> None:
        """Save a version snapshot for a prompt."""
        versions_dir = self._metadata_dir / "versions" / name
        versions_dir.mkdir(parents=True, exist_ok=True)

        # Find next version number
        existing_versions = []
        if versions_dir.exists():
            existing_versions = sorted(
                [int(f.stem) for f in versions_dir.glob("*.json") if f.stem.isdigit()]
            )

        next_version = (existing_versions[-1] + 1) if existing_versions else 1

        # Save version file
        version_data = {
            "version": next_version,
            "content": content,
            "revision_comment": revision_comment,
            "timestamp": self._get_timestamp(),
        }

        version_file = versions_dir / f"{next_version}.json"
        version_file.write_text(json.dumps(version_data, indent=2), encoding="utf-8")

        # Cap versions at 20 most recent
        if len(existing_versions) >= 20:
            versions_to_delete = len(existing_versions) - 19
            for old_version in existing_versions[:versions_to_delete]:
                (versions_dir / f"{old_version}.json").unlink()

    def get_prompt_version(self, name: str, version: Optional[int] = None) -> str:
        """
        Get a specific version of a prompt.

        Args:
            name: Prompt name
            version: Version number (None for latest)

        Returns:
            Prompt content

        Raises:
            PromptNotFoundError: If prompt or version not found
        """
        if version is None:
            # Return current content
            if name not in self._content_store:
                raise PromptNotFoundError(f"Prompt not found: {name}")
            return self._content_store[name]

        # Return historical version
        versions_dir = self._metadata_dir / "versions" / name
        version_file = versions_dir / f"{version}.json"

        if not version_file.exists():
            raise PromptNotFoundError(
                f"Prompt not found: {name} (version {version})"
            )

        try:
            data = json.loads(version_file.read_text(encoding="utf-8"))
            return data["content"]
        except Exception as e:
            raise PromptNotFoundError(
                f"Failed to read prompt version: {name} (version {version}): {e}"
            )

    def list_prompt_versions(self, name: str) -> List[Dict[str, Any]]:
        """
        List all versions of a prompt.

        Args:
            name: Prompt name

        Returns:
            List of {version, timestamp, revision_comment}

        Raises:
            PromptNotFoundError: If prompt not found
        """
        if name not in self._content_store:
            raise PromptNotFoundError(f"Prompt not found: {name}")

        versions_dir = self._metadata_dir / "versions" / name
        if not versions_dir.exists():
            return []

        versions = []
        for version_file in sorted(versions_dir.glob("*.json")):
            try:
                data = json.loads(version_file.read_text(encoding="utf-8"))
                versions.append({
                    "version": data["version"],
                    "timestamp": data.get("timestamp"),
                    "revision_comment": data.get("revision_comment"),
                })
            except Exception as e:
                logger.warning(f"Failed to read version file {version_file}: {e}")

        return sorted(versions, key=lambda x: x["version"])

    # Variable Sets Management Methods

    def create_variable_set(
        self, name: str, variables: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a new variable set.

        Args:
            name: Variable set name
            variables: Dict of key-value pairs

        Returns:
            Variable set ID
        """
        if variables is None:
            variables = {}

        sets = self._load_json_store("variable_sets.json")
        set_id = str(uuid.uuid4())

        sets[set_id] = {
            "id": set_id,
            "name": name,
            "variables": variables,
        }

        self._save_json_store("variable_sets.json", sets)
        return set_id

    def get_variable_set(self, set_id: str) -> Optional[Dict[str, Any]]:
        """Get a variable set by ID."""
        sets = self._load_json_store("variable_sets.json")
        return sets.get(set_id)

    def list_variable_sets(self) -> List[Dict[str, Any]]:
        """List all variable sets."""
        sets = self._load_json_store("variable_sets.json")
        return sorted(sets.values(), key=lambda x: x["name"])

    def update_variable_set(
        self,
        set_id: str,
        name: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
    ) -> None:
        """Update a variable set."""
        sets = self._load_json_store("variable_sets.json")
        if set_id not in sets:
            return

        if name:
            sets[set_id]["name"] = name
        if variables is not None:
            sets[set_id]["variables"] = variables

        self._save_json_store("variable_sets.json", sets)

    def delete_variable_set(self, set_id: str) -> None:
        """Delete a variable set."""
        sets = self._load_json_store("variable_sets.json")
        if set_id in sets:
            del sets[set_id]
            self._save_json_store("variable_sets.json", sets)

        # Clean up selections
        selections = self._load_json_store("variable_set_selections.json")
        for prompt_name in list(selections.keys()):
            if isinstance(selections[prompt_name], list):
                selections[prompt_name] = [
                    s for s in selections[prompt_name] if s != set_id
                ]
                if not selections[prompt_name]:
                    del selections[prompt_name]
        self._save_json_store("variable_set_selections.json", selections)

        # Clean up overrides
        overrides = self._load_json_store("variable_set_overrides.json")
        for prompt_name in list(overrides.keys()):
            if set_id in overrides[prompt_name]:
                del overrides[prompt_name][set_id]
                if not overrides[prompt_name]:
                    del overrides[prompt_name]
        self._save_json_store("variable_set_overrides.json", overrides)

    def get_active_variable_sets(self, prompt_name: str) -> List[Dict[str, Any]]:
        """Get all active variable sets for a prompt, in order."""
        selections = self._load_json_store("variable_set_selections.json")
        set_ids = selections.get(prompt_name, [])

        sets = self._load_json_store("variable_sets.json")
        result = []
        for set_id in set_ids:
            if set_id in sets:
                result.append(sets[set_id])

        return result

    def set_active_variable_sets(self, prompt_name: str, set_ids: List[str]) -> None:
        """Set the active variable sets for a prompt."""
        selections = self._load_json_store("variable_set_selections.json")
        selections[prompt_name] = set_ids
        self._save_json_store("variable_set_selections.json", selections)

    def get_variable_overrides(
        self, prompt_name: str, set_id: str
    ) -> Dict[str, str]:
        """Get override values for a specific set in a prompt."""
        overrides = self._load_json_store("variable_set_overrides.json")
        return overrides.get(prompt_name, {}).get(set_id, {})

    def set_variable_overrides(
        self, prompt_name: str, set_id: str, overrides: Dict[str, str]
    ) -> None:
        """Set override values for a specific set in a prompt."""
        all_overrides = self._load_json_store("variable_set_overrides.json")
        if prompt_name not in all_overrides:
            all_overrides[prompt_name] = {}
        all_overrides[prompt_name][set_id] = overrides
        self._save_json_store("variable_set_overrides.json", all_overrides)

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

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
