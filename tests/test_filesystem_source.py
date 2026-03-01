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
        assert names == ["personas_expert", "task"]

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
        assert "level1_level2_prompt" in source.list()

    def test_name_with_hyphens_and_spaces(self, temp_dir):
        """Test name building with hyphens and spaces."""
        subdir = temp_dir / "my-dir"
        subdir.mkdir()
        (subdir / "my-file.prompt").write_text("content")

        source = FileSystemSource(temp_dir)
        assert "my_dir_my_file" in source.list()


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
        assert source.find_by_tag("persona") == ["personas_expert"]

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
