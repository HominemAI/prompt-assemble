"""
Flask REST API server for Prompt Assemble.

Provides REST API endpoints for:
- Listing prompts
- CRUD operations on prompts
- Tag management
- Revision history
- Export functionality
- Variable sets management
"""

__all__ = ["create_app", "run_server"]


def __getattr__(name):
    """Lazy import to avoid import warnings when running server.py as __main__"""
    if name == "create_app":
        from .server import create_app
        return create_app
    elif name == "run_server":
        from .server import run_server
        return run_server
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
