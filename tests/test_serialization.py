"""Tests for serialization utilities."""

import json

import pytest

from prompt_assemble.serialization import serialize_value, serialize_variables


class TestSerializeValue:
    """Test serialize_value function."""

    def test_string_passthrough(self):
        """Test that strings are returned as-is."""
        assert serialize_value("hello") == "hello"
        assert serialize_value("") == ""
        assert serialize_value("with [[sigils]]") == "with [[sigils]]"

    def test_integer(self):
        """Test integer serialization."""
        assert serialize_value(42) == "42"
        assert serialize_value(0) == "0"
        assert serialize_value(-100) == "-100"

    def test_float(self):
        """Test float serialization."""
        assert serialize_value(3.14) == "3.14"
        assert serialize_value(0.0) == "0.0"

    def test_boolean(self):
        """Test boolean serialization."""
        assert serialize_value(True) == "True"
        assert serialize_value(False) == "False"

    def test_none(self):
        """Test None serialization."""
        assert serialize_value(None) == ""

    def test_list(self):
        """Test list serialization."""
        result = serialize_value([1, 2, 3])
        assert result == json.dumps([1, 2, 3])

    def test_dict(self):
        """Test dict serialization."""
        result = serialize_value({"key": "value"})
        assert result == json.dumps({"key": "value"})

    def test_object_with_dict(self):
        """Test serialization of objects with __dict__."""

        class MyObj:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        obj = MyObj(1, 2)
        result = serialize_value(obj)
        parsed = json.loads(result)
        assert parsed["x"] == 1
        assert parsed["y"] == 2

    def test_object_with_dict_serialization(self):
        """Test serialization of generic objects with __dict__."""

        class Person:
            def __init__(self, name, age):
                self.name = name
                self.age = age

        person = Person("Alice", 30)
        result = serialize_value(person)
        parsed = json.loads(result)
        assert parsed["name"] == "Alice"
        assert parsed["age"] == 30


class TestSerializeVariables:
    """Test serialize_variables function."""

    def test_empty_dict(self):
        """Test serializing empty dictionary."""
        result = serialize_variables({})
        assert result == {}

    def test_mixed_types(self):
        """Test serializing mixed types."""
        variables = {
            "name": "Alice",
            "age": 30,
            "score": 95.5,
            "active": True,
            "tags": ["a", "b"],
        }
        result = serialize_variables(variables)

        assert result["name"] == "Alice"
        assert result["age"] == "30"
        assert result["score"] == "95.5"
        assert result["active"] == "True"
        assert result["tags"] == json.dumps(["a", "b"])

    def test_preserves_all_keys(self):
        """Test that all keys are preserved."""
        variables = {"a": 1, "b": 2, "c": 3}
        result = serialize_variables(variables)
        assert set(result.keys()) == {"a", "b", "c"}
