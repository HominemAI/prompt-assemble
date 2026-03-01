"""Custom exception hierarchy for prompt-assemble."""


class PromptAssembleError(Exception):
    """Base exception for all prompt-assemble errors."""

    pass


class PromptNotFoundError(PromptAssembleError):
    """Raised when a prompt cannot be found in the source."""

    pass


class TagResolutionError(PromptAssembleError):
    """Raised when tag resolution fails."""

    pass


class SourceConnectionError(PromptAssembleError):
    """Raised when a source cannot be connected or initialized."""

    pass


class SubstitutionError(PromptAssembleError):
    """Raised when substitution fails."""

    pass
