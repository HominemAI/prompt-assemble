"""Serialization utilities for converting values to strings."""

import json
from typing import Any


def serialize_value(value: Any) -> str:
    """
    Serialize a value to a string.

    Args:
        value: Value to serialize

    Returns:
        String representation of the value

    Rules:
        - str: returned as-is
        - int, float, bool: converted via str()
        - None: converted to empty string
        - list, dict: converted via json.dumps()
        - objects with __dict__: converted via json.dumps(vars())
        - fallback: str()
    """
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    # Try to serialize as JSON if object has __dict__
    if hasattr(value, "__dict__"):
        return json.dumps(vars(value))
    # Fallback
    return str(value)


def serialize_variables(variables: dict[str, Any]) -> dict[str, str]:
    """
    Serialize all variables in a dictionary to strings.

    Args:
        variables: Dictionary of variable_name -> value

    Returns:
        Dictionary of variable_name -> string_value
    """
    return {name: serialize_value(value) for name, value in variables.items()}
