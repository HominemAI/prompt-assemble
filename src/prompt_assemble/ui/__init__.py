"""
Prompt management UI module.

This module provides an environment-toggled React-based interface for comprehensive
prompt management, exploration, and editing.

Environment Variable:
    PROMPT_ASSEMBLE_UI: Set to "true" to enable the UI server

Usage:
    export PROMPT_ASSEMBLE_UI=true
    python -m prompt_assemble.ui
"""

from .server import create_app, run_server

__all__ = ["create_app", "run_server"]
