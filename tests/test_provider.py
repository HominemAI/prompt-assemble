"""Tests for PromptProvider."""

from unittest.mock import Mock

import pytest

from prompt_assemble import PromptProvider, ReadOnlySourceError, bulk_import
from prompt_assemble.exceptions import PromptNotFoundError
from prompt_assemble.registry import Registry, RegistryEntry
from prompt_assemble.sources.base import PromptSource


class MockSource(PromptSource):
    """Mock prompt source for testing."""

    def __init__(self):
        """Initialize mock source with test data."""
        super().__init__()
        self.prompts = {}
        self.tags = {}  # prompt_name -> list of tags
        self._registry = Registry()  # For bulk_import metadata
        self.variable_sets = {}  # set_id -> {id, name, owner, variables}
        self.active_variable_sets = {}  # prompt_name -> [set_ids]
        self.variable_overrides = {}  # prompt_name -> {set_id -> {key -> value}}

    def get_raw(self, name: str) -> str:
        """Get raw prompt content."""
        if name not in self.prompts:
            raise PromptNotFoundError(f"Prompt not found: {name}")
        return self.prompts[name]

    def find_by_tag(self, *tags: str) -> list[str]:
        """Find prompts by tags (AND intersection)."""
        if not tags:
            return list(self.prompts.keys())

        matching = []
        for name, prompt_tags in self.tags.items():
            if all(tag in prompt_tags for tag in tags):
                matching.append(name)
        return matching

    def find_by_owner(self, owner: str) -> list[str]:
        """Find prompts by owner."""
        matching = []
        for name in self.prompts.keys():
            entry = self._registry.get(name)
            if entry and entry.owner == owner:
                matching.append(name)
        return matching

    def list(self) -> list[str]:
        """List all prompt names."""
        return list(self.prompts.keys())

    def refresh(self) -> None:
        """Refresh (no-op for mock)."""
        pass

    def add_prompt(self, name: str, content: str, tags: list = None, owner: str = None):
        """Add a prompt to the mock source."""
        self.prompts[name] = content
        self.tags[name] = tags or []
        # Register in registry
        entry = RegistryEntry(name=name, tags=tags or [], owner=owner)
        self._registry.register(entry)

    def create_variable_set(self, name: str, variables=None, owner=None):
        """Create a variable set."""
        import uuid
        if variables is None:
            variables = {}
        set_id = str(uuid.uuid4())
        self.variable_sets[set_id] = {
            "id": set_id,
            "name": name,
            "owner": owner,
            "variables": variables.copy(),
        }
        return set_id

    def get_variable_set(self, set_id: str):
        """Get a variable set by ID."""
        return self.variable_sets.get(set_id)

    def list_variable_sets(self):
        """List all variable sets."""
        return list(self.variable_sets.values())

    def update_variable_set(self, set_id: str, name=None, variables=None, owner=None):
        """Update a variable set."""
        if set_id not in self.variable_sets:
            return
        if name:
            self.variable_sets[set_id]["name"] = name
        if owner is not None:
            self.variable_sets[set_id]["owner"] = owner
        if variables is not None:
            self.variable_sets[set_id]["variables"] = variables.copy()

    def delete_variable_set(self, set_id: str):
        """Delete a variable set."""
        if set_id in self.variable_sets:
            del self.variable_sets[set_id]

    def get_active_variable_sets(self, prompt_name: str):
        """Get active variable sets for a prompt."""
        set_ids = self.active_variable_sets.get(prompt_name, [])
        return [self.variable_sets[sid] for sid in set_ids if sid in self.variable_sets]

    def set_active_variable_sets(self, prompt_name: str, set_ids: list):
        """Set active variable sets for a prompt."""
        self.active_variable_sets[prompt_name] = set_ids

    def get_variable_overrides(self, prompt_name: str, set_id: str):
        """Get overrides for a set in a prompt."""
        return self.variable_overrides.get(prompt_name, {}).get(set_id, {})

    def set_variable_overrides(self, prompt_name: str, set_id: str, overrides: dict):
        """Set overrides for a set in a prompt."""
        if prompt_name not in self.variable_overrides:
            self.variable_overrides[prompt_name] = {}
        self.variable_overrides[prompt_name][set_id] = overrides.copy()

    def add_variable_to_set(self, set_id: str, key: str, value: str, tag=None):
        """Add a variable to a set."""
        if set_id not in self.variable_sets:
            return
        if tag:
            self.variable_sets[set_id]["variables"][key] = {"value": value, "tag": tag}
        else:
            self.variable_sets[set_id]["variables"][key] = value

    def remove_variable_from_set(self, set_id: str, key: str):
        """Remove a variable from a set."""
        if set_id in self.variable_sets and key in self.variable_sets[set_id]["variables"]:
            del self.variable_sets[set_id]["variables"][key]

    def find_variable_sets(self, name=None, owner=None, match_type="exact"):
        """Find variable sets by name and/or owner."""
        results = []
        for vs in self.variable_sets.values():
            # Filter by name if specified
            if name is not None:
                if match_type == "partial":
                    if name.lower() not in vs["name"].lower():
                        continue
                else:
                    if vs["name"] != name:
                        continue

            # Filter by owner if specified (including explicit None check)
            # If owner parameter was passed (even if None), filter by it
            # We need to check if 'owner' was explicitly provided
            # Since we can't distinguish between not passed and passed None,
            # we use a sentinel pattern in the test instead
            if owner is not None:
                if vs.get("owner") != owner:
                    continue

            results.append(vs)
        return sorted(results, key=lambda x: x["name"])


@pytest.fixture
def mock_source():
    """Create a mock source."""
    return MockSource()


@pytest.fixture
def provider(mock_source):
    """Create a provider with mock source."""
    return PromptProvider(mock_source)


class TestPromptProviderBasics:
    """Test basic PromptProvider functionality."""

    def test_get_raw(self, provider, mock_source):
        """Test getting raw prompt."""
        mock_source.add_prompt("greeting", "Hello there!")
        assert provider.get_raw("greeting") == "Hello there!"

    def test_get_raw_nonexistent(self, provider):
        """Test getting nonexistent prompt."""
        with pytest.raises(PromptNotFoundError):
            provider.get_raw("nonexistent")

    def test_list(self, provider, mock_source):
        """Test listing prompts."""
        mock_source.add_prompt("first", "1")
        mock_source.add_prompt("second", "2")
        assert set(provider.list()) == {"first", "second"}

    def test_find_by_tag(self, provider, mock_source):
        """Test finding prompts by tag."""
        mock_source.add_prompt("a", "content_a", tags=["foo"])
        mock_source.add_prompt("b", "content_b", tags=["bar"])
        mock_source.add_prompt("c", "content_c", tags=["foo", "bar"])

        assert set(provider.find_by_tag("foo")) == {"a", "c"}
        assert set(provider.find_by_tag("bar")) == {"b", "c"}


class TestPromptProviderRender:
    """Test prompt rendering with substitution."""

    def test_render_simple_variable(self, provider, mock_source):
        """Test rendering with simple variable."""
        mock_source.add_prompt("test", "Hello [[NAME]]")
        result = provider.render("test", variables={"NAME": "Alice"})
        assert result == "Hello Alice"

    def test_render_multiple_variables(self, provider, mock_source):
        """Test rendering with multiple variables."""
        mock_source.add_prompt("test", "[[NAME]] is [[AGE]] years old")
        result = provider.render(
            "test", variables={"NAME": "Bob", "AGE": 30}
        )
        assert result == "Bob is 30 years old"

    def test_render_serializes_variables(self, provider, mock_source):
        """Test that variables are automatically serialized."""
        mock_source.add_prompt("test", "Age: [[AGE]], Active: [[ACTIVE]]")
        result = provider.render(
            "test", variables={"AGE": 30, "ACTIVE": True}
        )
        assert result == "Age: 30, Active: True"

    def test_render_nonexistent(self, provider):
        """Test rendering nonexistent prompt."""
        with pytest.raises(PromptNotFoundError):
            provider.render("nonexistent")

    def test_render_missing_variable(self, provider, mock_source):
        """Test rendering with missing variable logs and returns empty string."""
        mock_source.add_prompt("test", "Hello [[NAME]]!")
        result = provider.render("test")
        assert result == "Hello !"


class TestPromptProviderComponentInjection:
    """Test component injection (PROMPT: sigil)."""

    def test_render_component_injection(self, provider, mock_source):
        """Test injecting other prompts as components."""
        mock_source.add_prompt("greeting", "Hello there!")
        mock_source.add_prompt("task", "Complete the task: [[PROMPT: greeting]]")

        result = provider.render("task")
        assert result == "Complete the task: Hello there!"

    def test_render_nested_components(self, provider, mock_source):
        """Test nested component injection."""
        mock_source.add_prompt("inner", "INNER")
        mock_source.add_prompt("middle", "MIDDLE [[PROMPT: inner]]")
        mock_source.add_prompt("outer", "OUTER [[PROMPT: middle]]")

        result = provider.render("outer")
        assert result == "OUTER MIDDLE INNER"

    def test_render_component_with_variables(self, provider, mock_source):
        """Test component injection with variable substitution."""
        mock_source.add_prompt("greeting", "Hello [[NAME]]!")
        mock_source.add_prompt("task", "Please: [[PROMPT: greeting]]")

        result = provider.render("task", variables={"NAME": "Alice"})
        assert result == "Please: Hello Alice!"


class TestPromptProviderTagInjection:
    """Test PROMPT_TAG sigil functionality."""

    def test_render_prompt_tag_single_result(self, provider, mock_source):
        """Test injecting prompts by tag."""
        mock_source.add_prompt("system_1", "System prompt 1", tags=["system"])
        mock_source.add_prompt("system_2", "System prompt 2", tags=["system"])
        mock_source.add_prompt("main", "[[PROMPT_TAG: system]]")

        result = provider.render("main")
        # Should contain both in reverse order (most recent first)
        lines = result.strip().split("\n\n")
        assert len(lines) == 2
        assert "System prompt 2" in result
        assert "System prompt 1" in result

    def test_render_prompt_tag_limit(self, provider, mock_source):
        """Test PROMPT_TAG with limit."""
        mock_source.add_prompt("p1", "Prompt 1", tags=["x"])
        mock_source.add_prompt("p2", "Prompt 2", tags=["x"])
        mock_source.add_prompt("p3", "Prompt 3", tags=["x"])
        mock_source.add_prompt("main", "Limited: [[PROMPT_TAG:1: x]]")

        result = provider.render("main")
        # Should only include last one (p3)
        assert "Prompt 3" in result
        assert "Prompt 1" not in result
        assert "Prompt 2" not in result

    def test_render_prompt_tag_multiple_tags(self, provider, mock_source):
        """Test PROMPT_TAG with multiple tags (AND intersection)."""
        mock_source.add_prompt("a", "A", tags=["x"])
        mock_source.add_prompt("b", "B", tags=["y"])
        mock_source.add_prompt("c", "C", tags=["x", "y"])
        mock_source.add_prompt("main", "[[PROMPT_TAG: x, y]]")

        result = provider.render("main")
        assert "C" in result
        assert "A" not in result
        assert "B" not in result

    def test_render_prompt_tag_no_matches(self, provider, mock_source):
        """Test PROMPT_TAG with no matching prompts."""
        mock_source.add_prompt("a", "A", tags=["foo"])
        mock_source.add_prompt("main", "Result: [[PROMPT_TAG: nonexistent]]")

        result = provider.render("main")
        assert result == "Result: "


class TestPromptProviderRecursion:
    """Test recursion behavior."""

    def test_render_no_recursion(self, provider, mock_source):
        """Test with recursive=False."""
        mock_source.add_prompt("test", "[[VAR1]]")
        result = provider.render(
            "test", variables={"VAR1": "[[VAR2]]"}, recursive=False
        )
        assert result == "[[VAR2]]"

    def test_render_with_recursion(self, provider, mock_source):
        """Test with recursive=True."""
        mock_source.add_prompt("test", "[[VAR1]]")
        result = provider.render(
            "test",
            variables={"VAR1": "[[VAR2]]", "VAR2": "resolved"},
            recursive=True,
        )
        assert result == "resolved"

    def test_render_max_depth(self, provider, mock_source):
        """Test max_depth parameter."""
        mock_source.add_prompt("test", "[[VAR]]")
        with pytest.raises(RecursionError):
            provider.render(
                "test", variables={"VAR": "[[VAR]]"}, max_depth=5
            )


class TestCrossSigilNesting:
    """Test interactions between different sigil types."""

    def test_prompt_tag_result_has_variable(self, provider, mock_source):
        """Test PROMPT_TAG result containing variables."""
        mock_source.add_prompt("greeting", "Hello [[NAME]]", tags=["intro"])
        mock_source.add_prompt("main", "[[PROMPT_TAG: intro]]")

        result = provider.render("main", variables={"NAME": "Alice"})
        assert result == "Hello Alice"

    def test_prompt_tag_result_has_prompt(self, provider, mock_source):
        """Test PROMPT_TAG result containing another PROMPT: sigil."""
        mock_source.add_prompt("base", "Base text")
        mock_source.add_prompt("with_prompt", "[[PROMPT: base]] extended", tags=["combo"])
        mock_source.add_prompt("main", "[[PROMPT_TAG: combo]]")

        result = provider.render("main")
        assert result == "Base text extended"

    def test_prompt_body_uses_prompt_tag(self, provider, mock_source):
        """Test injected prompt containing PROMPT_TAG: sigil."""
        mock_source.add_prompt("tag1", "Content 1", tags=["section"])
        mock_source.add_prompt("tag2", "Content 2", tags=["section"])
        mock_source.add_prompt("aggregator", "Sections: [[PROMPT_TAG: section]]")
        mock_source.add_prompt("main", "[[PROMPT: aggregator]]")

        result = provider.render("main")
        assert "Content 1" in result
        assert "Content 2" in result

    def test_prompt_tag_n_greater_than_available(self, provider, mock_source):
        """Test PROMPT_TAG:N: when N exceeds available results."""
        mock_source.add_prompt("a", "First", tags=["tag"])
        mock_source.add_prompt("b", "Second", tags=["tag"])
        mock_source.add_prompt("main", "[[PROMPT_TAG:10: tag]]")

        result = provider.render("main")
        assert "First" in result
        assert "Second" in result

    def test_prompt_tag_limit_zero(self, provider, mock_source):
        """Test PROMPT_TAG:0: returns empty."""
        mock_source.add_prompt("a", "Content", tags=["tag"])
        mock_source.add_prompt("main", "Start [[PROMPT_TAG:0: tag]] End")

        result = provider.render("main")
        assert result == "Start  End"

    def test_self_referential_raises(self, provider, mock_source):
        """Test that self-referential PROMPT: raises RecursionError."""
        mock_source.add_prompt("self", "[[PROMPT: self]]")

        with pytest.raises(RecursionError):
            provider.render("self", max_depth=5)

    def test_component_resolver_exception(self, provider, mock_source):
        """Test error handling when component resolver fails."""
        mock_source.add_prompt("main", "[[PROMPT: missing]]")

        with pytest.raises(ValueError, match="Undefined component"):
            provider.render("main")

    def test_multi_level_variable_substitution(self, provider, mock_source):
        """Test variable inside variable inside prompt."""
        mock_source.add_prompt(
            "template", "Value: [[RESULT]]"
        )
        mock_source.add_prompt(
            "main", "[[PROMPT: template]]"
        )

        result = provider.render(
            "main",
            variables={"RESULT": "[[INNER]]", "INNER": "final"},
            recursive=True,
        )
        assert result == "Value: final"

    def test_all_variable_types_one_prompt(self, provider, mock_source):
        """Test serializing all variable types in a single prompt."""
        mock_source.add_prompt(
            "main",
            "str=[[STR]], int=[[INT]], float=[[FLOAT]], bool=[[BOOL]], none=[[NONE]]",
        )

        result = provider.render(
            "main",
            variables={
                "STR": "hello",
                "INT": 42,
                "FLOAT": 3.14,
                "BOOL": True,
                "NONE": None,
            },
        )
        assert result == "str=hello, int=42, float=3.14, bool=True, none="

    def test_deeply_nested_cross_sigil_chain(self, provider, mock_source):
        """Test 4-level deep nesting with multiple sigil types."""
        # Level 4: simple prompt
        mock_source.add_prompt("base", "[[VALUE]]", tags=["leaf"])

        # Level 3: prompt that uses PROMPT_TAG
        mock_source.add_prompt("aggregator", "Result: [[PROMPT_TAG: leaf]]")

        # Level 2: prompt that uses PROMPT
        mock_source.add_prompt("wrapper", "Wrapped: [[PROMPT: aggregator]]")

        # Level 1: main prompt with variable
        mock_source.add_prompt("main", "Final: [[PROMPT: wrapper]]")

        result = provider.render(
            "main",
            variables={"VALUE": "Deep value"},
        )
        assert "Deep value" in result


class TestPromptProviderSave:
    """Test save and delete functionality."""

    def test_save_via_provider(self, provider, mock_source):
        """Test that provider.save_prompt delegates to source."""
        # First, add save_prompt to the mock source
        mock_source.save_prompt = Mock()

        provider.save_prompt("test", "content", description="Test")
        mock_source.save_prompt.assert_called_once_with(
            "test", "content", description="Test"
        )

    def test_delete_via_provider(self, provider, mock_source):
        """Test that provider.delete_prompt delegates to source."""
        # First, add delete_prompt to the mock source
        mock_source.delete_prompt = Mock()

        provider.delete_prompt("test")
        mock_source.delete_prompt.assert_called_once_with("test")

    def test_save_on_readonly_source_raises(self, provider):
        """Test that save on read-only source raises ReadOnlySourceError."""
        with pytest.raises(
            ReadOnlySourceError, match="does not support saving"
        ):
            provider.save_prompt("test", "content")

    def test_delete_on_readonly_source_raises(self, provider):
        """Test that delete on read-only source raises ReadOnlySourceError."""
        with pytest.raises(
            ReadOnlySourceError, match="does not support deleting"
        ):
            provider.delete_prompt("test")


class TestBulkImport:
    """Test bulk import functionality."""

    def test_bulk_import_all_prompts(self, mock_source):
        """Test importing all prompts from source to target."""
        # Set up source with prompts and metadata
        mock_source.add_prompt("p1", "Content 1", tags=["tag1"])
        mock_source.add_prompt("p2", "Content 2", tags=["tag2", "tag1"])
        source_provider = PromptProvider(mock_source)

        # Set up target with save capability
        target_source = MockSource()
        target_source.save_prompt = Mock()
        target_provider = PromptProvider(target_source)

        # Run bulk import
        results = bulk_import(source_provider, target_provider)

        # Verify results
        assert results["imported"] == 2
        assert results["errors"] == 0
        assert results["skipped"] == 0
        assert target_source.save_prompt.call_count == 2

    def test_bulk_import_transfers_metadata(self, mock_source):
        """Test that metadata (tags, description, owner) is transferred."""
        # Add prompt with full metadata to mock source
        mock_source.add_prompt("greeting", "Hello [[NAME]]!", tags=["hello", "greeting"])
        # Manually set metadata in registry
        entry = mock_source._registry.get("greeting")
        entry.description = "Greeting prompt"
        entry.owner = "alice"

        source_provider = PromptProvider(mock_source)

        # Set up target
        target_source = MockSource()
        target_source.save_prompt = Mock()
        target_provider = PromptProvider(target_source)

        # Run bulk import
        bulk_import(source_provider, target_provider)

        # Verify metadata was passed
        call_args = target_source.save_prompt.call_args
        assert call_args[0][0] == "greeting"  # name
        assert call_args[0][1] == "Hello [[NAME]]!"  # content
        assert call_args[1]["description"] == "Greeting prompt"
        assert call_args[1]["owner"] == "alice"
        assert set(call_args[1]["tags"]) == {"hello", "greeting"}

    def test_bulk_import_skip_existing(self, mock_source):
        """Test overwrite=False (default) skips existing prompts."""
        mock_source.add_prompt("p1", "Original content")
        source_provider = PromptProvider(mock_source)

        # Target already has p1
        target_source = MockSource()
        target_source.add_prompt("p1", "Existing content")
        target_source.save_prompt = Mock()
        target_provider = PromptProvider(target_source)

        # Import with overwrite=False (default)
        results = bulk_import(
            source_provider, target_provider, overwrite=False
        )

        # Should skip p1
        assert results["skipped"] == 1
        assert results["imported"] == 0
        target_source.save_prompt.assert_not_called()

    def test_bulk_import_overwrite_existing(self, mock_source):
        """Test overwrite=True overwrites existing prompts."""
        mock_source.add_prompt("p1", "New content")
        source_provider = PromptProvider(mock_source)

        # Target already has p1
        target_source = MockSource()
        target_source.add_prompt("p1", "Old content")
        target_source.save_prompt = Mock()
        target_provider = PromptProvider(target_source)

        # Import with overwrite=True
        results = bulk_import(
            source_provider, target_provider, overwrite=True
        )

        # Should import/overwrite p1
        assert results["imported"] == 1
        assert results["skipped"] == 0
        target_source.save_prompt.assert_called_once()

    def test_bulk_import_readonly_target_raises(self, mock_source):
        """Test that read-only target raises ReadOnlySourceError."""
        mock_source.add_prompt("p1", "content")
        source_provider = PromptProvider(mock_source)

        # Target is read-only (MockSource without save_prompt)
        readonly_source = MockSource()
        target_provider = PromptProvider(readonly_source)

        with pytest.raises(
            ReadOnlySourceError, match="does not support saving"
        ):
            bulk_import(source_provider, target_provider)

    def test_bulk_import_handles_errors_gracefully(self, mock_source):
        """Test that import continues despite individual errors."""
        mock_source.add_prompt("p1", "Content 1")
        mock_source.add_prompt("p2", "Content 2")
        source_provider = PromptProvider(mock_source)

        # Target that fails on p1 but works on p2
        target_source = MockSource()
        def save_with_error(name, content, **kwargs):
            if name == "p1":
                raise ValueError("Simulated error")
            target_source.add_prompt(name, content, tags=kwargs.get("tags", []))

        target_source.save_prompt = save_with_error
        target_provider = PromptProvider(target_source)

        # Run bulk import
        results = bulk_import(source_provider, target_provider)

        # Should report 1 imported, 1 error
        assert results["imported"] == 1
        assert results["errors"] == 1
        assert len(results["errors_list"]) == 1
        assert results["errors_list"][0]["name"] == "p1"
        assert "Simulated error" in results["errors_list"][0]["error"]

    def test_bulk_import_empty_source(self, mock_source):
        """Test importing from empty source."""
        source_provider = PromptProvider(mock_source)

        target_source = MockSource()
        target_source.save_prompt = Mock()
        target_provider = PromptProvider(target_source)

        results = bulk_import(source_provider, target_provider)

        assert results["imported"] == 0
        assert results["errors"] == 0


class TestVariableSetsRendering:
    """Test variable set functionality in render()."""

    def test_render_with_variable_sets_param(self, provider, mock_source):
        """Test render with explicit variable_sets parameter."""
        # Create a variable set
        mock_source.add_prompt("test", "Hello [[NAME]]")
        set_id = mock_source.create_variable_set("greeting_set", variables={"NAME": "Alice"})

        # Render using the variable set
        result = provider.render("test", variable_sets=[set_id])
        assert result == "Hello Alice"

    def test_render_variable_set_merge_order(self, provider, mock_source):
        """Test that explicit variables override set variables."""
        mock_source.add_prompt("test", "[[NAME]] is [[AGE]]")
        set_id = mock_source.create_variable_set("set1", variables={"NAME": "Alice", "AGE": 30})

        # Explicit variables should override set variables
        result = provider.render("test", variable_sets=[set_id], variables={"NAME": "Bob"})
        assert result == "Bob is 30"

    def test_render_subscribed_sets_then_additional(self, provider, mock_source):
        """Test merge priority: subscribed < additional < explicit."""
        mock_source.add_prompt("test", "[[NAME]] [[ROLE]]")

        # Create two variable sets
        set1_id = mock_source.create_variable_set("set1", variables={"NAME": "Alice", "ROLE": "user"})
        set2_id = mock_source.create_variable_set("set2", variables={"NAME": "Bob", "ROLE": "admin"})

        # Subscribe prompt to set1
        mock_source.set_active_variable_sets("test", [set1_id])

        # Additional set2 should override subscribed set1
        result = provider.render("test", variable_sets=[set2_id])
        assert result == "Bob admin"

        # Explicit variables should override everything
        result = provider.render("test", variable_sets=[set2_id], variables={"NAME": "Charlie"})
        assert result == "Charlie admin"

    def test_render_tagged_variable(self, provider, mock_source):
        """Test rendering a tagged variable."""
        mock_source.add_prompt("test", "Content: [[VALUE]]")

        # Create a variable set with a tagged variable
        set_id = mock_source.create_variable_set(
            "tagged_set",
            variables={"VALUE": {"value": "important", "tag": "emphasis"}}
        )

        # Render should wrap in XML tags
        result = provider.render("test", variable_sets=[set_id])
        assert "<emphasis>" in result
        assert "important" in result
        assert "</emphasis>" in result

    def test_render_multiple_variable_sets(self, provider, mock_source):
        """Test rendering with multiple variable sets."""
        mock_source.add_prompt("test", "[[GREETING]] [[NAME]]")

        set1_id = mock_source.create_variable_set("set1", variables={"GREETING": "Hello"})
        set2_id = mock_source.create_variable_set("set2", variables={"NAME": "Alice"})

        # Both sets should be merged
        result = provider.render("test", variable_sets=[set1_id, set2_id])
        assert result == "Hello Alice"


class TestVariableSetOperations:
    """Test granular variable set operations via provider."""

    def test_provider_add_variable_to_set(self, provider, mock_source):
        """Test adding a variable to a set via provider."""
        set_id = mock_source.create_variable_set("test_set", variables={"KEY1": "value1"})

        # Add a new variable
        provider.add_variable_to_set(set_id, "KEY2", "value2")

        # Verify both variables exist
        vs = provider.get_variable_set(set_id)
        assert vs["variables"]["KEY1"] == "value1"
        assert vs["variables"]["KEY2"] == "value2"

    def test_provider_add_variable_with_tag(self, provider, mock_source):
        """Test adding a tagged variable via provider."""
        set_id = mock_source.create_variable_set("test_set")

        # Add a tagged variable
        provider.add_variable_to_set(set_id, "ROLE", "admin", tag="persona")

        # Verify it's stored with tag
        vs = provider.get_variable_set(set_id)
        assert vs["variables"]["ROLE"]["value"] == "admin"
        assert vs["variables"]["ROLE"]["tag"] == "persona"

    def test_provider_remove_variable_from_set(self, provider, mock_source):
        """Test removing a variable from a set via provider."""
        set_id = mock_source.create_variable_set("test_set", variables={"KEY1": "value1", "KEY2": "value2"})

        # Remove a variable
        provider.remove_variable_from_set(set_id, "KEY1")

        # Verify only KEY2 remains
        vs = provider.get_variable_set(set_id)
        assert "KEY1" not in vs["variables"]
        assert "KEY2" in vs["variables"]

    def test_provider_find_variable_sets_by_name(self, provider, mock_source):
        """Test finding variable sets by name."""
        mock_source.create_variable_set("greeting_set", variables={"NAME": "Alice"})
        mock_source.create_variable_set("greeting_formal", variables={"NAME": "Mr. Smith"})
        mock_source.create_variable_set("farewell_set", variables={"NAME": "Goodbye"})

        # Exact match
        results = provider.find_variable_sets(name="greeting_set")
        assert len(results) == 1
        assert results[0]["name"] == "greeting_set"

        # Partial match
        results = provider.find_variable_sets(name="greeting", match_type="partial")
        assert len(results) == 2
        names = {r["name"] for r in results}
        assert names == {"greeting_set", "greeting_formal"}

    def test_provider_find_variable_sets_by_owner(self, provider, mock_source):
        """Test finding variable sets by owner."""
        mock_source.create_variable_set("alice_set", variables={"NAME": "Alice"}, owner="alice")
        mock_source.create_variable_set("bob_set", variables={"NAME": "Bob"}, owner="bob")
        mock_source.create_variable_set("global_set", variables={"NAME": "Everyone"}, owner=None)

        # Find by owner
        results = provider.find_variable_sets(owner="alice")
        assert len(results) == 1
        assert results[0]["name"] == "alice_set"

        # Find by owner=bob
        results = provider.find_variable_sets(owner="bob")
        assert len(results) == 1
        assert results[0]["name"] == "bob_set"
