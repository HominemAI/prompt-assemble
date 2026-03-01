"""
Core substitution engine for prompt assembly.

Supports sigil-based substitution:
- [[VAR_NAME]]: Simple variable substitution
- [[PROMPT: name]]: Inject named prompt components
- [[PROMPT_TAG: tag1, tag2]]: Inject prompts matching all tags
- [[PROMPT_TAG:N: tag1, tag2]]: Inject first N prompts matching all tags
"""

import logging
import re
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


TagResolver = Callable[[list[str]], list[str]]  # tags -> prompt names


def _parse_prompt_tag_sigil(content: str) -> Tuple[Optional[int], list[str]]:
    """
    Parse PROMPT_TAG sigil content.

    Args:
        content: Content after "PROMPT_TAG" (e.g., "tag1, tag2" or "3: tag1, tag2")

    Returns:
        Tuple of (limit, tags) where limit is None or int >= 1

    Examples:
        "tag1, tag2" -> (None, ['tag1', 'tag2'])
        "3: tag1, tag2" -> (3, ['tag1', 'tag2'])
        "0: tag1" -> (0, ['tag1'])  # Will log warning
    """
    content = content.strip()

    # Check if there's a limit specifier (N:)
    if ":" in content:
        limit_str, tags_str = content.split(":", 1)
        try:
            limit = int(limit_str.strip())
        except ValueError:
            raise ValueError(f"Invalid PROMPT_TAG limit: {limit_str}")

        if limit == 0:
            logger.warning("PROMPT_TAG with limit 0 will return empty string")

        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
    else:
        limit = None
        tags = [tag.strip() for tag in content.split(",") if tag.strip()]

    return limit, tags


def _strip_comments(text: str) -> str:
    """
    Strip single-line and multiline comments from text.

    Single-line: #! comment
    Multiline: <!-- comment -->
    """
    # Remove single-line comments
    text = re.sub(r'#!.*?$', '', text, flags=re.MULTILINE)

    # Remove multiline comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    return text


def substitute(
    text: str,
    variables: Optional[Dict[str, Any]] = None,
    components: Optional[Dict[str, str]] = None,
    recursive: bool = True,
    max_depth: int = 10,
    component_resolver: Optional[Callable[[str], str]] = None,
    tag_resolver: Optional[TagResolver] = None,
) -> str:
    """
    Perform sigil-based substitution on text.

    Args:
        text: Template text containing sigils
        variables: Dictionary of VAR_NAME -> value (all values converted to str)
        components: Dictionary of component_name -> component text (backward compat)
        recursive: Whether to resolve nested sigils in substituted values
        max_depth: Maximum recursion depth to prevent infinite loops
        component_resolver: Function(name: str) -> str to resolve [[PROMPT: name]] sigils.
                           Supersedes components dict when provided.
        tag_resolver: Function(tags: list[str]) -> list[str] to resolve [[PROMPT_TAG: ...]] sigils.
                     Returns list of prompt names matching ALL tags.

    Returns:
        Text with all sigils replaced

    Raises:
        ValueError: If sigil references undefined variable or component
        SubstitutionError: If PROMPT_TAG sigil encountered without tag_resolver
        RecursionError: If substitution depth exceeds max_depth
    """
    # Import here to avoid circular dependency
    from .exceptions import SubstitutionError

    if variables is None:
        variables = {}
    if components is None:
        components = {}

    # Strip comments before processing
    text = _strip_comments(text)

    def replace_sigil(match: re.Match) -> str:
        """Replace a single sigil match."""
        full_match = match.group(0)
        content = match.group(1).strip()

        # Check if it's a PROMPT_TAG: sigil
        if content.startswith("PROMPT_TAG:"):
            if tag_resolver is None:
                raise SubstitutionError(
                    "PROMPT_TAG sigil encountered but no tag_resolver provided"
                )

            tags_content = content[11:].strip()  # Remove "PROMPT_TAG:"
            limit, tags = _parse_prompt_tag_sigil(tags_content)

            if not tags:
                raise ValueError("PROMPT_TAG must specify at least one tag")

            # Get matching prompts
            matching_names = tag_resolver(tags)

            if limit is not None:
                matching_names = matching_names[:limit]

            # Fetch content for each matching prompt
            results = []
            for name in matching_names:
                try:
                    # Assume component_resolver can fetch by prompt name
                    if component_resolver:
                        content_text = component_resolver(name)
                    else:
                        content_text = components.get(name, "")
                    results.append(content_text)
                except Exception as e:
                    raise ValueError(f"Failed to fetch prompt '{name}': {e}")

            # Join with double newline
            return "\n\n".join(results)

        # Check if it's a PROMPT: sigil
        if content.startswith("PROMPT:"):
            component_name = content[7:].strip()
            if component_resolver:
                try:
                    return component_resolver(component_name)
                except Exception as e:
                    raise ValueError(f"Undefined component: {component_name}: {e}")
            else:
                if component_name not in components:
                    raise ValueError(f"Undefined component: {component_name}")
                return str(components[component_name])

        # Simple variable substitution
        if content not in variables:
            raise ValueError(f"Undefined variable: {content}")
        return str(variables[content])

    # Perform substitution with optional recursion
    current_text = text
    for depth in range(max_depth):
        new_text = re.sub(r'\[\[([^\[\]]+)\]\]', replace_sigil, current_text)

        # If no changes, check if we're done or in an infinite loop
        if new_text == current_text:
            # If still has sigils, we're in an infinite loop
            if re.search(r'\[\[([^\[\]]+)\]\]', new_text):
                raise RecursionError(f"Substitution recursion exceeded max depth of {max_depth}")
            break

        current_text = new_text

        # If not recursive, stop after first pass
        if not recursive:
            break
    else:
        # Max depth exceeded
        raise RecursionError(f"Substitution recursion exceeded max depth of {max_depth}")

    return current_text


def assemble(
    template: str,
    variables: Optional[Dict[str, Any]] = None,
    components: Optional[Dict[str, str]] = None,
    output_format: str = "text",
) -> Any:
    """
    Assemble a prompt from a template and substitutions.

    Args:
        template: Template text (loose XML, JSON, or plain text)
        variables: Dictionary of VAR_NAME -> value
        components: Dictionary of component_name -> component text
        output_format: Output format - "text", "json", or "template"
                      (For now, only "text" is fully supported)

    Returns:
        Assembled prompt (str for text format, dict for JSON format)
    """
    result = substitute(
        template,
        variables=variables,
        components=components,
    )

    if output_format == "text":
        return result
    elif output_format == "json":
        # Parse and return as structured data
        # This is a placeholder for future JSON parsing
        return result
    elif output_format == "template":
        # Return template format
        return result
    else:
        raise ValueError(f"Unknown output format: {output_format}")
