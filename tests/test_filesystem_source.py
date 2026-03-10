"""Tests for FileSystemSource."""

import json
import tempfile
from pathlib import Path

import pytest

from prompt_assemble.exceptions import PromptNotFoundError, SourceConnectionError
from prompt_assemble.sources import FileSystemSource


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestFileSystemSourceBasics:
    """Test basic FileSystemSource functionality."""

    def test_init_valid_directory(self, temp_dir):
        """Test initialization with valid directory."""
        source = FileSystemSource(temp_dir)
        assert source.root == temp_dir

    def test_init_nonexistent_directory(self):
        """Test initialization with nonexistent directory."""
        with pytest.raises(SourceConnectionError, match="does not exist"):
            FileSystemSource("/nonexistent/path")

    def test_init_file_instead_of_directory(self, temp_dir):
        """Test initialization with a file instead of directory."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("test")

        with pytest.raises(SourceConnectionError, match="not a directory"):
            FileSystemSource(file_path)

    def test_list_empty_directory(self, temp_dir):
        """Test listing prompts from empty directory."""
        source = FileSystemSource(temp_dir)
        assert source.list() == []


class TestFileSystemSourcePromptLoading:
    """Test loading prompts from filesystem."""

    def test_load_single_prompt(self, temp_dir):
        """Test loading a single prompt file."""
        prompt_file = temp_dir / "greeting.prompt"
        prompt_file.write_text("Hello there!")

        source = FileSystemSource(temp_dir)
        assert source.list() == ["greeting"]
        assert source.get_raw("greeting") == "Hello there!"

    def test_load_multiple_prompts(self, temp_dir):
        """Test loading multiple prompt files."""
        (temp_dir / "greeting.prompt").write_text("Hello")
        (temp_dir / "farewell.prompt").write_text("Goodbye")

        source = FileSystemSource(temp_dir)
        names = sorted(source.list())
        assert names == ["farewell", "greeting"]

    def test_load_prompts_from_subdirectories(self, temp_dir):
        """Test loading prompts from subdirectories."""
        subdir = temp_dir / "personas"
        subdir.mkdir()

        (subdir / "expert.prompt").write_text("Expert content")
        (temp_dir / "task.prompt").write_text("Task content")

        source = FileSystemSource(temp_dir)
        names = sorted(source.list())
        # Names are just filenames without directory paths
        assert names == ["expert", "task"]

    def test_get_raw_nonexistent(self, temp_dir):
        """Test getting nonexistent prompt."""
        source = FileSystemSource(temp_dir)
        with pytest.raises(PromptNotFoundError):
            source.get_raw("nonexistent")


class TestFileSystemSourceNameBuilding:
    """Test prompt name building."""

    def test_name_from_flat_file(self, temp_dir):
        """Test name building for flat file."""
        (temp_dir / "test.prompt").write_text("content")
        source = FileSystemSource(temp_dir)

        assert "test" in source.list()

    def test_name_from_nested_file(self, temp_dir):
        """Test name building for nested file."""
        subdir = temp_dir / "level1" / "level2"
        subdir.mkdir(parents=True)
        (subdir / "prompt.prompt").write_text("content")

        source = FileSystemSource(temp_dir)
        # Names are just filenames without directory paths
        assert "prompt" in source.list()

    def test_name_with_hyphens_and_spaces(self, temp_dir):
        """Test name building with hyphens and spaces."""
        subdir = temp_dir / "my-dir"
        subdir.mkdir()
        (subdir / "my-file.prompt").write_text("content")

        source = FileSystemSource(temp_dir)
        # Names are just filenames without directory paths; hyphens preserved
        assert "my-file" in source.list()


class TestFileSystemSourceRegistry:
    """Test registry integration."""

    def test_empty_registry_for_file_without_metadata(self, temp_dir):
        """Test that files without registry metadata have empty registry."""
        (temp_dir / "test.prompt").write_text("content")
        source = FileSystemSource(temp_dir)

        # Should still be listed but have no tags
        assert source.find_by_tag("foo") == []
        assert source.list() == ["test"]

    def test_load_registry_json(self, temp_dir):
        """Test loading _registry.json metadata."""
        (temp_dir / "expert.prompt").write_text("Expert instructions")

        registry_file = temp_dir / "_registry.json"
        registry_file.write_text(
            json.dumps(
                {
                    "expert": {
                        "description": "Expert persona",
                        "tags": ["persona", "technical"],
                        "owner": "alice",
                    }
                }
            )
        )

        source = FileSystemSource(temp_dir)
        assert source.find_by_tag("persona") == ["expert"]
        assert source.find_by_tag("technical") == ["expert"]
        assert source.find_by_tag("persona", "technical") == ["expert"]

    def test_registry_in_subdirectory(self, temp_dir):
        """Test loading registry from subdirectory."""
        subdir = temp_dir / "personas"
        subdir.mkdir()

        (subdir / "expert.prompt").write_text("content")
        registry_file = subdir / "_registry.json"
        registry_file.write_text(
            json.dumps(
                {"expert": {"tags": ["persona"], "description": "Expert"}}
            )
        )

        source = FileSystemSource(temp_dir)
        # Names are just filenames without directory paths
        assert source.find_by_tag("persona") == ["expert"]

    def test_orphaned_registry_entry_ignored(self, temp_dir):
        """Test that orphaned registry entries (no file) are silently ignored."""
        registry_file = temp_dir / "_registry.json"
        registry_file.write_text(
            json.dumps(
                {
                    "nonexistent": {"description": "No file for this", "tags": []}
                }
            )
        )

        # Should not raise, orphaned entry is silently ignored
        source = FileSystemSource(temp_dir)
        assert source.list() == []


class TestFileSystemSourceRefresh:
    """Test refresh functionality."""

    def test_refresh_picks_up_new_files(self, temp_dir):
        """Test that refresh picks up newly added files."""
        source = FileSystemSource(temp_dir)
        assert source.list() == []

        # Add a new prompt
        (temp_dir / "new.prompt").write_text("new content")
        source.refresh()

        assert source.list() == ["new"]
        assert source.get_raw("new") == "new content"

    def test_is_stale_detects_new_files(self, temp_dir):
        """Test is_stale detects new files."""
        source = FileSystemSource(temp_dir)
        assert not source.is_stale()  # No new files

        (temp_dir / "new.prompt").write_text("content")
        assert source.is_stale()  # New file added


class TestFileSystemSourceSave:
    """Test save functionality."""

    def test_save_creates_new_prompt(self, temp_dir):
        """Test that save creates a new prompt file."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("greeting", "Hello there!")

        assert "greeting" in source.list()
        assert source.get_raw("greeting") == "Hello there!"

    def test_save_updates_existing_prompt(self, temp_dir):
        """Test that save updates an existing prompt."""
        (temp_dir / "greeting.prompt").write_text("Old content")
        source = FileSystemSource(temp_dir)
        assert source.get_raw("greeting") == "Old content"

        source.save_prompt("greeting", "New content")
        assert source.get_raw("greeting") == "New content"

    def test_save_updates_registry_metadata(self, temp_dir):
        """Test that save persists tags, description, and owner."""
        source = FileSystemSource(temp_dir)
        source.save_prompt(
            "expert",
            "Expert instructions",
            description="Expert persona",
            tags=["persona", "technical"],
            owner="alice",
        )

        # Verify metadata in registry
        assert source.find_by_tag("persona") == ["expert"]
        assert source.find_by_tag("technical") == ["expert"]
        assert source.find_by_tag("persona", "technical") == ["expert"]

    def test_delete_removes_prompt(self, temp_dir):
        """Test that delete removes the prompt and its metadata."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("greeting", "Hello", tags=["greeting_tag"])

        assert "greeting" in source.list()
        source.delete_prompt("greeting")
        assert "greeting" not in source.list()

    def test_delete_nonexistent_raises(self, temp_dir):
        """Test that deleting nonexistent prompt raises error."""
        source = FileSystemSource(temp_dir)
        with pytest.raises(PromptNotFoundError):
            source.delete_prompt("nonexistent")

    def test_save_prompt_appears_in_list(self, temp_dir):
        """Test that newly saved prompt appears in list."""
        source = FileSystemSource(temp_dir)
        assert source.list() == []

        source.save_prompt("first", "content1")
        assert "first" in source.list()

        source.save_prompt("second", "content2")
        names = sorted(source.list())
        assert names == ["first", "second"]


class TestFileSystemSourceVersioning:
    """Test versioning functionality."""

    def test_save_prompt_creates_version(self, temp_dir):
        """Test that save creates a version file when increment_version=True."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "Content v1", increment_version=True)

        versions = source.list_prompt_versions("test")
        assert len(versions) == 1
        assert versions[0]["version"] == 1

    def test_save_prompt_no_version_when_disabled(self, temp_dir):
        """Test that no version is created when increment_version=False."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "Content v1", increment_version=False)

        versions = source.list_prompt_versions("test")
        assert len(versions) == 0

    def test_get_prompt_version_latest(self, temp_dir):
        """Test getting latest version (version=None)."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "Content v1", increment_version=True)
        source.save_prompt("test", "Content v2", increment_version=True)

        content = source.get_prompt_version("test", version=None)
        assert content == "Content v2"

    def test_get_prompt_version_historical(self, temp_dir):
        """Test getting a specific historical version."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "Content v1", increment_version=True)
        source.save_prompt("test", "Content v2", increment_version=True)

        v1_content = source.get_prompt_version("test", version=1)
        assert v1_content == "Content v1"

        v2_content = source.get_prompt_version("test", version=2)
        assert v2_content == "Content v2"

    def test_get_prompt_version_not_found(self, temp_dir):
        """Test getting nonexistent version raises error."""
        source = FileSystemSource(temp_dir)
        with pytest.raises(PromptNotFoundError):
            source.get_prompt_version("nonexistent")

    def test_get_prompt_version_invalid_version_number(self, temp_dir):
        """Test getting nonexistent version number raises error."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "Content v1", increment_version=True)

        with pytest.raises(PromptNotFoundError):
            source.get_prompt_version("test", version=99)

    def test_version_history_capped_at_20(self, temp_dir):
        """Test that only 20 most recent versions are kept."""
        source = FileSystemSource(temp_dir)

        # Create 25 versions
        for i in range(1, 26):
            source.save_prompt("test", f"Content v{i}", increment_version=True)

        versions = source.list_prompt_versions("test")
        assert len(versions) == 20

        # Should have versions 6-25, not 1-5
        version_numbers = [v["version"] for v in versions]
        assert version_numbers == list(range(6, 26))

    def test_list_prompt_versions(self, temp_dir):
        """Test listing all versions of a prompt."""
        source = FileSystemSource(temp_dir)
        source.save_prompt(
            "test", "Content v1", increment_version=True, revision_comment="Initial"
        )
        source.save_prompt(
            "test", "Content v2", increment_version=True, revision_comment="Update"
        )

        versions = source.list_prompt_versions("test")
        assert len(versions) == 2
        assert versions[0]["version"] == 1
        assert versions[0]["revision_comment"] == "Initial"
        assert versions[1]["version"] == 2
        assert versions[1]["revision_comment"] == "Update"


class TestFileSystemSourceVariableSets:
    """Test variable sets functionality."""

    def test_create_variable_set(self, temp_dir):
        """Test creating a variable set."""
        source = FileSystemSource(temp_dir)
        set_id = source.create_variable_set(
            "test_set", {"key1": "value1", "key2": "value2"}
        )

        assert set_id is not None
        var_set = source.get_variable_set(set_id)
        assert var_set is not None
        assert var_set["name"] == "test_set"
        assert var_set["variables"] == {"key1": "value1", "key2": "value2"}

    def test_get_variable_set(self, temp_dir):
        """Test retrieving a variable set by ID."""
        source = FileSystemSource(temp_dir)
        set_id = source.create_variable_set("test_set", {"x": "y"})

        retrieved = source.get_variable_set(set_id)
        assert retrieved["id"] == set_id
        assert retrieved["name"] == "test_set"
        assert retrieved["variables"]["x"] == "y"

    def test_list_variable_sets(self, temp_dir):
        """Test listing all variable sets."""
        source = FileSystemSource(temp_dir)
        source.create_variable_set("set_a", {"x": "1"})
        source.create_variable_set("set_b", {"y": "2"})

        sets = source.list_variable_sets()
        assert len(sets) == 2
        names = [s["name"] for s in sets]
        assert "set_a" in names
        assert "set_b" in names

    def test_update_variable_set(self, temp_dir):
        """Test updating a variable set."""
        source = FileSystemSource(temp_dir)
        set_id = source.create_variable_set("original", {"x": "1"})

        source.update_variable_set(set_id, name="updated", variables={"y": "2"})

        updated = source.get_variable_set(set_id)
        assert updated["name"] == "updated"
        assert updated["variables"] == {"y": "2"}

    def test_delete_variable_set(self, temp_dir):
        """Test deleting a variable set."""
        source = FileSystemSource(temp_dir)
        set_id = source.create_variable_set("to_delete", {"x": "1"})

        source.delete_variable_set(set_id)

        assert source.get_variable_set(set_id) is None

    def test_delete_variable_set_cascades(self, temp_dir):
        """Test that deleting a set removes it from selections and overrides."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "content")
        set_id = source.create_variable_set("test_set", {"x": "1"})

        source.set_active_variable_sets("test", [set_id])
        source.set_variable_overrides("test", set_id, {"x": "override"})

        source.delete_variable_set(set_id)

        # Selection should be gone
        active = source.get_active_variable_sets("test")
        assert len(active) == 0

        # Overrides should be gone
        overrides = source.get_variable_overrides("test", set_id)
        assert overrides == {}


class TestFileSystemSourceVariableSetSelections:
    """Test variable set selections."""

    def test_get_active_variable_sets(self, temp_dir):
        """Test getting active variable sets for a prompt."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "content")
        set_id1 = source.create_variable_set("set1", {"x": "1"})
        set_id2 = source.create_variable_set("set2", {"y": "2"})

        source.set_active_variable_sets("test", [set_id1, set_id2])

        active = source.get_active_variable_sets("test")
        assert len(active) == 2
        assert active[0]["name"] == "set1"
        assert active[1]["name"] == "set2"

    def test_set_active_variable_sets(self, temp_dir):
        """Test setting active variable sets for a prompt."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "content")
        set_id = source.create_variable_set("test_set", {"x": "1"})

        source.set_active_variable_sets("test", [set_id])

        active = source.get_active_variable_sets("test")
        assert len(active) == 1
        assert active[0]["id"] == set_id

    def test_set_active_variable_sets_replaces(self, temp_dir):
        """Test that setting selections replaces previous ones."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "content")
        set_id1 = source.create_variable_set("set1", {"x": "1"})
        set_id2 = source.create_variable_set("set2", {"y": "2"})

        source.set_active_variable_sets("test", [set_id1])
        source.set_active_variable_sets("test", [set_id2])

        active = source.get_active_variable_sets("test")
        assert len(active) == 1
        assert active[0]["id"] == set_id2


class TestFileSystemSourceVariableOverrides:
    """Test variable overrides."""

    def test_get_variable_overrides(self, temp_dir):
        """Test getting override values."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "content")
        set_id = source.create_variable_set("test_set", {"x": "1", "y": "2"})

        source.set_variable_overrides("test", set_id, {"x": "override"})

        overrides = source.get_variable_overrides("test", set_id)
        assert overrides == {"x": "override"}

    def test_set_variable_overrides(self, temp_dir):
        """Test setting override values."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "content")
        set_id = source.create_variable_set("test_set", {"x": "1"})

        source.set_variable_overrides("test", set_id, {"x": "overridden"})

        overrides = source.get_variable_overrides("test", set_id)
        assert overrides == {"x": "overridden"}

    def test_set_variable_overrides_replaces(self, temp_dir):
        """Test that setting overrides replaces previous ones."""
        source = FileSystemSource(temp_dir)
        source.save_prompt("test", "content")
        set_id = source.create_variable_set("test_set", {"x": "1", "y": "2"})

        source.set_variable_overrides("test", set_id, {"x": "a"})
        source.set_variable_overrides("test", set_id, {"y": "b"})

        overrides = source.get_variable_overrides("test", set_id)
        assert overrides == {"y": "b"}


class TestFileSystemSourceTaggedVariables:
    """Test tagged variable functionality."""

    def test_variable_tagged_format(self, temp_dir):
        """Test creating and retrieving tagged variables."""
        source = FileSystemSource(temp_dir)

        # Create a set with a tagged variable
        set_id = source.create_variable_set(
            "tagged_set",
            variables={"ROLE": {"value": "expert", "tag": "persona"}}
        )

        # Retrieve and verify
        vs = source.get_variable_set(set_id)
        assert "ROLE" in vs["variables"]
        assert vs["variables"]["ROLE"]["value"] == "expert"
        assert vs["variables"]["ROLE"]["tag"] == "persona"

    def test_variable_mixed_format(self, temp_dir):
        """Test set with both simple and tagged variables."""
        source = FileSystemSource(temp_dir)

        set_id = source.create_variable_set(
            "mixed_set",
            variables={
                "NAME": "Alice",
                "ROLE": {"value": "admin", "tag": "persona"},
                "AGE": 30,
            }
        )

        vs = source.get_variable_set(set_id)
        assert vs["variables"]["NAME"] == "Alice"
        assert vs["variables"]["ROLE"]["tag"] == "persona"
        assert vs["variables"]["AGE"] == 30


class TestFileSystemSourceGranularVariableOps:
    """Test granular variable set operations."""

    def test_add_variable_to_set(self, temp_dir):
        """Test adding a variable to an existing set."""
        source = FileSystemSource(temp_dir)
        set_id = source.create_variable_set("test_set", variables={"KEY1": "value1"})

        # Add a new variable
        source.add_variable_to_set(set_id, "KEY2", "value2")

        # Verify both exist
        vs = source.get_variable_set(set_id)
        assert vs["variables"]["KEY1"] == "value1"
        assert vs["variables"]["KEY2"] == "value2"

    def test_add_variable_with_tag(self, temp_dir):
        """Test adding a tagged variable to a set."""
        source = FileSystemSource(temp_dir)
        set_id = source.create_variable_set("test_set")

        # Add a tagged variable
        source.add_variable_to_set(set_id, "ROLE", "admin", tag="persona")

        # Verify
        vs = source.get_variable_set(set_id)
        assert vs["variables"]["ROLE"]["value"] == "admin"
        assert vs["variables"]["ROLE"]["tag"] == "persona"

    def test_add_variable_updates_existing(self, temp_dir):
        """Test that add_variable_to_set updates existing variables."""
        source = FileSystemSource(temp_dir)
        set_id = source.create_variable_set("test_set", variables={"KEY": "old_value"})

        # Update the variable
        source.add_variable_to_set(set_id, "KEY", "new_value")

        # Verify it was updated
        vs = source.get_variable_set(set_id)
        assert vs["variables"]["KEY"] == "new_value"

    def test_remove_variable_from_set(self, temp_dir):
        """Test removing a variable from a set."""
        source = FileSystemSource(temp_dir)
        set_id = source.create_variable_set(
            "test_set", variables={"KEY1": "value1", "KEY2": "value2"}
        )

        # Remove one variable
        source.remove_variable_from_set(set_id, "KEY1")

        # Verify only KEY2 remains
        vs = source.get_variable_set(set_id)
        assert "KEY1" not in vs["variables"]
        assert "KEY2" in vs["variables"]

    def test_remove_nonexistent_variable(self, temp_dir):
        """Test removing a nonexistent variable (should not error)."""
        source = FileSystemSource(temp_dir)
        set_id = source.create_variable_set("test_set", variables={"KEY": "value"})

        # Remove a nonexistent variable
        source.remove_variable_from_set(set_id, "NONEXISTENT")

        # Original variable should still exist
        vs = source.get_variable_set(set_id)
        assert "KEY" in vs["variables"]


class TestFileSystemSourceFindVariableSets:
    """Test finding variable sets by name and owner."""

    def test_find_variable_sets_exact_match(self, temp_dir):
        """Test exact name matching."""
        source = FileSystemSource(temp_dir)
        source.create_variable_set("greeting_set", variables={})
        source.create_variable_set("farewell_set", variables={})

        results = source.find_variable_sets(name="greeting_set")
        assert len(results) == 1
        assert results[0]["name"] == "greeting_set"

    def test_find_variable_sets_partial_match(self, temp_dir):
        """Test partial name matching."""
        source = FileSystemSource(temp_dir)
        source.create_variable_set("greeting_set", variables={})
        source.create_variable_set("greeting_formal", variables={})
        source.create_variable_set("farewell_set", variables={})

        results = source.find_variable_sets(name="greeting", match_type="partial")
        assert len(results) == 2
        names = {r["name"] for r in results}
        assert names == {"greeting_set", "greeting_formal"}

    def test_find_variable_sets_by_owner(self, temp_dir):
        """Test finding sets by owner."""
        source = FileSystemSource(temp_dir)
        source.create_variable_set("alice_set", variables={}, owner="alice")
        source.create_variable_set("bob_set", variables={}, owner="bob")
        source.create_variable_set("global_set", variables={}, owner=None)

        # Find by owner
        alice_sets = source.find_variable_sets(owner="alice")
        assert len(alice_sets) == 1
        assert alice_sets[0]["name"] == "alice_set"

        # Find by owner=bob
        bob_sets = source.find_variable_sets(owner="bob")
        assert len(bob_sets) == 1
        assert bob_sets[0]["name"] == "bob_set"

    def test_find_variable_sets_combined_filters(self, temp_dir):
        """Test finding with both name and owner filters."""
        source = FileSystemSource(temp_dir)
        source.create_variable_set("greeting_alice", variables={}, owner="alice")
        source.create_variable_set("greeting_bob", variables={}, owner="bob")
        source.create_variable_set("farewell_alice", variables={}, owner="alice")

        # Find greeting sets by alice
        results = source.find_variable_sets(name="greeting", owner="alice", match_type="partial")
        assert len(results) == 1
        assert results[0]["name"] == "greeting_alice"

    def test_list_global_variable_sets(self, temp_dir):
        """Test listing only global (unscoped) variable sets."""
        source = FileSystemSource(temp_dir)
        source.create_variable_set("global1", variables={}, owner=None)
        source.create_variable_set("global2", variables={}, owner=None)
        source.create_variable_set("scoped", variables={}, owner="alice")

        results = source.list_global_variable_sets()
        assert len(results) == 2
        names = {r["name"] for r in results}
        assert names == {"global1", "global2"}

    def test_list_variable_sets_by_owner(self, temp_dir):
        """Test listing sets scoped to a specific owner."""
        source = FileSystemSource(temp_dir)
        source.create_variable_set("alice1", variables={}, owner="alice")
        source.create_variable_set("alice2", variables={}, owner="alice")
        source.create_variable_set("bob1", variables={}, owner="bob")

        results = source.list_variable_sets_by_owner("alice")
        assert len(results) == 2
        names = {r["name"] for r in results}
        assert names == {"alice1", "alice2"}

    def test_get_available_variable_sets(self, temp_dir):
        """Test getting available sets (global + scoped)."""
        source = FileSystemSource(temp_dir)
        source.create_variable_set("global", variables={}, owner=None)
        source.create_variable_set("alice_scoped", variables={}, owner="alice")
        source.create_variable_set("bob_scoped", variables={}, owner="bob")

        # For alice: global + alice_scoped
        results = source.get_available_variable_sets(owner="alice")
        assert len(results) == 2
        names = {r["name"] for r in results}
        assert names == {"global", "alice_scoped"}

        # No owner: just global
        results = source.get_available_variable_sets(owner=None)
        assert len(results) == 1
        assert results[0]["name"] == "global"
