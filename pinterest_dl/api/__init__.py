"""API module for Pinterest scraping.

This module provides the main API client for interacting with Pinterest's unofficial API.
"""

import warnings

from .api import Api

__all__ = ["Api"]


def __getattr__(name: str):
    """Provide backward compatibility with deprecation warnings for renamed classes."""
    if name == "PinterestAPI":
        warnings.warn(
            "PinterestAPI has been renamed to Api and will be removed in version 1.1.0. "
            "Use: from pinterest_dl.api import Api",
            DeprecationWarning,
            stacklevel=2,
        )
        return Api

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
