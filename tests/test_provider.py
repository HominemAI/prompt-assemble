"""Tests for PromptProvider."""

from unittest.mock import Mock

import pytest

from prompt_assemble import PromptProvider
from prompt_assemble.exceptions import PromptNotFoundError
from prompt_assemble.sources.base import PromptSource


class MockSource(PromptSource):
    """Mock prompt source for testing."""

    def __init__(self):
        """Initialize mock source with test data."""
        self.prompts = {}
        self.tags = {}  # prompt_name -> list of tags

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

    def list(self) -> list[str]:
        """List all prompt names."""
        return list(self.prompts.keys())

    def refresh(self) -> None:
        """Refresh (no-op for mock)."""
        pass

    def add_prompt(self, name: str, content: str, tags: list = None):
        """Add a prompt to the mock source."""
        self.prompts[name] = content
        self.tags[name] = tags or []


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
        """Test rendering with missing variable."""
        mock_source.add_prompt("test", "[[NAME]]")
        with pytest.raises(ValueError, match="Undefined variable"):
            provider.render("test")


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
