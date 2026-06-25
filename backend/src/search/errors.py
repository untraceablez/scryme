"""Search-specific exceptions."""


class SearchError(ValueError):
    """Raised for malformed queries or unknown filters. The message is user-facing."""
