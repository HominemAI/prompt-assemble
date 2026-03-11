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
        """Test undefined variable is logged and replaced with empty string."""
        template = "Hello [[UNDEFINED]] world"
        result = substitute(template)
        assert result == "Hello  world"

    def test_undefined_variable_only(self):
        """Test undefined variable as sole content returns empty string."""
        template = "[[UNDEFINED]]"
        result = substitute(template)
        assert result == ""

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


class TestPromptTagSigil:
    """Test PROMPT_TAG: sigil substitution."""

    def test_prompt_tag_basic(self):
        """Test basic PROMPT_TAG: substitution with single result."""
        template = "[[PROMPT_TAG: expert]]"

        def tag_resolver(tags):
            assert tags == ["expert"]
            return ["prompt1"]

        result = substitute(
            template,
            components={"prompt1": "I am an expert"},
            tag_resolver=tag_resolver,
        )
        assert result == "I am an expert"

    def test_prompt_tag_multiple_results(self):
        """Test PROMPT_TAG: with multiple matching results."""
        template = "Results: [[PROMPT_TAG: helpful]]"

        def tag_resolver(tags):
            assert tags == ["helpful"]
            return ["p1", "p2", "p3"]

        result = substitute(
            template,
            components={
                "p1": "First",
                "p2": "Second",
                "p3": "Third",
            },
            tag_resolver=tag_resolver,
        )
        assert result == "Results: First\n\nSecond\n\nThird"

    def test_prompt_tag_with_limit(self):
        """Test PROMPT_TAG:N: with limit."""
        template = "Top 2: [[PROMPT_TAG:2: recent]]"

        def tag_resolver(tags):
            assert tags == ["recent"]
            return ["old", "newer", "newest"]

        result = substitute(
            template,
            components={
                "old": "Old content",
                "newer": "Newer content",
                "newest": "Newest content",
            },
            tag_resolver=tag_resolver,
        )
        assert result == "Top 2: Old content\n\nNewer content"

    def test_prompt_tag_limit_zero(self):
        """Test PROMPT_TAG:0: returns empty string."""
        template = "Empty: [[PROMPT_TAG:0: tag]]"

        def tag_resolver(tags):
            return ["p1"]

        result = substitute(
            template,
            components={"p1": "Content"},
            tag_resolver=tag_resolver,
        )
        assert result == "Empty: "

    def test_prompt_tag_no_resolver(self):
        """Test that PROMPT_TAG without tag_resolver raises SubstitutionError."""
        from prompt_assemble.exceptions import SubstitutionError

        template = "[[PROMPT_TAG: tag]]"
        with pytest.raises(SubstitutionError, match="tag_resolver"):
            substitute(template)

    def test_prompt_tag_and_intersection(self):
        """Test PROMPT_TAG: with multiple tags (AND logic)."""
        template = "[[PROMPT_TAG: persona, technical]]"

        def tag_resolver(tags):
            # Should receive both tags
            assert set(tags) == {"persona", "technical"}
            return ["prompt_with_both"]

        result = substitute(
            template,
            components={"prompt_with_both": "Expert persona"},
            tag_resolver=tag_resolver,
        )
        assert result == "Expert persona"

    def test_prompt_tag_no_matches(self):
        """Test PROMPT_TAG: with no matching results."""
        template = "No matches: [[PROMPT_TAG: nonexistent]]"

        def tag_resolver(tags):
            return []

        result = substitute(
            template,
            tag_resolver=tag_resolver,
        )
        assert result == "No matches: "

    def test_prompt_tag_result_recursive(self):
        """Test that PROMPT_TAG results are recursively substituted."""
        template = "[[PROMPT_TAG: greeting]]"

        def tag_resolver(tags):
            return ["greeting1"]

        result = substitute(
            template,
            variables={"NAME": "Alice"},
            components={"greeting1": "Hello [[NAME]]"},
            tag_resolver=tag_resolver,
            recursive=True,
        )
        assert result == "Hello Alice"

    def test_deeply_nested_all_sigils(self):
        """Test deeply nested substitution across all sigil types."""
        template = "[[PROMPT_TAG: intro]]"

        def tag_resolver(tags):
            return ["intro_prompt"]

        def component_resolver(name):
            if name == "intro_prompt":
                return "Hi [[NAME]], [[PROMPT: task]]"
            if name == "task":
                return "Do [[ACTION]]"
            raise ValueError(f"Unknown: {name}")

        result = substitute(
            template,
            variables={"NAME": "Bob", "ACTION": "stuff"},
            component_resolver=component_resolver,
            tag_resolver=tag_resolver,
            recursive=True,
        )
        assert result == "Hi Bob, Do stuff"

    def test_circular_prompt_exceeds_depth(self):
        """Test that self-referential prompts raise RecursionError."""
        template = "[[PROMPT: self_ref]]"

        def component_resolver(name):
            if name == "self_ref":
                return "[[PROMPT: self_ref]]"
            raise ValueError(f"Unknown: {name}")

        with pytest.raises(RecursionError, match="max depth"):
            substitute(
                template,
                component_resolver=component_resolver,
                max_depth=5,
            )

    def test_prompt_tag_invalid_limit(self):
        """Test that invalid limit raises ValueError."""
        template = "[[PROMPT_TAG:abc: tag]]"

        with pytest.raises(ValueError, match="Invalid PROMPT_TAG limit"):
            substitute(template, tag_resolver=lambda t: [])

    def test_prompt_tag_limit_greater_than_available(self):
        """Test PROMPT_TAG:N: when N > available results."""
        template = "[[PROMPT_TAG:10: tag]]"

        def tag_resolver(tags):
            return ["p1", "p2"]

        result = substitute(
            template,
            components={"p1": "First", "p2": "Second"},
            tag_resolver=tag_resolver,
        )
        # Should return both even though limit is higher
        assert result == "First\n\nSecond"
