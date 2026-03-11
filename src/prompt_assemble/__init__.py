"""
prompt-assemble: Lightweight prompt assembly with sigil-based substitution.

A simple, logic-free way to build dynamic prompts using variable and component substitution.
"""

__version__ = "0.3.8"
__author__ = "Adam Sanchez"
__email__ = "agentpython@proton.me"
__license__ = "MIT"

# Backward-compatible low-level API (unchanged)
from .core import assemble, substitute

# New high-level API
from .provider import PromptProvider, bulk_import
from .sources import (
    PromptSource,
    FileSystemSource,
    DatabaseSource,
    create_database_source_from_env,
)
from .exceptions import (
    PromptAssembleError,
    PromptNotFoundError,
    TagResolutionError,
    SourceConnectionError,
    SubstitutionError,
    ReadOnlySourceError,
)
from .registry import RegistryEvent, RegistryListener
from .sources.base import SourceListener

__all__ = [
    # Low-level API
    "assemble",
    "substitute",
    # High-level API
    "PromptProvider",
    "bulk_import",
    # Sources
    "PromptSource",
    "FileSystemSource",
    "DatabaseSource",
    "create_database_source_from_env",
    # Exceptions
    "PromptAssembleError",
    "PromptNotFoundError",
    "TagResolutionError",
    "SourceConnectionError",
    "SubstitutionError",
    "ReadOnlySourceError",
    # Listeners
    "RegistryEvent",
    "RegistryListener",
    "SourceListener",
]
