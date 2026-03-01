"""Tests for core substitution engine."""

import pytest

from prompt_assemble.core import assemble, substitute


class TestSubstituteSimpleVariables:
    """Test simple variable substitution."""

    def test_single_variable(self):
        """Test substituting a single variable."""
        template = "The color is [[COLOR]]"
        result = substitute(template, variables={"COLOR": "red"})
        assert result == "The color is red"

    def test_multiple_variables(self):
        """Test substituting multiple variables."""
        template = "[[NAME]] is [[AGE]] years old"
        result = substitute(
            template,
            variables={"NAME": "Alice", "AGE": "30"},
        )
        assert result == "Alice is 30 years old"

    def test_repeated_variable(self):
        """Test using the same variable multiple times."""
        template = "[[ITEM]] and [[ITEM]]"
        result = substitute(template, variables={"ITEM": "apple"})
        assert result == "apple and apple"


class TestSubstitutePromptComponents:
    """Test PROMPT: sigil substitution."""

    def test_single_component(self):
        """Test substituting a single component."""
        template = "Instructions: [[PROMPT: instructions]]"
        result = substitute(
            template,
            components={"instructions": "Be helpful"},
        )
        assert result == "Instructions: Be helpful"

    def test_multiple_components(self):
        """Test substituting multiple components."""
        template = "[[PROMPT: intro]] [[PROMPT: task]]"
        result = substitute(
            template,
            components={
                "intro": "Hello",
                "task": "Please help",
            },
        )
        assert result == "Hello Please help"


class TestRecursiveSubstitution:
    """Test recursive substitution."""

    def test_variable_in_component(self):
        """Test variable inside substituted component."""
        template = "[[PROMPT: greeting]]"
        result = substitute(
            template,
            variables={"NAME": "Bob"},
            components={"greeting": "Hello [[NAME]]"},
            recursive=True,
        )
        assert result == "Hello Bob"

    def test_nested_variables(self):
        """Test deeply nested substitution."""
        template = "[[VAR1]]"
        result = substitute(
            template,
            variables={
                "VAR1": "[[VAR2]]",
                "VAR2": "deep",
            },
            recursive=True,
        )
        assert result == "deep"

    def test_recursive_disabled(self):
        """Test that recursive=False stops after one pass."""
        template = "[[VAR1]]"
        result = substitute(
            template,
            variables={"VAR1": "[[VAR2]]"},
            recursive=False,
        )
        assert result == "[[VAR2]]"


class TestComments:
    """Test comment stripping."""

    def test_single_line_comment(self):
        """Test single-line comment removal."""
        template = "Hello #! This is a comment\nWorld"
        result = substitute(template)
        assert result == "Hello \nWorld"

    def test_multiline_comment(self):
        """Test multiline comment removal."""
        template = "Start <!-- This is\n     a comment --> End"
        result = substitute(template)
        assert result == "Start  End"

    def test_comments_with_variables(self):
        """Test that comments are stripped before variable substitution."""
        template = "Value: [[VAR]] #! Comment with [[UNUSED]]"
        result = substitute(template, variables={"VAR": "test"})
        assert result == "Value: test "


class TestErrors:
    """Test error handling."""

    def test_undefined_variable(self):
        """Test error on undefined variable."""
        template = "[[UNDEFINED]]"
        with pytest.raises(ValueError, match="Undefined variable"):
            substitute(template)

    def test_undefined_component(self):
        """Test error on undefined component."""
        template = "[[PROMPT: undefined]]"
        with pytest.raises(ValueError, match="Undefined component"):
            substitute(template)

    def test_max_depth_exceeded(self):
        """Test error when recursion exceeds max depth."""
        template = "[[VAR]]"
        variables = {"VAR": "[[VAR]]"}  # Infinite loop
        with pytest.raises(RecursionError, match="max depth"):
            substitute(template, variables=variables, max_depth=5)


class TestAssemble:
    """Test high-level assemble function."""

    def test_basic_assembly(self):
        """Test basic prompt assembly."""
        template = "You are a [[ROLE]]. [[PROMPT: task]]"
        result = assemble(
            template,
            variables={"ROLE": "teacher"},
            components={"task": "Help the student learn."},
        )
        assert result == "You are a teacher. Help the student learn."

    def test_xml_template(self):
        """Test assembly with loose XML template."""
        template = """<system>
[[PROMPT: system-prompt]]
</system>

<task>
[[PROMPT: task-instructions]]
</task>"""
        result = assemble(
            template,
            components={
                "system-prompt": "You are helpful",
                "task-instructions": "Answer the question",
            },
        )
        assert "<system>" in result
        assert "You are helpful" in result
        assert "Answer the question" in result

    def test_output_format_text(self):
        """Test text output format."""
        template = "[[MESSAGE]]"
        result = assemble(
            template,
            variables={"MESSAGE": "Hello"},
            output_format="text",
        )
        assert result == "Hello"
        assert isinstance(result, str)
