"""Domain module for core data models.

This module contains the core domain models like PinterestMedia.
"""

import warnings

from .cookies import CookieJar
from .media import PinterestMedia, VideoStreamInfo

__all__ = ["PinterestMedia", "VideoStreamInfo", "CookieJar"]


def __getattr__(name: str):
    """Provide backward compatibility with deprecation warnings for renamed classes."""
    if name == "PinterestCookieJar":
        warnings.warn(
            "PinterestCookieJar has been renamed to CookieJar and will be removed in version 1.1.0. "
            "Use: from pinterest_dl.domain import CookieJar",
            DeprecationWarning,
            stacklevel=2,
        )
        return CookieJar

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
